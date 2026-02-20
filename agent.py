import os
import time
import hashlib
import json
import requests
import uuid
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

    def mkdir(self, folder_name, parent_id=None):
        """Cria uma pasta na API e retorna o ID dela."""
        payload = {"name": folder_name, "parent_id": parent_id}
        try:
            r = requests.post(f"{self.url}?action=mkdir", headers=self.headers, json=payload)
            if r.status_code in [200, 201]:
                return r.json().get('id')
        except Exception as e:
            print(f"❌ Erro API mkdir: {e}")
        return None

    def upload(self, local_path, filename, folder_id=None):
        with open(local_path, 'rb') as f:
            data = {'folder_id': folder_id} if folder_id else {}
            r = requests.post(f"{self.url}?action=upload", 
                              headers=self.headers, 
                              files={'file': (filename, f)},
                              data=data)
            return r.json().get('id') if r.status_code == 200 else None
        
    def delete(self, item_id, is_folder=False):
        """Remove arquivo ou pasta na API."""
        item_type = "folder" if is_folder else "file"
        payload = {"id": item_id, "type": item_type, "permanent": False}
        try:
            r = requests.post(f"{self.url}?action=delete", headers=self.headers, json=payload)
            return r.status_code == 200
        except Exception as e:
            print(f"❌ Erro API delete: {e}")
            return False

class FTPTransport:
    def __init__(self, config):
        self.cfg = config

    def _get_conn(self):
        ftp = FTP(self.cfg['HOST'])
        ftp.login(self.cfg['USER'], self.cfg['PASS'])
        return ftp

    def mkdir(self, remote_path):
        """Cria pastas recursivamente no FTP."""
        ftp = self._get_conn()
        parts = remote_path.split(os.sep)
        current_path = self.cfg.get('REMOTE_DIR', '/')
        ftp.cwd(current_path)
        
        for part in parts:
            if not part: continue
            try:
                ftp.cwd(part)
            except:
                ftp.mkd(part)
                ftp.cwd(part)
        ftp.quit()

    def upload(self, local_path, filename, remote_subfolder=""):
        try:
            ftp = self._get_conn()
            target_dir = os.path.join(self.cfg.get('REMOTE_DIR', '/'), remote_subfolder)
            
            # Garante que a pasta de destino existe
            try: ftp.cwd(target_dir)
            except: self.mkdir(remote_subfolder); ftp.cwd(target_dir)
            
            with open(local_path, 'rb') as f:
                ftp.storbinary(f'STOR {filename}', f)
            ftp.quit()
            return filename
        except Exception as e:
            print(f"❌ Erro FTP Upload: {e}")
            return None
        
    def delete(self, remote_path, is_folder=False):
        """Remove arquivo ou pasta no FTP."""
        try:
            ftp = self._get_conn()
            if is_folder:
                # Nota: FTP padrão só deleta pastas vazias via rmd. 
                # Para pastas com conteúdo, teríamos que limpar tudo dentro.
                # Aqui removemos a pasta alvo.
                ftp.rmd(remote_path)
            else:
                ftp.delete(remote_path)
            ftp.quit()
            return True
        except Exception as e:
            print(f"⚠️ Aviso FTP delete: {e}")
            return False

