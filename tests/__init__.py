"""
Pasta de testes para o sistema OCR Notas Fiscais

Este diretório contém todos os scripts de teste e validação do sistema:

📋 Testes de API:
- test_api_complete.py: Testa a API completa com upload de arquivos
- test_service.py: Testa os serviços principais da API

🔍 Testes de OCR:
- test_pdf_processing.py: Testa processamento de PDFs e conversão para imagem

📁 Testes de Google Drive:
- test_drive.py: Testa funcionalidades básicas do Google Drive
- verify_drive_structure.py: Verifica estrutura de pastas criadas
- check_drive_account.py: Verifica informações da conta conectada

🔧 Configuração:
- setup_oauth.py: Configurador OAuth2 para Google Drive pessoal

Como usar:
1. Execute os testes individuais: python tests/test_*.py
2. Configure OAuth2: python tests/setup_oauth.py
3. Verifique estruturas: python tests/verify_*.py
"""
