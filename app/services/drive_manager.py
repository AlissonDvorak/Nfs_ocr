import io
import logging
from typing import Dict, Any, Optional, Union
from datetime import datetime
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor

from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google.oauth2.credentials import Credentials as OAuthCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError

from ..config.settings import settings
from .local_file_manager import local_file_manager

# Configurar logging
logger = logging.getLogger(__name__)

class GoogleDriveManager:
    """Gerenciador para Google Drive API"""
    
    def __init__(self):
        """Inicializa o gerenciador do Google Drive"""
        self.service = None
        self.root_folder_id = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        if settings.GOOGLE_DRIVE_ENABLED:
            try:
                self._initialize_service()
                logger.info("Google Drive Manager inicializado com sucesso")
            except Exception as e:
                logger.error(f"Erro ao inicializar Google Drive Manager: {e}")
                raise
        else:
            logger.info("Google Drive desabilitado nas configurações")
    
    def _initialize_service(self):
        """Inicializa o serviço do Google Drive"""
        try:
            if settings.GOOGLE_DRIVE_USE_OAUTH:
                # Usar OAuth2 para acesso ao Drive pessoal
                credentials = self._get_oauth_credentials()
            else:
                # Usar Service Account (modo anterior)
                credentials = ServiceAccountCredentials.from_service_account_file(
                    settings.GOOGLE_DRIVE_CREDENTIALS_FILE,
                    scopes=['https://www.googleapis.com/auth/drive']
                )
            
            # Criar serviço do Google Drive
            self.service = build('drive', 'v3', credentials=credentials)
            
            # Obter ou criar pasta raiz
            self.root_folder_id = self._get_or_create_folder(settings.GOOGLE_DRIVE_ROOT_FOLDER_NAME)
            
        except Exception as e:
            logger.error(f"Erro ao inicializar serviço do Google Drive: {e}")
            raise
    
    def _get_oauth_credentials(self):
        """Obtém credenciais OAuth2 para acesso ao Drive pessoal"""
        SCOPES = ['https://www.googleapis.com/auth/drive']
        creds = None
        
        # Verificar se já existe token salvo
        token_file = Path(settings.GOOGLE_DRIVE_TOKEN_FILE)
        if token_file.exists():
            try:
                creds = OAuthCredentials.from_authorized_user_file(str(token_file), SCOPES)
                logger.info("Token OAuth2 carregado com sucesso")
            except Exception as e:
                logger.warning(f"Erro ao carregar token existente: {e}")
        
        # Se não há credenciais válidas disponíveis, fazer login
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Token OAuth2 renovado com sucesso")
                except Exception as e:
                    logger.warning(f"Erro ao renovar token: {e}")
                    creds = None
            
            if not creds:
                # Iniciar fluxo de autorização
                logger.info("Iniciando fluxo de autorização OAuth2...")
                
                credentials_file = Path(settings.GOOGLE_DRIVE_CREDENTIALS_FILE)
                if not credentials_file.exists():
                    raise FileNotFoundError(f"Arquivo de credenciais OAuth2 não encontrado: {credentials_file}")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(credentials_file), SCOPES
                )
                creds = flow.run_local_server(port=0)
                logger.info("Autorização OAuth2 concluída com sucesso")
            
            # Salvar credenciais para próxima execução
            with open(token_file, 'w') as f:
                f.write(creds.to_json())
            logger.info(f"Token OAuth2 salvo em: {token_file}")
        
        return creds
    
    def _get_or_create_folder(self, folder_name: str, parent_id: str = None) -> str:
        """Obtém ou cria uma pasta no Google Drive"""
        try:
            # Procurar pasta existente
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
            if parent_id:
                query += f" and '{parent_id}' in parents"
            
            results = self.service.files().list(q=query).execute()
            items = results.get('files', [])
            
            if items:
                logger.info(f"Pasta '{folder_name}' encontrada: {items[0]['id']}")
                return items[0]['id']
            
            # Criar nova pasta
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_id:
                folder_metadata['parents'] = [parent_id]
            
            folder = self.service.files().create(body=folder_metadata).execute()
            folder_id = folder.get('id')
            
            logger.info(f"Pasta '{folder_name}' criada: {folder_id}")
            return folder_id
            
        except HttpError as e:
            logger.error(f"Erro ao criar/obter pasta '{folder_name}': {e}")
            raise
    
    def _create_cnpj_folder_structure(self, cnpj: str) -> Dict[str, str]:
        """Cria a estrutura de pastas para um CNPJ específico"""
        try:
            # Pasta do CNPJ
            cnpj_folder_name = f"CNPJ-{cnpj}"
            cnpj_folder_id = self._get_or_create_folder(cnpj_folder_name, self.root_folder_id)
            
            # Pasta da data atual
            current_date = datetime.now().strftime("%Y-%m-%d")
            date_folder_id = self._get_or_create_folder(current_date, cnpj_folder_id)
            
            return {
                'cnpj_folder_id': cnpj_folder_id,
                'date_folder_id': date_folder_id,
                'cnpj_folder_name': cnpj_folder_name,
                'date_folder_name': current_date
            }
            
        except Exception as e:
            logger.error(f"Erro ao criar estrutura de pastas para CNPJ {cnpj}: {e}")
            raise
    
    def _upload_file_sync(
        self, 
        file_content: bytes, 
        filename: str, 
        parent_folder_id: str,
        mime_type: str = None
    ) -> Dict[str, Any]:
        """Upload síncrono de arquivo (executado em thread separada)"""
        try:
            # Detectar mime type se não fornecido
            if not mime_type:
                file_extension = Path(filename).suffix.lower()
                mime_type_map = {
                    '.pdf': 'application/pdf',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png'
                }
                mime_type = mime_type_map.get(file_extension, 'application/octet-stream')
            
            # Preparar upload
            media = MediaIoBaseUpload(
                io.BytesIO(file_content),
                mimetype=mime_type,
                resumable=False  # Tentar upload não-resumable primeiro
            )
            
            # Metadados do arquivo
            file_metadata = {
                'name': filename,
                'parents': [parent_folder_id]
            }
            
            # Fazer upload
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,size,webViewLink,webContentLink'
            ).execute()
            
            logger.info(f"Arquivo '{filename}' enviado para Google Drive: {file.get('id')}")
            
            return {
                'success': True,
                'file_id': file.get('id'),
                'file_name': file.get('name'),
                'file_size': file.get('size'),
                'web_view_link': file.get('webViewLink'),
                'download_link': file.get('webContentLink')
            }
            
        except HttpError as e:
            error_details = e.error_details if hasattr(e, 'error_details') else []
            
            # Verificar se é problema de quota de service account
            if e.resp.status == 403 and any('storageQuotaExceeded' in str(detail) for detail in error_details):
                logger.warning(f"Service Account sem quota de storage. Tentando salvar em pasta específica...")
                
                # Tentar uma abordagem alternativa: salvar apenas os metadados
                return {
                    'success': False,
                    'error': 'Service Account não possui quota de storage no Google Drive pessoal',
                    'suggestion': 'Configure um Google Drive compartilhado ou use OAuth delegation',
                    'file_metadata': {
                        'filename': filename,
                        'size': len(file_content),
                        'mime_type': mime_type,
                        'attempted_parent': parent_folder_id
                    }
                }
            
            logger.error(f"Erro no upload do arquivo '{filename}': {e}")
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Erro inesperado no upload: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def save_nota_fiscal_file(
        self,
        file_content: bytes,
        filename: str,
        cnpj: str,
        mime_type: str = None
    ) -> Dict[str, Any]:
        """
        Salva um arquivo de nota fiscal no Google Drive ou localmente como fallback
        
        Args:
            file_content: Conteúdo do arquivo em bytes
            filename: Nome do arquivo
            cnpj: CNPJ do emissor
            mime_type: Tipo MIME do arquivo
            
        Returns:
            Resultado do upload
        """
        if not settings.GOOGLE_DRIVE_ENABLED or not self.service:
            # Usar armazenamento local como fallback
            logger.info("Google Drive não disponível, usando armazenamento local")
            return await local_file_manager.save_nota_fiscal_file(
                file_content, filename, cnpj, mime_type, ocr_success=True
            )
        
        try:
            # Criar estrutura de pastas
            folder_structure = self._create_cnpj_folder_structure(cnpj)
            
            # Executar upload em thread separada para não bloquear
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._upload_file_sync,
                file_content,
                filename,
                folder_structure['date_folder_id'],
                mime_type
            )
            
            # Se falhou por problemas de quota, usar fallback local
            if not result['success'] and 'storageQuotaExceeded' in str(result.get('error', '')):
                logger.warning("Quota do Google Drive excedida, usando armazenamento local como fallback")
                return await local_file_manager.save_nota_fiscal_file(
                    file_content, filename, cnpj, mime_type, ocr_success=True
                )
            
            if result['success']:
                result.update({
                    'folder_structure': folder_structure,
                    'full_path': f"{settings.GOOGLE_DRIVE_ROOT_FOLDER_NAME}/{folder_structure['cnpj_folder_name']}/{folder_structure['date_folder_name']}/{filename}",
                    'storage_type': 'google_drive'
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao salvar arquivo no Google Drive, tentando localmente: {e}")
            # Usar armazenamento local como fallback em caso de erro
            return await local_file_manager.save_nota_fiscal_file(
                file_content, filename, cnpj, mime_type, ocr_success=True
            )
    
    async def list_files_by_cnpj(self, cnpj: str, date: str = None) -> Dict[str, Any]:
        """
        Lista arquivos de um CNPJ específico (Google Drive ou local)
        
        Args:
            cnpj: CNPJ do emissor
            date: Data específica (formato YYYY-MM-DD), se None lista todas as datas
            
        Returns:
            Lista de arquivos encontrados
        """
        if not settings.GOOGLE_DRIVE_ENABLED or not self.service:
            # Usar listagem local
            return await local_file_manager.list_files_by_cnpj(cnpj, date)
        
        try:
            # Procurar pasta do CNPJ
            cnpj_folder_name = f"CNPJ-{cnpj}"
            query = f"name='{cnpj_folder_name}' and mimeType='application/vnd.google-apps.folder' and '{self.root_folder_id}' in parents"
            
            results = self.service.files().list(q=query).execute()
            cnpj_folders = results.get('files', [])
            
            if not cnpj_folders:
                # Tentar listagem local como fallback
                return await local_file_manager.list_files_by_cnpj(cnpj, date)
            
            cnpj_folder_id = cnpj_folders[0]['id']
            all_files = []
            
            # Se data específica foi fornecida
            if date:
                date_query = f"name='{date}' and mimeType='application/vnd.google-apps.folder' and '{cnpj_folder_id}' in parents"
                date_results = self.service.files().list(q=date_query).execute()
                date_folders = date_results.get('files', [])
                
                if date_folders:
                    files_query = f"'{date_folders[0]['id']}' in parents and mimeType!='application/vnd.google-apps.folder'"
                    files_results = self.service.files().list(q=files_query, fields='files(id,name,size,createdTime,webViewLink)').execute()
                    files = files_results.get('files', [])
                    
                    for file in files:
                        all_files.append({
                            'file_id': file['id'],
                            'filename': file['name'],
                            'size': file.get('size', 0),
                            'created_time': file.get('createdTime'),
                            'date_folder': date,
                            'web_view_link': file.get('webViewLink'),
                            'storage_type': 'google_drive'
                        })
            else:
                # Listar todas as pastas de data
                date_folders_query = f"'{cnpj_folder_id}' in parents and mimeType='application/vnd.google-apps.folder'"
                date_folders_results = self.service.files().list(q=date_folders_query).execute()
                date_folders = date_folders_results.get('files', [])
                
                for date_folder in date_folders:
                    files_query = f"'{date_folder['id']}' in parents and mimeType!='application/vnd.google-apps.folder'"
                    files_results = self.service.files().list(q=files_query, fields='files(id,name,size,createdTime,webViewLink)').execute()
                    files = files_results.get('files', [])
                    
                    for file in files:
                        all_files.append({
                            'file_id': file['id'],
                            'filename': file['name'],
                            'size': file.get('size', 0),
                            'created_time': file.get('createdTime'),
                            'date_folder': date_folder['name'],
                            'web_view_link': file.get('webViewLink'),
                            'storage_type': 'google_drive'
                        })
            
            return {
                'success': True,
                'files': all_files,
                'total_files': len(all_files),
                'cnpj': cnpj,
                'storage_type': 'google_drive'
            }
            
        except Exception as e:
            logger.error(f"Erro ao listar arquivos do CNPJ {cnpj} no Google Drive, tentando localmente: {e}")
            # Fallback para listagem local
            return await local_file_manager.list_files_by_cnpj(cnpj, date)
    
    def health_check(self) -> Dict[str, Any]:
        """Verifica o status da conexão com Google Drive e armazenamento local"""
        if not settings.GOOGLE_DRIVE_ENABLED:
            # Verificar apenas armazenamento local
            local_health = local_file_manager.health_check()
            return {
                'status': 'local_only',
                'message': 'Google Drive está desabilitado, usando armazenamento local',
                'local_storage': local_health
            }
        
        try:
            if not self.service:
                local_health = local_file_manager.health_check()
                return {
                    'status': 'unhealthy',
                    'error': 'Serviço do Google Drive não inicializado',
                    'local_storage': local_health
                }
            
            # Testar conexão listando arquivos da pasta raiz
            self.service.files().list(
                q=f"'{self.root_folder_id}' in parents",
                pageSize=1
            ).execute()
            
            local_health = local_file_manager.health_check()
            
            return {
                'status': 'healthy',
                'google_drive': {
                    'root_folder_id': self.root_folder_id,
                    'root_folder_name': settings.GOOGLE_DRIVE_ROOT_FOLDER_NAME,
                    'connected': True
                },
                'local_storage': local_health
            }
            
        except Exception as e:
            local_health = local_file_manager.health_check()
            return {
                'status': 'drive_error',
                'error': str(e),
                'message': 'Google Drive com problemas, usando armazenamento local como fallback',
                'local_storage': local_health
            }

# Instância global do gerenciador
drive_manager = GoogleDriveManager()
