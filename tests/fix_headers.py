#!/usr/bin/env python3
"""
Script para verificar e corrigir cabeçalhos das planilhas Google Sheets
"""

import sys
import asyncio
from pathlib import Path

# Adicionar o diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.sheets_manager import sheets_manager
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Função principal"""
    try:
        print("🔧 Verificando e corrigindo cabeçalhos das planilhas Google Sheets...")
        
        # Verificar conexão
        health = sheets_manager.health_check()
        if not health.get("connected", False):
            print("❌ Erro: Não foi possível conectar com Google Sheets")
            print(f"   Detalhes: {health.get('error', 'Erro desconhecido')}")
            return False
        
        print(f"✅ Conectado à planilha: {health['spreadsheet']['title']}")
        
        # Obter cabeçalhos atuais
        print("\n📋 Cabeçalhos atuais:")
        resumo_headers = sheets_manager.worksheet_resumo.row_values(1)
        itens_headers = sheets_manager.worksheet_itens.row_values(1)
        
        print(f"   Resumo: {len(resumo_headers)} colunas")
        print(f"   Itens:  {len(itens_headers)} colunas")
        
        if resumo_headers:
            print(f"   Primeiros cabeçalhos do resumo: {resumo_headers[:3]}")
        if itens_headers:
            print(f"   Primeiros cabeçalhos dos itens: {itens_headers[:3]}")
        
        # Perguntar se deseja forçar recriação
        print("\n🤔 Deseja forçar a recriação completa dos cabeçalhos? (s/N): ", end="")
        force_recreation = input().lower().strip() == 's'
        
        # Corrigir cabeçalhos
        print(f"\n🔧 {'Recriando' if force_recreation else 'Verificando'} cabeçalhos...")
        sheets_manager.ensure_headers(force_recreation=force_recreation)
        
        # Verificar resultado
        print("\n📋 Cabeçalhos após correção:")
        resumo_headers_new = sheets_manager.worksheet_resumo.row_values(1)
        itens_headers_new = sheets_manager.worksheet_itens.row_values(1)
        
        print(f"   Resumo: {len(resumo_headers_new)} colunas")
        print(f"   Itens:  {len(itens_headers_new)} colunas")
        
        # Testar obtenção de dados
        print("\n🧪 Testando obtenção de dados...")
        try:
            recent_data = sheets_manager.get_recent_entries(limit=2, worksheet_type="all")
            print(f"   ✅ Dados de resumo: {len(recent_data.get('resumo', []))} registros")
            print(f"   ✅ Dados de itens: {len(recent_data.get('itens', []))} registros")
            
            if recent_data.get('resumo'):
                sample_keys = list(recent_data['resumo'][0].keys())[:3]
                print(f"   📝 Exemplo de chaves do resumo: {sample_keys}")
                
        except Exception as e:
            print(f"   ❌ Erro ao testar dados: {e}")
        
        # Obter estatísticas
        print("\n📊 Estatísticas das planilhas:")
        try:
            stats = sheets_manager.get_statistics()
            print(f"   📋 Total de notas: {stats.get('resumo', {}).get('total_notas', 0)}")
            print(f"   📦 Total de itens: {stats.get('itens', {}).get('total_itens', 0)}")
            print(f"   🏢 Planilhas CNPJ: {stats.get('cnpj_worksheets', 0)}")
            
        except Exception as e:
            print(f"   ❌ Erro ao obter estatísticas: {e}")
        
        print("\n✅ Processo concluído com sucesso!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro durante execução: {e}")
        logger.error(f"Erro no script: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
