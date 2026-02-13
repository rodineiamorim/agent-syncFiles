#!/bin/bash

echo "🚀 Iniciando setup do Agent-SyncFiles"

# 1. Pastas
mkdir -p meus_documentos

# 2. Python Deps
echo "📦 Instalando dependências..."
pip install requests

# 3. Config JSON
if [ ! -f config.json ]; then
cat <<EOF > config.json
{
    "WATCH_DIRECTORY": "./meus_documentos",
    "CHECK_INTERVAL": 10,
    "MAX_FILE_SIZE_MB": 50,
    "SYNC_DESTINATIONS": {
        "api": true,
        "ftp": false
    },
    "API_CONFIG": {
        "URL": "https://ylhuinvbvqwleknpwljs.supabase.co/functions/v1/sync",
        "TOKEN": "SEU_TOKEN_AQUI"
    },
    "FTP_CONFIG": {
        "HOST": "ftp.exemplo.com",
        "USER": "usuario",
        "PASS": "senha",
        "REMOTE_DIR": "/"
    }
}
EOF
    echo "✅ config.json criado."
fi

# 4. DB JSON
if [ ! -f sync_db.json ]; then
    echo "{}" > sync_db.json
fi

echo "✨ Tudo pronto! Edite o config.json e execute: python3 agent.py"