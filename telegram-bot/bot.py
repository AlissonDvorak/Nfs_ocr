#!/usr/bin/env python3
"""
Bot do Telegram para OCR de Notas Fiscais
Consome a API do serviço de OCR e processa imagens enviadas pelos usuários
"""

import os
import sys
import asyncio
import aiohttp
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import json
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env do projeto principal
project_root = Path(__file__).parent.parent
env_file = project_root / '.env'

if env_file.exists():
    load_dotenv(env_file)
    print(f"✅ Arquivo .env carregado: {env_file}")
else:
    print(f"❌ Arquivo .env não encontrado: {env_file}")

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes,
    CallbackQueryHandler
)
from telegram.constants import ParseMode

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramOCRBot:
    """Bot do Telegram para OCR de Notas Fiscais"""
    
    def __init__(self, bot_token: str, api_base_url: str):
        """
        Inicializa o bot
        
        Args:
            bot_token: Token do bot do Telegram
            api_base_url: URL base da API de OCR
        """
        logger.info("Inicializando bot do Telegram...")
        
        self.bot_token = bot_token
        self.api_base_url = api_base_url.rstrip('/')
        
        logger.info(f"API URL configurada: {self.api_base_url}")
        logger.info("Criando aplicação do Telegram...")
        
        self.application = Application.builder().token(bot_token).build()
        
        logger.info("Configurando handlers...")
        # Configurar handlers
        self._setup_handlers()
        
        logger.info("Bot inicializado com sucesso!")
    
    def _setup_handlers(self):
        """Configura os handlers do bot"""
        logger.info("Configurando handlers de comandos...")
        
        # Comandos
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("recent", self.recent_command))
        self.application.add_handler(CommandHandler("health", self.health_command))
        
        logger.info("Configurando handler de botões...")
        # Callback queries (botões inline)
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        logger.info("Configurando handlers de mídia...")
        # Mensagens com fotos
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        
        # Mensagens com documentos (PDF)
        self.application.add_handler(MessageHandler(filters.Document.PDF, self.handle_document))
        
        # Mensagens de texto
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        
        logger.info("Todos os handlers configurados!")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        logger.info(f"Comando /start recebido do usuário {update.effective_user.id}")
        
        try:
            welcome_message = (
                "🤖 *Bot OCR para Notas Fiscais*\n\n"
                "Olá! Eu sou o bot para processamento de Notas Fiscais brasileiras.\n\n"
                "📋 *Como usar:*\n"
                "• Envie uma foto da sua Nota Fiscal\n"
                "• Ou envie um arquivo PDF da NF\n"
                "• Aguarde enquanto processo os dados\n"
                "• Receba o resultado estruturado\n\n"
                "🔧 *Comandos disponíveis:*\n"
                "/help - Ajuda detalhada\n"
                "/stats - Estatísticas do serviço\n"
                "/recent - Últimas notas processadas\n"
                "/health - Status do serviço\n\n"
                "📤 *Comece enviando uma imagem ou PDF!*"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("📊 Estatísticas", callback_data="stats"),
                    InlineKeyboardButton("🔍 Últimas NFs", callback_data="recent")
                ],
                [
                    InlineKeyboardButton("💚 Status", callback_data="health"),
                    InlineKeyboardButton("❓ Ajuda", callback_data="help")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                welcome_message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            
            logger.info("Mensagem de boas-vindas enviada com sucesso")
            
        except Exception as e:
            logger.error(f"Erro no comando /start: {e}")
            await update.message.reply_text("❌ Erro interno. Tente novamente.")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /help"""
        help_message = (
            "📚 *Ajuda - Bot OCR Notas Fiscais*\n\n"
            "🖼️ *Formatos suportados:*\n"
            "• Imagens: JPG, PNG\n"
            "• Documentos: PDF\n"
            "• Tamanho máximo: 10MB\n\n"
            "⚡ *Processo:*\n"
            "1. Envie a imagem/PDF\n"
            "2. Aguarde o processamento (5-30s)\n"
            "3. Receba os dados extraídos\n"
            "4. Dados são salvos automaticamente\n\n"
            "📊 *Dados extraídos:*\n"
            "• Número e série da NF\n"
            "• Datas de emissão/vencimento\n"
            "• Dados do emissor e destinatário\n"
            "• Valores (total, impostos, etc.)\n"
            "• Lista completa de itens\n"
            "• Chave de acesso\n\n"
            "🔧 *Comandos:*\n"
            "/start - Tela inicial\n"
            "/stats - Ver estatísticas\n"
            "/recent - Últimas 5 NFs\n"
            "/health - Status da API\n\n"
            "❓ *Problemas?*\n"
            "Se a imagem não for processada:\n"
            "• Verifique se está legível\n"
            "• Tente uma foto melhor\n"
            "• Contate o suporte"
        )
        
        await update.message.reply_text(help_message, parse_mode=ParseMode.MARKDOWN)
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /stats - Estatísticas do serviço"""
        try:
            stats = await self._get_api_stats()
            if stats:
                stats_message = self._format_stats_message(stats)
                await update.message.reply_text(stats_message, parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text("❌ Erro ao obter estatísticas da API")
        except Exception as e:
            logger.error(f"Erro no comando stats: {e}")
            await update.message.reply_text("❌ Erro interno ao obter estatísticas")
    
    async def recent_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /recent - Últimas notas processadas"""
        try:
            recent_data = await self._get_recent_entries()
            if recent_data:
                recent_message = self._format_recent_message(recent_data)
                await update.message.reply_text(recent_message, parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text("❌ Erro ao obter dados recentes da API")
        except Exception as e:
            logger.error(f"Erro no comando recent: {e}")
            await update.message.reply_text("❌ Erro interno ao obter dados recentes")
    
    async def health_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /health - Status do serviço"""
        try:
            health = await self._get_api_health()
            if health:
                health_message = self._format_health_message(health)
                await update.message.reply_text(health_message, parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text("❌ Serviço indisponível")
        except Exception as e:
            logger.error(f"Erro no comando health: {e}")
            await update.message.reply_text("❌ Erro ao verificar status do serviço")
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler para botões inline"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "stats":
            await self.stats_command(update, context)
        elif query.data == "recent":
            await self.recent_command(update, context)
        elif query.data == "health":
            await self.health_command(update, context)
        elif query.data == "help":
            await self.help_command(update, context)
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa fotos enviadas pelos usuários"""
        try:
            # Obter a foto de maior resolução
            photo = update.message.photo[-1]
            
            # Verificar tamanho do arquivo
            if photo.file_size > 10 * 1024 * 1024:  # 10MB
                await update.message.reply_text(
                    "❌ Arquivo muito grande! Tamanho máximo: 10MB"
                )
                return
            
            # Enviar mensagem de processamento
            processing_msg = await update.message.reply_text(
                "🔄 Processando sua Nota Fiscal...\n⏳ Isso pode levar alguns segundos..."
            )
            
            # Baixar a foto
            file = await context.bot.get_file(photo.file_id)
            file_bytes = await file.download_as_bytearray()
            
            # Processar via API
            result = await self._process_nota_fiscal(file_bytes, "image/jpeg", "foto.jpg")
            
            # Atualizar mensagem com resultado
            await processing_msg.edit_text("✅ Processamento concluído!")
            
            # Enviar resultado
            if result and result.get("success"):
                response_message = self._format_ocr_result(result)
                await update.message.reply_text(response_message, parse_mode=ParseMode.MARKDOWN)
            else:
                error_msg = result.get("error", "Erro desconhecido") if result else "Erro na API"
                await update.message.reply_text(f"❌ Erro no processamento: {error_msg}")
                
        except Exception as e:
            logger.error(f"Erro ao processar foto: {e}")
            await update.message.reply_text("❌ Erro interno ao processar a imagem")
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa documentos PDF enviados pelos usuários"""
        try:
            document = update.message.document
            
            # Verificar se é PDF
            if not document.mime_type == "application/pdf":
                await update.message.reply_text("❌ Apenas arquivos PDF são suportados")
                return
            
            # Verificar tamanho
            if document.file_size > 10 * 1024 * 1024:  # 10MB
                await update.message.reply_text("❌ Arquivo muito grande! Tamanho máximo: 10MB")
                return
            
            # Enviar mensagem de processamento
            processing_msg = await update.message.reply_text(
                "🔄 Processando seu PDF...\n⏳ Isso pode levar alguns segundos..."
            )
            
            # Baixar o documento
            file = await context.bot.get_file(document.file_id)
            file_bytes = await file.download_as_bytearray()
            
            # Processar via API
            result = await self._process_nota_fiscal(file_bytes, "application/pdf", document.file_name)
            
            # Atualizar mensagem com resultado
            await processing_msg.edit_text("✅ Processamento concluído!")
            
            # Enviar resultado
            if result and result.get("success"):
                response_message = self._format_ocr_result(result)
                await update.message.reply_text(response_message, parse_mode=ParseMode.MARKDOWN)
            else:
                error_msg = result.get("error", "Erro desconhecido") if result else "Erro na API"
                await update.message.reply_text(f"❌ Erro no processamento: {error_msg}")
                
        except Exception as e:
            logger.error(f"Erro ao processar documento: {e}")
            await update.message.reply_text("❌ Erro interno ao processar o documento")
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa mensagens de texto"""
        text_message = (
            "📝 *Mensagem recebida!*\n\n"
            "Para processar uma Nota Fiscal, envie:\n"
            "📸 Uma foto da NF\n"
            "📄 Um arquivo PDF\n\n"
            "Digite /help para mais informações"
        )
        
        keyboard = [
            [InlineKeyboardButton("❓ Ajuda", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def _process_nota_fiscal(self, file_bytes: bytes, content_type: str, filename: str) -> Optional[Dict[str, Any]]:
        """Processa nota fiscal via API"""
        try:
            # Preparar dados para upload
            data = aiohttp.FormData()
            data.add_field('file', file_bytes, filename=filename, content_type=content_type)
            
            # Fazer requisição para API
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/nota-fiscal/process",
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status in [200, 422]:  # 422 pode ser erro de OCR mas ainda retorna dados
                        return await response.json()
                    else:
                        logger.error(f"Erro na API: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Erro ao chamar API: {e}")
            return None
    
    async def _get_api_health(self) -> Optional[Dict[str, Any]]:
        """Obtém status da API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base_url}/nota-fiscal/health") as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except Exception as e:
            logger.error(f"Erro ao obter health: {e}")
            return None
    
    async def _get_api_stats(self) -> Optional[Dict[str, Any]]:
        """Obtém estatísticas da API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base_url}/nota-fiscal/sheets/statistics") as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except Exception as e:
            logger.error(f"Erro ao obter stats: {e}")
            return None
    
    async def _get_recent_entries(self) -> Optional[Dict[str, Any]]:
        """Obtém entradas recentes da API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base_url}/nota-fiscal/sheets/recent?limit=5") as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except Exception as e:
            logger.error(f"Erro ao obter dados recentes: {e}")
            return None
    
    def _format_ocr_result(self, result: Dict[str, Any]) -> str:
        """Formata resultado do OCR para o Telegram"""
        if not result.get("success"):
            return f"❌ Erro: {result.get('error', 'Erro desconhecido')}"
        
        ocr_data = result.get("ocr_result", {})
        sheets_data = result.get("sheets_result", {})
        
        # Dados básicos da NF
        nf_data = ocr_data.get("data", {})
        
        message = "✅ *Nota Fiscal Processada com Sucesso!*\n\n"
        
        # Informações principais
        message += "📋 *Dados da NF:*\n"
        message += f"• Número: {nf_data.get('numero_nota', 'N/A')}\n"
        message += f"• Série: {nf_data.get('serie', 'N/A')}\n"
        message += f"• Data Emissão: {nf_data.get('data_emissao', 'N/A')}\n"
        message += f"• Valor Total: R$ {nf_data.get('valor_total', 'N/A')}\n\n"
        
        # Emissor
        message += "🏢 *Emissor:*\n"
        message += f"• {nf_data.get('razao_social_emissor', 'N/A')}\n"
        message += f"• CNPJ: {nf_data.get('cnpj_emissor', 'N/A')}\n\n"
        
        # Destinatário
        message += "📍 *Destinatário:*\n"
        message += f"• {nf_data.get('razao_social_destinatario', 'N/A')}\n"
        message += f"• CNPJ: {nf_data.get('cnpj_destinatario', 'N/A')}\n\n"
        
        # Itens
        items = nf_data.get("items", [])
        if items:
            message += f"📦 *Itens ({len(items)}):*\n"
            for i, item in enumerate(items[:3], 1):  # Mostrar apenas 3 primeiros
                message += f"{i}. {item.get('descricao', 'N/A')[:40]}...\n"
                message += f"   Qtd: {item.get('quantidade', 'N/A')} | Valor: R$ {item.get('valor_total', 'N/A')}\n"
            
            if len(items) > 3:
                message += f"... e mais {len(items) - 3} itens\n"
            message += "\n"
        
        # Status do salvamento
        if sheets_data.get("sheets_updated"):
            message += "💾 *Dados salvos no Google Sheets!*\n"
            updated_sheets = sheets_data.get("sheets_updated", [])
            if updated_sheets:
                message += f"• Planilhas atualizadas: {', '.join(updated_sheets)}\n"
        
        # Tempo de processamento
        processing_time = result.get("processing_time_seconds", 0)
        message += f"\n⏱️ Processado em {processing_time}s"
        
        return message
    
    def _format_health_message(self, health: Dict[str, Any]) -> str:
        """Formata mensagem de status da API"""
        status = health.get("overall_status", "unknown")
        
        if status == "healthy":
            emoji = "✅"
            status_text = "Serviço Funcionando"
        elif status == "partial":
            emoji = "⚠️"
            status_text = "Funcionamento Parcial"
        else:
            emoji = "❌"
            status_text = "Serviço com Problemas"
        
        message = f"{emoji} *{status_text}*\n\n"
        
        services = health.get("services", {})
        
        # Status dos serviços
        message += "🔧 *Componentes:*\n"
        
        ocr_status = services.get("ocr_gemini", {}).get("status", "unknown")
        sheets_status = services.get("google_sheets", {}).get("status", "unknown")
        
        message += f"• OCR (Gemini): {'✅' if ocr_status == 'healthy' else '❌'}\n"
        message += f"• Google Sheets: {'✅' if sheets_status == 'healthy' else '❌'}\n\n"
        
        # Configurações
        config = health.get("configuration", {})
        message += "⚙️ *Configuração:*\n"
        message += f"• Modelo: {config.get('gemini_model', 'N/A')}\n"
        message += f"• Tamanho máx: {config.get('max_file_size_mb', 'N/A')}MB\n"
        
        return message
    
    def _format_stats_message(self, stats: Dict[str, Any]) -> str:
        """Formata mensagem de estatísticas"""
        stats_data = stats.get("statistics", {})
        
        message = "📊 *Estatísticas do Serviço*\n\n"
        
        # Resumo
        resumo = stats_data.get("resumo", {})
        message += "📋 *Notas Fiscais:*\n"
        message += f"• Total processadas: {resumo.get('total_notas', 0)}\n"
        message += f"• Valor total: R$ {resumo.get('valor_total_sum', 0):,.2f}\n"
        
        if resumo.get('last_processed'):
            message += f"• Última: {resumo['last_processed']}\n"
        message += "\n"
        
        # Itens
        itens = stats_data.get("itens", {})
        message += "📦 *Itens:*\n"
        message += f"• Total de itens: {itens.get('total_itens', 0)}\n"
        message += "\n"
        
        # Empresas
        cnpj_count = stats_data.get("cnpj_worksheets", 0)
        message += f"🏢 *Empresas ativas:* {cnpj_count}\n"
        
        empresas = stats_data.get("empresas_ativas", [])
        if empresas:
            message += f"• {', '.join(empresas[:3])}"
            if len(empresas) > 3:
                message += f" e mais {len(empresas) - 3}"
        
        return message
    
    def _format_recent_message(self, recent: Dict[str, Any]) -> str:
        """Formata mensagem de dados recentes"""
        data = recent.get("data", {})
        resumo_data = data.get("resumo", [])
        
        if not resumo_data:
            return "📋 Nenhuma nota fiscal encontrada recentemente"
        
        message = f"🔍 *Últimas {len(resumo_data)} Notas Fiscais:*\n\n"
        
        for i, nf in enumerate(resumo_data, 1):
            message += f"{i}. *NF {nf.get('Número Nota', 'N/A')}*\n"
            message += f"   • Emissor: {nf.get('Razão Social Emissor', 'N/A')[:30]}...\n"
            message += f"   • Valor: R$ {nf.get('Valor Total', 'N/A')}\n"
            message += f"   • Data: {nf.get('Data Emissão', 'N/A')}\n\n"
        
        return message
    
    def run(self):
        """Inicia o bot"""
        logger.info("Iniciando bot do Telegram...")
        
        try:
            logger.info("Iniciando polling...")
            # Usar run_polling de forma simples
            self.application.run_polling()
        except Exception as e:
            logger.error(f"Erro ao iniciar polling: {e}")
            raise

def main():
    """Função principal"""
    print("🤖 Iniciando Bot do Telegram para OCR de Notas Fiscais...")
    
    # Configurações do bot
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    print(f"Token configurado: {'✅' if BOT_TOKEN else '❌'}")
    print(f"API URL: {API_BASE_URL}")
    
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN não encontrado nas variáveis de ambiente")
        print("   Verifique o arquivo .env na raiz do projeto")
        logger.error("TELEGRAM_BOT_TOKEN não encontrado nas variáveis de ambiente")
        sys.exit(1)
    
    # Mostrar configurações (sem expor token completo)
    print(f"🔧 Configurações:")
    print(f"   Token: {BOT_TOKEN[:10]}...")
    print(f"   API: {API_BASE_URL}")
    
    # Criar e iniciar o bot
    print("🚀 Criando instância do bot...")
    try:
        bot = TelegramOCRBot(BOT_TOKEN, API_BASE_URL)
        print("✅ Bot criado com sucesso")
        
        print("🔄 Iniciando polling...")
        print("   Bot rodando - procure por ele no Telegram!")
        print("   Pressione Ctrl+C para parar")
        
        bot.run()
        
    except KeyboardInterrupt:
        print("\n⚠️  Bot interrompido pelo usuário")
        logger.info("Bot interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro no bot: {e}")
        logger.error(f"Erro no bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
