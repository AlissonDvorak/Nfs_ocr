#!/usr/bin/env python3
"""
Script de teste para verificar se o token do bot está funcionando
"""

import os
import sys
import asyncio
from pathlib import Path

# Adicionar o diretório atual ao path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Carregar variáveis de ambiente
from config import config

async def test_bot_token():
    """Testa se o token do bot está válido"""
    
    print("🧪 Testando Token do Bot do Telegram")
    print("=" * 40)
    
    try:
        # Importar depois de configurar o path
        from telegram import Bot
        
        # Validar configurações
        config.validate()
        print(f"✅ Token configurado: {config.TELEGRAM_BOT_TOKEN[:10]}...")
        
        # Criar bot
        bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
        
        # Testar conexão
        print("🔗 Testando conexão com API do Telegram...")
        
        # Obter informações do bot
        bot_info = await bot.get_me()
        
        print(f"✅ Bot conectado com sucesso!")
        print(f"   Nome: {bot_info.first_name}")
        print(f"   Username: @{bot_info.username}")
        print(f"   ID: {bot_info.id}")
        print(f"   Pode receber mensagens: {'✅' if bot_info.can_read_all_group_messages else '❌'}")
        
        # Testar obter updates
        print("\n🔍 Verificando mensagens pendentes...")
        updates = await bot.get_updates(limit=1)
        
        if updates:
            print(f"   📬 {len(updates)} mensagens pendentes encontradas")
            last_update = updates[-1]
            print(f"   Última mensagem ID: {last_update.update_id}")
        else:
            print("   📭 Nenhuma mensagem pendente")
        
        print(f"\n🎯 Bot está funcionando corretamente!")
        print(f"   Para testar, procure por @{bot_info.username} no Telegram")
        print(f"   Envie /start para o bot")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        
        if "Unauthorized" in str(e):
            print("   🔑 Token inválido ou revogado")
            print("   Verifique se o token no .env está correto")
        elif "Network" in str(e) or "timeout" in str(e).lower():
            print("   🌐 Problema de conexão")
            print("   Verifique sua conexão com a internet")
        else:
            print("   🐛 Erro inesperado")
        
        return False

async def test_api_connection():
    """Testa conexão com a API local"""
    
    print(f"\n🔗 Testando API Local ({config.API_BASE_URL})")
    print("-" * 40)
    
    try:
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{config.API_BASE_URL}/nota-fiscal/health",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    status = data.get('overall_status', 'unknown')
                    print(f"✅ API local conectada - Status: {status}")
                    return True
                else:
                    print(f"⚠️  API respondeu com status {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Erro ao conectar com API: {e}")
        print("   🔧 Certifique-se de que a API esteja rodando:")
        print("   python -m app.main")
        return False

def main():
    """Função principal"""
    print("🧪 TESTE DO BOT DO TELEGRAM")
    print("Verificando se tudo está configurado corretamente\n")
    
    try:
        # Testar token do bot
        bot_ok = asyncio.run(test_bot_token())
        
        # Testar API local
        api_ok = asyncio.run(test_api_connection())
        
        print("\n" + "=" * 40)
        print("📋 RESUMO DOS TESTES:")
        print(f"   Bot do Telegram: {'✅' if bot_ok else '❌'}")
        print(f"   API Local: {'✅' if api_ok else '❌'}")
        
        if bot_ok and api_ok:
            print("\n🎉 Tudo funcionando! Você pode iniciar o bot:")
            print("   python run_bot.py")
        elif bot_ok:
            print("\n⚠️  Bot OK, mas API não está rodando")
            print("   Inicie a API primeiro: python -m app.main")
        else:
            print("\n❌ Problemas encontrados - verifique as configurações")
        
    except KeyboardInterrupt:
        print("\n⚠️  Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro durante teste: {e}")

if __name__ == "__main__":
    main()
