import os
import time
import hashlib
import json
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- CONFIGURAÇÕES ---
WATCH_DIRECTORY = "./meus_documentos"
DB_FILE = "sync_db.json"
BASE_URL = "https://ylhuinvbvqwleknpwljs.supabase.co/functions/v1/sync"
TOKEN = "SEU_USER_TOKEN_AQUI"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

class LocalDatabase:
    """Gerencia o mapeamento local de arquivos, hashes e IDs do servidor."""
    def __init__(self, db_path):
        self.db_path = db_path
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.db_path):
            with open(self.db_path, 'r') as f:
                return json.load(f)
        return {}

    def save(self):
        with open(self.db_path, 'w') as f:
            json.dump(self.data, f, indent=4)

    def update_file(self, path, file_id, file_hash):
        self.data[path] = {"id": file_id, "hash": file_hash, "last_sync": time.time()}
        self.save()

    def get_info(self, path):
        return self.data.get(path)

    def remove_file(self, path):
        if path in self.data:
            del self.data[path]
            self.save()

def get_hash(path):
    hasher = hashlib.md5()
    try:
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except: return None

class SyncAgent(FileSystemEventHandler):
    def __init__(self):
        self.db = LocalDatabase(DB_FILE)
        print(f"🗄️ Banco de dados local carregado: {len(self.db.data)} arquivos rastreados.")

    def on_created(self, event):
        if not event.is_directory: self.upload(event.src_path)

    def on_modified(self, event):
        if not event.is_directory: self.upload(event.src_path)

    def on_deleted(self, event):
        info = self.db.get_info(event.src_path)
        if info:
            print(f"🗑️ Detectada exclusão local. Removendo no servidor: {os.path.basename(event.src_path)}")
            try:
                # payload conforme sua especificação de POST delete
                payload = {"id": info['id'], "type": "file", "permanent": False}
                r = requests.post(f"{BASE_URL}?action=delete", headers=HEADERS, json=payload)
                if r.status_code == 200:
                    self.db.remove_file(event.src_path)
                    print("✅ Removido do servidor e do banco local.")
            except Exception as e:
                print(f"❌ Erro ao deletar no servidor: {e}")

    def upload(self, file_path):
        # Ignora arquivos temporários (comum em editores de texto)
        if "~" in file_path or file_path.endswith(".tmp"): return

        fname = os.path.basename(file_path)
        new_hash = get_hash(file_path)
        cached_info = self.db.get_info(file_path)

        if cached_info and cached_info['hash'] == new_hash:
            return # Arquivo idêntico ao do servidor, ignora.

        print(f"📤 Uploading: {fname}...")
        try:
            # Verifica limite de 50MB antes de tentar
            if os.path.getsize(file_path) > 50 * 1024 * 1024:
                print(f"⚠️ Arquivo {fname} excede o limite de 50MB.")
                return

            with open(file_path, 'rb') as f:
                files = {'file': (fname, f)}
                r = requests.post(f"{BASE_URL}?action=upload", headers=HEADERS, files=files)
                
                if r.status_code == 200:
                    server_data = r.json()
                    # Salva no JSON o ID retornado pelo seu Supabase e o novo Hash
                    self.db.update_file(file_path, server_data.get('id'), new_hash)
                    print(f"✅ Sincronizado: {fname}")
                else:
                    print(f"⚠️ Servidor recusou {fname}: {r.status_code} - {r.text}")
        except Exception as e:
            print(f"💥 Erro de conexão no upload: {e}")

if __name__ == "__main__":
    if not os.path.exists(WATCH_DIRECTORY): os.makedirs(WATCH_DIRECTORY)
    
    event_handler = SyncAgent()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIRECTORY, recursive=True)
    observer.start()
    
    print(f"🚀 Agente Ativo | Monitorando: {WATCH_DIRECTORY}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()