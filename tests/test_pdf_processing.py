#!/usr/bin/env python3
"""
Script para testar o processamento de PDFs da API de Nota Fiscal
"""

import asyncio
import sys
import os
from pathlib import Path

# Adicionar o diretório do projeto ao path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.ocr_processor import ocr_processor


async def test_pdf_detection():
    """Testa a detecção de PDF"""
    print("=== Teste de Detecção de PDF ===")
    
    # Simular dados de um PDF (cabeçalho)
    pdf_data = b'%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj'
    
    is_pdf = await ocr_processor._is_pdf_data(pdf_data)
    print(f"PDF detectado corretamente: {is_pdf}")
    
    # Simular dados de uma imagem
    image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
    is_pdf = await ocr_processor._is_pdf_data(image_data)
    print(f"Imagem não detectada como PDF: {not is_pdf}")
    
    print()


async def test_with_sample_pdf():
    """Testa com um PDF de exemplo se disponível"""
    print("=== Teste com PDF de Exemplo ===")
    
    # Procurar por arquivos PDF no diretório atual
    pdf_files = list(Path(".").glob("*.pdf"))
    
    if not pdf_files:
        print("Nenhum arquivo PDF encontrado no diretório atual.")
        print("Para testar com PDF, coloque um arquivo PDF de nota fiscal no diretório do projeto.")
        return
    
    pdf_file = pdf_files[0]
    print(f"Testando com arquivo: {pdf_file}")
    
    try:
        result = await ocr_processor.process_nota_fiscal(
            image_data=str(pdf_file),
            image_format="pdf"
        )
        
        print(f"Sucesso: {result.get('success', False)}")
        print(f"Páginas processadas: {result.get('pages_processed', 0)}")
        print(f"Páginas com sucesso: {result.get('pages_successful', 0)}")
        
        if result.get('success') and result.get('data'):
            data = result['data']
            print(f"Número da nota: {data.get('numero_nota', 'N/A')}")
            print(f"CNPJ emissor: {data.get('cnpj_emissor', 'N/A')}")
            print(f"Razão social: {data.get('razao_social_emissor', 'N/A')}")
            print(f"Valor total: {data.get('valor_total', 'N/A')}")
            print(f"Número de itens: {len(data.get('items', []))}")
        
        if result.get('error'):
            print(f"Erro: {result['error']}")
            
    except Exception as e:
        print(f"Erro durante o teste: {e}")
    
    print()


async def test_health():
    """Testa o health check do serviço"""
    print("=== Teste de Health Check ===")
    
    try:
        health = ocr_processor.health_check()
        print(f"Status: {health.get('status', 'unknown')}")
        print(f"Modelo: {health.get('model', 'N/A')}")
        print(f"API conectada: {health.get('api_connected', False)}")
        
        if health.get('error'):
            print(f"Erro: {health['error']}")
            
    except Exception as e:
        print(f"Erro no health check: {e}")
    
    print()


async def main():
    """Função principal de teste"""
    print("🧪 Testando Processamento de PDF da API Nota Fiscal")
    print("=" * 60)
    
    # Verificar se as variáveis de ambiente estão configuradas
    if not os.getenv('GOOGLE_API_KEY'):
        print("❌ GOOGLE_API_KEY não configurada!")
        print("Configure a variável de ambiente ou o arquivo .env")
        return
    
    print("✅ Variáveis de ambiente carregadas")
    
    # Executar testes
    await test_health()
    await test_pdf_detection()
    await test_with_sample_pdf()
    
    print("🏁 Testes concluídos!")


if __name__ == "__main__":
    # Carregar variáveis de ambiente
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(main())
