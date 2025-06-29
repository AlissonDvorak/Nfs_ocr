#!/usr/bin/env python3
"""
Configurações do Bot do Telegram para OCR de Notas Fiscais
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env do projeto principal
project_root = Path(__file__).parent.parent
env_file = project_root / '.env'

if env_file.exists():
    load_dotenv(env_file)

class BotConfig:
    """Configurações do bot"""
    
    # Token do bot do Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # URL da API do serviço OCR
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    # Configurações opcionais
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Limites
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 10485760))  # 10MB
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 60))   # 60s
    
    # Webhook (se usar webhook ao invés de polling)
    WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL")
    WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET")
    WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", 8443))
    
    @classmethod
    def validate(cls):
        """Valida as configurações necessárias"""
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN é obrigatório")
        
        if not cls.API_BASE_URL:
            raise ValueError("API_BASE_URL é obrigatório")
    
    @classmethod
    def print_config(cls):
        """Imprime configurações (sem dados sensíveis)"""
        print("🤖 Configurações do Bot:")
        print(f"  API URL: {cls.API_BASE_URL}")
        print(f"  Debug: {cls.DEBUG}")
        print(f"  Log Level: {cls.LOG_LEVEL}")
        print(f"  Max File Size: {cls.MAX_FILE_SIZE / 1024 / 1024:.1f}MB")
        print(f"  Request Timeout: {cls.REQUEST_TIMEOUT}s")
        print(f"  Token configurado: {'✅' if cls.TELEGRAM_BOT_TOKEN else '❌'}")
        
        if cls.WEBHOOK_URL:
            print(f"  Webhook URL: {cls.WEBHOOK_URL}")
            print(f"  Webhook Port: {cls.WEBHOOK_PORT}")

# Instância global de configuração
config = BotConfig()
