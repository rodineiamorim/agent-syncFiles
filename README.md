# agent-syncFiles
Agente para sincronizar arquivos (cliente em python3)

# 📂 Agent-SyncFiles

**Agent-SyncFiles** é um agente de sincronização de arquivos leve, resiliente e multiplataforma. Ele permite monitorar pastas locais e espelhar arquivos automaticamente para múltiplos destinos, como servidores **FTP** e **APIs REST (Supabase/Edge Functions)**, de forma simultânea ou seletiva.

---

## ✨ Funcionalidades

- 🔄 **Sincronização Híbrida:** Envie arquivos para uma API REST, um servidor FTP ou ambos ao mesmo tempo.
- 🚀 **Polling Inteligente:** Sistema de varredura periódica que detecta mudanças sem depender de eventos instáveis do Sistema Operacional.
- 🛡️ **Deduplicação por Hash:** Utiliza MD5 para garantir que apenas arquivos que sofreram alteração real de conteúdo sejam enviados, economizando banda.
- 📦 **Gerenciamento de Exclusões:** Detecta quando um arquivo é deletado localmente e replica a ação no servidor remoto.
- ⚙️ **Configuração Dinâmica:** Todo o comportamento (Tokens, Hosts, Intervalos) é gerenciado via arquivo JSON externo.
- 🗄️ **Persistência de Estado:** Mantém um banco de dados local (`sync_db.json`) para rastrear IDs remotos e versões de arquivos.

---

## 🚀 Como Começar

### Pré-requisitos
- Python 3.8 ou superior
- Pip (gerenciador de pacotes)

### Instalação Rápida

1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/rodineiamorim/agent-syncFiles.git](https://github.com/rodineiamorim/agent-syncFiles.git)
   cd agent-syncFiles


# Execute o script de setup:

No Windows: setup.bat

No Linux/Ubuntu: chmod +x setup.sh && ./setup.sh

Configure suas credenciais:
Edite o arquivo config.json gerado na raiz do projeto com suas informações de API ou FTP.

{
    "WATCH_DIRECTORY": "<pasta que deseja sincronizar>",
    "CHECK_INTERVAL": <segundos>,
    "MAX_FILE_SIZE_MB": <tamanho em mega, ex: 50 = 50MB>,
    "SYNC_DESTINATIONS": {
        "api": true,
        "ftp": true
    },
    "API_CONFIG": {
        "URL": "<url da sua storage>",
        "TOKEN": "<token bearer de autenticacao>",
         "RECURSIVE_RM": true ou false <exclusao recursiva>
    },
    "FTP_CONFIG": {
        "HOST": "<host do servidor ftp>,
        "USER": "<usuario>",
        "PASS": "<senha>",
        "REMOTE_DIR": "<pasta de destino, ex: /backup>",
        "USE_TLS": false,
        "RECURSIVE_RM": true ou false <exclusao recursiva>
    }
}

Inicie o agente:

🛠️ Configuração (config.json)

🏗️ Arquitetura do Projeto
O projeto utiliza o padrão Strategy para os transportes, facilitando a expansão para novos destinos no futuro:

agent.py: Núcleo do sistema e lógica de polling.

LocalDatabase: Gerencia o mapeamento de arquivos e hashes.

APITransport: Implementação para comunicação via REST/Multipart-form.

FTPTransport: Implementação para comunicação via protocolo FTP clássico.

🚧 Roadmap de Evolução
[ ] Suporte para Amazon S3 / Google Cloud Storage.

[ ] Criptografia ponta-a-ponta (E2EE) antes do upload.

[ ] Sincronização bidirecional (baixar mudanças do servidor).

[ ] Interface gráfica (Tray Icon) para monitoramento visual.

🤝 Contribuições
Contribuições são o que fazem a comunidade open source um lugar incrível para aprender, inspirar e criar.

Faça um Fork do projeto.

Crie uma Branch para sua funcionalidade (git checkout -b feature/NovaFuncionalidade).

Faça o Commit de suas alterações (git commit -m 'Add: Nova Funcionalidade').

Envie para a Branch (git push origin feature/NovaFuncionalidade).

Abra um Pull Request.


* Diagnostico

Como usar o Diagnóstico
Sempre que mudar o Token ou a senha do FTP, rode: python check_health.py.

Ele vai te dizer exatamente onde está o erro (se é no login do FTP, na URL da API ou no Token expirado).


* Diagrama

                [ LOCAL MACHINE ]                    [ REMOTE DESTINATIONS ]
              +-----------------+                  +------------------------+
              |  WATCH FOLDER   |                  |    API (Supabase)      |
              |  (Files/Dirs)   |                  |  [mkdir] [upload] [del]|
              +--------+--------+                  +-----------^------------+
                       |                                       |
                       v           (HTTPS / REST)              |
              +-----------------+------------------------------+
              |   SYNC AGENT    |
              |  (Python Core)  <------[ config.json ]
              +--------+--------+
                       |           (FTP Protocol)              |
           [sync_db.json]      |                               |
           (Hashes / IDs)      +-------------------------------+
                       |                                       |
                       v                               +-------v--------+
              +-----------------+                      |  FTP SERVER    |
              |  LOCAL TRACKING |                      | [mkd] [stor]   |
              +-----------------+                      +----------------+

📄 Licença
Distribuído sob a licença MIT. Veja LICENSE para mais informações.

Desenvolvido por  Rodinei Amorim / Rudi H Amorim
