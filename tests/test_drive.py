#!/usr/bin/env python3
"""
Script para testar a funcionalidade do Google Drive
"""

import asyncio
import sys
import os
from pathlib import Path

# Adicionar o diretório do projeto ao path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.drive_manager import drive_manager
from app.config.settings import settings


async def test_drive_health():
    """Testa o health check do Google Drive"""
    print("=== Teste de Health Check do Google Drive ===")
    
    try:
        health = drive_manager.health_check()
        print(f"Status: {health.get('status', 'unknown')}")
        
        if health['status'] == 'disabled':
            print("Google Drive está desabilitado nas configurações")
        elif health['status'] == 'healthy':
            gd_info = health.get('google_drive', {})
            print(f"Pasta raiz: {gd_info.get('root_folder_name', 'N/A')}")
            print(f"ID da pasta raiz: {gd_info.get('root_folder_id', 'N/A')}")
            print(f"Conectado: {gd_info.get('connected', False)}")
        else:
            print(f"Erro: {health.get('error', 'Erro desconhecido')}")
            
    except Exception as e:
        print(f"Erro no health check: {e}")
    
    print()


async def test_folder_creation():
    """Testa a criação de estrutura de pastas"""
    print("=== Teste de Criação de Estrutura de Pastas ===")
    
    if not settings.GOOGLE_DRIVE_ENABLED:
        print("Google Drive não está habilitado. Pulando teste.")
        return
    
    try:
        # Testar com CNPJ fictício
        test_cnpj = "12345678000199"
        
        # Criar estrutura de pastas
        folder_structure = drive_manager._create_cnpj_folder_structure(test_cnpj)
        
        print(f"Estrutura criada com sucesso:")
        print(f"  - Pasta CNPJ: {folder_structure['cnpj_folder_name']} (ID: {folder_structure['cnpj_folder_id']})")
        print(f"  - Pasta Data: {folder_structure['date_folder_name']} (ID: {folder_structure['date_folder_id']})")
        
    except Exception as e:
        print(f"Erro ao criar estrutura de pastas: {e}")
    
    print()


async def test_file_upload():
    """Testa o upload de um arquivo de exemplo"""
    print("=== Teste de Upload de Arquivo ===")
    
    if not settings.GOOGLE_DRIVE_ENABLED:
        print("Google Drive não está habilitado. Pulando teste.")
        return
    
    try:
        # Criar arquivo de teste
        test_content = "Este é um arquivo de teste para o Google Drive.".encode('utf-8')
        test_filename = "teste_upload.txt"
        test_cnpj = "12345678000199"
        
        # Fazer upload
        result = await drive_manager.save_nota_fiscal_file(
            file_content=test_content,
            filename=test_filename,
            cnpj=test_cnpj,
            mime_type="text/plain"
        )
        
        if result['success']:
            print(f"Upload realizado com sucesso!")
            print(f"  - Arquivo: {result['file_name']}")
            print(f"  - ID: {result['file_id']}")
            print(f"  - Tamanho: {result['file_size']} bytes")
            print(f"  - Caminho: {result['full_path']}")
            print(f"  - Link: {result.get('web_view_link', 'N/A')}")
        else:
            print(f"Erro no upload: {result['error']}")
            
    except Exception as e:
        print(f"Erro no teste de upload: {e}")
    
    print()


async def test_file_listing():
    """Testa a listagem de arquivos"""
    print("=== Teste de Listagem de Arquivos ===")
    
    if not settings.GOOGLE_DRIVE_ENABLED:
        print("Google Drive não está habilitado. Pulando teste.")
        return
    
    try:
        # Listar arquivos do CNPJ de teste
        test_cnpj = "12345678000199"
        
        result = await drive_manager.list_files_by_cnpj(test_cnpj)
        
        if result['success']:
            print(f"Arquivos encontrados para CNPJ {test_cnpj}:")
            print(f"Total: {result['total_files']} arquivos")
            
            for file_info in result['files']:
                print(f"  - {file_info['filename']} ({file_info['size']} bytes)")
                print(f"    Data: {file_info['date_folder']}")
                print(f"    Criado: {file_info['created_time']}")
                print()
        else:
            print(f"Erro ao listar arquivos: {result['error']}")
            
    except Exception as e:
        print(f"Erro no teste de listagem: {e}")
    
    print()


async def main():
    """Função principal de teste"""
    print("🧪 Testando Funcionalidade do Google Drive")
    print("=" * 50)
    
    # Verificar configurações
    print(f"Google Drive habilitado: {settings.GOOGLE_DRIVE_ENABLED}")
    print(f"Pasta raiz: {settings.GOOGLE_DRIVE_ROOT_FOLDER_NAME}")
    print(f"Arquivo de credenciais: {settings.GOOGLE_DRIVE_CREDENTIALS_FILE}")
    print()
    
    # Executar testes
    await test_drive_health()
    
    if settings.GOOGLE_DRIVE_ENABLED:
        await test_folder_creation()
        await test_file_upload()
        await test_file_listing()
    
    print("🏁 Testes concluídos!")


if __name__ == "__main__":
    # Carregar variáveis de ambiente
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(main())
