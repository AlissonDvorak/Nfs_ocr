from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import sys
from datetime import datetime

from .config.settings import settings
from .api.nota_fiscal import router as nota_fiscal_router

# Configurar logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Criar aplicação FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    🔍 **API para Processamento de Notas Fiscais**
    
    Sistema inteligente que utiliza **Google Gemini 2.0 Flash** para extrair dados estruturados de notas fiscais 
    e salva automaticamente os resultados no **Google Sheets**.
    
    ## Funcionalidades principais:
    - 📄 Processamento de imagens de notas fiscais (JPG, PNG, PDF)
    - 🤖 Extração inteligente de dados usando IA
    - 📊 Salvamento automático no Google Sheets
    - 📈 Monitoramento e estatísticas
    - 🔍 Extração de texto simples (OCR)
    
    ## Como usar:
    1. Faça upload de uma imagem de nota fiscal no endpoint `/api/v1/nota-fiscal/process`
    2. Os dados serão extraídos automaticamente e salvos no Google Sheets
    3. Consulte o status e resultados através dos endpoints de monitoramento
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Suporte OCR Nota Fiscal",
        "email": "suporte@example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique os domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(nota_fiscal_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """Evento executado na inicialização da aplicação"""
    logger.info("=" * 60)
    logger.info(f"🚀 Iniciando {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info("=" * 60)
    
    # Verificar configurações essenciais
    config_status = []
    
    # Verificar Google API Key
    if settings.GOOGLE_API_KEY:
        config_status.append("✅ Google API Key configurada")
    else:
        config_status.append("❌ Google API Key NÃO configurada")
        logger.error("GOOGLE_API_KEY não configurada!")
    
    # Verificar Google Sheets
    if settings.GOOGLE_SHEETS_SPREADSHEET_ID:
        config_status.append("✅ Google Sheets ID configurado")
    else:
        config_status.append("❌ Google Sheets ID NÃO configurado")
        logger.error("GOOGLE_SHEETS_SPREADSHEET_ID não configurado!")
    
    # Log das configurações
    logger.info("📋 Status das Configurações:")
    for status in config_status:
        logger.info(f"   {status}")
    
    logger.info(f"🤖 Modelo Gemini: {settings.GEMINI_MODEL}")
    logger.info(f"📊 Planilha: {settings.GOOGLE_SHEETS_WORKSHEET_NAME}")
    logger.info(f"🔧 Modo debug: {settings.DEBUG}")
    logger.info(f"📁 Tamanho máximo de arquivo: {settings.MAX_FILE_SIZE / 1024 / 1024:.1f}MB")
    
    # Verificar se há configurações críticas faltando
    if not settings.GOOGLE_API_KEY or not settings.GOOGLE_SHEETS_SPREADSHEET_ID:
        logger.warning("⚠️  Configurações críticas faltando - alguns recursos podem não funcionar")
    else:
        logger.info("✅ Todas as configurações críticas estão presentes")
    
    logger.info("=" * 60)
    logger.info("🎯 Aplicação iniciada com sucesso!")
    logger.info("📖 Documentação disponível em: /docs")
    logger.info("🔍 Health check disponível em: /api/v1/nota-fiscal/health")
    logger.info("=" * 60)

@app.on_event("shutdown")
async def shutdown_event():
    """Evento executado no encerramento da aplicação"""
    logger.info("🔴 Encerrando aplicação...")

@app.get("/")
async def root():
    """Endpoint raiz da API"""
    return JSONResponse(
        content={
            "message": f"🔍 Bem-vindo ao {settings.APP_NAME} v{settings.APP_VERSION}",
            "description": "Sistema de OCR para Notas Fiscais com Google Gemini 2.0 Flash",
            "features": [
                "Processamento inteligente de notas fiscais",
                "Extração de dados estruturados",
                "Salvamento automático no Google Sheets",
                "Monitoramento e estatísticas em tempo real"
            ],
            "endpoints": {
                "docs": "/docs",
                "health": "/api/v1/nota-fiscal/health",
                "process": "/api/v1/nota-fiscal/process",
                "stats": "/api/v1/nota-fiscal/stats"
            },
            "powered_by": "Google Gemini 2.0 Flash",
            "timestamp": datetime.now().isoformat()
        }
    )

@app.get("/health")
async def health_check():
    """Health check geral da aplicação"""
    return JSONResponse(
        content={
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "timestamp": datetime.now().isoformat(),
            "uptime": "Sistema operacional",
            "detailed_health": "/api/v1/nota-fiscal/health"
        }
    )

@app.get("/info")
async def app_info():
    """Informações detalhadas da aplicação"""
    return JSONResponse(
        content={
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "gemini_model": settings.GEMINI_MODEL,
            "debug_mode": settings.DEBUG,
            "max_file_size_mb": settings.MAX_FILE_SIZE / 1024 / 1024,
            "allowed_extensions": settings.ALLOWED_EXTENSIONS,
            "google_sheets_configured": bool(settings.GOOGLE_SHEETS_SPREADSHEET_ID),
            "worksheet_name": settings.GOOGLE_SHEETS_WORKSHEET_NAME,
            "timestamp": datetime.now().isoformat()
        }
    )

# Handler para erros não tratados
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handler global para exceções não tratadas"""
    logger.error(f"Erro não tratado na rota {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Erro interno do servidor",
            "detail": str(exc) if settings.DEBUG else "Erro interno - verifique os logs",
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )

# Handler para erros HTTP
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handler para exceções HTTP"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Iniciando servidor de desenvolvimento...")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
        access_log=True
    )