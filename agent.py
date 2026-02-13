import os
import time
import hashlib
import json
import requests
from ftplib import FTP
from io import BytesIO

class Config:
    def __init__(self, path="config.json"):
        with open(path, 'r') as f:
            self.data = json.load(f)
        self.WATCH_DIR = self.data.get("WATCH_DIRECTORY", "./sync")
        self.INTERVAL = self.data.get("CHECK_INTERVAL", 5)
        self.MAX_SIZE = self.data.get("MAX_FILE_SIZE_MB", 50) * 1024 * 1024
        self.DESTINATIONS = self.data.get("SYNC_DESTINATIONS", {})

# --- TRANSPORTES ---

class APITransport:
    def __init__(self, config):
        self.url = config['URL']
        self.headers = {"Authorization": f"Bearer {config['TOKEN']}"}

    def upload(self, local_path, filename):
        with open(local_path, 'rb') as f:
            r = requests.post(f"{self.url}?action=upload", headers=self.headers, files={'file': (filename, f)})
            return r.json().get('id') if r.status_code == 200 else None

    def delete(self, file_id):
        payload = {"id": file_id, "type": "file", "permanent": False}
        requests.post(f"{self.url}?action=delete", headers=self.headers, json=payload)

class FTPTransport:
    def __init__(self, config):
        self.cfg = config

    def _get_conn(self):
        ftp = FTP(self.cfg['HOST'])
        ftp.login(self.cfg['USER'], self.cfg['PASS'])
        if self.cfg['REMOTE_DIR']:
            ftp.cwd(self.cfg['REMOTE_DIR'])
        return ftp

    def upload(self, local_path, filename):
        try:
            ftp = self._get_conn()
            with open(local_path, 'rb') as f:
                ftp.storbinary(f'STOR {filename}', f)
            ftp.quit()
            return filename # FTP não tem UUID, usamos o nome como ID
        except Exception as e:
            print(f"❌ Erro FTP: {e}")
            return None

    def delete(self, filename):
        try:
            ftp = self._get_conn()
            ftp.delete(filename)
            ftp.quit()
        except: pass

# --- CORE DO AGENTE ---

class SyncAgent:
    def __init__(self):
        self.config = Config()
        self.db_path = "sync_db.json"
        self.db = self._load_db()
        
        # Inicializa transportes ativos
        self.transports = {}
        if self.config.DESTINATIONS.get("api"):
            self.transports["api"] = APITransport(self.config.data['API_CONFIG'])
        if self.config.DESTINATIONS.get("ftp"):
            self.transports["ftp"] = FTPTransport(self.config.data['FTP_CONFIG'])

    def _load_db(self):
        if os.path.exists(self.db_path):
            with open(self.db_path, 'r') as f: return json.load(f)
        return {}

    def _save_db(self):
        with open(self.db_path, 'w') as f: json.dump(self.db, f, indent=4)

    def get_hash(self, path):
        hasher = hashlib.md5()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""): hasher.update(chunk)
        return hasher.hexdigest()

    def sync(self):
        current_paths = {}
        for root, _, files in os.walk(self.config.WATCH_DIR):
            for name in files:
                if "~" in name or name.endswith(".tmp"): continue
                path = os.path.join(root, name)
                current_paths[path] = True
                
                f_hash = self.get_hash(path)
                cached = self.db.get(path, {})

                if cached.get('hash') != f_hash:
                    print(f"🔄 Sincronizando: {name}")
                    ids = {}
                    # Envia para todos os transportes ativos
                    for t_name, transport in self.transports.items():
                        res_id = transport.upload(path, name)
                        if res_id: ids[t_name] = res_id
                    
                    if ids:
                        self.db[path] = {"hash": f_hash, "ids": ids}
                        self._save_db()

        # Check exclusões
        for path in list(self.db.keys()):
            if path not in current_paths:
                print(f"🗑️ Deletando remoto: {os.path.basename(path)}")
                cached = self.db[path]
                for t_name, transport in self.transports.items():
                    remote_id = cached.get('ids', {}).get(t_name)
                    if remote_id: transport.delete(remote_id)
                del self.db[path]
                self._save_db()

if __name__ == "__main__":
    agent = SyncAgent()
    print(f"🚀 Agente Híbrido Iniciado (Destinos: {list(agent.transports.keys())})")
    while True:
        try:
            agent.sync()
        except Exception as e:
            print(f"⚠️ Erro no ciclo: {e}")
        time.sleep(agent.config.INTERVAL)