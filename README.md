# agent-syncFiles
Agente para sincronizar arquivos (cliente em python3)

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
        "TOKEN": "<token bearer de autenticacao>"
    },
    "FTP_CONFIG": {
        "HOST": "<host do servidor ftp>,
        "USER": "<usuario>",
        "PASS": "<senha>",
        "REMOTE_DIR": "<pasta de destino, ex: /backup>"
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

📄 Licença
Distribuído sob a licença MIT. Veja LICENSE para mais informações.

Desenvolvido por  🚀
