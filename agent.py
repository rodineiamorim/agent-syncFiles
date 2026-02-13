import os
import time
import hashlib
import json
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class Config:
    """Carrega as configurações do arquivo config.json."""
    def __init__(self, config_path="config.json"):
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configure o arquivo {config_path} antes de iniciar.")
        
        with open(config_path, 'r') as f:
            data = json.load(f)
            self.WATCH_DIR = data.get("WATCH_DIRECTORY", "./sync_folder")
            self.BASE_URL = data.get("BASE_URL")
            self.HEADERS = {"Authorization": f"Bearer {data.get('TOKEN')}"}
            self.CHECK_INTERVAL = data.get("CHECK_INTERVAL", 1)
            self.MAX_SIZE = data.get("MAX_FILE_SIZE_MB", 50) * 1024 * 1024

class LocalDatabase:
    """Gerencia o histórico de IDs e Hashes para evitar duplicatas."""
    def __init__(self, db_path="sync_db.json"):
        self.db_path = db_path
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def save(self):
        with open(self.db_path, 'w') as f:
            json.dump(self.data, f, indent=4)

    def update(self, path, file_id, file_hash):
        self.data[path] = {"id": file_id, "hash": file_hash}
        self.save()

    def get(self, path):
        return self.data.get(path)

    def remove(self, path):
        if path in self.data:
            del self.data[path]
            self.save()

def calculate_hash(path):
    """Gera hash MD5 de forma eficiente em termos de memória."""
    hasher = hashlib.md5()
    try:
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except:
        return None

class SyncAgent(FileSystemEventHandler):
    def __init__(self, config, db):
        self.config = config
        self.db = db

    def on_modified(self, event):
        if not event.is_directory: self.sync_file(event.src_path)

    def on_created(self, event):
        if not event.is_directory: self.sync_file(event.src_path)

    def on_deleted(self, event):
        info = self.db.get(event.src_path)
        if info:
            print(f"🗑️ Removendo no servidor: {os.path.basename(event.src_path)}")
            try:
                payload = {"id": info['id'], "type": "file", "permanent": False}
                r = requests.post(f"{self.config.BASE_URL}?action=delete", 
                                  headers=self.config.HEADERS, json=payload)
                if r.status_code == 200:
                    self.db.remove(event.src_path)
            except Exception as e:
                print(f"❌ Erro ao deletar: {e}")

    def sync_file(self, file_path):
        if "~" in file_path or file_path.endswith(".tmp"): return
        
        fname = os.path.basename(file_path)
        current_hash = calculate_hash(file_path)
        cached = self.db.get(file_path)

        if cached and cached['hash'] == current_hash:
            return

        # Validação de tamanho
        if os.path.getsize(file_path) > self.config.MAX_SIZE:
            print(f"⚠️ {fname} ignorado (maior que 50MB)")
            return

        print(f"📤 Sincronizando: {fname}...")
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (fname, f)}
                r = requests.post(f"{self.config.BASE_URL}?action=upload", 
                                  headers=self.config.HEADERS, files=files)
                
                if r.status_code == 200:
                    file_id = r.json().get('id')
                    self.db.update(file_path, file_id, current_hash)
                    print(f"✅ {fname} atualizado.")
                else:
                    print(f"⚠️ Erro {r.status_code} em {fname}")
        except Exception as e:
            print(f"💥 Falha de conexão: {e}")

if __name__ == "__main__":
    # 1. Carrega Configs e DB
    cfg = Config()
    database = LocalDatabase()

    if not os.path.exists(cfg.WATCH_DIR):
        os.makedirs(cfg.WATCH_DIR)

    # 2. Inicia Monitoramento
    handler = SyncAgent(cfg, database)
    observer = Observer()
    observer.schedule(handler, cfg.WATCH_DIR, recursive=True)
    observer.start()

    print(f"🚀 Agente Online | Pasta: {cfg.WATCH_DIR}")
    try:
        while True:
            time.sleep(cfg.CHECK_INTERVAL)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()