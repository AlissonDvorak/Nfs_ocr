#!/usr/bin/env python3
"""
Script de demonstração do Bot do Telegram
Exemplo de como o bot funciona e suas funcionalidades
"""

import asyncio
import aiohttp
import json
from pathlib import Path

# URL base da API (ajuste conforme necessário)
API_BASE_URL = "http://localhost:8000"

async def demo_api_calls():
    """Demonstra as chamadas de API que o bot faz"""
    
    print("🔍 Demonstração das Funcionalidades do Bot")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        
        # 1. Health Check
        print("\n1️⃣ Verificando status da API...")
        try:
            async with session.get(f"{API_BASE_URL}/nota-fiscal/health") as response:
                if response.status == 200:
                    data = await response.json()
                    status = data.get('overall_status', 'unknown')
                    print(f"   ✅ Status: {status}")
                    
                    services = data.get('services', {})
                    print(f"   • OCR: {services.get('ocr_gemini', {}).get('status', 'N/A')}")
                    print(f"   • Sheets: {services.get('google_sheets', {}).get('status', 'N/A')}")
                else:
                    print(f"   ❌ Erro: {response.status}")
        except Exception as e:
            print(f"   ❌ Erro de conexão: {e}")
        
        # 2. Estatísticas
        print("\n2️⃣ Obtendo estatísticas...")
        try:
            async with session.get(f"{API_BASE_URL}/nota-fiscal/sheets/statistics") as response:
                if response.status == 200:
                    data = await response.json()
                    stats = data.get('statistics', {})
                    
                    resumo = stats.get('resumo', {})
                    itens = stats.get('itens', {})
                    
                    print(f"   📋 Total de NFs: {resumo.get('total_notas', 0)}")
                    print(f"   💰 Valor total: R$ {resumo.get('valor_total_sum', 0):,.2f}")
                    print(f"   📦 Total de itens: {itens.get('total_itens', 0)}")
                    print(f"   🏢 Empresas ativas: {stats.get('cnpj_worksheets', 0)}")
                else:
                    print(f"   ❌ Erro: {response.status}")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
        
        # 3. Dados recentes
        print("\n3️⃣ Obtendo dados recentes...")
        try:
            async with session.get(f"{API_BASE_URL}/nota-fiscal/sheets/recent?limit=3") as response:
                if response.status == 200:
                    data = await response.json()
                    recent_data = data.get('data', {})
                    resumo_data = recent_data.get('resumo', [])
                    
                    if resumo_data:
                        print(f"   📋 Últimas {len(resumo_data)} notas:")
                        for i, nf in enumerate(resumo_data[:3], 1):
                            numero = nf.get('Número Nota', 'N/A')
                            emissor = nf.get('Razão Social Emissor', 'N/A')
                            valor = nf.get('Valor Total', 'N/A')
                            print(f"   {i}. NF {numero} - {emissor[:20]}... - R$ {valor}")
                    else:
                        print("   📋 Nenhuma nota encontrada")
                else:
                    print(f"   ❌ Erro: {response.status}")
        except Exception as e:
            print(f"   ❌ Erro: {e}")

