#!/usr/bin/env python3
"""
Script de inicialização do Bot do Telegram para OCR de Notas Fiscais - Versão Corrigida
"""

import sys
import asyncio
import logging
from pathlib import Path

# Adicionar o diretório atual ao path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from config import config
from bot import TelegramOCRBot

# Configurar logging
def setup_logging():
    """Configura o sistema de logging"""
    log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
    
    # Formato de log
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configurar logging básico
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('bot.log', encoding='utf-8')
        ]
    )
    
    # Reduzir verbosidade de algumas bibliotecas
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.INFO)

async def test_api_connection():
    """Testa a conexão com a API"""
    import aiohttp
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{config.API_BASE_URL}/nota-fiscal/health",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    status = data.get('overall_status', 'unknown')
                    return True, status
                else:
                    return False, f"HTTP {response.status}"
    except Exception as e:
        return False, str(e)

async def run_bot():
    """Função assíncrona para rodar o bot"""
    
    print("🤖 Iniciando Bot do Telegram para OCR de Notas Fiscais")
    print("=" * 60)
    
    # Configurar logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Validar configurações
        config.validate()
        config.print_config()
        
        print("\n🔗 Testando conexão com API...")
        
        # Testar conexão com API
        api_ok, api_status = await test_api_connection()
        
        if api_ok:
            print(f"✅ API conectada - Status: {api_status}")
        else:
            print(f"❌ Falha na conexão com API: {api_status}")
            print("⚠️  API não está disponível, mas o bot ainda pode ser iniciado")
            print("   Certifique-se de que o serviço OCR esteja rodando em:")
            print(f"   {config.API_BASE_URL}")
        
        print(f"\n🚀 Iniciando bot...")
        print(f"   Token: {config.TELEGRAM_BOT_TOKEN[:10]}...")
        print(f"   API: {config.API_BASE_URL}")
        print("   Pressione Ctrl+C para parar\n")
        
        # Criar bot
        bot = TelegramOCRBot(config.TELEGRAM_BOT_TOKEN, config.API_BASE_URL)
        
        # Iniciar bot usando asyncio diretamente
        await bot.application.initialize()
        await bot.application.start()
        await bot.application.updater.start_polling()
        
        # Manter rodando até interrupção
        try:
            # Aguardar indefinidamente
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            print("\n\n⚠️  Bot interrompido pelo usuário")
            logger.info("Bot interrompido pelo usuário")
        finally:
            # Parar o bot graciosamente
            await bot.application.updater.stop()
            await bot.application.stop()
            await bot.application.shutdown()
        
    except ValueError as e:
        print(f"\n❌ Erro de configuração: {e}")
        print("   Verifique o arquivo .env na raiz do projeto")
        logger.error(f"Erro de configuração: {e}")
        return 1
        
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        logger.error(f"Erro inesperado: {e}", exc_info=True)
        return 1
    
    finally:
        print("\n👋 Bot finalizado")
    
    return 0

def main():
    """Função principal"""
    try:
        # Rodar o bot com asyncio
        return asyncio.run(run_bot())
    except KeyboardInterrupt:
        print("\n⚠️  Interrompido pelo usuário")
        return 0
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
