#!/usr/bin/env python3
"""
Script para iniciar o sistema completo:
1. API de OCR de Notas Fiscais
2. Bot do Telegram

Permite escolher executar ambos ou apenas um componente
"""

import os
import sys
import time
import signal
import subprocess
import threading
from pathlib import Path

def print_banner():
    """Imprime banner do sistema"""
    print("🚀 SISTEMA OCR NOTAS FISCAIS + BOT TELEGRAM")
    print("=" * 60)
    print("Sistema completo para processamento de Notas Fiscais")
    print("com integração Google Sheets e Bot do Telegram")
    print("=" * 60)

def check_env_file():
    """Verifica se o arquivo .env existe e tem as configurações necessárias"""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("❌ Arquivo .env não encontrado!")
        print("   Copie o arquivo teste.env para .env e configure suas credenciais")
        return False
    
    # Verificar variáveis essenciais
    required_vars = [
        "GOOGLE_API_KEY",
        "GOOGLE_SHEETS_CREDENTIALS_FILE", 
        "GOOGLE_SHEETS_SPREADSHEET_ID",
        "TELEGRAM_BOT_TOKEN"
    ]
    
    missing_vars = []
    
    with open(env_file, 'r') as f:
        content = f.read()
        for var in required_vars:
            if f"{var}=" not in content or f"{var}=" in content and content.split(f"{var}=")[1].split('\n')[0].strip() == "":
                missing_vars.append(var)
    
    if missing_vars:
        print("⚠️  Variáveis de ambiente não configuradas:")
        for var in missing_vars:
            print(f"   • {var}")
        print("\n   Configure essas variáveis no arquivo .env")
        return False
    
    print("✅ Arquivo .env configurado corretamente")
    return True

def check_credentials():
    """Verifica se o arquivo de credenciais do Google existe"""
    creds_file = Path("credentials.json")
    
    if not creds_file.exists():
        print("⚠️  Arquivo credentials.json não encontrado")
        print("   Baixe o arquivo de credenciais do Google Cloud Console")
        print("   e salve como 'credentials.json' na raiz do projeto")
        return False
    
    print("✅ Credenciais do Google encontradas")
    return True

def install_dependencies():
    """Instala dependências se necessário"""
    print("📦 Verificando dependências...")
    
    # Dependências principais
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Dependências principais instaladas")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar dependências principais: {e}")
        return False
    
    # Dependências do bot
    bot_requirements = Path("telegram-bot/requirements.txt")
    if bot_requirements.exists():
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(bot_requirements)], 
                          check=True, capture_output=True)
            print("✅ Dependências do bot instaladas")
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao instalar dependências do bot: {e}")
            return False
    
    return True

