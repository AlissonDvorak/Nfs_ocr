# 🚀 GUIA DE CONFIGURAÇÃO - OCR NOTA FISCAL

## Pré-requisitos

1. **Python 3.8+**
2. **Chave de API do Google Gemini**
3. **Credenciais do Google Sheets**

## 📋 Passo a Passo

### 1. Configurar Google Gemini API

1. Acesse [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Crie uma nova chave de API
3. Sua chave já está no arquivo `.env`: `xxxxxxxxxxxxxxxxxxxx`

### 2. Configurar Google Sheets

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto ou selecione um existente
3. Ative as APIs:
   - Google Sheets API
   - Google Drive API

4. Crie uma conta de serviço:
   - Vá para IAM & Admin > Service Accounts
   - Clique em "Create Service Account"
   - Preencha os dados e crie
   - Gere uma chave JSON

5. Baixe o arquivo JSON e renomeie para `credentials.json`
6. Coloque o arquivo na raiz do projeto

### 3. Configurar Google Sheets

1. Crie uma nova planilha no Google Sheets
2. Copie o ID da planilha da URL (já configurado no .env)
3. Compartilhe a planilha com o email da conta de serviço (do credentials.json)
4. Dê permissão de "Editor" para a conta de serviço

### 4. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 5. Verificar Configuração

Execute o teste de configuração:

```bash
python -c "from app.config.settings import settings; print('✅ Configuração OK')"
```

### 6. Iniciar o Serviço

```bash
python -m app.main
```

O serviço estará disponível em: http://localhost:8000

### 7. Testar o Serviço

```bash
python test_service.py
```

## 🔧 Estrutura de Arquivos Necessários

```
Ocr-Nf/
├── .env                 # ✅ Já existe
├── credentials.json     # ❗ Você precisa criar
├── requirements.txt     # ✅ Já existe
└── app/                 # ✅ Já existe
```

## 📊 Planilha do Google Sheets

ID da sua planilha: `XXXXXXXXXXXXXXXXXXXXXXXXXXXX`
Worksheet: `OCR Notas Fiscais`

## 🆘 Troubleshooting

### Erro: "Arquivo de credenciais não encontrado"
- Certifique-se de que `credentials.json` está na raiz do projeto
- Verifique se o caminho no .env está correto

### Erro: "Permission denied" no Google Sheets
- Compartilhe a planilha com o email da conta de serviço
- Dê permissão de "Editor"

### Erro: "GOOGLE_API_KEY não configurada"
- Verifique se o arquivo `.env` existe
- Confirme se a chave está válida

## 📱 Endpoints Principais

- **Processar NF**: `POST /api/v1/nota-fiscal/process`
- **OCR apenas**: `POST /api/v1/nota-fiscal/upload-only`
- **Health check**: `GET /api/v1/nota-fiscal/health`
- **Entradas recentes**: `GET /api/v1/nota-fiscal/sheets/recent`
- **Documentação**: `GET /docs`

## 🎯 Pronto para Usar!

Após seguir todos os passos, você terá um sistema completo que:

1. ✅ Recebe imagens de notas fiscais
2. ✅ Extrai dados com Gemini 2.0 Flash
3. ✅ Salva automaticamente no Google Sheets
4. ✅ Fornece APIs REST para integração
