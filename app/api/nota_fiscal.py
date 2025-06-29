from fastapi import APIRouter, UploadFile, File, HTTPException, status, Query
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from ..services.ocr_processor import ocr_processor
from ..services.sheets_manager import sheets_manager
from ..services.drive_manager import drive_manager
from ..config.settings import settings

# Configurar logging
logger = logging.getLogger(__name__)

# Router para endpoints de nota fiscal
router = APIRouter(prefix="/nota-fiscal", tags=["Nota Fiscal"])

@router.post("/process", response_model=Dict[str, Any])
async def process_and_save_nota_fiscal(
    file: UploadFile = File(..., description="Arquivo da nota fiscal (JPG, PNG, PDF)")
) -> JSONResponse:
    """
    Processa uma nota fiscal com OCR e salva os dados no Google Sheets
    
    Args:
        file: Arquivo da nota fiscal
        
    Returns:
        Resultado do processamento e salvamento
    """
    start_time = datetime.now()
    
    try:
        # Validar tipo de arquivo
        if not file.content_type or not file.content_type.startswith(('image/', 'application/pdf')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de arquivo não suportado. Use JPG, PNG ou PDF."
            )
        
        # Validar tamanho do arquivo
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Arquivo muito grande. Tamanho máximo: {settings.MAX_FILE_SIZE / 1024 / 1024:.1f}MB"
            )
        
        logger.info(f"Processando arquivo: {file.filename} ({file_size} bytes)")
        
        # 1. Processar com OCR (Gemini 2.0 Flash)
        ocr_result = await ocr_processor.process_nota_fiscal(
            image_data=file_content,
            image_format="auto"
        )
        
        # 2. Salvar no Google Sheets (se OCR foi bem-sucedido)
        sheets_result = {"sheets_updated": False}
        drive_result = {"file_saved": False}
        
        if ocr_result.get("success", False):
            try:
                sheets_result = await sheets_manager.save_nota_fiscal_data(
                    ocr_data=ocr_result,
                    filename=file.filename or "unknown"
                )
            except Exception as e:
                logger.error(f"Erro ao salvar no Google Sheets: {e}")
                sheets_result = {
                    "success": False,
                    "error": f"Erro ao salvar no Sheets: {str(e)}",
                    "sheets_updated": False
                }
            
            # 3. Salvar arquivo no Google Drive (se OCR foi bem-sucedido e temos CNPJ)
            if settings.GOOGLE_DRIVE_ENABLED and ocr_result.get("data", {}).get("cnpj_emissor"):
                try:
                    cnpj = ocr_result["data"]["cnpj_emissor"]
                    drive_result = await drive_manager.save_nota_fiscal_file(
                        file_content=file_content,
                        filename=file.filename or "unknown",
                        cnpj=cnpj,
                        mime_type=file.content_type
                    )
                    logger.info(f"Resultado do Google Drive: {drive_result}")
                except Exception as e:
                    logger.error(f"Erro ao salvar no Google Drive: {e}")
                    drive_result = {
                        "success": False,
                        "error": f"Erro ao salvar no Drive: {str(e)}",
                        "file_saved": False
                    }
        
        # Calcular tempo de processamento
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Preparar resposta consolidada
        response_data = {
            "success": ocr_result.get("success", False),
            "processing_time_seconds": round(processing_time, 2),
            "file_info": {
                "filename": file.filename,
                "content_type": file.content_type,
                "file_size": file_size
            },
            "ocr_result": ocr_result,
            "sheets_result": sheets_result,
            "drive_result": drive_result
        }
        
        # Status HTTP baseado no sucesso do OCR
        response_status = (
            status.HTTP_200_OK 
            if ocr_result.get("success", False) 
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        
        return JSONResponse(
            status_code=response_status,
            content=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro geral ao processar nota fiscal: {e}")
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": f"Erro interno do servidor: {str(e)}",
                "processing_time_seconds": round(processing_time, 2),
                "file_info": {
                    "filename": getattr(file, 'filename', 'unknown'),
                    "content_type": getattr(file, 'content_type', 'unknown'),
                    "file_size": 0
                },
                "ocr_result": {"success": False, "error": str(e)},
                "sheets_result": {"sheets_updated": False}
            }
        )

