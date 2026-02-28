import tkinter as tk
from tkinter import messagebox, scrolledtext
import subprocess
import threading
import os
import sys

class AgentControlApp:
  def __init__(self, root):
    self.root = root
    self.root.title("Controle do Agent SyncFiles")
    self.root.geometry("600x450")
    self.process = None
    
    # Estilização básica
    self.setup_ui()

  def setup_ui(self):
    # Frame de Botões
    btn_frame = tk.Frame(self.root)
    btn_frame.pack(pady=20)

    self.btn_start = tk.Button(btn_frame, text="INICIAR AGENTE", command=self.start_agent, bg="#4CAF50", fg="white", width=15)
    self.btn_start.grid(row=0, column=0, padx=5)

    self.btn_stop = tk.Button(btn_frame, text="PARAR AGENTE", command=self.stop_agent, bg="#f44336", fg="white", width=15, state="disabled")
    self.btn_stop.grid(row=0, column=1, padx=5)

    self.btn_restart = tk.Button(btn_frame, text="REINICIAR", command=self.restart_agent, bg="#2196F3", fg="white", width=15, state="disabled")
    self.btn_restart.grid(row=0, column=2, padx=5)

    # Log de Execução
    tk.Label(self.root, text="Logs do Sistema:").pack(anchor="w", padx=20)
    self.log_area = scrolledtext.ScrolledText(self.root, height=15, padx=10, pady=10, bg="#1e1e1e", fg="#d4d4d4")
    self.log_area.pack(fill="both", padx=20, pady=10)

  def log(self, message):
    self.log_area.insert(tk.END, message + "\n")
    self.log_area.see(tk.END)

  def start_agent(self):
    if self.process is None:
      self.log("[SISTEMA] Iniciando o agent.py...")
      try:
        # Executa o script em um subprocesso
        self.process = subprocess.Popen(
          [sys.executable, "agent.py"],
          stdout=subprocess.PIPE,
          stderr=subprocess.STDOUT,
          text=True,
          bufsize=1
        )
        
        # Thread para ler o output sem travar a interface
        threading.Thread(target=self.read_output, daemon=True).start()
        
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.btn_restart.config(state="normal")
      except Exception as e:
        messagebox.showerror("Erro", f"Falha ao iniciar: {e}")

  def read_output(self):
    for line in iter(self.process.stdout.readline, ""):
      self.log(f"[{self.get_time()}] {line.strip()}")
    
    self.process.stdout.close()
    return_code = self.process.wait()
    self.log(f"[SISTEMA] Agente finalizado (Code: {return_code})")
    self.process = None
    self.root.after(0, self.reset_buttons)

  def stop_agent(self):
    if self.process:
      self.log("[SISTEMA] Parando o agente...")
      self.process.terminate()
      self.process = None
      self.reset_buttons()

  def restart_agent(self):
    self.log("[SISTEMA] Reiniciando...")
    self.stop_agent()
    # Pequeno delay para garantir o fechamento antes de reabrir
    self.root.after(1000, self.start_agent)

  def reset_buttons(self):
    self.btn_start.config(state="normal")
    self.btn_stop.config(state="disabled")
    self.btn_restart.config(state="disabled")

  def get_time(self):
    from datetime import datetime
    return datetime.now().strftime("%H:%M:%S")

if __name__ == "__main__":
  root = tk.Tk()
  app = AgentControlApp(root)
  
  # Garante que o processo feche se fechar a janela
  def on_closing():
    if app.process:
      app.process.terminate()
    root.destroy()
    
  root.protocol("WM_DELETE_WINDOW", on_closing)
  root.mainloop()