class SpeedProTransport:
    def __init__(self, config):
        self.base_url = config['BASE_URL']
        self.auth_url = self.base_url + config['AUTH_URL']
        self.manager_url = self.base_url + config['MANAGER_URL']
        self.upload_url = self.base_url + config['UPLOAD_URL']
        self.registerfile_url = self.base_url + config['REGISTERFILE_URL']
        self.email = config['EMAIL']
        self.password = config['PASSWORD']
        self.api_key = config['APIKEY']
        self.token = None
        self.user_id = None
        self._authenticate()

    def _authenticate(self):
        """Realiza o login e obtém o access_token."""
        print("🔑 SpeedPro: Autenticando...")
        payload = {
            "email": self.email,
            "password": self.password
        }
        
        if self.api_key:
            headers = {"apikey": self.api_key} 
        else:
            headers = {}
        
        try:
            r = requests.post(self.auth_url, json=payload, headers=headers)
            if r.status_code == 200:
                self.token = r.json().get('access_token')
                self.user_id = r.json().get('user').get('id')
                print("✅ SpeedPro: Autenticado com sucesso!")
            else:
                print(f"❌ SpeedPro Auth Erro: {r.status_code} - {r.text}")
        except Exception as e:
            print(f"❌ SpeedPro Auth Falha: {e}")

    @property
    def headers(self):
        """Retorna os headers sempre atualizados com o token."""
        return {
            "Authorization": f"Bearer {self.token}",
            "apikey": self.api_key,
            "Content-Type" : "application/json"
        }

    def mkdir(self, name, parent_id=None):
        print(f"criando diretorio {name}")
        payload = {"name": name, "parent_id": parent_id}
        r = requests.post(f"{self.base_url}?action=mkdir", headers=self.headers, json=payload)
        return r.json().get('id') if r.status_code in [200, 201] else None

    def upload(self, local_path, filename, folder_id=None):
        with open(local_path, 'rb') as f:
            payload = f.read()
            filename_uuid = uuid.uuid4()
            extensao = os.path.splitext(filename)
            r = requests.post(f"{self.upload_url}/{self.user_id}/{filename_uuid}.{extensao}", 
                              headers=self.headers, 
                              data=payload)
            if r.json().get('Id'):
                print("arquivo enviado, agora registrando na tabela de arquivos")
                
                url = self.registerfile_url

                # Definição dos headers conforme a especificação
                headers = self.headers
                headers['Prefer'] = "return=representation"

                # Dados do registro a ser criado
                payload = {
                    "name": filename,
                    "file_type": "document",
                    "size_bytes": len(payload),
                    "storage_path": f"{self.user_id}/{filename_uuid}.pdf",
                    "folder_id": None, 
                    "user_id": f"{self.user_id}"
                    }

                try:
                    # Realizando a chamada POST enviando o payload como JSON
                    response = requests.post(url, headers=headers, json=payload)

                    # Validação do status da resposta
                    if response.ok:
                        print("Registro criado com sucesso na tabela 'files'!")
                        print(f"Dados retornados: {response.json()}")
                    else:
                        print(f"Falha ao criar registro. Status: {response.status_code}")
                        print(f"Erro: {response.text}")

                except requests.exceptions.RequestException as e:
                    print(f"Erro de conexão ou na requisição: {e}")                
                
            return r.json().get('Id') if r.status_code == 200 else None

    def delete(self, item_id, is_folder=False):
        payload = {"id": item_id, "type": "folder" if is_folder else "file", "permanent": False}
        r = requests.post(f"{self.base_url}?action=delete", headers=self.headers, json=payload)
        return r.status_code == 200
    
            
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
        if self.config.DESTINATIONS.get("speedpro"):
            self.transports["speedpro"] = SpeedProTransport(self.config.data['SPEEDPRO_CONFIG'])            

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
        for root, dirs, files in os.walk(self.config.WATCH_DIR):
            # 1. Sincronizar Pastas Primeiro
            relative_path = os.path.relpath(root, self.config.WATCH_DIR)
            
            if relative_path != ".":
                # Lógica para garantir que a pasta existe no DB/Servidor
                if root not in self.db:
                    print(f"📂 Criando pasta remota: {relative_path}")
                    ids = {}
                    if "api" in self.transports:
                        # Para APIs complexas, você precisaria do ID da pasta pai. 
                        # Aqui simplificamos criando a pasta pelo nome.
                        res_id = self.transports["api"].mkdir(os.path.basename(root))
                        if res_id: ids["api"] = res_id
                    
                    if "ftp" in self.transports:
                        self.transports["ftp"].mkdir(relative_path)
                        ids["ftp"] = relative_path
                    
                    self.db[root] = {"type": "folder", "ids": ids, "hash": "dir"}
                    self._save_db()

            # 2. Sincronizar Arquivos
            for name in files:
                if "~" in name or name.endswith(".tmp"): continue
                if name == "sync_db.json": continue  # Ignora o arquivo de banco de dados
                path = os.path.join(root, name)
                current_paths[path] = True
                
                f_hash = self.get_hash(path)
                cached = self.db.get(path, {})

                if cached.get('hash') != f_hash:
                    print(f"🔄 Sincronizando arquivo: {name}")
                    
                    # Recupera o ID da pasta onde o arquivo está (para a API)
                    parent_folder_info = self.db.get(root, {})
                    folder_id_api = parent_folder_info.get('ids', {}).get('api')
                    
                    ids = {}
                    if "api" in self.transports:
                        res_id = self.transports["api"].upload(path, name, folder_id_api)
                        if res_id: ids["api"] = res_id
                    
                    if "ftp" in self.transports:
                        res_id = self.transports["ftp"].upload(path, name, relative_path)
                        if res_id: ids["ftp"] = res_id

                    if "speedpro" in self.transports:
                        res_id = self.transports["speedpro"].upload(path, name, relative_path)
                        if res_id: ids["speedpro"] = res_id
                        
                    if ids:
                        self.db[path] = {"type": "file", "hash": f_hash, "ids": ids}
                        self._save_db()
                        
if __name__ == "__main__":
    agent = SyncAgent()
    # Checa se o diretório de monitoramento existe
    if not os.path.exists(agent.config.WATCH_DIR):
        print(f"❌ Diretório de monitoramento não encontrado: {agent.config.WATCH_DIR}. Encerrando.")
        exit(1)
    print(f"🚀 Agente Híbrido Iniciado (Destinos: {list(agent.transports.keys())})")
    while True:
        try:
            agent.sync()
        except Exception as e:
            print(f"⚠️ Erro no ciclo: {e}")
        time.sleep(agent.config.INTERVAL)