@router.post("/upload-only", response_model=Dict[str, Any])
async def upload_nota_fiscal_only(
    file: UploadFile = File(..., description="Arquivo da nota fiscal para OCR apenas")
) -> JSONResponse:
    """
    Apenas processa uma nota fiscal com OCR (sem salvar no Sheets)
    
    Args:
        file: Arquivo da nota fiscal
        
    Returns:
        Dados extraídos da nota fiscal
    """
    try:
        # Validar tipo de arquivo
        if not file.content_type or not file.content_type.startswith(('image/', 'application/pdf')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de arquivo não suportado. Use JPG, PNG ou PDF."
            )
        
        # Validar tamanho do arquivo
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Arquivo muito grande. Tamanho máximo: {settings.MAX_FILE_SIZE / 1024 / 1024:.1f}MB"
            )
        
        # Processar com OCR
        logger.info(f"Processando arquivo (OCR only): {file.filename} ({file_size} bytes)")
        result = await ocr_processor.process_nota_fiscal(
            image_data=file_content,
            image_format="auto"
        )
        
        # Adicionar metadados
        result["metadata"] = {
            "filename": file.filename,
            "content_type": file.content_type,
            "file_size": file_size
        }
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar nota fiscal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )

@router.post("/extract-text", response_model=Dict[str, Any])
async def extract_text_only(
    file: UploadFile = File(..., description="Arquivo de imagem para extração de texto")
) -> JSONResponse:
    """
    Extrai apenas o texto de uma imagem (OCR simples)
    
    Args:
        file: Arquivo de imagem
        
    Returns:
        Texto extraído da imagem
    """
    try:
        # Validar tipo de arquivo
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Apenas arquivos de imagem são suportados para extração de texto."
            )
        
        # Ler conteúdo do arquivo
        file_content = await file.read()
        
        # Validar tamanho
        if len(file_content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Arquivo muito grande. Tamanho máximo: {settings.MAX_FILE_SIZE / 1024 / 1024:.1f}MB"
            )
        
        # Extrair texto
        logger.info(f"Extraindo texto do arquivo: {file.filename}")
        text = await ocr_processor.extract_text_only(file_content)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "text": text,
                "metadata": {
                    "filename": file.filename,
                    "content_type": file.content_type,
                    "file_size": len(file_content)
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao extrair texto: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )

@router.get("/sheets/recent", response_model=Dict[str, Any])
async def get_recent_entries(
    limit: int = Query(default=10, ge=1, le=100, description="Número de entradas a retornar"),
    type: str = Query(default="resumo", description="Tipo de dados (resumo, itens, all)")
) -> JSONResponse:
    """
    Recupera as entradas mais recentes das planilhas do Google Sheets
    
    Args:
        limit: Número máximo de entradas para retornar (1-100)
        type: Tipo da planilha ("resumo", "itens", "all")
        
    Returns:
        Lista com as entradas mais recentes
    """
    try:
        if type not in ["resumo", "itens", "all"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo deve ser 'resumo', 'itens' ou 'all'"
            )
        
        entries = sheets_manager.get_recent_entries(limit=limit, worksheet_type=type)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "type": type,
                "limit": limit,
                "data": entries,
                "spreadsheet_id": settings.GOOGLE_SHEETS_SPREADSHEET_ID
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao recuperar entradas do Sheets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao acessar Google Sheets: {str(e)}"
        )

@router.get("/sheets/cnpj-worksheets", response_model=Dict[str, Any])
async def get_cnpj_worksheets() -> JSONResponse:
    """
    Lista todas as planilhas de CNPJ criadas
    
    Returns:
        Lista das planilhas organizadas por CNPJ
    """
    try:
        cnpj_worksheets = sheets_manager.get_cnpj_worksheets()
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "count": len(cnpj_worksheets),
                "cnpj_worksheets": cnpj_worksheets,
                "spreadsheet_id": settings.GOOGLE_SHEETS_SPREADSHEET_ID
            }
        )
        
    except Exception as e:
        logger.error(f"Erro ao listar worksheets CNPJ: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao acessar Google Sheets: {str(e)}"
        )

