# Bot do Telegram - OCR Notas Fiscais

Bot do Telegram que consome a API de OCR de Notas Fiscais, permitindo que usuários processem suas notas fiscais enviando imagens ou PDFs diretamente pelo Telegram.

## 🚀 Funcionalidades

### 📤 Processamento de Documentos
- **Imagens**: JPG, PNG (até 10MB)
- **PDFs**: Arquivos PDF (até 10MB)
- **Processamento automático** via API de OCR
- **Salvamento automático** no Google Sheets

### 🤖 Comandos Disponíveis
- `/start` - Tela inicial com boas-vindas
- `/help` - Ajuda detalhada sobre como usar
- `/stats` - Estatísticas do serviço (total de NFs, valores, etc.)
- `/recent` - Últimas 5 notas fiscais processadas  
- `/health` - Status da API (OCR + Google Sheets)

### 📊 Recursos Avançados
- **Botões interativos** para fácil navegação
- **Formatação rica** das respostas
- **Tratamento de erros** com mensagens amigáveis
- **Logs detalhados** para debugging

## 🛠️ Configuração

### 1. Pré-requisitos
- Python 3.8+
- API de OCR rodando (porta 8000 por padrão)
- Token do bot do Telegram

### 2. Instalação das Dependências
```bash
cd telegram-bot
pip install -r requirements.txt
```

### 3. Configuração das Variáveis de Ambiente
No arquivo `.env` na raiz do projeto, adicione:
```properties
# Token do bot do Telegram
TELEGRAM_BOT_TOKEN=seu_token_aqui

# URL da API de OCR (opcional, padrão: http://localhost:8000)  
API_BASE_URL=http://localhost:8000

# Configurações opcionais
DEBUG=False
LOG_LEVEL=INFO
MAX_FILE_SIZE=10485760
REQUEST_TIMEOUT=60
```

### 4. Como obter o Token do Bot

1. Abra o Telegram e procure por **@BotFather**
2. Digite `/newbot` e siga as instruções
3. Escolha um nome para seu bot (ex: "MeuBotOCR")
4. Escolha um username (ex: "meu_bot_ocr_bot")
5. Copie o token fornecido e cole no `.env`

## 🚀 Execução

### Método 1: Script de Inicialização (Recomendado)
```bash
cd telegram-bot
python run_bot.py
```

### Método 2: Execução Direta
```bash
cd telegram-bot
python bot.py
```

### Exemplo de Saída
```
🤖 Iniciando Bot do Telegram para OCR de Notas Fiscais
============================================================
🤖 Configurações do Bot:
  API URL: http://localhost:8000
  Debug: False
  Log Level: INFO
  Max File Size: 10.0MB
  Request Timeout: 60s
  Token configurado: ✅

🔗 Testando conexão com API...
✅ API conectada - Status: healthy

🚀 Iniciando bot...
   Token: 8037768210...
   API: http://localhost:8000
   Pressione Ctrl+C para parar
```

## 📱 Como Usar o Bot

### 1. Iniciar Conversa
- Procure seu bot no Telegram pelo username
- Digite `/start` para ver as opções

### 2. Processar Nota Fiscal
- Envie uma **foto** da nota fiscal, ou
- Envie um **arquivo PDF** da nota fiscal
- Aguarde o processamento (5-30 segundos)
- Receba os dados extraídos formatados

### 3. Exemplo de Resposta
```
✅ Nota Fiscal Processada com Sucesso!

📋 Dados da NF:
• Número: 123456
• Série: 1
• Data Emissão: 15/06/2025
• Valor Total: R$ 1.250,00

🏢 Emissor:
• Empresa Exemplo LTDA
• CNPJ: 12.345.678/0001-90

📍 Destinatário:
• João da Silva
• CNPJ: 98.765.432/0001-10

📦 Itens (3):
1. Produto A - Qtd: 2 | Valor: R$ 500,00
2. Produto B - Qtd: 1 | Valor: R$ 750,00

💾 Dados salvos no Google Sheets!
⏱️ Processado em 12.5s
```

## 🔧 Estrutura do Projeto

```
telegram-bot/
├── bot.py              # Código principal do bot
├── config.py           # Configurações e variáveis de ambiente
├── run_bot.py          # Script de inicialização
├── requirements.txt    # Dependências Python
├── README.md          # Este arquivo
└── bot.log            # Logs do bot (criado automaticamente)
```

## 🔍 Logs e Debugging

### Visualizar Logs em Tempo Real
```bash
tail -f telegram-bot/bot.log
```

### Logs Importantes
- Conexões com API
- Erros de processamento
- Mensagens dos usuários
- Status do serviço

## ⚠️ Tratamento de Erros

O bot possui tratamento robusto de erros:

- **Arquivo muito grande**: "❌ Arquivo muito grande! Tamanho máximo: 10MB"
- **Formato não suportado**: "❌ Apenas arquivos PDF são suportados"
- **API indisponível**: "❌ Erro na API" com detalhes do problema
- **Erro de processamento**: "❌ Erro no processamento: [detalhes]"

## 🔒 Segurança

- **Token protegido**: Nunca exponha o token do bot
- **Validação de arquivos**: Verificação de tipo e tamanho
- **Timeout de requisições**: Evita travamentos
- **Logs seguros**: Não logam dados sensíveis

## 🧪 Testes

Para testar o bot sem usuários reais:
1. Adicione seu bot aos seus contatos
2. Envie comandos e arquivos de teste
3. Verifique os logs para debugging

## 🆘 Problemas Comuns

### Bot não responde
1. Verifique se o token está correto
2. Confirme se o bot está rodando
3. Verifique os logs para erros

### API não conecta
1. Confirme se a API OCR está rodando
2. Verifique a URL no `.env`
3. Teste a API diretamente no navegador

### Arquivos não processam
1. Verifique o tamanho do arquivo
2. Confirme o formato (JPG, PNG, PDF)
3. Verifique se a API está funcionando

## 🤝 Suporte

Em caso de problemas:
1. Verifique os logs: `tail -f telegram-bot/bot.log`
2. Teste a API diretamente: `curl http://localhost:8000/nota-fiscal/health`
3. Reinicie o bot: `python run_bot.py`
