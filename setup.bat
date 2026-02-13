@echo off
echo [1/4] Criando pastas do projeto...
if not exist "meus_documentos" mkdir meus_documentos

echo [2/4] Instalando dependencias (requests)...
pip install requests

echo [3/4] Gerando arquivo de configuracao padrao (config.json)...
if not exist "config.json" (
    echo {> config.json
    echo     "WATCH_DIRECTORY": "./meus_documentos",>> config.json
    echo     "CHECK_INTERVAL": 10,>> config.json
    echo     "MAX_FILE_SIZE_MB": 50,>> config.json
    echo     "SYNC_DESTINATIONS": {>> config.json
    echo         "api": true,>> config.json
    echo         "ftp": false>> config.json
    echo     },>> config.json
    echo     "API_CONFIG": {>> config.json
    echo         "URL": "https://ylhuinvbvqwleknpwljs.supabase.co/functions/v1/sync",>> config.json
    echo         "TOKEN": "SEU_TOKEN_AQUI">> config.json
    echo     },>> config.json
    echo     "FTP_CONFIG": {>> config.json
    echo         "HOST": "ftp.exemplo.com",>> config.json
    echo         "USER": "usuario",>> config.json
    echo         "PASS": "senha",>> config.json
    echo         "REMOTE_DIR": "/">> config.json
    echo     }>> config.json
    echo }>> config.json
    echo ✅ config.json criado.
) else (
    echo ⚠️ config.json ja existe. Pulando...
)

echo [4/4] Inicializando banco de dados local...
if not exist "sync_db.json" echo {}> sync_db.json

echo.
echo ======================================================
echo Instalação concluída! 
echo 1. Edite o 'config.json' com suas credenciais.
echo 2. Execute o agente com: python agent.py
echo ======================================================
pause