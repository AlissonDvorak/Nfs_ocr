import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

class Settings:
    """Configurações da aplicação"""
    
    # Configurações do Gemini
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
    
    # Configurações do Google Sheets
    GOOGLE_SHEETS_CREDENTIALS_FILE: str = os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE", "credentials.json")
    GOOGLE_SHEETS_SPREADSHEET_ID: str = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "")
    GOOGLE_SHEETS_WORKSHEET_NAME: str = os.getenv("GOOGLE_SHEETS_WORKSHEET_NAME", "OCR Notas Fiscais")
    
    # Configurações do Google Drive
    GOOGLE_DRIVE_ENABLED: bool = os.getenv("GOOGLE_DRIVE_ENABLED", "False").lower() == "true"
    GOOGLE_DRIVE_ROOT_FOLDER_NAME: str = os.getenv("GOOGLE_DRIVE_ROOT_FOLDER_NAME", "NFEs")
    GOOGLE_DRIVE_CREDENTIALS_FILE: str = os.getenv("GOOGLE_DRIVE_CREDENTIALS_FILE", "credentials.json")
    GOOGLE_DRIVE_USE_OAUTH: bool = os.getenv("GOOGLE_DRIVE_USE_OAUTH", "False").lower() == "true"
    GOOGLE_DRIVE_TOKEN_FILE: str = os.getenv("GOOGLE_DRIVE_TOKEN_FILE", "token.json")
    
    # Configurações do Telegram Bot (para futuro uso)
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_WEBHOOK_URL: str = os.getenv("TELEGRAM_WEBHOOK_URL", "")
    TELEGRAM_WEBHOOK_SECRET: str = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
    
    # Configurações da aplicação
    APP_NAME: str = "OCR Nota Fiscal"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Configurações de upload
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    ALLOWED_EXTENSIONS: list = [".jpg", ".jpeg", ".png", ".pdf"]
    
    # Timeout para requisições
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    
    def __init__(self):
        if not self.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY não está configurada nas variáveis de ambiente")
        if not self.GOOGLE_SHEETS_SPREADSHEET_ID:
            raise ValueError("GOOGLE_SHEETS_SPREADSHEET_ID não está configurada nas variáveis de ambiente")

# Instância global das configurações
settings = Settings()