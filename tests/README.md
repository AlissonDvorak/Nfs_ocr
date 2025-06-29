# 🧪 Pasta de Testes - OCR Notas Fiscais

Esta pasta contém todos os scripts de teste e configuração do sistema OCR de Notas Fiscais.

## 📁 Estrutura dos Arquivos

### 🔧 Scripts de Configuração
- **`setup_oauth.py`** - Configura OAuth2 para Google Drive pessoal
- **`fix_headers.py`** - Corrige cabeçalhos das planilhas Google Sheets

### 🧪 Scripts de Teste
- **`test_api_complete.py`** - Testa a API FastAPI completa
- **`test_drive.py`** - Testa funcionalidades do Google Drive
- **`test_pdf_processing.py`** - Testa processamento de PDFs
- **`test_service.py`** - Health check de todos os serviços

### 🔍 Scripts de Verificação
- **`check_drive_account.py`** - Verifica conta Google Drive conectada
- **`verify_drive_structure.py`** - Verifica estrutura de pastas no Drive

## 🚀 Como Usar

### Executar Todos os Testes (Recomendado)
```bash
# Na raiz do projeto
python run_tests.py
```

### Executar Testes Individuais
```bash
# Health check de todos os serviços
python tests/test_service.py

# Testar processamento de PDFs
python tests/test_pdf_processing.py

# Testar Google Drive
python tests/test_drive.py

# Testar API completa
python tests/test_api_complete.py

# Verificar estrutura do Drive
python tests/verify_drive_structure.py

# Verificar conta do Drive
python tests/check_drive_account.py
```

### Configuração Inicial OAuth2
```bash
# Configurar OAuth2 para Google Drive pessoal
python tests/setup_oauth.py
```

### Correção de Cabeçalhos
```bash
# Corrigir cabeçalhos das planilhas (se necessário)
python tests/fix_headers.py
```

## 📋 Pré-requisitos

1. **API rodando**: Certifique-se que a API FastAPI está rodando em `http://localhost:8000`
2. **Credenciais configuradas**: Arquivo `.env` com todas as variáveis necessárias
3. **OAuth2 (opcional)**: Para usar Google Drive pessoal, configure com `setup_oauth.py`

## 🔄 Fluxo Recomendado de Testes

1. **Configuração OAuth2** (primeira vez)
   ```bash
   python tests/setup_oauth.py
   ```

2. **Health Check**
   ```bash
   python tests/test_service.py
   ```

3. **Testes Específicos**
   ```bash
   python tests/test_pdf_processing.py
   python tests/test_drive.py
   ```

4. **Teste Completo da API**
   ```bash
   python tests/test_api_complete.py
   ```

## 📊 Interpretando os Resultados

- ✅ **Verde**: Teste passou com sucesso
- ❌ **Vermelho**: Teste falhou - verifique logs
- ⚠️ **Amarelo**: Aviso - funcionalidade parcial

## 🐛 Solução de Problemas

### Erro de Import
Se encontrar erros de import, certifique-se de estar executando da raiz do projeto:
```bash
cd /home/alisson/Projetos/.Pessoais/Ocr-Nf
python tests/nome_do_teste.py
```

### API não responde
Verifique se a API está rodando:
```bash
python start_system.py
```

### Problemas com Google Drive
1. Verifique credenciais no arquivo `.env`
2. Execute `python tests/check_drive_account.py`
3. Se necessário, reconfigure OAuth2 com `python tests/setup_oauth.py`

## 📝 Logs e Debug

Os scripts de teste produzem logs detalhados. Em caso de erro:
1. Leia as mensagens de erro completas
2. Verifique o arquivo `.env`
3. Teste componentes individuais antes do teste completo
4. Use o script `run_tests.py` para visão geral

## 🔧 Adicionando Novos Testes

Para adicionar um novo script de teste:
1. Crie o arquivo na pasta `tests/`
2. Use o padrão de nomenclatura `test_*.py`
3. Adicione imports necessários (veja exemplos nos outros arquivos)
4. Atualize o `run_tests.py` na raiz se necessário
