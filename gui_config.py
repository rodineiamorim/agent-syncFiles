import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

class ConfigApp:
  def __init__(self, root):
    self.root = root
    self.root.title("Configurações - Agent SyncFiles")
    self.root.geometry("600x700")
    self.file_path = 'config.json'
    
    # Carregar dados iniciais
    self.config_data = self.load_config()
    
    # Criar abas (Tabs)
    self.tab_control = ttk.Notebook(root)
    
    self.tab_geral = ttk.Frame(self.tab_control)
    self.tab_api = ttk.Frame(self.tab_control)
    self.tab_ftp = ttk.Frame(self.tab_control)
    self.tab_speedpro = ttk.Frame(self.tab_control)
    
    self.tab_control.add(self.tab_geral, text='Geral / Destinos')
    self.tab_control.add(self.tab_api, text='API')
    self.tab_control.add(self.tab_ftp, text='FTP')
    self.tab_control.add(self.tab_speedpro, text='SpeedPro')
    self.tab_control.pack(expand=1, fill="both", padx=10, pady=10)
    
    self.setup_geral()
    self.setup_api()
    self.setup_ftp()
    self.setup_speedpro()
    
    # Botão Salvar
    btn_save = tk.Button(root, text="SALVAR CONFIGURAÇÃO", command=self.save_to_json, bg="#4CAF50", fg="white", font=('Arial', 10, 'bold'))
    btn_save.pack(pady=10, fill="x", padx=20)

  def load_config(self):
    if os.path.exists(self.file_path):
      with open(self.file_path, 'r', encoding='utf-8') as f:
        return json.load(f)
    return {}

  def setup_geral(self):
    # Campos Principais
    frame = ttk.LabelFrame(self.tab_geral, text=" Configurações de Monitoramento ")
    frame.pack(fill="x", padx=10, pady=10)
    
    self.watch_dir = self.create_input(frame, "Diretório de Origem:", self.config_data.get("WATCH_DIRECTORY", ""))
    self.check_interval = self.create_input(frame, "Intervalo (Minutos):", self.config_data.get("CHECK_INTERVAL", 5))
    self.max_size = self.create_input(frame, "Tam. Máximo Arquivo (MB):", self.config_data.get("MAX_FILE_SIZE_MB", 100))
    
    # Checkboxes de Destino
    dest_frame = ttk.LabelFrame(self.tab_geral, text=" Destinos Ativos ")
    dest_frame.pack(fill="x", padx=10, pady=10)
    
    sync_dest = self.config_data.get("SYNC_DESTINATIONS", {})
    self.sync_api = tk.BooleanVar(value=sync_dest.get("api", False))
    self.sync_ftp = tk.BooleanVar(value=sync_dest.get("ftp", False))
    self.sync_speedpro = tk.BooleanVar(value=sync_dest.get("speedpro", False))
    
    tk.Checkbutton(dest_frame, text="Habilitar API", variable=self.sync_api).pack(anchor="w", padx=5)
    tk.Checkbutton(dest_frame, text="Habilitar FTP", variable=self.sync_ftp).pack(anchor="w", padx=5)
    tk.Checkbutton(dest_frame, text="Habilitar SpeedPro", variable=self.sync_speedpro).pack(anchor="w", padx=5)

  def setup_api(self):
    api_cfg = self.config_data.get("API_CONFIG", {})
    self.api_url = self.create_input(self.tab_api, "URL da API:", api_cfg.get("URL", ""))
    self.api_token = self.create_input(self.tab_api, "Token:", api_cfg.get("TOKEN", ""))
    self.api_recursive = tk.BooleanVar(value=api_cfg.get("RECURSIVE_RM", False))
    tk.Checkbutton(self.tab_api, text="Leitura Recursiva", variable=self.api_recursive).pack(pady=5)

  def setup_ftp(self):
    ftp_cfg = self.config_data.get("FTP_CONFIG", {})
    self.ftp_host = self.create_input(self.tab_ftp, "Host/IP:", ftp_cfg.get("HOST", ""))
    self.ftp_user = self.create_input(self.tab_ftp, "Usuário:", ftp_cfg.get("USER", ""))
    self.ftp_pass = self.create_input(self.tab_ftp, "Senha:", ftp_cfg.get("PASS", ""), show="*")
    self.ftp_dir = self.create_input(self.tab_ftp, "Diretório Remoto:", ftp_cfg.get("REMOTE_DIR", "/"))
    self.ftp_tls = tk.BooleanVar(value=ftp_cfg.get("USE_TLS", False))
    self.ftp_recursive = tk.BooleanVar(value=ftp_cfg.get("RECURSIVE_RM", False))
    tk.Checkbutton(self.tab_ftp, text="Usar TLS", variable=self.ftp_tls).pack()
    tk.Checkbutton(self.tab_ftp, text="Leitura Recursiva", variable=self.ftp_recursive).pack()

  def setup_speedpro(self):
    sp_cfg = self.config_data.get("SPEEDPRO_CONFIG", {})
    self.sp_base = self.create_input(self.tab_speedpro, "Base URL:", sp_cfg.get("BASE_URL", ""))
    self.sp_email = self.create_input(self.tab_speedpro, "Email:", sp_cfg.get("EMAIL", ""))
    self.sp_pass = self.create_input(self.tab_speedpro, "Senha:", sp_cfg.get("PASSWORD", ""), show="*")
    self.sp_key = self.create_input(self.tab_speedpro, "API Key:", sp_cfg.get("APIKEY", ""))
    self.sp_recursive = tk.BooleanVar(value=sp_cfg.get("RECURSIVE_RM", False))
    tk.Checkbutton(self.tab_speedpro, text="Leitura Recursiva", variable=self.sp_recursive).pack()

  def create_input(self, parent, label_text, default_value, show=None):
    frame = ttk.Frame(parent)
    frame.pack(fill="x", padx=10, pady=5)
    ttk.Label(frame, text=label_text).pack(anchor="w")
    entry = ttk.Entry(frame, show=show)
    entry.insert(0, str(default_value))
    entry.pack(fill="x")
    return entry

  def save_to_json(self):
    try:
      new_config = {
        "WATCH_DIRECTORY": self.watch_dir.get(),
        "CHECK_INTERVAL": int(self.check_interval.get()),
        "MAX_FILE_SIZE_MB": int(self.max_size.get()),
        "SYNC_DESTINATIONS": {
          "api": self.sync_api.get(),
          "ftp": self.sync_ftp.get(),
          "speedpro": self.sync_speedpro.get()
        },
        "API_CONFIG": {
          "URL": self.api_url.get(),
          "TOKEN": self.api_token.get(),
          "RECURSIVE_RM": self.api_recursive.get()
        },
        "FTP_CONFIG": {
          "HOST": self.ftp_host.get(),
          "USER": self.ftp_user.get(),
          "PASS": self.ftp_pass.get(),
          "REMOTE_DIR": self.ftp_dir.get(),
          "USE_TLS": self.ftp_tls.get(),
          "RECURSIVE_RM": self.ftp_recursive.get()
        },
        "SPEEDPRO_CONFIG": {
          "BASE_URL": self.sp_base.get(),
          "AUTH_URL": "/auth/v1/token?grant_type=password",
          "MANAGER_URL": "/functions/v1/filesync",
          "UPLOAD_URL": "/storage/v1/object/user-files",
          "REGISTERFILE_URL": "/rest/v1/files",
          "EMAIL": self.sp_email.get(),
          "PASSWORD": self.sp_pass.get(),
          "APIKEY": self.sp_key.get(),
          "RECURSIVE_RM": self.sp_recursive.get()
        }
      }
      
      with open(self.file_path, 'w', encoding='utf-8') as f:
        json.dump(new_config, f, indent=2)
      
      messagebox.showinfo("Sucesso", "Configuração salva com sucesso!")
    except Exception as e:
      messagebox.showerror("Erro", f"Erro ao salvar: {str(e)}")

if __name__ == "__main__":
  root = tk.Tk()
  app = ConfigApp(root)
  root.mainloop()