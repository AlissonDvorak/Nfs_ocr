#!/usr/bin/env python3
"""
Script para verificar informações da conta Google Drive sendo usada
"""

import sys
from pathlib import Path

# Adicionar o diretório do projeto ao path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.drive_manager import drive_manager
from app.config.settings import settings


def check_drive_account_info():
    """Verifica informações da conta do Google Drive"""
    print("=== Informações da Conta Google Drive ===")
    
    if not settings.GOOGLE_DRIVE_ENABLED or not drive_manager.service:
        print("❌ Google Drive não está disponível")
        return
    
    try:
        # Obter informações sobre a conta
        about = drive_manager.service.about().get(fields='user,storageQuota').execute()
        
        user_info = about.get('user', {})
        storage_quota = about.get('storageQuota', {})
        
        print(f"👤 Usuário:")
        print(f"  - Nome: {user_info.get('displayName', 'N/A')}")
        print(f"  - Email: {user_info.get('emailAddress', 'N/A')}")
        print(f"  - Foto: {user_info.get('photoLink', 'N/A')}")
        
        print(f"\n💾 Quota de Armazenamento:")
        limit = int(storage_quota.get('limit', 0))
        usage = int(storage_quota.get('usage', 0))
        
        if limit > 0:
            limit_gb = limit / (1024**3)
            usage_gb = usage / (1024**3)
            percent_used = (usage / limit) * 100
            
            print(f"  - Limite: {limit_gb:.2f} GB")
            print(f"  - Usado: {usage_gb:.2f} GB ({percent_used:.1f}%)")
            print(f"  - Disponível: {(limit_gb - usage_gb):.2f} GB")
        else:
            print(f"  - Uso: {usage / (1024**3):.2f} GB")
            print(f"  - Limite: Ilimitado ou não disponível")
        
    except Exception as e:
        print(f"❌ Erro ao obter informações da conta: {e}")
    
    print()


def check_credentials_info():
    """Verifica informações das credenciais"""
    print("=== Informações das Credenciais ===")
    
    credentials_file = Path(settings.GOOGLE_DRIVE_CREDENTIALS_FILE)
    
    if not credentials_file.exists():
        print(f"❌ Arquivo de credenciais não encontrado: {credentials_file}")
        return
    
    try:
        import json
        with open(credentials_file, 'r') as f:
            creds_data = json.load(f)
        
        print(f"📄 Arquivo: {credentials_file.name}")
        print(f"🔑 Tipo: {creds_data.get('type', 'N/A')}")
        print(f"📧 Email da Service Account: {creds_data.get('client_email', 'N/A')}")
        print(f"🏢 Projeto: {creds_data.get('project_id', 'N/A')}")
        print(f"🆔 Client ID: {creds_data.get('client_id', 'N/A')}")
        
        # Verificar permissões
        if 'client_email' in creds_data:
            service_email = creds_data['client_email']
            print(f"\n⚠️  IMPORTANTE:")
            print(f"   Esta Service Account ({service_email})")
            print(f"   está criando pastas no Google Drive associado ao projeto.")
            print(f"   As pastas podem estar sendo criadas em um Drive compartilhado")
            print(f"   ou no Drive da conta que deu permissões para esta Service Account.")
        
    except Exception as e:
        print(f"❌ Erro ao ler credenciais: {e}")
    
    print()


def check_root_folder_access():
    """Verifica acesso à pasta raiz e suas permissões"""
    print("=== Informações da Pasta Raiz NFEs ===")
    
    if not drive_manager.root_folder_id:
        print("❌ ID da pasta raiz não disponível")
        return
    
    try:
        # Obter informações detalhadas da pasta raiz
        folder_info = drive_manager.service.files().get(
            fileId=drive_manager.root_folder_id,
            fields='id,name,createdTime,modifiedTime,owners,permissions,parents,webViewLink'
        ).execute()
        
        print(f"📁 Pasta: {folder_info.get('name', 'N/A')}")
        print(f"🆔 ID: {folder_info.get('id', 'N/A')}")
        print(f"🔗 Link: {folder_info.get('webViewLink', 'N/A')}")
        print(f"📅 Criada: {folder_info.get('createdTime', 'N/A')}")
        print(f"📝 Modificada: {folder_info.get('modifiedTime', 'N/A')}")
        
        # Verificar proprietários
        owners = folder_info.get('owners', [])
        print(f"\n👑 Proprietários:")
        for owner in owners:
            print(f"  - {owner.get('displayName', 'N/A')} ({owner.get('emailAddress', 'N/A')})")
        
        # Verificar pasta pai (se houver)
        parents = folder_info.get('parents', [])
        if parents:
            print(f"\n📂 Pasta pai: {parents[0]}")
        else:
            print(f"\n📂 Pasta pai: Raiz do Drive")
        
        # Tentar listar permissões (pode falhar dependendo das permissões)
        try:
            permissions = drive_manager.service.permissions().list(
                fileId=drive_manager.root_folder_id,
                fields='permissions(id,type,role,emailAddress,displayName)'
            ).execute()
            
            perms = permissions.get('permissions', [])
            if perms:
                print(f"\n🔐 Permissões ({len(perms)}):")
                for perm in perms:
                    role = perm.get('role', 'N/A')
                    perm_type = perm.get('type', 'N/A')
                    email = perm.get('emailAddress', 'N/A')
                    name = perm.get('displayName', 'N/A')
                    print(f"  - {role} ({perm_type}): {name} ({email})")
        except Exception as e:
            print(f"\n🔐 Permissões: Não foi possível listar ({e})")
        
    except Exception as e:
        print(f"❌ Erro ao obter informações da pasta: {e}")
    
    print()


def main():
    """Função principal"""
    print("🔍 Verificando Conta e Permissões do Google Drive")
    print("=" * 55)
    
    check_credentials_info()
    check_drive_account_info()
    check_root_folder_access()
    
    print("✅ Verificação concluída!")
    print("\n💡 Dica: Acesse o link da pasta raiz para ver onde as pastas estão sendo criadas")


if __name__ == "__main__":
    # Carregar variáveis de ambiente
    from dotenv import load_dotenv
    load_dotenv()
    
    main()
