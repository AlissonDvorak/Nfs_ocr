import gspread
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import json
import re

from ..config.settings import settings

# Configurar logging
logger = logging.getLogger(__name__)

class GoogleSheetsManager:
    """Gerenciador estruturado do Google Sheets para salvar dados de notas fiscais"""
    
    def __init__(self):
        """Inicializa o gerenciador do Google Sheets"""
        self.gc = None
        self.spreadsheet = None
        self.worksheet_resumo = None
        self.worksheet_itens = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Inicializa o cliente do Google Sheets"""
        try:
            # Verificar se o arquivo de credenciais existe
            credentials_path = Path(settings.GOOGLE_SHEETS_CREDENTIALS_FILE)
            if not credentials_path.exists():
                logger.error(f"Arquivo de credenciais não encontrado: {credentials_path}")
                raise FileNotFoundError(f"Arquivo de credenciais não encontrado: {credentials_path}")
            
            # Inicializar cliente gspread
            self.gc = gspread.service_account(filename=str(credentials_path))
            
            # Abrir planilha principal
            self.spreadsheet = self.gc.open_by_key(settings.GOOGLE_SHEETS_SPREADSHEET_ID)
            
            # Configurar worksheets principais
            self._setup_main_worksheets()
            
        except Exception as e:
            logger.error(f"Erro ao inicializar Google Sheets: {e}")
            raise
    
    def _setup_main_worksheets(self):
        """Configura as worksheets principais (resumo e itens)"""
        
        # 1. Worksheet de resumo das notas fiscais
        resumo_name = "OCR Notas Fiscais"
        try:
            self.worksheet_resumo = self.spreadsheet.worksheet(resumo_name)
            logger.info(f"Worksheet '{resumo_name}' encontrada")
            
            # Verificar se os cabeçalhos estão corretos
            existing_headers = self.worksheet_resumo.row_values(1)
            if not existing_headers or len(existing_headers) < 20:
                logger.info("Cabeçalhos incompletos ou ausentes, reconfigurando...")
                self._setup_resumo_headers()
                
        except gspread.WorksheetNotFound:
            # Criar nova worksheet de resumo
            self.worksheet_resumo = self.spreadsheet.add_worksheet(
                title=resumo_name,
                rows=1000,
                cols=25
            )
            logger.info(f"Nova worksheet '{resumo_name}' criada")
            self._setup_resumo_headers()
        
        # 2. Worksheet de itens das notas fiscais
        itens_name = "OCR Notas Fiscais - Itens"
        try:
            self.worksheet_itens = self.spreadsheet.worksheet(itens_name)
            logger.info(f"Worksheet '{itens_name}' encontrada")
            
            # Verificar se os cabeçalhos estão corretos
            existing_headers = self.worksheet_itens.row_values(1)
            if not existing_headers or len(existing_headers) < 15:
                logger.info("Cabeçalhos de itens incompletos ou ausentes, reconfigurando...")
                self._setup_itens_headers()
                
        except gspread.WorksheetNotFound:
            # Criar nova worksheet de itens
            self.worksheet_itens = self.spreadsheet.add_worksheet(
                title=itens_name,
                rows=5000,
                cols=20
            )
            logger.info(f"Nova worksheet '{itens_name}' criada")
            self._setup_itens_headers()
    
    def _setup_resumo_headers(self):
        """Configura os cabeçalhos da planilha de resumo"""
        headers = [
            "ID Processamento",
            "Data/Hora Processamento", 
            "Nome Arquivo",
            "Número Nota",
            "Série",
            "Data Emissão",
            "Data Vencimento",
            "CNPJ Emissor",
            "Razão Social Emissor",
            "CNPJ Destinatário",
            "Razão Social Destinatário",
            "Valor Total",
            "Valor ICMS",
            "Valor IPI",
            "Valor PIS",
            "Valor COFINS",
            "Base Cálculo ICMS",
            "Valor Desconto",
            "Valor Frete",
            "Chave Acesso",
            "Protocolo Autorização",
            "Natureza Operação",
            "Quantidade Itens",
            "Status Processamento"
        ]
        
        try:
            # Limpar a planilha completamente
            self.worksheet_resumo.clear()
            
            # Aguardar um momento para garantir que a limpeza foi processada
            import time
            time.sleep(1)
            
            # Inserir cabeçalhos na primeira linha usando update range
            range_name = f'A1:{chr(ord("A") + len(headers) - 1)}1'
            self.worksheet_resumo.update(range_name, [headers], value_input_option='RAW')
            
            # Aguardar processamento
            time.sleep(1)
            
            # Aplicar formatação aos cabeçalhos
            try:
                self.worksheet_resumo.format(range_name, {
                    'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 1.0},
                    'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
                    'horizontalAlignment': 'CENTER'
                })
            except Exception as format_error:
                logger.warning(f"Erro na formatação dos cabeçalhos de resumo: {format_error}")
            
            # Congelar a primeira linha
            try:
                self.worksheet_resumo.freeze(rows=1)
            except Exception as freeze_error:
                logger.warning(f"Erro ao congelar primeira linha: {freeze_error}")
            
            # Verificar se os cabeçalhos foram inseridos corretamente
            verification_headers = self.worksheet_resumo.row_values(1)
            if len(verification_headers) != len(headers):
                logger.warning(f"Verificação falhou: esperado {len(headers)} cabeçalhos, obtido {len(verification_headers)}")
                # Tentar novamente com método alternativo
                for i, header in enumerate(headers, 1):
                    self.worksheet_resumo.update_acell(f'{chr(ord("A") + i - 1)}1', header)
            
            logger.info(f"Cabeçalhos de resumo configurados: {len(headers)} colunas")
        except Exception as e:
            logger.error(f"Erro ao configurar cabeçalhos de resumo: {e}")
            raise
    
    def _setup_itens_headers(self):
        """Configura os cabeçalhos da planilha de itens"""
        headers = [
            "ID Processamento",
            "Número Nota",
            "CNPJ Emissor",
            "Razão Social Emissor",
            "Item Sequencia",
            "Código Produto",
            "Descrição Produto",
            "Quantidade",
            "Unidade",
            "Valor Unitário",
            "Valor Total Item",
            "NCM",
            "CFOP",
            "CST ICMS",
            "Alíquota ICMS",
            "Valor ICMS Item",
            "Data Processamento",
            "Nome Arquivo"
        ]
        
        try:
            # Limpar a planilha completamente
            self.worksheet_itens.clear()
            
            # Aguardar um momento para garantir que a limpeza foi processada
            import time
            time.sleep(1)
            
            # Inserir cabeçalhos na primeira linha usando update range
            range_name = f'A1:{chr(ord("A") + len(headers) - 1)}1'
            self.worksheet_itens.update(range_name, [headers], value_input_option='RAW')
            
            # Aguardar processamento
            time.sleep(1)
            
            # Aplicar formatação aos cabeçalhos
            try:
                self.worksheet_itens.format(range_name, {
                    'backgroundColor': {'red': 0.0, 'green': 0.7, 'blue': 0.3},
                    'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
                    'horizontalAlignment': 'CENTER'
                })
            except Exception as format_error:
                logger.warning(f"Erro na formatação dos cabeçalhos de itens: {format_error}")
            
            # Congelar a primeira linha
            try:
                self.worksheet_itens.freeze(rows=1)
            except Exception as freeze_error:
                logger.warning(f"Erro ao congelar primeira linha: {freeze_error}")
            
            # Verificar se os cabeçalhos foram inseridos corretamente
            verification_headers = self.worksheet_itens.row_values(1)
            if len(verification_headers) != len(headers):
                logger.warning(f"Verificação falhou: esperado {len(headers)} cabeçalhos, obtido {len(verification_headers)}")
                # Tentar novamente com método alternativo
                for i, header in enumerate(headers, 1):
                    self.worksheet_itens.update_acell(f'{chr(ord("A") + i - 1)}1', header)
            
            logger.info(f"Cabeçalhos de itens configurados: {len(headers)} colunas")
        except Exception as e:
            logger.error(f"Erro ao configurar cabeçalhos de itens: {e}")
            raise
    
    def _get_or_create_cnpj_worksheet(self, cnpj: str, razao_social: str) -> Optional[gspread.Worksheet]:
        """
        Obtém ou cria uma worksheet específica para um CNPJ
        
        Args:
            cnpj: CNPJ do emissor
            razao_social: Razão social do emissor
            
        Returns:
            Worksheet específica do CNPJ ou None se houver erro
        """
        try:
            if not cnpj or cnpj == "N/A":
                return None
            
            # Limpar CNPJ para nome da worksheet
            cnpj_clean = re.sub(r'[^\d]', '', str(cnpj))
            if len(cnpj_clean) != 14:
                logger.warning(f"CNPJ inválido para criar worksheet: {cnpj}")
                return None
            
            # Criar nome da worksheet (limitado a 100 caracteres)
            razao_clean = re.sub(r'[^\w\s-]', '', str(razao_social))[:30] if razao_social else "Empresa"
            worksheet_name = f"CNPJ_{cnpj_clean[:8]}_{razao_clean}"
            
            # Tentar encontrar worksheet existente
            try:
                worksheet = self.spreadsheet.worksheet(worksheet_name)
                logger.info(f"Worksheet CNPJ encontrada: {worksheet_name}")
                return worksheet
            except gspread.WorksheetNotFound:
                # Criar nova worksheet para o CNPJ
                worksheet = self.spreadsheet.add_worksheet(
                    title=worksheet_name,
                    rows=1000,
                    cols=25
                )
                
                # Configurar cabeçalhos específicos para o CNPJ
                self._setup_cnpj_headers(worksheet, cnpj_clean, razao_social)
                
                logger.info(f"Nova worksheet CNPJ criada: {worksheet_name}")
                return worksheet
                
        except Exception as e:
            logger.error(f"Erro ao criar/obter worksheet CNPJ {cnpj}: {e}")
            return None
    
    def _setup_cnpj_headers(self, worksheet: gspread.Worksheet, cnpj: str, razao_social: str):
        """Configura cabeçalhos para worksheet específica de CNPJ"""
        
        # Informações da empresa
        info_headers = [
            f"CNPJ: {cnpj}",
            f"Razão Social: {razao_social}",
            f"Relatório gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        ]
        
        # Cabeçalhos dos dados
        data_headers = [
            "Data Processamento",
            "Número Nota",
            "Série",
            "Data Emissão",
            "CNPJ Destinatário",
            "Razão Social Destinatário",
            "Valor Total",
            "Valor ICMS",
            "Valor IPI",
            "Chave Acesso",
            "Quantidade Itens",
            "Nome Arquivo",
            "Status"
        ]
        
        try:
            # Inserir informações da empresa
            for i, info in enumerate(info_headers, 1):
                worksheet.update(f'A{i}', info)
            
            # Inserir cabeçalhos dos dados na linha 5
            worksheet.update('A5:M5', [data_headers])
            
            # Formatação
            worksheet.format('A1:A3', {
                'backgroundColor': {'red': 1.0, 'green': 0.9, 'blue': 0.2},
                'textFormat': {'bold': True}
            })
            worksheet.format('A5:M5', {
                'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8},
                'textFormat': {'bold': True}
            })
            
        except Exception as e:
            logger.error(f"Erro ao configurar cabeçalhos CNPJ: {e}")
    
    def _generate_processing_id(self) -> str:
        """Gera um ID único para o processamento"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"OCR_{timestamp}"
    
    async def save_nota_fiscal_data(
        self, 
        ocr_data: Dict[str, Any], 
        filename: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Salva os dados da nota fiscal de forma estruturada nas planilhas
        
        Args:
            ocr_data: Dados extraídos pelo OCR
            filename: Nome do arquivo processado
            
        Returns:
            Resultado da operação
        """
        try:
            if not ocr_data.get("success", False):
                logger.warning("Dados OCR indicam falha no processamento")
                return {
                    "success": False,
                    "error": "Dados OCR indicam falha no processamento",
                    "sheets_updated": False
                }
            
            data = ocr_data.get("data", {})
            if not data:
                logger.warning("Nenhum dado encontrado para salvar")
                return {
                    "success": False,
                    "error": "Nenhum dado encontrado para salvar",
                    "sheets_updated": False
                }
            
            # Gerar ID único para este processamento
            processing_id = self._generate_processing_id()
            
            # 1. Salvar dados resumidos na planilha principal
            resumo_result = await self._save_resumo_data(data, filename, processing_id)
            
            # 2. Salvar itens na planilha de itens
            itens_result = await self._save_itens_data(data, filename, processing_id)
            
            # 3. Salvar na planilha específica do CNPJ (se possível)
            cnpj_result = await self._save_cnpj_data(data, filename, processing_id)
            
            # Consolidar resultados
            sheets_updated = []
            if resumo_result.get("success"):
                sheets_updated.append("Resumo")
            if itens_result.get("success"):
                sheets_updated.append("Itens")
            if cnpj_result.get("success"):
                sheets_updated.append("CNPJ")
            
            success = len(sheets_updated) > 0
            
            logger.info(f"Dados salvos - ID: {processing_id}, Planilhas: {', '.join(sheets_updated)}")
            
            return {
                "success": success,
                "message": f"Dados salvos em {len(sheets_updated)} planilha(s)",
                "processing_id": processing_id,
                "sheets_updated": sheets_updated,
                "details": {
                    "resumo": resumo_result,
                    "itens": itens_result,
                    "cnpj": cnpj_result
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao salvar dados nas planilhas: {e}")
            return {
                "success": False,
                "error": str(e),
                "sheets_updated": []
            }
    
    async def _save_resumo_data(self, data: Dict[str, Any], filename: str, processing_id: str) -> Dict[str, Any]:
        """Salva dados resumidos na planilha principal"""
        try:
            # Função helper para conversão segura
            def safe_str(value, default=""):
                if value is None:
                    return default
                return str(value)
            
            def safe_float_str(value, default=""):
                if value is None or value == "":
                    return default
                try:
                    return str(float(value))
                except (ValueError, TypeError):
                    return default
            
            items = data.get("items", [])
            items_count = len(items)
            
            # Preparar linha de dados resumidos
            row_data = [
                processing_id,                                      # ID Processamento
                datetime.now().strftime("%d/%m/%Y %H:%M:%S"),      # Data/Hora Processamento
                safe_str(filename),                                # Nome Arquivo
                safe_str(data.get("numero_nota")),                # Número Nota
                safe_str(data.get("serie")),                      # Série
                safe_str(data.get("data_emissao")),               # Data Emissão
                safe_str(data.get("data_vencimento")),            # Data Vencimento
                safe_str(data.get("cnpj_emissor")),               # CNPJ Emissor
                safe_str(data.get("razao_social_emissor")),       # Razão Social Emissor
                safe_str(data.get("cnpj_destinatario")),          # CNPJ Destinatário
                safe_str(data.get("razao_social_destinatario")),  # Razão Social Destinatário
                safe_float_str(data.get("valor_total")),          # Valor Total
                safe_float_str(data.get("valor_icms")),           # Valor ICMS
                safe_float_str(data.get("valor_ipi")),            # Valor IPI
                safe_float_str(data.get("valor_pis")),            # Valor PIS
                safe_float_str(data.get("valor_cofins")),         # Valor COFINS
                safe_float_str(data.get("base_calculo_icms")),    # Base Cálculo ICMS
                safe_float_str(data.get("valor_desconto")),       # Valor Desconto
                safe_float_str(data.get("valor_frete")),          # Valor Frete
                safe_str(data.get("chave_acesso")),               # Chave Acesso
                safe_str(data.get("protocolo_autorizacao")),      # Protocolo Autorização
                safe_str(data.get("natureza_operacao")),          # Natureza Operação
                str(items_count),                                 # Quantidade Itens
                "Processado com Sucesso"                          # Status Processamento
            ]
            
            # Inserir na planilha de resumo
            self.worksheet_resumo.append_row(row_data)
            
            return {
                "success": True,
                "message": "Dados resumidos salvos com sucesso",
                "rows_added": 1
            }
            
        except Exception as e:
            logger.error(f"Erro ao salvar dados resumidos: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _save_itens_data(self, data: Dict[str, Any], filename: str, processing_id: str) -> Dict[str, Any]:
        """Salva itens detalhados na planilha de itens"""
        try:
            items = data.get("items", [])
            if not items:
                return {
                    "success": True,
                    "message": "Nenhum item para salvar",
                    "rows_added": 0
                }
            
            # Função helper para conversão segura
            def safe_str(value, default=""):
                if value is None:
                    return default
                return str(value)
            
            def safe_float_str(value, default=""):
                if value is None or value == "":
                    return default
                try:
                    return str(float(value))
                except (ValueError, TypeError):
                    return default
            
            # Preparar dados dos itens
            items_rows = []
            for i, item in enumerate(items, 1):
                item_row = [
                    processing_id,                                    # ID Processamento
                    safe_str(data.get("numero_nota")),              # Número Nota
                    safe_str(data.get("cnpj_emissor")),             # CNPJ Emissor
                    safe_str(data.get("razao_social_emissor")),     # Razão Social Emissor
                    str(i),                                         # Item Sequencia
                    safe_str(item.get("codigo")),                   # Código Produto
                    safe_str(item.get("descricao")),                # Descrição Produto
                    safe_str(item.get("quantidade")),               # Quantidade
                    safe_str(item.get("unidade")),                  # Unidade
                    safe_float_str(item.get("valor_unitario")),     # Valor Unitário
                    safe_float_str(item.get("valor_total")),        # Valor Total Item
                    safe_str(item.get("ncm")),                      # NCM
                    safe_str(item.get("cfop")),                     # CFOP
                    safe_str(item.get("cst_icms")),                 # CST ICMS
                    safe_str(item.get("aliquota_icms")),            # Alíquota ICMS
                    safe_float_str(item.get("valor_icms_item")),    # Valor ICMS Item
                    datetime.now().strftime("%d/%m/%Y %H:%M:%S"),   # Data Processamento
                    safe_str(filename)                              # Nome Arquivo
                ]
                items_rows.append(item_row)
            
            # Inserir todos os itens de uma vez
            if items_rows:
                # Encontrar a próxima linha vazia
                next_row = len(self.worksheet_itens.get_all_values()) + 1
                
                # Definir range para inserção
                end_col = chr(ord('A') + len(items_rows[0]) - 1)  # R = 18ª coluna
                range_name = f"A{next_row}:{end_col}{next_row + len(items_rows) - 1}"
                
                # Inserir dados
                self.worksheet_itens.update(range_name, items_rows)
            
            return {
                "success": True,
                "message": f"{len(items_rows)} itens salvos com sucesso",
                "rows_added": len(items_rows)
            }
            
        except Exception as e:
            logger.error(f"Erro ao salvar itens: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _save_cnpj_data(self, data: Dict[str, Any], filename: str, processing_id: str) -> Dict[str, Any]:
        """Salva dados na planilha específica do CNPJ"""
        try:
            cnpj = data.get("cnpj_emissor")
            razao_social = data.get("razao_social_emissor")
            
            if not cnpj or cnpj == "N/A":
                return {
                    "success": False,
                    "message": "CNPJ não disponível para criar planilha específica"
                }
            
            # Obter ou criar worksheet específica
            cnpj_worksheet = self._get_or_create_cnpj_worksheet(cnpj, razao_social)
            if not cnpj_worksheet:
                return {
                    "success": False,
                    "message": "Não foi possível criar/acessar worksheet do CNPJ"
                }
            
            # Função helper para conversão segura
            def safe_str(value, default=""):
                if value is None:
                    return default
                return str(value)
            
            def safe_float_str(value, default=""):
                if value is None or value == "":
                    return default
                try:
                    return str(float(value))
                except (ValueError, TypeError):
                    return default
            
            # Preparar dados específicos do CNPJ
            cnpj_row = [
                datetime.now().strftime("%d/%m/%Y %H:%M:%S"),     # Data Processamento
                safe_str(data.get("numero_nota")),               # Número Nota
                safe_str(data.get("serie")),                     # Série
                safe_str(data.get("data_emissao")),              # Data Emissão
                safe_str(data.get("cnpj_destinatario")),         # CNPJ Destinatário
                safe_str(data.get("razao_social_destinatario")), # Razão Social Destinatário
                safe_float_str(data.get("valor_total")),         # Valor Total
                safe_float_str(data.get("valor_icms")),          # Valor ICMS
                safe_float_str(data.get("valor_ipi")),           # Valor IPI
                safe_str(data.get("chave_acesso")),              # Chave Acesso
                str(len(data.get("items", []))),                 # Quantidade Itens
                safe_str(filename),                              # Nome Arquivo
                "Processado"                                     # Status
            ]
            
            # Inserir na worksheet específica (a partir da linha 6)
            cnpj_worksheet.append_row(cnpj_row)
            
            return {
                "success": True,
                "message": f"Dados salvos na planilha do CNPJ {cnpj}",
                "worksheet_name": cnpj_worksheet.title
            }
            
        except Exception as e:
            logger.error(f"Erro ao salvar dados do CNPJ: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_recent_entries(self, limit: int = 10, worksheet_type: str = "resumo") -> List[Dict[str, Any]]:
        """
        Recupera as últimas entradas das planilhas
        
        Args:
            limit: Número máximo de entradas para retornar
            worksheet_type: Tipo da planilha ("resumo", "itens", "all")
            
        Returns:
            Lista com as últimas entradas
        """
        try:
            result = {}
            
            if worksheet_type in ["resumo", "all"]:
                # Obter dados da planilha de resumo
                try:
                    # Verificar se há cabeçalhos primeiro
                    headers = self.worksheet_resumo.row_values(1)
                    if not headers or len(headers) < 10:
                        logger.warning("Cabeçalhos de resumo ausentes ou incompletos, reconfigurando...")
                        self._setup_resumo_headers()
                        headers = self.worksheet_resumo.row_values(1)
                    
                    # Obter todos os dados usando get_all_values para garantir estrutura
                    all_values = self.worksheet_resumo.get_all_values()
                    if len(all_values) <= 1:  # Só cabeçalhos ou vazio
                        resumo_records = []
                    else:
                        # Converter para dicionários manualmente usando os cabeçalhos
                        resumo_records = []
                        for row in all_values[1:]:  # Pular cabeçalhos
                            if any(cell.strip() for cell in row):  # Linha não vazia
                                record = {}
                                for i, header in enumerate(headers):
                                    if i < len(row):
                                        record[header] = row[i]
                                    else:
                                        record[header] = ""
                                resumo_records.append(record)
                    
                    recent_resumo = resumo_records[-limit:] if len(resumo_records) > limit else resumo_records
                    recent_resumo.reverse()  # Mais recentes primeiro
                    result["resumo"] = recent_resumo
                    
                except Exception as e:
                    logger.error(f"Erro ao obter dados de resumo: {e}")
                    result["resumo"] = []
            
            if worksheet_type in ["itens", "all"]:
                # Obter dados da planilha de itens
                try:
                    # Verificar se há cabeçalhos primeiro
                    headers = self.worksheet_itens.row_values(1)
                    if not headers or len(headers) < 10:
                        logger.warning("Cabeçalhos de itens ausentes ou incompletos, reconfigurando...")
                        self._setup_itens_headers()
                        headers = self.worksheet_itens.row_values(1)
                    
                    # Obter todos os dados usando get_all_values para garantir estrutura
                    all_values = self.worksheet_itens.get_all_values()
                    if len(all_values) <= 1:  # Só cabeçalhos ou vazio
                        itens_records = []
                    else:
                        # Converter para dicionários manualmente usando os cabeçalhos
                        itens_records = []
                        for row in all_values[1:]:  # Pular cabeçalhos
                            if any(cell.strip() for cell in row):  # Linha não vazia
                                record = {}
                                for i, header in enumerate(headers):
                                    if i < len(row):
                                        record[header] = row[i]
                                    else:
                                        record[header] = ""
                                itens_records.append(record)
                    
                    recent_itens = itens_records[-limit*3:] if len(itens_records) > limit*3 else itens_records
                    recent_itens.reverse()  # Mais recentes primeiro
                    result["itens"] = recent_itens
                    
                except Exception as e:
                    logger.error(f"Erro ao obter dados de itens: {e}")
                    result["itens"] = []
            
            if worksheet_type == "all":
                return result
            elif worksheet_type == "resumo":
                return result.get("resumo", [])
            elif worksheet_type == "itens":
                return result.get("itens", [])
            
            return []
            
        except Exception as e:
            logger.error(f"Erro ao recuperar entradas recentes: {e}")
            return []
    
    def get_cnpj_worksheets(self) -> List[Dict[str, str]]:
        """
        Lista todas as worksheets de CNPJ existentes
        
        Returns:
            Lista com informações das worksheets de CNPJ
        """
        try:
            worksheets = self.spreadsheet.worksheets()
            cnpj_worksheets = []
            
            for ws in worksheets:
                if ws.title.startswith("CNPJ_"):
                    # Extrair informações do nome
                    parts = ws.title.split("_", 2)
                    if len(parts) >= 3:
                        cnpj_part = parts[1]
                        empresa_part = parts[2]
                        
                        cnpj_worksheets.append({
                            "worksheet_name": ws.title,
                            "cnpj": cnpj_part,
                            "empresa": empresa_part,
                            "url": ws.url
                        })
            
            return cnpj_worksheets
            
        except Exception as e:
            logger.error(f"Erro ao listar worksheets CNPJ: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtém estatísticas das planilhas
        
        Returns:
            Estatísticas consolidadas
        """
        try:
            stats = {
                "resumo": {
                    "total_notas": 0,
                    "valor_total_sum": 0.0,
                    "last_processed": None
                },
                "itens": {
                    "total_itens": 0,
                    "last_processed": None
                },
                "cnpj_worksheets": 0,
                "empresas_ativas": []
            }
            
            # Estatísticas do resumo
            try:
                # Verificar cabeçalhos primeiro
                headers = self.worksheet_resumo.row_values(1)
                if not headers or len(headers) < 10:
                    logger.warning("Cabeçalhos de resumo ausentes, reconfigurando...")
                    self._setup_resumo_headers()
                    headers = self.worksheet_resumo.row_values(1)
                
                # Obter dados usando get_all_values
                all_values = self.worksheet_resumo.get_all_values()
                if len(all_values) > 1:  # Tem dados além dos cabeçalhos
                    resumo_records = []
                    for row in all_values[1:]:  # Pular cabeçalhos
                        if any(cell.strip() for cell in row):  # Linha não vazia
                            record = {}
                            for i, header in enumerate(headers):
                                if i < len(row):
                                    record[header] = row[i]
                                else:
                                    record[header] = ""
                            resumo_records.append(record)
                    
                    stats["resumo"]["total_notas"] = len(resumo_records)
                    
                    if resumo_records:
                        stats["resumo"]["last_processed"] = resumo_records[-1].get("Data/Hora Processamento")
                        
                        # Somar valores totais
                        for record in resumo_records:
                            try:
                                valor = float(record.get("Valor Total", 0) or 0)
                                stats["resumo"]["valor_total_sum"] += valor
                            except (ValueError, TypeError):
                                pass
                else:
                    stats["resumo"]["total_notas"] = 0
                    
            except Exception as e:
                logger.error(f"Erro ao obter estatísticas de resumo: {e}")
            
            # Estatísticas dos itens
            try:
                # Verificar cabeçalhos primeiro
                headers = self.worksheet_itens.row_values(1)
                if not headers or len(headers) < 10:
                    logger.warning("Cabeçalhos de itens ausentes, reconfigurando...")
                    self._setup_itens_headers()
                    headers = self.worksheet_itens.row_values(1)
                
                # Obter dados usando get_all_values
                all_values = self.worksheet_itens.get_all_values()
                if len(all_values) > 1:  # Tem dados além dos cabeçalhos
                    itens_records = []
                    for row in all_values[1:]:  # Pular cabeçalhos
                        if any(cell.strip() for cell in row):  # Linha não vazia
                            record = {}
                            for i, header in enumerate(headers):
                                if i < len(row):
                                    record[header] = row[i]
                                else:
                                    record[header] = ""
                            itens_records.append(record)
                    
                    stats["itens"]["total_itens"] = len(itens_records)
                    
                    if itens_records:
                        stats["itens"]["last_processed"] = itens_records[-1].get("Data Processamento")
                else:
                    stats["itens"]["total_itens"] = 0
                    
            except Exception as e:
                logger.error(f"Erro ao obter estatísticas de itens: {e}")
            
            # Estatísticas de CNPJ
            cnpj_worksheets = self.get_cnpj_worksheets()
            stats["cnpj_worksheets"] = len(cnpj_worksheets)
            stats["empresas_ativas"] = [ws["empresa"] for ws in cnpj_worksheets]
            
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {}
    
    def health_check(self) -> Dict[str, Any]:
        """Verifica o status da conexão com Google Sheets"""
        try:
            # Testar conexão obtendo informações da planilha
            spreadsheet_info = {
                "id": self.spreadsheet.id,
                "title": self.spreadsheet.title,
                "url": self.spreadsheet.url
            }
            
            worksheets = self.spreadsheet.worksheets()
            worksheet_info = []
            
            for ws in worksheets:
                worksheet_info.append({
                    "title": ws.title,
                    "rows": ws.row_count,
                    "cols": ws.col_count
                })
            
            # Obter estatísticas básicas
            stats = self.get_statistics()
            
            return {
                "status": "healthy",
                "connected": True,
                "spreadsheet": spreadsheet_info,
                "worksheets": worksheet_info,
                "total_worksheets": len(worksheets),
                "cnpj_worksheets": len([ws for ws in worksheets if ws.title.startswith("CNPJ_")]),
                "statistics": stats
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e)
            }
    
    def ensure_headers(self, force_recreation: bool = False):
        """
        Garante que os cabeçalhos das planilhas principais estejam corretos
        
        Args:
            force_recreation: Se True, força a recriação dos cabeçalhos
        """
        try:
            # Verificar e corrigir cabeçalhos da planilha de resumo
            if force_recreation:
                logger.info("Forçando recriação dos cabeçalhos de resumo...")
                self._setup_resumo_headers()
            else:
                headers = self.worksheet_resumo.row_values(1)
                expected_headers = [
                    "ID Processamento", "Data/Hora Processamento", "Nome Arquivo",
                    "Número Nota", "Série", "Data Emissão", "Data Vencimento",
                    "CNPJ Emissor", "Razão Social Emissor", "CNPJ Destinatário",
                    "Razão Social Destinatário", "Valor Total", "Valor ICMS",
                    "Valor IPI", "Valor PIS", "Valor COFINS", "Base Cálculo ICMS",
                    "Valor Desconto", "Valor Frete", "Chave Acesso",
                    "Protocolo Autorização", "Natureza Operação", "Quantidade Itens",
                    "Status Processamento"
                ]
                
                if not headers or len(headers) < len(expected_headers) or headers[:len(expected_headers)] != expected_headers:
                    logger.warning("Cabeçalhos de resumo incorretos, corrigindo...")
                    self._setup_resumo_headers()
            
            # Verificar e corrigir cabeçalhos da planilha de itens
            if force_recreation:
                logger.info("Forçando recriação dos cabeçalhos de itens...")
                self._setup_itens_headers()
            else:
                headers = self.worksheet_itens.row_values(1)
                expected_headers = [
                    "ID Processamento", "Número Nota", "CNPJ Emissor",
                    "Razão Social Emissor", "Item Sequencia", "Código Produto",
                    "Descrição Produto", "Quantidade", "Unidade", "Valor Unitário",
                    "Valor Total Item", "NCM", "CFOP", "CST ICMS", "Alíquota ICMS",
                    "Valor ICMS Item", "Data Processamento", "Nome Arquivo"
                ]
                
                if not headers or len(headers) < len(expected_headers) or headers[:len(expected_headers)] != expected_headers:
                    logger.warning("Cabeçalhos de itens incorretos, corrigindo...")
                    self._setup_itens_headers()
                    
            logger.info("Verificação de cabeçalhos concluída")
            
        except Exception as e:
            logger.error(f"Erro ao verificar cabeçalhos: {e}")

    def get_safe_records(self, worksheet, worksheet_name: str) -> List[Dict[str, Any]]:
        """
        Obtém registros de uma planilha de forma segura, garantindo que os cabeçalhos existam
        
        Args:
            worksheet: Planilha do Google Sheets
            worksheet_name: Nome da planilha (para logging)
            
        Returns:
            Lista de registros com nomes de colunas corretos
        """
        try:
            # Verificar se há cabeçalhos
            headers = worksheet.row_values(1)
            if not headers:
                logger.warning(f"Planilha {worksheet_name} sem cabeçalhos")
                return []
            
            # Obter todos os dados
            all_values = worksheet.get_all_values()
            if len(all_values) <= 1:  # Só cabeçalhos ou vazio
                return []
            
            # Converter para dicionários usando os cabeçalhos
            records = []
            for row in all_values[1:]:  # Pular cabeçalhos
                if any(cell.strip() for cell in row):  # Linha não vazia
                    record = {}
                    for i, header in enumerate(headers):
                        if i < len(row):
                            record[header] = row[i]
                        else:
                            record[header] = ""
                    records.append(record)
            
            return records
            
        except Exception as e:
            logger.error(f"Erro ao obter registros seguros de {worksheet_name}: {e}")
            return []

# Instância global do gerenciador
sheets_manager = GoogleSheetsManager()