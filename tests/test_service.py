#!/usr/bin/env python3
"""
Script de teste completo para o serviço de OCR de Nota Fiscal
Testa OCR + Google Sheets + todas as funcionalidades
"""

import asyncio
import aiohttp
import json
from pathlib import Path
import time
import requests

async def test_health_check(base_url: str = "http://localhost:8000"):
    """Testa o health check completo do serviço"""
    
    print("🏥 Testando Health Check Completo...")
    url = f"{base_url}/api/v1/nota-fiscal/health"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                result = await response.json()
                
                print(f"   Status HTTP: {response.status}")
                print(f"   Status Geral: {result.get('overall_status', 'unknown')}")
                
                services = result.get('services', {})
                ocr_status = services.get('ocr_gemini', {}).get('status', 'unknown')
                sheets_status = services.get('google_sheets', {}).get('status', 'unknown')
                
                print(f"   OCR Gemini: {'✅' if ocr_status == 'healthy' else '❌'} {ocr_status}")
                print(f"   Google Sheets: {'✅' if sheets_status == 'healthy' else '❌'} {sheets_status}")
                
                return result.get('overall_status') == 'healthy'
                
        except Exception as e:
            print(f"   ❌ Erro no health check: {e}")
            return False

async def test_process_and_save(image_path: str, base_url: str = "http://localhost:8000"):
    """Testa o processamento completo: OCR + Salvamento no Sheets"""
    
    if not Path(image_path).exists():
        print(f"   ❌ Arquivo não encontrado: {image_path}")
        return False
    
    print(f"📋 Testando Processamento Completo: {Path(image_path).name}")
    url = f"{base_url}/api/v1/nota-fiscal/process"
    
    async with aiohttp.ClientSession() as session:
        with open(image_path, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('file', f, filename=Path(image_path).name)
            
            print(f"   Enviando arquivo: {image_path}")
            start_time = time.time()
            
            try:
                async with session.post(url, data=data) as response:
                    result = await response.json()
                    processing_time = time.time() - start_time
                    
                    print(f"   Status HTTP: {response.status}")
                    print(f"   Tempo de processamento: {processing_time:.2f}s")
                    print(f"   Sucesso OCR: {'✅' if result.get('ocr_result', {}).get('success') else '❌'}")
                    print(f"   Salvo no Sheets: {'✅' if result.get('sheets_result', {}).get('sheets_updated') else '❌'}")
                    
                    # Exibir dados extraídos se disponível
                    ocr_data = result.get('ocr_result', {}).get('data', {})
                    if ocr_data:
                        print(f"   📊 Dados extraídos:")
                        print(f"      Número NF: {ocr_data.get('numero_nota', 'N/A')}")
                        print(f"      Valor Total: R$ {ocr_data.get('valor_total', 'N/A')}")
                        print(f"      CNPJ Emissor: {ocr_data.get('cnpj_emissor', 'N/A')}")
                        print(f"      Qtd Itens: {len(ocr_data.get('items', []))}")
                    
                    return result.get('success', False)
                    
            except Exception as e:
                print(f"   ❌ Erro na requisição: {e}")
                return False

async def test_recent_entries(base_url: str = "http://localhost:8000"):
    """Testa a recuperação de entradas recentes das planilhas estruturadas"""
    
    print("📊 Testando Entradas Recentes das Planilhas...")
    
    # Testar diferentes tipos de planilhas
    for sheet_type in ["resumo", "itens"]:
        print(f"\n   📋 Testando planilha: {sheet_type}")
        url = f"{base_url}/api/v1/nota-fiscal/sheets/recent?limit=5&type={sheet_type}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    result = await response.json()
                    
                    print(f"      Status HTTP: {response.status}")
                    
                    if result.get('success'):
                        data = result.get('data', [])
                        print(f"      ✅ {len(data)} entradas encontradas ({sheet_type})")
                        
                        # Mostrar algumas entradas de exemplo
                        if isinstance(data, list) and data:
                            for i, entry in enumerate(data[:2], 1):  # Mostrar apenas 2
                                if sheet_type == "resumo":
                                    filename = entry.get('Nome Arquivo', 'N/A')
                                    numero_nf = entry.get('Número Nota', 'N/A')
                                    print(f"         {i}. NF {numero_nf} - {filename}")
                                else:  # itens
                                    descricao = entry.get('Descrição Produto', 'N/A')[:30]
                                    numero_nf = entry.get('Número Nota', 'N/A')
                                    print(f"         {i}. NF {numero_nf} - {descricao}...")
                    else:
                        print(f"      ❌ Erro ao recuperar entradas ({sheet_type})")
                        
            except Exception as e:
                print(f"      ❌ Erro na requisição ({sheet_type}): {e}")
    
    return True

async def test_cnpj_worksheets(base_url: str = "http://localhost:8000"):
    """Testa a listagem de planilhas por CNPJ"""
    
    print("🏢 Testando Planilhas por CNPJ...")
    url = f"{base_url}/api/v1/nota-fiscal/sheets/cnpj-worksheets"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                result = await response.json()
                
                print(f"   Status HTTP: {response.status}")
                
                if result.get('success'):
                    worksheets = result.get('cnpj_worksheets', [])
                    count = result.get('count', 0)
                    
                    print(f"   ✅ {count} planilhas de CNPJ encontradas")
                    
                    for i, ws in enumerate(worksheets[:3], 1):  # Mostrar apenas 3
                        cnpj = ws.get('cnpj', 'N/A')
                        empresa = ws.get('empresa', 'N/A')
                        print(f"      {i}. CNPJ {cnpj} - {empresa}")
                    
                    return True
                else:
                    print(f"   ❌ Erro ao recuperar planilhas CNPJ")
                    return False
                    
        except Exception as e:
            print(f"   ❌ Erro na requisição: {e}")
            return False

async def test_sheets_statistics(base_url: str = "http://localhost:8000"):
    """Testa as estatísticas detalhadas das planilhas"""
    
    print("📈 Testando Estatísticas das Planilhas...")
    url = f"{base_url}/api/v1/nota-fiscal/sheets/statistics"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                result = await response.json()
                
                print(f"   Status HTTP: {response.status}")
                
                if result.get('success'):
                    stats = result.get('statistics', {})
                    
                    print(f"   ✅ Estatísticas obtidas:")
                    
                    # Estatísticas de resumo
                    resumo_stats = stats.get('resumo', {})
                    print(f"      📋 Resumo:")
                    print(f"         Total NFs: {resumo_stats.get('total_notas', 0)}")
                    print(f"         Valor Total: R$ {resumo_stats.get('valor_total_sum', 0):,.2f}")
                    
                    # Estatísticas de itens
                    itens_stats = stats.get('itens', {})
                    print(f"      📦 Itens:")
                    print(f"         Total Itens: {itens_stats.get('total_itens', 0)}")
                    
                    # Planilhas CNPJ
                    cnpj_count = stats.get('cnpj_worksheets', 0)
                    print(f"      🏢 Planilhas CNPJ: {cnpj_count}")
                    
                    empresas = stats.get('empresas_ativas', [])
                    if empresas:
                        print(f"      Empresas ativas: {', '.join(empresas[:3])}{'...' if len(empresas) > 3 else ''}")
                    
                    return True
                else:
                    print(f"   ❌ Erro ao obter estatísticas das planilhas")
                    return False
                    
        except Exception as e:
            print(f"   ❌ Erro na requisição: {e}")
            return False

def test_ensure_headers(base_url: str = "http://localhost:8000"):
    """Testa o endpoint de verificação e correção de cabeçalhos"""
    print("\n=== Testando Verificação de Cabeçalhos ===")
    
    # Testar verificação normal
    response = requests.post(f"{base_url}/nota-fiscal/sheets/ensure-headers")
    print(f"Status verificação normal: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Sucesso: {data.get('success')}")
        print(f"Mensagem: {data.get('message')}")
        details = data.get('details', {})
        print(f"Cabeçalhos resumo: {details.get('resumo_headers_count', 0)}")
        print(f"Cabeçalhos itens: {details.get('itens_headers_count', 0)}")
    else:
        print(f"Erro: {response.text}")
    
    # Testar com força de recriação
    print("\nTestando com force_recreation=true...")
    response = requests.post(f"{base_url}/nota-fiscal/sheets/ensure-headers?force_recreation=true")
    print(f"Status força recriação: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Recriação forçada concluída: {data.get('success')}")
    else:
        print(f"Erro na recriação: {response.text}")

async def main():
    """Função principal de teste"""
    
    print("🧪 TESTE COMPLETO DO SERVIÇO OCR NOTA FISCAL")
    print("=" * 60)
    
    base_url = input("Digite a URL base do serviço (Enter para localhost:8000): ").strip()
    if not base_url:
        base_url = "http://localhost:8000"
    
    print(f"🎯 Testando serviço em: {base_url}")
    print("=" * 60)
    
    # Teste 1: Health Check
    print("\n1️⃣ HEALTH CHECK COMPLETO")
    health_ok = await test_health_check(base_url)
    
    # Teste 2: Upload de nota fiscal (se fornecido)
    print("\n2️⃣ PROCESSAMENTO DE NOTA FISCAL")
    image_path = input("Digite o caminho para uma imagem de nota fiscal (ou Enter para pular): ").strip()
    
    if image_path and Path(image_path).exists():
        success = await test_process_and_save(image_path, base_url)
        if success:
            print("   ✅ Teste completo realizado com sucesso!")
        else:
            print("   ❌ Teste apresentou problemas")
    else:
        print("   ⏭️  Teste de processamento pulado - arquivo não fornecido")
    
    # Testes adicionais para novos recursos
    print("\n3️⃣ TESTES DE RECURSOS DAS PLANILHAS")
    await test_recent_entries(base_url)
    await test_cnpj_worksheets(base_url)
    await test_sheets_statistics(base_url)
    
    # Teste 4: Verificação de Cabeçalhos
    print("\n4️⃣ VERIFICAÇÃO DE CABEÇALHOS")
    test_ensure_headers(base_url)
    
    print("\n" + "=" * 60)
    if health_ok:
        print("🎉 Serviço está funcionando corretamente!")
    else:
        print("⚠️  Serviço apresenta problemas - verifique a configuração")

if __name__ == "__main__":
    print("🔍 TESTE DO SERVIÇO OCR NOTA FISCAL COM GOOGLE SHEETS")
    print("Certifique-se de que o serviço esteja rodando")
    print("Para iniciar: python -m app.main")
    print()
    
    asyncio.run(main())
