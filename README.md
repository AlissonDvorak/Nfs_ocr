# 🧾 OCR Notas Fiscais - Sistema Completo

Sistema completo para processamento automático de Notas Fiscais brasileiras usando Google Gemini 2.0 Flash para OCR, com salvamento no Google Sheets e interface via Bot do Telegram.

## 🌟 Funcionalidades

### 🔍 Processamento OCR
- **Google Gemini 2.0 Flash** para extração de dados estruturados
- **Formatos suportados**: JPG, PNG, PDF (até 10MB)
- **Dados extraídos**: Número, série, valores, impostos, itens, empresas, etc.
- **Processamento inteligente** com validação e limpeza de dados

### 📊 Google Sheets Integration
- **Salvamento automático** em múltiplas planilhas
- **Planilha principal**: Resumo das notas fiscais
- **Planilha de itens**: Todos os itens de todas as NFs
- **Planilhas por CNPJ**: Uma planilha para cada empresa emissora
- **Cabeçalhos automáticos** e formatação profissional

### 🤖 Bot do Telegram
- **Interface amigável** via Telegram
- **Processamento direto**: Envie foto/PDF e receba dados estruturados
- **Comandos úteis**: Estatísticas, dados recentes, status do sistema
- **Respostas formatadas** com emojis e organização clara

### 🛠️ API RESTful
- **FastAPI** com documentação automática
- **Endpoints robustos** para todos os recursos
- **Validação de dados** e tratamento de erros
- **Logs detalhados** para debugging

## 🏗️ Arquitetura

```
📁 Ocr-Nf/
├── 📁 app/                          # API Principal
│   ├── 📁 api/                      # Endpoints REST
│   ├── 📁 config/                   # Configurações
│   ├── 📁 services/                 # Lógica de negócio
│   └── main.py                      # FastAPI app
├── 📁 telegram-bot/                 # Bot do Telegram
│   ├── bot.py                       # Código principal do bot
│   ├── config.py                    # Configurações do bot
│   └── run_bot.py                   # Script de inicialização
├── 📁 tests/                        # Scripts de teste e configuração
│   ├── test_*.py                    # Testes automatizados
│   ├── setup_oauth.py               # Configuração OAuth2
│   └── README.md                    # Documentação dos testes
├── .env                             # Variáveis de ambiente
├── requirements.txt                 # Dependências principais
├── start_system.py                  # Inicialização completa
├── run_tests.py                     # Menu principal de testes
└── README.md                        # Este arquivo
```

## 🚀 Instalação e Configuração

### 1. Clone o Repositório
```bash
git clone <url-do-repositorio>
cd Ocr-Nf
```

### 2. Configure as Variáveis de Ambiente
Copie e configure o arquivo `.env`:
```bash
cp teste.env .env
# Edite o .env com suas credenciais
```

**Variáveis necessárias:**
```properties
# Google Gemini
GOOGLE_API_KEY=sua_chave_gemini

# Google Sheets
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=id_da_sua_planilha

# Telegram Bot
TELEGRAM_BOT_TOKEN=token_do_seu_bot

# Opcional
API_BASE_URL=http://localhost:8000
DEBUG=False
```

### 3. Configure as Credenciais do Google
1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um projeto ou use existente
3. Ative as APIs: Google Sheets API e Google Drive API
4. Crie credenciais de conta de serviço
5. Baixe o arquivo JSON e salve como `credentials.json`

### 4. Configure o Bot do Telegram
1. No Telegram, procure por **@BotFather**
2. Digite `/newbot` e siga as instruções
3. Copie o token fornecido para o `.env`

### 5. Instale e Execute
```bash
# Instalar dependências e executar tudo
python start_system.py

# Ou individualmente:
# Apenas API
python -m app.main

# Apenas Bot
cd telegram-bot && python run_bot.py
```

### 6. Execute os Testes (Recomendado)
```bash
# Menu principal de testes
python run_tests.py

# Ou testes específicos
python tests/test_service.py        # Health check
python tests/test_pdf_processing.py # Teste PDFs
python tests/test_api_complete.py   # API completa
```

## 🧪 Testes e Validação

O sistema inclui uma suíte completa de testes para validar todas as funcionalidades.

### Menu Principal de Testes
```bash
python run_tests.py
```

### Testes Disponíveis
- **Health Check**: Valida API, serviços e conectividade
- **Processamento PDF**: Testa OCR em arquivos PDF
- **Google Drive**: Valida upload e estrutura de pastas
- **API Completa**: Testa todos os endpoints REST
- **Configuração OAuth2**: Para Google Drive pessoal

### Documentação Detalhada
Veja `tests/README.md` para instruções completas sobre:
- Como executar cada teste
- Interpretação dos resultados
- Solução de problemas
- Adição de novos testes

## 📱 Como Usar

### Via Bot do Telegram
1. **Procure seu bot** no Telegram
2. **Envie `/start`** para ver as opções
3. **Envie uma foto** da nota fiscal ou arquivo PDF
4. **Aguarde o processamento** (5-30 segundos)
5. **Receba os dados** estruturados e formatados

