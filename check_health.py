import os
import json
import requests
from ftplib import FTP

def test_api(config):
    print("🌐 Testando API Supabase...")
    url = f"{config['URL']}?action=state"
    headers = {"Authorization": f"Bearer {config['TOKEN']}"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            print("  ✅ API: Conectada e Token Válido!")
            return True
        else:
            print(f"  ❌ API: Erro {r.status_code} - {r.text}")
    except Exception as e:
        print(f"  ❌ API: Falha na conexão - {e}")
    return False

def test_ftp(config):
    print("📂 Testando Conexão FTP...")
    try:
        ftp = FTP(config['HOST'])
        ftp.login(config['USER'], config['PASS'])
        print(f"  ✅ FTP: Login bem-sucedido em {config['HOST']}")
        
        # Teste de permissão de escrita
        remote_dir = config.get('REMOTE_DIR', '/')
        ftp.cwd(remote_dir)
        test_filename = ".health_check_test"
        ftp.storbinary(f'STOR {test_filename}', iter([b'test']))
        ftp.delete(test_filename)
        
        print(f"  ✅ FTP: Permissão de escrita confirmada em '{remote_dir}'")
        ftp.quit()
        return True
    except Exception as e:
        print(f"  ❌ FTP: Falha - {e}")
    return False

def test_speedpro(config):
    print("🚀 Testando SpeedPro (Auth + Sync)...")
    auth_url = "https://ylhuinvbvqwleknpwljs.supabase.co/auth/v1/token?grant_type=password"
    payload = {"email": config['EMAIL'], "password": config['PASSWORD']}
    
    try:
        r = requests.post(auth_url, json=payload)
        if r.status_code == 200:
            token = r.json().get('access_token')
            print("  ✅ SpeedPro: Login OK!")
            # Testar se o token funciona no método state
            headers = {"Authorization": f"Bearer {token}"}
            r_sync = requests.get("https://ylhuinvbvqwleknpwljs.supabase.co/functions/v1/sync?action=state", headers=headers)
            if r_sync.status_code == 200:
                print("  ✅ SpeedPro: Permissão de Sync OK!")
                return True
        else:
            print(f"  ❌ SpeedPro: Falha no login ({r.status_code})")
    except Exception as e:
        print(f"  ❌ SpeedPro: Erro de conexão - {e}")
    return False

def run_diagnostics():
    print("🔍 INICIANDO DIAGNÓSTICO DO AGENTE\n" + "="*40)
    
    if not os.path.exists("config.json"):
        print("❌ Erro: config.json não encontrado!")
        return

    with open("config.json", "r") as f:
        cfg = json.load(f)

    results = []
    if cfg["SYNC_DESTINATIONS"].get("api"):
        results.append(test_api(cfg["API_CONFIG"]))
    
    if cfg["SYNC_DESTINATIONS"].get("ftp"):
        results.append(test_ftp(cfg["FTP_CONFIG"]))

    print("="*40)
    if all(results):
        print("🚀 TUDO PRONTO! Você pode iniciar o agent.py com segurança.")
    else:
        print("⚠️ ALERTA: Alguns serviços falharam. Verifique as configurações.")

if __name__ == "__main__":
    run_diagnostics()