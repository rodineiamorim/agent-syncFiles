import os
import time
import hashlib
import json
import requests
import ftplib
import socket

class Config:
    def __init__(self, config_path="config.json"):
        with open(config_path, 'r') as f:
            data = json.load(f)
            self.WATCH_DIR = data.get("WATCH_DIRECTORY", "./sync_folder")
            self.BASE_URL = data.get("BASE_URL")
            self.HEADERS = {"Authorization": f"Bearer {data.get('TOKEN')}"}
            self.INTERVAL = data.get("CHECK_INTERVAL", 5) # Intervalo de varredura
            self.MAX_SIZE = data.get("MAX_FILE_SIZE_MB", 50) * 1024 * 1024
            
            # Tipo de envio: POST, FTP ou BOTH
            self.TYPE = (data.get("TYPE", "POST") or "POST").upper()

            # Configurações FTP (opcionais)
            self.FTP_HOST = data.get("FTP_HOST")
            self.FTP_PORT = data.get("FTP_PORT", 21)
            self.FTP_USER = data.get("FTP_USER")
            self.FTP_PASS = data.get("FTP_PASS")
            self.FTP_PATH = data.get("FTP_PATH", "/")

class LocalDatabase:
    def __init__(self, db_path="sync_db.json"):
        self.db_path = db_path
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r') as f:
                    return json.load(f)
            except: return {}
        return {}

    def save(self):
        with open(self.db_path, 'w') as f:
            json.dump(self.data, f, indent=4)

def get_hash(path):
    hasher = hashlib.md5()
    try:
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except: return None

class PollingAgent:
    def __init__(self, config, db):
        self.config = config
        self.db = db

    def upload_via_post(self, path, fname):
        try:
            with open(path, 'rb') as f:
                files = {'file': (fname, f)}
                r = requests.post(f"{self.config.BASE_URL}?action=upload",
                                  headers=self.config.HEADERS, files=files)
                if r.status_code == 200:
                    return r.json().get('id')
                else:
                    print(f"❌ Falha POST {r.status_code} em {fname}: {r.text}")
        except Exception as e:
            print(f"❌ Erro upload POST {fname}: {e}")
        return None

    def upload_via_ftp(self, path, fname):
        cfg = self.config
        if not cfg.FTP_HOST:
            print("⚠️ FTP não configurado (FTP_HOST ausente). Ignorando FTP.")
            return None
        try:
            ftp = ftplib.FTP()
            ftp.connect(cfg.FTP_HOST, int(cfg.FTP_PORT), timeout=10)
            ftp.login(cfg.FTP_USER or 'anonymous', cfg.FTP_PASS or '')

            remote_dir = cfg.FTP_PATH or '/'
            try:
                ftp.cwd(remote_dir)
            except Exception:
                # cria diretórios recursivamente
                parts = [p for p in remote_dir.split('/') if p]
                cur = ''
                for p in parts:
                    cur = f"{cur}/{p}"
                    try:
                        ftp.mkd(cur)
                    except Exception:
                        pass
                ftp.cwd(remote_dir)

            with open(path, 'rb') as f:
                ftp.storbinary(f'STOR {fname}', f)

            ftp.quit()
            return os.path.join(remote_dir, fname)
        except (ftplib.all_errors, socket.error) as e:
            print(f"❌ Erro FTP {fname}: {e}")
            return None

    def scan_and_sync(self):
        """Varre a pasta em busca de novos, alterados ou removidos."""
        current_files = {}

        # 1. Varredura de Arquivos Existentes
        for root, dirs, files in os.walk(self.config.WATCH_DIR):
            for name in files:
                if "~" in name or name.endswith(".tmp"): continue
                
                full_path = os.path.join(root, name)
                current_files[full_path] = True
                
                file_hash = get_hash(full_path)
                cached = self.db.data.get(full_path)

                # Se não está no banco ou o hash mudou -> Upload
                if not cached or cached['hash'] != file_hash:
                    self.upload(full_path, file_hash)

        # 2. Detecção de Exclusões (O que está no DB mas não no disco)
        to_delete = [path for path in self.db.data if path not in current_files]
        for path in to_delete:
            self.delete_remote(path)

    def upload(self, path, file_hash):
        if os.path.getsize(path) > self.config.MAX_SIZE: return
        
        fname = os.path.basename(path)
        print(f"📤 Sincronizando: {fname}...")

        ids = {}

        if 'POST' in self.config.TYPE:
            post_id = self.upload_via_post(path, fname)
            if post_id:
                ids['post'] = post_id

        if 'FTP' in self.config.TYPE:
            ftp_path = self.upload_via_ftp(path, fname)
            if ftp_path:
                ids['ftp'] = ftp_path

        if ids:
            stored_id = ids if len(ids) > 1 else (ids.get('post') or ids.get('ftp'))
            self.db.data[path] = {"id": stored_id, "hash": file_hash}
            self.db.save()
            print(f"✅ {fname} sincronizado. IDs: {stored_id}")
        else:
            print(f"❌ Falha ao sincronizar {fname} (nenhum método obteve sucesso)")

    def delete_remote(self, path):
        info = self.db.data.get(path)
        if info:
            print(f"🗑️ Removendo do servidor: {os.path.basename(path)}")
            try:
                stored = info.get('id')

                # compatibilidade: stored pode ser string (post id) ou dict {post,ftp}
                post_id = None
                ftp_path = None
                if isinstance(stored, dict):
                    post_id = stored.get('post')
                    ftp_path = stored.get('ftp')
                else:
                    post_id = stored

                deleted_any = False
                if post_id and 'POST' in self.config.TYPE:
                    payload = {"id": post_id, "type": "file", "permanent": False}
                    r = requests.post(f"{self.config.BASE_URL}?action=delete",
                                      headers=self.config.HEADERS, json=payload)
                    if r.status_code == 200:
                        deleted_any = True

                if ftp_path and 'FTP' in self.config.TYPE:
                    try:
                        ftp = ftplib.FTP()
                        ftp.connect(self.config.FTP_HOST, int(self.config.FTP_PORT), timeout=10)
                        ftp.login(self.config.FTP_USER or 'anonymous', self.config.FTP_PASS or '')
                        remote_dir, remote_fname = os.path.split(ftp_path)
                        if remote_dir:
                            try:
                                ftp.cwd(remote_dir)
                            except Exception:
                                pass
                        ftp.delete(remote_fname)
                        ftp.quit()
                        deleted_any = True
                    except Exception as e:
                        print(f"❌ Erro ao deletar via FTP: {e}")

                if deleted_any:
                    del self.db.data[path]
                    self.db.save()
            except Exception as e:
                print(f"❌ Erro ao deletar: {e}")

if __name__ == "__main__":
    cfg = Config()
    db = LocalDatabase()
    agent = PollingAgent(cfg, db)

    print(f"🚀 Agente Polling iniciado (Intervalo: {cfg.INTERVAL}s)")
    print(f"📂 Monitorando: {cfg.WATCH_DIR}")

    try:
        while True:
            agent.scan_and_sync()
            time.sleep(cfg.INTERVAL)
    except KeyboardInterrupt:
        print("\n👋 Agente encerrado.")