### Via API REST
```bash
# Documentação interativa
http://localhost:8000/docs

# Processar nota fiscal
curl -X POST "http://localhost:8000/nota-fiscal/process" \
  -F "file=@nota_fiscal.jpg"

# Ver estatísticas
curl "http://localhost:8000/nota-fiscal/sheets/statistics"
```

### Comandos do Bot
- `/start` - Tela inicial com opções
- `/help` - Ajuda detalhada
- `/stats` - Estatísticas do sistema
- `/recent` - Últimas notas processadas
- `/health` - Status da API e serviços

## 📊 Estrutura das Planilhas

### Planilha Principal: "OCR Notas Fiscais"
- Resumo de cada nota fiscal processada
- Dados do emissor e destinatário
- Valores totais e impostos
- Status do processamento

### Planilha de Itens: "OCR Notas Fiscais - Itens"
- Todos os itens de todas as notas fiscais
- Detalhes completos: código, descrição, quantidade, valores
- Referência à nota fiscal origem

### Planilhas por CNPJ: "CNPJ_[numero]_[empresa]"
- Uma planilha para cada empresa emissora
- Histórico completo de notas da empresa
- Informações da empresa nas primeiras linhas

## 🔧 Recursos Técnicos

### OCR com Google Gemini
- **Modelo**: gemini-2.0-flash
- **Prompt otimizado** para notas fiscais brasileiras
- **Extração estruturada** em JSON
- **Validação e limpeza** automática de dados

### Tratamento de Erros
- **Validação de arquivos**: Tamanho, formato, conteúdo
- **Retry logic**: Tentativas automáticas em caso de falha
- **Logs detalhados**: Para debugging e monitoramento
- **Respostas informativas**: Usuário sempre sabe o que aconteceu

### Performance
- **Processamento assíncrono** para múltiplas requisições
- **Cache inteligente** de configurações
- **Otimização de API calls** para Google Sheets
- **Timeout configurável** para evitar travamentos

## 📈 Exemplos de Uso

### Resposta do Bot após Processar NF
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

📦 Itens (3):
1. Produto A - Qtd: 2 | Valor: R$ 500,00
2. Produto B - Qtd: 1 | Valor: R$ 750,00

💾 Dados salvos no Google Sheets!
⏱️ Processado em 12.5s
```

### Estatísticas do Sistema
```
📊 Estatísticas do Serviço

📋 Notas Fiscais:
• Total processadas: 147
• Valor total: R$ 45.678,90
• Última: 15/06/2025 14:30

📦 Itens:
• Total de itens: 892

🏢 Empresas ativas: 12
• Empresa A, Empresa B, Empresa C...
```

## 🔍 Monitoramento e Logs

### Logs da API
```bash
tail -f app.log
```

### Logs do Bot
```bash
tail -f telegram-bot/bot.log
```

### Health Check
```bash
curl http://localhost:8000/nota-fiscal/health
```

## 🛠️ Desenvolvimento

### Estrutura do Código
- **Modular**: Separação clara de responsabilidades
- **Async/Await**: Para performance otimizada
- **Type Hints**: Código mais robusto e legível
- **Error Handling**: Tratamento abrangente de erros

### Adicionando Novos Recursos
1. **API**: Adicione endpoints em `app/api/`
2. **Lógica**: Implemente em `app/services/`
3. **Bot**: Adicione comandos em `telegram-bot/bot.py`
4. **Teste**: Crie testes em `tests/` e atualize `run_tests.py`

### Extensibilidade
- **Novos formatos**: Adicione suporte a outros tipos de documento
- **Outras APIs OCR**: Implemente outros provedores além do Gemini
- **Novos destinos**: Salve dados em outros sistemas além de Sheets
- **Interfaces**: Crie web UI, mobile app, etc.

## 🔒 Considerações de Segurança

- **Credenciais**: Nunca commite arquivos com credenciais
- **Tokens**: Use variáveis de ambiente para tokens sensíveis
- **Validação**: Todos os inputs são validados antes do processamento
- **Logs**: Não logam dados sensíveis dos usuários

## 📞 Suporte

### Problemas Comuns
- **Bot não responde**: Verifique o token e se a API está rodando
- **OCR falha**: Confirme se a imagem está legível e o Gemini configurado
- **Sheets não atualiza**: Verifique credenciais e permissões da planilha

### Getting Help
1. **Execute os testes**: `python run_tests.py` para diagnóstico completo
2. Verifique os logs para erros específicos
3. Teste a API diretamente: `http://localhost:8000/docs`
4. Valide configurações: `python start_system.py` opção 4

## 🎯 Roadmap

- [ ] Interface web para visualização de dados
- [ ] Suporte a mais formatos de documento
- [ ] Integração com ERPs populares
- [ ] Dashboard com métricas avançadas
- [ ] API para terceiros consumirem dados
- [ ] Processamento em lote
- [ ] Notificações automáticas

---

**Desenvolvido com ❤️ para facilitar o processamento de Notas Fiscais brasileiras**
