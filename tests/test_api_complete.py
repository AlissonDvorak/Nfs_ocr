#!/usr/bin/env python3
"""
Script para testar o upload e processamento completo via API
"""

import requests
import json
from pathlib import Path


def test_api_health():
    """Testa o health check da API"""
    print("=== Testando Health Check da API ===")
    
    try:
        # Health check geral
        response = requests.get("http://localhost:8000/api/v1/nota-fiscal/health")
        if response.status_code == 200:
            print("✅ API está funcionando")
            data = response.json()
            print(f"OCR Status: {data.get('ocr_status', {}).get('status', 'N/A')}")
            print(f"Sheets Status: {data.get('sheets_status', {}).get('status', 'N/A')}")
        else:
            print(f"❌ API com problemas: {response.status_code}")
    
        # Health check do Google Drive
        response = requests.get("http://localhost:8000/api/v1/nota-fiscal/drive/health")
        if response.status_code == 200:
            print("✅ Google Drive/Storage funcionando")
            data = response.json()
            print(f"Storage Status: {data.get('status', 'N/A')}")
        else:
            print(f"❌ Storage com problemas: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro ao testar API: {e}")
    
    print()


def test_pdf_upload():
    """Testa o upload de um PDF fictício"""
    print("=== Testando Upload de PDF ===")
    
    try:
        # Criar um PDF fictício para teste
        pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n%%EOF"
        
        files = {
            'file': ('teste.pdf', pdf_content, 'application/pdf')
        }
        
        response = requests.post(
            "http://localhost:8000/api/v1/nota-fiscal/process",
            files=files,
            timeout=60
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.content:
            try:
                data = response.json()
                print(f"Sucesso: {data.get('success', False)}")
                print(f"Tempo de processamento: {data.get('processing_time_seconds', 0)}s")
                
                # Informações do OCR
                ocr_result = data.get('ocr_result', {})
                print(f"OCR Success: {ocr_result.get('success', False)}")
                if not ocr_result.get('success'):
                    print(f"OCR Error: {ocr_result.get('error', 'N/A')}")
                
                # Informações do Drive/Storage
                drive_result = data.get('drive_result', {})
                if drive_result:
                    print(f"Storage Success: {drive_result.get('success', False)}")
                    if drive_result.get('success'):
                        print(f"Arquivo salvo em: {drive_result.get('full_path', 'N/A')}")
                    else:
                        print(f"Storage Error: {drive_result.get('error', 'N/A')}")
                
            except json.JSONDecodeError:
                print(f"Resposta não é JSON válido: {response.text[:200]}...")
        else:
            print("Resposta vazia")
            
    except Exception as e:
        print(f"❌ Erro no teste de upload: {e}")
    
    print()


def test_image_upload():
    """Testa o upload de uma imagem fictícia"""
    print("=== Testando Upload de Imagem ===")
    
    try:
        # Header básico de PNG
        png_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
        
        files = {
            'file': ('teste.png', png_content, 'image/png')
        }
        
        response = requests.post(
            "http://localhost:8000/api/v1/nota-fiscal/process",
            files=files,
            timeout=60
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.content:
            try:
                data = response.json()
                print(f"Sucesso: {data.get('success', False)}")
                
                # Informações do OCR
                ocr_result = data.get('ocr_result', {})
                print(f"OCR Success: {ocr_result.get('success', False)}")
                if not ocr_result.get('success'):
                    print(f"OCR Error: {ocr_result.get('error', 'N/A')}")
                
            except json.JSONDecodeError:
                print(f"Resposta não é JSON válido: {response.text[:200]}...")
        else:
            print("Resposta vazia")
            
    except Exception as e:
        print(f"❌ Erro no teste de upload de imagem: {e}")
    
    print()


def main():
    """Função principal de teste"""
    print("🧪 Testando API Completa - Processamento de Arquivos")
    print("=" * 60)
    
    test_api_health()
    test_pdf_upload()
    test_image_upload()
    
    print("🏁 Testes concluídos!")


if __name__ == "__main__":
    main()