class ProcessManager:
    """Gerenciador de processos para API e Bot"""
    
    def __init__(self):
        self.api_process = None
        self.bot_process = None
        self.running = True
    
    def start_api(self):
        """Inicia a API"""
        print("🔧 Iniciando API de OCR...")
        try:
            self.api_process = subprocess.Popen([
                sys.executable, "-m", "app.main"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Aguardar alguns segundos para a API iniciar
            time.sleep(3)
            
            if self.api_process.poll() is None:
                print("✅ API iniciada na porta 8000")
                return True
            else:
                stdout, stderr = self.api_process.communicate()
                print(f"❌ Erro ao iniciar API: {stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao iniciar API: {e}")
            return False
    
    def start_bot(self):
        """Inicia o bot do Telegram"""
        print("🤖 Iniciando Bot do Telegram...")
        try:
            self.bot_process = subprocess.Popen([
                sys.executable, "telegram-bot/run_bot.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Aguardar alguns segundos para o bot iniciar
            time.sleep(2)
            
            if self.bot_process.poll() is None:
                print("✅ Bot do Telegram iniciado")
                return True
            else:
                stdout, stderr = self.bot_process.communicate()
                print(f"❌ Erro ao iniciar bot: {stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao iniciar bot: {e}")
            return False
    
    def stop_all(self):
        """Para todos os processos"""
        print("\n🛑 Parando serviços...")
        self.running = False
        
        if self.api_process and self.api_process.poll() is None:
            self.api_process.terminate()
            try:
                self.api_process.wait(timeout=5)
                print("✅ API finalizada")
            except subprocess.TimeoutExpired:
                self.api_process.kill()
                print("⚠️  API forçadamente finalizada")
        
        if self.bot_process and self.bot_process.poll() is None:
            self.bot_process.terminate()
            try:
                self.bot_process.wait(timeout=5)
                print("✅ Bot finalizado")
            except subprocess.TimeoutExpired:
                self.bot_process.kill()
                print("⚠️  Bot forçadamente finalizado")
    
    def monitor_processes(self):
        """Monitora os processos em execução"""
        while self.running:
            time.sleep(5)
            
            # Verificar API
            if self.api_process and self.api_process.poll() is not None:
                print("⚠️  API parou inesperadamente")
                self.running = False
            
            # Verificar Bot
            if self.bot_process and self.bot_process.poll() is not None:
                print("⚠️  Bot parou inesperadamente")
                self.running = False

def main():
    """Função principal"""
    print_banner()
    
    # Verificações iniciais
    if not check_env_file():
        return
    
    if not check_credentials():
        print("⚠️  Continuando sem verificar credenciais...")
    
    # Perguntar o que executar
    print("\n🤔 O que deseja executar?")
    print("1. Apenas API de OCR")
    print("2. Apenas Bot do Telegram") 
    print("3. Ambos (API + Bot)")
    print("4. Instalar dependências")
    
    choice = input("\nEscolha (1-4): ").strip()
    
    if choice == "4":
        print("\n📦 Instalando dependências...")
        if install_dependencies():
            print("✅ Dependências instaladas com sucesso!")
        else:
            print("❌ Erro na instalação das dependências")
        return
    
    # Instalar dependências automaticamente
    if not install_dependencies():
        print("❌ Erro ao instalar dependências")
        return
    
    # Inicializar gerenciador de processos
    manager = ProcessManager()
    
    # Configurar handler para Ctrl+C
    def signal_handler(signum, frame):
        manager.stop_all()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        if choice == "1":
            # Apenas API
            if manager.start_api():
                print("\n🎯 API rodando em http://localhost:8000")
                print("   Acesse http://localhost:8000/docs para ver a documentação")
                print("   Pressione Ctrl+C para parar")
                
                while manager.running:
                    time.sleep(1)
            
        elif choice == "2":
            # Apenas Bot
            if manager.start_bot():
                print("\n🤖 Bot do Telegram rodando")
                print("   Procure seu bot no Telegram e envie /start")
                print("   Pressione Ctrl+C para parar")
                
                while manager.running:
                    time.sleep(1)
        
        elif choice == "3":
            # Ambos
            api_ok = manager.start_api()
            if not api_ok:
                print("❌ Não foi possível iniciar a API")
                return
            
            bot_ok = manager.start_bot()
            if not bot_ok:
                print("❌ Não foi possível iniciar o Bot")
                manager.stop_all()
                return
            
            print("\n🎉 Sistema completo iniciado!")
            print("   API: http://localhost:8000")
            print("   Bot: Procure no Telegram e envie /start")
            print("   Pressione Ctrl+C para parar ambos")
            
            # Monitorar processos
            monitor_thread = threading.Thread(target=manager.monitor_processes)
            monitor_thread.daemon = True
            monitor_thread.start()
            
            while manager.running:
                time.sleep(1)
        
        else:
            print("❌ Opção inválida")
    
    except KeyboardInterrupt:
        pass
    finally:
        manager.stop_all()
        print("\n👋 Sistema finalizado")

if __name__ == "__main__":
    main()
