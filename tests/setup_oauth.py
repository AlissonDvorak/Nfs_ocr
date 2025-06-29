#!/usr/bin/env python3
"""
Script para configurar OAuth2 e autorizar acesso ao Google Drive pessoal
"""

import sys
from pathlib import Path

# Adicionar o diretório do projeto ao path
sys.path.append(str(Path(__file__).parent.parent))

from app.config.settings import settings


def create_oauth_credentials_template():
    """Cria um template para as credenciais OAuth2"""
    print("=== Criando Template de Credenciais OAuth2 ===")
    
    oauth_template = {
        "installed": {
            "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
            "project_id": "your-project-id",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": "YOUR_CLIENT_SECRET",
            "redirect_uris": ["http://localhost"]
        }
    }
    
    template_file = Path("oauth_credentials_template.json")
    
    import json
    with open(template_file, 'w') as f:
        json.dump(oauth_template, f, indent=2)
    
    print(f"✅ Template criado: {template_file}")
    print("\n📋 Passos para configurar OAuth2:")
    print("1. Vá para https://console.cloud.google.com/")
    print("2. Selecione seu projeto ou crie um novo")
    print("3. Vá em 'APIs & Services' > 'Credentials'")
    print("4. Clique 'Create Credentials' > 'OAuth 2.0 Client IDs'")
    print("5. Escolha 'Desktop application'")
    print("6. Baixe o arquivo JSON")
    print("7. Renomeie para 'oauth_credentials.json'")
    print("8. Execute novamente este script")
    print()


def check_oauth_setup():
    """Verifica se OAuth2 está configurado"""
    print("=== Verificando Configuração OAuth2 ===")
    
    oauth_file = Path("oauth_credentials.json")
    
    if not oauth_file.exists():
        print("❌ Arquivo oauth_credentials.json não encontrado")
        create_oauth_credentials_template()
        return False
    
    print("✅ Arquivo oauth_credentials.json encontrado")
    
    try:
        import json
        with open(oauth_file, 'r') as f:
            data = json.load(f)
        
        if 'installed' in data:
            client_id = data['installed'].get('client_id', '')
            if 'YOUR_CLIENT_ID' not in client_id:
                print("✅ Credenciais OAuth2 configuradas")
                return True
            else:
                print("❌ Credenciais OAuth2 não preenchidas")
                return False
        else:
            print("❌ Formato de credenciais OAuth2 inválido")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao ler credenciais: {e}")
        return False


def test_oauth_authorization():
    """Testa a autorização OAuth2"""
    print("=== Testando Autorização OAuth2 ===")
    
    try:
        # Atualizar configurações para usar OAuth2
        import os
        os.environ['GOOGLE_DRIVE_USE_OAUTH'] = 'True'
        os.environ['GOOGLE_DRIVE_CREDENTIALS_FILE'] = 'oauth_credentials.json'
        
        # Recarregar configurações
        from importlib import reload
        from app.config import settings as settings_module
        reload(settings_module)
        
        # Tentar inicializar o Google Drive Manager
        from app.services.drive_manager import GoogleDriveManager
        
        print("🔐 Iniciando processo de autorização...")
        print("📱 Uma janela do navegador será aberta para autorização")
        print("👆 Faça login com sua conta Gmail e autorize o acesso")
        
        manager = GoogleDriveManager()
        
        if manager.service and manager.root_folder_id:
            print("✅ Autorização OAuth2 bem-sucedida!")
            print(f"📁 Pasta NFEs criada no seu Google Drive")
            print(f"🔗 ID da pasta: {manager.root_folder_id}")
            
            # Verificar informações da conta
            about = manager.service.about().get(fields='user').execute()
            user_info = about.get('user', {})
            print(f"👤 Conectado como: {user_info.get('displayName', 'N/A')} ({user_info.get('emailAddress', 'N/A')})")
            
            return True
        else:
            print("❌ Falha na autorização OAuth2")
            return False
            
    except Exception as e:
        print(f"❌ Erro durante autorização: {e}")
        return False


def main():
    """Função principal"""
    print("🔧 Configurador OAuth2 para Google Drive Pessoal")
    print("=" * 55)
    
    print(f"📍 Configurações atuais:")
    print(f"  - OAuth habilitado: {settings.GOOGLE_DRIVE_USE_OAUTH}")
    print(f"  - Arquivo de credenciais: {settings.GOOGLE_DRIVE_CREDENTIALS_FILE}")
    print(f"  - Arquivo de token: {settings.GOOGLE_DRIVE_TOKEN_FILE}")
    print()
    
    if not check_oauth_setup():
        print("⚠️  Configure as credenciais OAuth2 primeiro!")
        return
    
    if test_oauth_authorization():
        print("\n🎉 Configuração OAuth2 concluída com sucesso!")
        print("💡 Agora o sistema salvará arquivos no seu Google Drive pessoal")
        
        # Atualizar .env
        env_file = Path(".env")
        if env_file.exists():
            with open(env_file, 'r') as f:
                content = f.read()
            
            # Atualizar configurações no .env
            lines = content.split('\n')
            updated_lines = []
            
            for line in lines:
                if line.startswith('GOOGLE_DRIVE_CREDENTIALS_FILE='):
                    updated_lines.append('GOOGLE_DRIVE_CREDENTIALS_FILE=oauth_credentials.json')
                elif line.startswith('GOOGLE_DRIVE_USE_OAUTH='):
                    updated_lines.append('GOOGLE_DRIVE_USE_OAUTH=True')
                else:
                    updated_lines.append(line)
            
            with open(env_file, 'w') as f:
                f.write('\n'.join(updated_lines))
            
            print(f"✅ Arquivo .env atualizado")
    else:
        print("\n❌ Falha na configuração OAuth2")


if __name__ == "__main__":
    # Carregar variáveis de ambiente
    from dotenv import load_dotenv
    load_dotenv()
    
    main()