@router.get("/sheets/statistics", response_model=Dict[str, Any])
async def get_sheets_statistics() -> JSONResponse:
    """
    Obtém estatísticas detalhadas das planilhas
    
    Returns:
        Estatísticas consolidadas das planilhas
    """
    try:
        statistics = sheets_manager.get_statistics()
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "statistics": statistics,
                "timestamp": datetime.now().isoformat(),
                "spreadsheet_id": settings.GOOGLE_SHEETS_SPREADSHEET_ID
            }
        )
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter estatísticas: {str(e)}"
        )

@router.get("/health")
async def health_check() -> JSONResponse:
    """
    Verifica o status completo do serviço (OCR + Google Sheets)
    
    Returns:
        Status detalhado do serviço
    """
    try:
        # Health check do OCR
        ocr_health = ocr_processor.health_check()
        
        # Health check do Google Sheets
        sheets_health = sheets_manager.health_check()
        
        # Status geral
        overall_status = (
            "healthy" 
            if ocr_health.get("status") == "healthy" and sheets_health.get("status") == "healthy"
            else "partial" if ocr_health.get("status") == "healthy" or sheets_health.get("status") == "healthy"
            else "unhealthy"
        )
        
        status_code = (
            status.HTTP_200_OK if overall_status == "healthy"
            else status.HTTP_206_PARTIAL_CONTENT if overall_status == "partial"
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        
        return JSONResponse(
            status_code=status_code,
            content={
                "overall_status": overall_status,
                "timestamp": datetime.now().isoformat(),
                "services": {
                    "ocr_gemini": ocr_health,
                    "google_sheets": sheets_health
                },
                "configuration": {
                    "gemini_model": settings.GEMINI_MODEL,
                    "max_file_size_mb": settings.MAX_FILE_SIZE / 1024 / 1024,
                    "allowed_extensions": settings.ALLOWED_EXTENSIONS
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Erro no health check: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "overall_status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        )

@router.get("/stats")
async def get_service_stats() -> JSONResponse:
    """
    Retorna estatísticas completas do serviço
    
    Returns:
        Estatísticas detalhadas do serviço e planilhas
    """
    try:
        # Obter estatísticas das planilhas
        sheets_stats = sheets_manager.get_statistics()
        
        # Obter entradas recentes para análise
        recent_resumo = sheets_manager.get_recent_entries(limit=50, worksheet_type="resumo")
        
        # Calcular estatísticas adicionais
        total_processed = len(recent_resumo)
        success_count = sum(1 for entry in recent_resumo 
                          if entry.get("Status Processamento") == "Processado com Sucesso")
        
        # Análise por período (últimos registros)
        monthly_data = {}
        for entry in recent_resumo:
            try:
                date_str = entry.get("Data/Hora Processamento", "")
                if date_str:
                    # Extrair mês/ano da data (formato DD/MM/YYYY HH:MM:SS)
                    month_year = "/".join(date_str.split()[0].split("/")[1:])  # MM/YYYY
                    if month_year not in monthly_data:
                        monthly_data[month_year] = {"count": 0, "valor_total": 0.0}
                    
                    monthly_data[month_year]["count"] += 1
                    
                    # Somar valor se disponível
                    try:
                        valor = float(entry.get("Valor Total", 0) or 0)
                        monthly_data[month_year]["valor_total"] += valor
                    except (ValueError, TypeError):
                        pass
            except:
                pass
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "service_stats": {
                    "total_processed_recent": total_processed,
                    "successful_recent": success_count,
                    "error_rate_recent": round((total_processed - success_count) / max(total_processed, 1) * 100, 2),
                    "last_processed": recent_resumo[0].get("Data/Hora Processamento") if recent_resumo else None
                },
                "sheets_stats": sheets_stats,
                "monthly_analysis": monthly_data,
                "service_info": {
                    "gemini_model": settings.GEMINI_MODEL,
                    "app_version": settings.APP_VERSION,
                    "debug_mode": settings.DEBUG,
                    "structured_sheets": True,
                    "features": [
                        "Planilha de resumo de notas fiscais",
                        "Planilha detalhada de itens",
                        "Planilhas específicas por CNPJ emissor",
                        "Análise estatística automática"
                    ]
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter estatísticas: {str(e)}"
        )

@router.post("/sheets/ensure-headers")
async def ensure_sheets_headers(force_recreation: bool = Query(False, description="Força recriação dos cabeçalhos")) -> JSONResponse:
    """
    Verifica e corrige os cabeçalhos das planilhas principais
    
    Args:
        force_recreation: Se True, força a recriação completa dos cabeçalhos
        
    Returns:
        Status da operação
    """
    try:
        logger.info("Verificando e corrigindo cabeçalhos das planilhas...")
        
        # Verificar e corrigir cabeçalhos
        sheets_manager.ensure_headers(force_recreation=force_recreation)
        
        # Obter informações atuais dos cabeçalhos
        resumo_headers = sheets_manager.worksheet_resumo.row_values(1)
        itens_headers = sheets_manager.worksheet_itens.row_values(1)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Cabeçalhos verificados e corrigidos com sucesso",
                "details": {
                    "resumo_headers_count": len(resumo_headers),
                    "itens_headers_count": len(itens_headers),
                    "force_recreation": force_recreation,
                    "resumo_headers": resumo_headers[:5] + ["..."] if len(resumo_headers) > 5 else resumo_headers,
                    "itens_headers": itens_headers[:5] + ["..."] if len(itens_headers) > 5 else itens_headers
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Erro ao verificar cabeçalhos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao verificar cabeçalhos: {str(e)}"
        )

# Endpoints do Google Drive
@router.get("/drive/files/{cnpj}")
async def list_drive_files_by_cnpj(
    cnpj: str,
    date: Optional[str] = Query(None, description="Data específica (YYYY-MM-DD)")
) -> JSONResponse:
    """
    Lista arquivos salvos no Google Drive para um CNPJ específico
    
    Args:
        cnpj: CNPJ do emissor
        date: Data específica (opcional)
        
    Returns:
        Lista de arquivos encontrados
    """
    try:
        if not settings.GOOGLE_DRIVE_ENABLED:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Google Drive não está habilitado"
            )
        
        result = await drive_manager.list_files_by_cnpj(cnpj, date)
        
        if result['success']:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=result
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result['error']
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao listar arquivos do CNPJ {cnpj}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar arquivos: {str(e)}"
        )

@router.get("/drive/health")
async def drive_health_check() -> JSONResponse:
    """
    Verifica o status da conexão com Google Drive
    
    Returns:
        Status da conexão
    """
    try:
        health = drive_manager.health_check()
        
        status_code = (
            status.HTTP_200_OK 
            if health['status'] in ['healthy', 'disabled'] 
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        
        return JSONResponse(
            status_code=status_code,
            content=health
        )
        
    except Exception as e:
        logger.error(f"Erro no health check do Google Drive: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                'status': 'error',
                'error': str(e)
            }
        )

@router.get("/drive/stats")
async def drive_statistics() -> JSONResponse:
    """
    Obtém estatísticas dos arquivos salvos no Google Drive
    
    Returns:
        Estatísticas dos arquivos
    """
    try:
        if not settings.GOOGLE_DRIVE_ENABLED:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "drive_enabled": False,
                    "message": "Google Drive não está habilitado"
                }
            )
        
        # Aqui você pode implementar estatísticas mais avançadas
        # Por enquanto, retornamos informações básicas
        health = drive_manager.health_check()
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "drive_enabled": True,
                "drive_status": health['status'],
                "root_folder": settings.GOOGLE_DRIVE_ROOT_FOLDER_NAME,
                "message": "Google Drive está configurado e funcionando"
            }
        )
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas do Google Drive: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter estatísticas: {str(e)}"
        )