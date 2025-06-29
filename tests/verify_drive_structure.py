#!/usr/bin/env python3
"""
Script para verificar as pastas criadas no Google Drive
"""

import asyncio
import sys
import os
from pathlib import Path

# Adicionar o diretório do projeto ao path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.drive_manager import drive_manager
from app.config.settings import settings


def list_all_folders():
    """Lista todas as pastas no Google Drive"""
    print("=== Listando Pastas no Google Drive ===")
    
    if not settings.GOOGLE_DRIVE_ENABLED or not drive_manager.service:
        print("Google Drive não está disponível")
        return
    
    try:
        # Listar pasta raiz
        print(f"Pasta raiz: {settings.GOOGLE_DRIVE_ROOT_FOLDER_NAME}")
        print(f"ID: {drive_manager.root_folder_id}")
        
        # Listar pastas dentro da pasta raiz
        query = f"'{drive_manager.root_folder_id}' in parents and mimeType='application/vnd.google-apps.folder'"
        results = drive_manager.service.files().list(
            q=query,
            fields='files(id,name,createdTime,modifiedTime)'
        ).execute()
        
        cnpj_folders = results.get('files', [])
        print(f"\n📁 Pastas de CNPJ encontradas: {len(cnpj_folders)}")
        
        for folder in cnpj_folders:
            print(f"  - {folder['name']} (ID: {folder['id']})")
            print(f"    Criada: {folder.get('createdTime', 'N/A')}")
            
            # Listar pastas de data dentro de cada CNPJ
            date_query = f"'{folder['id']}' in parents and mimeType='application/vnd.google-apps.folder'"
            date_results = drive_manager.service.files().list(
                q=date_query,
                fields='files(id,name,createdTime)'
            ).execute()
            
            date_folders = date_results.get('files', [])
            if date_folders:
                print(f"    📅 Datas: {len(date_folders)} pastas")
                for date_folder in date_folders:
                    print(f"      - {date_folder['name']} (ID: {date_folder['id']})")
                    
                    # Listar arquivos dentro da pasta de data
                    files_query = f"'{date_folder['id']}' in parents and mimeType!='application/vnd.google-apps.folder'"
                    files_results = drive_manager.service.files().list(
                        q=files_query,
                        fields='files(id,name,size)'
                    ).execute()
                    
                    files = files_results.get('files', [])
                    if files:
                        print(f"        📄 Arquivos: {len(files)}")
                        for file in files:
                            size_mb = int(file.get('size', 0)) / 1024 / 1024
                            print(f"          - {file['name']} ({size_mb:.2f} MB)")
                    else:
                        print(f"        (sem arquivos)")
            else:
                print(f"    (sem pastas de data)")
            print()
            
    except Exception as e:
        print(f"Erro ao listar pastas: {e}")


def get_drive_link():
    """Mostra o link para acessar o Google Drive"""
    print("=== Link para Google Drive ===")
    
    if drive_manager.root_folder_id:
        drive_link = f"https://drive.google.com/drive/folders/{drive_manager.root_folder_id}"
        print(f"🔗 Acesso direto à pasta NFEs: {drive_link}")
    else:
        print("ID da pasta raiz não disponível")
    
    print()


def main():
    """Função principal"""
    print("🔍 Verificando Estrutura de Pastas no Google Drive")
    print("=" * 55)
    
    if not settings.GOOGLE_DRIVE_ENABLED:
        print("❌ Google Drive não está habilitado")
        return
    
    list_all_folders()
    get_drive_link()
    
    print("✅ Verificação concluída!")


if __name__ == "__main__":
    # Carregar variáveis de ambiente
    from dotenv import load_dotenv
    load_dotenv()
    
    main()
