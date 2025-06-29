#!/usr/bin/env python3
"""
Script principal para executar todos os testes do sistema OCR Notas Fiscais
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(cmd, description):
    """Executa um comando e exibe o resultado"""
    print(f"\n🧪 {description}")
    print("=" * 50)
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Warnings/Errors:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro: {e}")
        if e.stdout:
            print("Output:", e.stdout)
        if e.stderr:
            print("Errors:", e.stderr)
        return False


def main():
    """Menu principal de testes"""
    print("🧪 Sistema de Testes - OCR Notas Fiscais")
    print("=" * 50)
    
    # Mudar para diretório do projeto
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    while True:
        print("\n📋 Opções de Teste:")
        print("1. 🔧 Configurar OAuth2 (Google Drive pessoal)")
        print("2. 🏥 Health Check - Todos os serviços")
        print("3. 📁 Teste Google Drive")
        print("4. 📄 Teste processamento PDF")
        print("5. 🌐 Teste API completa")
        print("6. 🔍 Verificar estrutura Google Drive")
        print("7. 👤 Verificar conta Google Drive")
        print("8. ▶️ Executar TODOS os testes")
        print("0. 🚪 Sair")
        
        choice = input("\n📝 Escolha uma opção: ").strip()
        
        if choice == "0":
            print("👋 Saindo...")
            break
        elif choice == "1":
            run_command("python tests/setup_oauth.py", "Configurando OAuth2")
        elif choice == "2":
            run_command("python tests/test_service.py", "Health Check dos Serviços")
        elif choice == "3":
            run_command("python tests/test_drive.py", "Testando Google Drive")
        elif choice == "4":
            run_command("python tests/test_pdf_processing.py", "Testando Processamento PDF")
        elif choice == "5":
            run_command("python tests/test_api_complete.py", "Testando API Completa")
        elif choice == "6":
            run_command("python tests/verify_drive_structure.py", "Verificando Estrutura Google Drive")
        elif choice == "7":
            run_command("python tests/check_drive_account.py", "Verificando Conta Google Drive")
        elif choice == "8":
            print("\n🚀 Executando TODOS os testes...")
            tests = [
                ("python tests/test_service.py", "Health Check"),
                ("python tests/test_pdf_processing.py", "Processamento PDF"),
                ("python tests/test_drive.py", "Google Drive"),
                ("python tests/verify_drive_structure.py", "Estrutura Drive"),
                ("python tests/check_drive_account.py", "Conta Drive"),
                ("python tests/test_api_complete.py", "API Completa")
            ]
            
            results = []
            for cmd, desc in tests:
                success = run_command(cmd, desc)
                results.append((desc, "✅" if success else "❌"))
            
            print("\n📊 Resumo dos Testes:")
            print("=" * 30)
            for desc, status in results:
                print(f"{status} {desc}")
        else:
            print("❌ Opção inválida!")


if __name__ == "__main__":
    main()
