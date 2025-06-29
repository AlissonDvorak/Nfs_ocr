import base64
import io
import json
import logging
from typing import Dict, Any, Optional, Union, List
from pathlib import Path
import tempfile
import os

import google.generativeai as genai
from PIL import Image
import aiofiles
from pdf2image import convert_from_bytes

from ..config.settings import settings

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OCRProcessor:
    """Classe responsável pelo processamento OCR usando Google Gemini 2.0 Flash"""
    
    def __init__(self):
        """Inicializa o processador OCR"""
        try:
            # Configurar a API do Gemini
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
            logger.info(f"OCR Processor inicializado com modelo: {settings.GEMINI_MODEL}")
        except Exception as e:
            logger.error(f"Erro ao inicializar OCR Processor: {e}")
            raise
    
    async def process_nota_fiscal(
        self, 
        image_data: Union[bytes, str, Path], 
        image_format: str = "auto"
    ) -> Dict[str, Any]:
        """
        Processa uma imagem de nota fiscal ou PDF usando Gemini 2.0 Flash
        
        Args:
            image_data: Dados da imagem/PDF (bytes, base64 ou caminho do arquivo)
            image_format: Formato da imagem ("auto", "jpeg", "png", "pdf")
            
        Returns:
            Dicionário com os dados extraídos da nota fiscal
        """
        try:
            # Detectar se é PDF
            is_pdf = await self._is_pdf_data(image_data)
            
            if is_pdf:
                # Processar PDF (múltiplas páginas)
                return await self._process_pdf(image_data)
            else:
                # Processar imagem única
                return await self._process_single_image(image_data, image_format)
            
        except Exception as e:
            logger.error(f"Erro ao processar nota fiscal: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": {}
            }
    
    async def _is_pdf_data(self, data: Union[bytes, str, Path]) -> bool:
        """Verifica se os dados são de um PDF"""
        try:
            if isinstance(data, (str, Path)):
                # Verificar extensão do arquivo
                path = Path(data)
                if path.suffix.lower() == '.pdf':
                    return True
                # Ler o arquivo para verificar o cabeçalho
                async with aiofiles.open(data, 'rb') as f:
                    header = await f.read(5)
            elif isinstance(data, str) and data.startswith('data:'):
                # Base64 data
                if 'application/pdf' in data:
                    return True
                header, encoded_data = data.split(',', 1)
                decoded_data = base64.b64decode(encoded_data)
                header = decoded_data[:5]
            else:
                # Bytes diretos
                header = data[:5] if len(data) >= 5 else data
            
            # Verificar cabeçalho PDF
            return header.startswith(b'%PDF-')
        except:
            return False
    
    async def _process_pdf(self, pdf_data: Union[bytes, str, Path]) -> Dict[str, Any]:
        """Processa um PDF convertendo cada página para imagem e agregando os resultados"""
        try:
            # Obter bytes do PDF
            if isinstance(pdf_data, (str, Path)):
                async with aiofiles.open(pdf_data, 'rb') as f:
                    pdf_bytes = await f.read()
            elif isinstance(pdf_data, str) and pdf_data.startswith('data:'):
                header, data = pdf_data.split(',', 1)
                pdf_bytes = base64.b64decode(data)
            else:
                pdf_bytes = pdf_data
            
            # Converter PDF para imagens
            logger.info("Convertendo PDF para imagens...")
            images = convert_from_bytes(
                pdf_bytes,
                dpi=200,  # Boa qualidade para OCR
                fmt='jpeg',
                thread_count=1  # Para evitar problemas de concorrência
            )
            
            logger.info(f"PDF convertido em {len(images)} páginas")
            
            # Processar cada página
            all_results = []
            aggregated_data = {
                "numero_nota": None,
                "serie": None,
                "data_emissao": None,
                "data_vencimento": None,
                "cnpj_emissor": None,
                "razao_social_emissor": None,
                "endereco_emissor": None,
                "cnpj_destinatario": None,
                "razao_social_destinatario": None,
                "endereco_destinatario": None,
                "valor_total": 0.0,
                "valor_icms": 0.0,
                "valor_ipi": 0.0,
                "valor_pis": 0.0,
                "valor_cofins": 0.0,
                "base_calculo_icms": 0.0,
                "valor_desconto": 0.0,
                "valor_frete": 0.0,
                "chave_acesso": None,
                "protocolo_autorizacao": None,
                "natureza_operacao": None,
                "tipo_pagamento": None,
                "observacoes": "",
                "items": []
            }
            
            for i, image in enumerate(images):
                logger.info(f"Processando página {i + 1} de {len(images)}")
                
                # Converter PIL Image para bytes
                buffer = io.BytesIO()
                image.save(buffer, format='JPEG', quality=95)
                image_bytes = buffer.getvalue()
                
                # Processar a página
                page_result = await self._process_single_image(image_bytes, "jpeg")
                all_results.append({
                    "page": i + 1,
                    "result": page_result
                })
                
                # Agregar dados se o processamento foi bem-sucedido
                if page_result.get("success") and page_result.get("data"):
                    page_data = page_result["data"]
                    
                    # Para a primeira página ou quando ainda não temos dados básicos
                    if i == 0 or not aggregated_data.get("numero_nota"):
                        for field in ["numero_nota", "serie", "data_emissao", "data_vencimento", 
                                    "cnpj_emissor", "razao_social_emissor", "endereco_emissor",
                                    "cnpj_destinatario", "razao_social_destinatario", "endereco_destinatario",
                                    "chave_acesso", "protocolo_autorizacao", "natureza_operacao", 
                                    "tipo_pagamento"]:
                            if page_data.get(field) and not aggregated_data.get(field):
                                aggregated_data[field] = page_data[field]
                    
                    # Agregar valores monetários
                    for field in ["valor_total", "valor_icms", "valor_ipi", "valor_pis", 
                                "valor_cofins", "base_calculo_icms", "valor_desconto", "valor_frete"]:
                        if page_data.get(field) and isinstance(page_data[field], (int, float)):
                            aggregated_data[field] += page_data[field]
                    
                    # Agregar observações
                    if page_data.get("observacoes"):
                        if aggregated_data["observacoes"]:
                            aggregated_data["observacoes"] += f" | Página {i+1}: {page_data['observacoes']}"
                        else:
                            aggregated_data["observacoes"] = f"Página {i+1}: {page_data['observacoes']}"
                    
                    # Agregar itens
                    if page_data.get("items") and isinstance(page_data["items"], list):
                        aggregated_data["items"].extend(page_data["items"])
            
            # Verificar se pelo menos uma página foi processada com sucesso
            success_count = sum(1 for result in all_results if result["result"].get("success"))
            
            result = {
                "success": success_count > 0,
                "pages_processed": len(images),
                "pages_successful": success_count,
                "data": aggregated_data if success_count > 0 else {},
                "page_results": all_results
            }
            
            if success_count > 0:
                logger.info(f"PDF processado com sucesso: {success_count}/{len(images)} páginas")
            else:
                logger.error("Nenhuma página do PDF foi processada com sucesso")
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao processar PDF: {e}")
            return {
                "success": False,
                "error": f"Erro ao processar PDF: {str(e)}",
                "data": {}
            }
    
    async def _process_single_image(
        self, 
        image_data: Union[bytes, str, Path], 
        image_format: str = "auto"
    ) -> Dict[str, Any]:
        """Processa uma única imagem"""
        try:
            # Preparar a imagem
            image = await self._prepare_image(image_data, image_format)
            
            # Criar o prompt para extração de dados da nota fiscal
            prompt = self._create_nota_fiscal_prompt()
            
            # Processar com Gemini
            response = await self._process_with_gemini(image, prompt)
            
            # Processar e validar a resposta
            result = self._parse_response(response)
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao processar imagem: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": {}
            }
    
    async def _prepare_image(
        self, 
        image_data: Union[bytes, str, Path], 
        image_format: str
    ) -> Image.Image:
        """Prepara a imagem para processamento"""
        
        if isinstance(image_data, (str, Path)):
            # Carregar de arquivo
            async with aiofiles.open(image_data, 'rb') as f:
                image_bytes = await f.read()
        elif isinstance(image_data, str) and image_data.startswith('data:'):
            # Dados base64
            header, data = image_data.split(',', 1)
            image_bytes = base64.b64decode(data)
        else:
            # Bytes diretos
            image_bytes = image_data
        
        # Converter para PIL Image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Converter para RGB se necessário
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Redimensionar se muito grande (otimização para Gemini 2.0)
        max_size = (3072, 3072)  # Gemini 2.0 suporta imagens maiores
        if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        return image
    
    def _create_nota_fiscal_prompt(self) -> str:
        """Criar prompt otimizado para Gemini 2.0 Flash para extração de dados de nota fiscal"""
        return """
Você é um especialista em análise de documentos fiscais brasileiros. Analise esta imagem de nota fiscal eletrônica (NFe) ou nota fiscal e extraia TODOS os dados disponíveis de forma precisa e estruturada.

IMPORTANTE: Retorne APENAS um JSON válido com a seguinte estrutura exata:

{
  "success": true,
  "data": {
    "numero_nota": "número da nota fiscal(ignote pontos e virgulas)",
    "serie": "série da nota",
    "data_emissao": "data de emissão no formato DD/MM/AAAA",
    "data_vencimento": "data de vencimento no formato DD/MM/AAAA ou null se não houver",
    "cnpj_emissor": "CNPJ do emissor (apenas números, sem pontuação)",
    "razao_social_emissor": "razão social completa do emissor",
    "endereco_emissor": "endereço completo do emissor",
    "cnpj_destinatario": "CNPJ do destinatário (apenas números, sem pontuação)",
    "razao_social_destinatario": "razão social completa do destinatário",
    "endereco_destinatario": "endereço completo do destinatário",
    "valor_total": 1234.56,
    "valor_icms": 123.45,
    "valor_ipi": 12.34,
    "valor_pis": 12.34,
    "valor_cofins": 12.34,
    "base_calculo_icms": 1234.56,
    "valor_desconto": 12.34,
    "valor_frete": 12.34,
    "chave_acesso": "chave de acesso da NFe (44 dígitos)",
    "protocolo_autorizacao": "protocolo de autorização",
    "natureza_operacao": "descrição da natureza da operação",
    "tipo_pagamento": "forma de pagamento",
    "observacoes": "observações gerais da nota",
    "items": [
      {
        "codigo": "código do produto/serviço",
        "descricao": "descrição completa do produto/serviço",
        "quantidade": "quantidade",
        "unidade": "unidade de medida",
        "valor_unitario": 123.45,
        "valor_total": 1234.56,
        "ncm": "código NCM/SH",
        "cfop": "código CFOP",
        "cst_icms": "CST do ICMS",
        "aliquota_icms": "alíquota do ICMS (%)",
        "valor_icms_item": 12.34
      }
    ]
  }
}

REGRAS IMPORTANTES:
1. Para valores numéricos, use sempre formato decimal (ex: 1234.56, não "1.234,56")
2. Para datas, use formato DD/MM/AAAA
3. Para CNPJs, remova toda pontuação (apenas números)
4. Se um campo não for encontrado, use null (não string vazia)
5. Para arrays vazios, use []
6. Seja muito preciso na extração de números e valores
7. Se não conseguir extrair dados essenciais, retorne: {"success": false, "error": "Descrição específica do problema"}

Extraia TODOS os itens/produtos listados na nota fiscal, mesmo que sejam muitos.
        """
    
    async def _process_with_gemini(self, image: Image.Image, prompt: str) -> str:
        """Processa imagem com Gemini 2.0 Flash"""
        try:
            # Converter imagem para o formato esperado pelo Gemini 2.0
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=95)  # Qualidade alta para Gemini 2.0
            buffer.seek(0)
            
            # Criar conteúdo para o Gemini 2.0
            response = self.model.generate_content([
                prompt,
                image
            ])
            
            return response.text
            
        except Exception as e:
            logger.error(f"Erro ao processar com Gemini 2.0: {e}")
            raise
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse e validação da resposta do Gemini 2.0"""
        try:
            # Limpar a resposta (remover markdown se houver)
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:-3].strip()
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:-3].strip()
            
            # Parse JSON
            result = json.loads(cleaned_response)
            
            # Validar estrutura básica
            if not isinstance(result, dict):
                raise ValueError("Resposta não é um objeto JSON válido")
            
            # Se success não estiver presente, assumir sucesso se há dados
            if "success" not in result:
                result["success"] = "data" in result and result["data"] is not None
            
            # Validar e limpar dados se necessário
            if result.get("success") and "data" in result:
                result["data"] = self._validate_and_clean_data(result["data"])
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao fazer parse da resposta JSON: {e}")
            logger.error(f"Resposta original: {response}")
            return {
                "success": False,
                "error": f"Erro ao interpretar resposta do Gemini: {str(e)}",
                "raw_response": response
            }
        except Exception as e:
            logger.error(f"Erro ao processar resposta: {e}")
            return {
                "success": False,
                "error": str(e),
                "raw_response": response
            }
    
    def _validate_and_clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida e limpa os dados extraídos"""
        try:
            # Converter valores monetários para float quando possível
            monetary_fields = [
                "valor_total", "valor_icms", "valor_ipi", "valor_pis", 
                "valor_cofins", "base_calculo_icms", "valor_desconto", "valor_frete"
            ]
            
            for field in monetary_fields:
                if field in data and data[field] is not None:
                    try:
                        data[field] = float(data[field])
                    except (ValueError, TypeError):
                        data[field] = None
            
            # Validar e limpar itens
            if "items" in data and isinstance(data["items"], list):
                cleaned_items = []
                for item in data["items"]:
                    if isinstance(item, dict):
                        # Limpar valores monetários dos itens
                        item_monetary_fields = ["valor_unitario", "valor_total", "valor_icms_item"]
                        for field in item_monetary_fields:
                            if field in item and item[field] is not None:
                                try:
                                    item[field] = float(item[field])
                                except (ValueError, TypeError):
                                    item[field] = None
                        cleaned_items.append(item)
                data["items"] = cleaned_items
            
            return data
            
        except Exception as e:
            logger.warning(f"Erro ao validar dados: {e}")
            return data
    
    async def extract_text_only(self, image_data: Union[bytes, str, Path]) -> str:
        """
        Extrai apenas o texto da imagem ou PDF (OCR simples)
        
        Args:
            image_data: Dados da imagem ou PDF
            
        Returns:
            Texto extraído da imagem ou PDF
        """
        try:
            # Verificar se é PDF
            is_pdf = await self._is_pdf_data(image_data)
            
            if is_pdf:
                # Processar PDF
                if isinstance(image_data, (str, Path)):
                    async with aiofiles.open(image_data, 'rb') as f:
                        pdf_bytes = await f.read()
                elif isinstance(image_data, str) and image_data.startswith('data:'):
                    header, data = image_data.split(',', 1)
                    pdf_bytes = base64.b64decode(data)
                else:
                    pdf_bytes = image_data
                
                # Converter PDF para imagens
                images = convert_from_bytes(pdf_bytes, dpi=200, fmt='jpeg')
                
                all_text = []
                for i, image in enumerate(images):
                    prompt = f"""
                    Extraia todo o texto visível desta imagem (página {i+1}) de forma precisa e organizada.
                    Mantenha a formatação e estrutura original do documento.
                    Retorne apenas o texto extraído, sem comentários adicionais.
                    """
                    
                    response = await self._process_with_gemini(image, prompt)
                    all_text.append(f"=== PÁGINA {i+1} ===\n{response.strip()}\n")
                
                return "\n".join(all_text)
            else:
                # Processar imagem única
                image = await self._prepare_image(image_data, "auto")
                
                prompt = """
                Extraia todo o texto visível desta imagem de forma precisa e organizada.
                Mantenha a formatação e estrutura original do documento.
                Retorne apenas o texto extraído, sem comentários adicionais.
                """
                
                response = await self._process_with_gemini(image, prompt)
                return response.strip()
            
        except Exception as e:
            logger.error(f"Erro ao extrair texto: {e}")
            return f"Erro ao extrair texto: {str(e)}"
    
    def health_check(self) -> Dict[str, Any]:
        """Verifica o status do serviço"""
        try:
            # Testar conexão com a API
            models = genai.list_models()
            model_count = len(list(models))
            
            return {
                "status": "healthy",
                "model": settings.GEMINI_MODEL,
                "api_connected": True,
                "available_models": model_count,
                "gemini_version": "2.0-flash"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "api_connected": False
            }

# Instância global do processador
ocr_processor = OCRProcessor()