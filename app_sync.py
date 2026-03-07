import tkinter as tk
from tkinter import messagebox, scrolledtext
import subprocess
import threading
import json
import os
import sys
from pystray import Icon as TrayIcon, Menu, MenuItem
from PIL import Image, ImageDraw

class AppSync:
  def __init__(self, root):
    self.root = root
    self.root.title("Agent SyncFiles - Controle")
    self.root.geometry("700x550")
    self.process = None
    self.config_file = 'config.json'
    
    # Configuração do fechamento da janela (esconder no tray)
    self.root.protocol('WM_DELETE_WINDOW', self.hide_window)
    
    self.setup_ui()
    self.create_tray_icon()
    
    # Autostart: Se houver config, inicia automático
    self.check_autostart()

  def setup_ui(self):
    btn_frame = tk.Frame(self.root)
    btn_frame.pack(pady=20)

    self.btn_start = tk.Button(btn_frame, text="INICIAR AGENTE", command=self.start_agent, bg="#4CAF50", fg="white", width=15)
    self.btn_start.grid(row=0, column=0, padx=5)

    self.btn_stop = tk.Button(btn_frame, text="PARAR AGENTE", command=self.stop_agent, bg="#f44336", fg="white", width=15, state="disabled")
    self.btn_stop.grid(row=0, column=1, padx=5)

    self.btn_restart = tk.Button(btn_frame, text="REINICIAR", command=self.restart_agent, bg="#2196F3", fg="white", width=15, state="disabled")
    self.btn_restart.grid(row=0, column=2, padx=5)

    tk.Label(self.root, text="Monitoramento de Sincronia:").pack(anchor="w", padx=20)
    self.log_area = scrolledtext.ScrolledText(self.root, height=20, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 10))
    self.log_area.pack(fill="both", padx=20, pady=10)

  def log(self, message):
    if message.strip():
      self.log_area.insert(tk.END, f"[{self.get_time()}] {message}\n")
      self.log_area.see(tk.END)

  def get_time(self):
    from datetime import datetime
    return datetime.now().strftime("%H:%M:%S")

  def check_autostart(self):
    # Verifica se o arquivo existe e tem conteúdo válido
    if os.path.exists(self.config_file):
      try:
        with open(self.config_file, 'r', encoding='utf-8') as f:
          config = json.load(f)
          # Se o diretório de monitoramento estiver definido, inicia
          if config.get("WATCH_DIRECTORY") and config["WATCH_DIRECTORY"] != "":
            self.log("Sistema: Configuração detectada. Iniciando automaticamente...")
            self.start_agent()
          else:
            self.log("Sistema: Aguardando configuração manual (WATCH_DIRECTORY vazio).")
      except Exception as e:
        self.log(f"Erro ao ler config para autostart: {e}")
    else:
      self.log("Sistema: Arquivo config.json não encontrado. Configure antes de iniciar.")

  def start_agent(self):
    if self.process is None:
      try:
        # Definimos o ambiente para UTF-8 explicitamente para o processo filho
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        self.process = subprocess.Popen(
          [sys.executable, "-u", "agent.py"], # O "-u" força o modo UNBUFFERED
          stdout=subprocess.PIPE,
          stderr=subprocess.STDOUT,
          text=True,
          bufsize=1,
          encoding='utf-8',
          errors='replace',
          env=env # Passa o ambiente configurado
        )
        threading.Thread(target=self.read_output, daemon=True).start()
        self.update_buttons("running")
      except Exception as e:
        messagebox.showerror("Erro", f"Falha ao iniciar agent.py: {e}")

  def read_output(self):
    for line in iter(self.process.stdout.readline, ""):
      self.root.after(0, self.log, line.strip())
    
    self.process.stdout.close()
    self.process.wait()
    self.process = None
    self.root.after(0, lambda: self.update_buttons("stopped"))
    self.root.after(0, self.log, "Sistema: Agente interrompido.")

  def stop_agent(self):
    if self.process:
      self.log("Sistema: Solicitando parada do agente...")
      self.process.terminate()
      self.update_buttons("stopped")

  def restart_agent(self):
    self.stop_agent()
    self.root.after(1200, self.start_agent)

  def update_buttons(self, state):
    if state == "running":
      self.btn_start.config(state="disabled")
      self.btn_stop.config(state="normal")
      self.btn_restart.config(state="normal")
    else:
      self.btn_start.config(state="normal")
      self.btn_stop.config(state="disabled")
      self.btn_restart.config(state="disabled")

  # --- Lógica do Tray Icon ---
  def create_image(self):
    # Gera um ícone verde básico (64x64)
    image = Image.new('RGB', (64, 64), (46, 125, 50))
    d = ImageDraw.Draw(image)
    # Desenha um "S" estilizado ou apenas um detalhe branco
    d.rectangle([10, 10, 54, 54], outline=(255, 255, 255), width=4)
    return image

  def hide_window(self):
    self.root.withdraw()

  def show_window(self):
    self.root.deiconify()

  def exit_app(self):
    if self.process:
      self.process.terminate()
    self.tray_icon.stop()
    self.root.quit()
    os._exit(0) # Força o encerramento de todas as threads no Ubuntu

  def create_tray_icon(self):
    menu = Menu(
      MenuItem('Abrir Painel', self.show_window, default=True),
      MenuItem('Sair Completamente', self.exit_app)
    )
    self.tray_icon = TrayIcon("AgentSync", self.create_image(), "Agent SyncFiles", menu)
    threading.Thread(target=self.tray_icon.run, daemon=True).start()

if __name__ == "__main__":
  root = tk.Tk()
  app = AppSync(root)
  root.mainloop()