def demo_bot_responses():
    """Demonstra como o bot formata as respostas"""
    
    print("\n\n🤖 Exemplos de Respostas do Bot")
    print("=" * 50)
    
    # Exemplo de resposta de boas-vindas
    print("\n📱 Resposta do comando /start:")
    print("-" * 30)
    welcome_msg = """🤖 *Bot OCR para Notas Fiscais*

Olá! Eu sou o bot para processamento de Notas Fiscais brasileiras.

📋 *Como usar:*
• Envie uma foto da sua Nota Fiscal
• Ou envie um arquivo PDF da NF
• Aguarde enquanto processo os dados
• Receba o resultado estruturado

🔧 *Comandos disponíveis:*
/help - Ajuda detalhada
/stats - Estatísticas do serviço
/recent - Últimas notas processadas
/health - Status do serviço

📤 *Comece enviando uma imagem ou PDF!*"""
    
    print(welcome_msg)
    
    # Exemplo de resposta de processamento
    print("\n📱 Resposta após processar uma NF:")
    print("-" * 30)
    success_msg = """✅ *Nota Fiscal Processada com Sucesso!*

📋 *Dados da NF:*
• Número: 123456
• Série: 1
• Data Emissão: 15/06/2025
• Valor Total: R$ 1.250,00

🏢 *Emissor:*
• Empresa Exemplo LTDA
• CNPJ: 12.345.678/0001-90

📍 *Destinatário:*
• João da Silva
• CNPJ: 98.765.432/0001-10

📦 *Itens (3):*
1. Produto A - Qtd: 2 | Valor: R$ 500,00
2. Produto B - Qtd: 1 | Valor: R$ 750,00
... e mais 1 itens

💾 *Dados salvos no Google Sheets!*
• Planilhas atualizadas: OCR Notas Fiscais, OCR Notas Fiscais - Itens

⏱️ Processado em 12.5s"""
    
    print(success_msg)

def demo_user_interaction():
    """Demonstra a interação do usuário com o bot"""
    
    print("\n\n👤 Fluxo de Interação do Usuário")
    print("=" * 50)
    
    interactions = [
        ("👤 Usuário", "Encontra o bot no Telegram e clica em 'Iniciar'"),
        ("🤖 Bot", "Envia mensagem de boas-vindas com botões"),
        ("👤 Usuário", "Envia foto de uma nota fiscal"),
        ("🤖 Bot", "Responde: '🔄 Processando sua Nota Fiscal...'"),
        ("🤖 Bot", "Faz chamada para API: POST /nota-fiscal/process"),
        ("⚙️ API", "Processa com OCR (Gemini) e salva no Google Sheets"),
        ("🤖 Bot", "Atualiza: '✅ Processamento concluído!'"),
        ("🤖 Bot", "Envia resultado formatado com todos os dados"),
        ("👤 Usuário", "Pode enviar /stats para ver estatísticas"),
        ("🤖 Bot", "Consulta API e retorna estatísticas formatadas"),
    ]
    
    for i, (actor, action) in enumerate(interactions, 1):
        print(f"{i:2d}. {actor}: {action}")

def demo_error_handling():
    """Demonstra o tratamento de erros do bot"""
    
    print("\n\n⚠️ Tratamento de Erros")
    print("=" * 50)
    
    errors = [
        ("Arquivo muito grande", "❌ Arquivo muito grande! Tamanho máximo: 10MB"),
        ("Formato inválido", "❌ Apenas arquivos PDF são suportados"),
        ("API indisponível", "❌ Erro na API - Serviço temporariamente indisponível"),
        ("Erro de processamento", "❌ Erro no processamento: Imagem não legível"),
        ("Timeout", "❌ Processamento demorou muito - Tente novamente"),
    ]
    
    for error_type, response in errors:
        print(f"• {error_type}: {response}")

async def main():
    """Função principal da demonstração"""
    
    print("🎯 DEMONSTRAÇÃO DO BOT TELEGRAM - OCR NOTAS FISCAIS")
    print("Este script mostra como o bot funciona e suas capacidades")
    print()
    
    # Demonstrar chamadas de API
    await demo_api_calls()
    
    # Demonstrar respostas do bot
    demo_bot_responses()
    
    # Demonstrar interação do usuário
    demo_user_interaction()
    
    # Demonstrar tratamento de erros
    demo_error_handling()
    
    print("\n\n🎉 Demonstração concluída!")
    print("\nPara testar o bot:")
    print("1. Configure o token no arquivo .env")
    print("2. Execute: python run_bot.py")
    print("3. Procure seu bot no Telegram")
    print("4. Envie /start para começar")

if __name__ == "__main__":
    asyncio.run(main())
