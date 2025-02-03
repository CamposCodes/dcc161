# 📈 Pipeline de Dados de Ações com Prefect

[![Prefect](https://img.shields.io/badge/prefect-2.0+-blue.svg)](https://www.prefect.io/)
[![yfinance](https://img.shields.io/badge/yfinance-0.2.37-green.svg)](https://pypi.org/project/yfinance/)
[![Google Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/)

Um pipeline automatizado para coleta, análise e relatório de dados do mercado de ações brasileiro usando a orquestração de workflows do Prefect.

## 🌟 Funcionalidades

- **Coleta de Dados Automatizada**: Download diário de dados de ações do Yahoo Finance.
- **Indicadores Técnicos**: Cálculo de Média Móvel Simples (SMA-50) e volatilidade.
- **Relatórios Visuais**: Geração de gráficos interativos de preços.
- **Integração com a Nuvem**: Armazenamento automático no Google Drive.
- **Alertas Inteligentes**: Identifica as maiores altas e baixas do dia.
- **Execução Programada**: Execuções diárias automatizadas com Prefect Cloud.

## 🚀 Início Rápido

### Instalação
```bash
!pip install -U prefect yfinance nest_asyncio matplotlib
```

### Configuração
1. **Montar o Google Drive**:
```python
from google.colab import drive
drive.mount('/content/drive')
```

2. **Configurar o Prefect Cloud**:
```python
from prefect.blocks.system import Secret
secret_block = Secret.load("prefect-cloud-api-key")
```

## 📊 Visão Geral do Workflow

### Estrutura do Pipeline
1. **Aquisição de Dados** (`download_stock_data`)
   - Obtém dados históricos de mais de 100 ações brasileiras.
   - Repetição automática para downloads falhos.

2. **Análise Técnica** (`calculate_indicators`)
   - Calcula:
     - Média Móvel Simples de 50 dias (SMA-50)
     - Volatilidade de 50 dias

3. **Relatórios Visuais** (`generate_reports`)
   - Gera gráficos interativos com:
     - Tendências de preço
     - Sobreposição da SMA
     - Faixas de volatilidade

4. **Armazenamento na Nuvem** (`upload_to_drive_and_create_link`)
   - Salva os dados no Google Drive:
   ```plaintext
   /My Drive/stock_data/[TICKER]_stock_data_[DATE].csv
   ```

5. **Análise de Mercado** (`record_top_movers`)
   - Identifica os 3 maiores ganhadores/perdedores do dia.
   - Cria artifacts do Prefect para monitoramento.

## ⚙️ Integração com Prefect Cloud

### Configuração do Deploy
```python
deployment = Deployment.build_from_flow(
    flow=stock_workflow,
    name="stock-data-daily",
    schedule=CronSchedule(cron="0 0 * * *"),  # Meia-noite UTC
    infrastructure=Process(),
    tags=["br-stocks", "daily-analysis"]
)
```

### Monitoramento
- Acompanhe execuções na interface do Prefect Cloud.
- Consulte links de artifacts para relatórios gerados.
- Monitore taxas de sucesso das tarefas.

## 📈 Exemplos de Saídas

### Tabela de Maiores Movimentos
| Maiores Altas       | Maiores Baixas       |
|---------------------|---------------------|
| PETR4: +2.45%      | BBDC4: -1.87%       |
| VALE3: +1.92%      | ITUB4: -1.23%       |
| MGLU3: +1.15%      | BBAS3: -0.98%       |

### Exemplo de Relatório
![Gráfico de Preço](https://via.placeholder.com/800x400.png?text=Stock+Price+Chart+Example)

## 🔧 Personalização

### Modificar a Lista de Tickers
```python
tickers = [
    "PETR4.SA",
    "VALE3.SA",
    # Adicione/remova tickers conforme necessário
]
```

### Ajustar Período de Análise
```python
start_date = end_date - timedelta(days=30)  # Janela de 30 dias
```

### Adicionar Novos Indicadores
```python
df['RSI'] = ta.rsi(df['Close'], window=14)
```

## 🛠 Solução de Problemas

**Problemas Comuns**:
1. **Erros de Autenticação**:
   - Verifique a API key do Prefect.
   - Confira as permissões do Google Drive.

2. **Falhas no Download de Dados**:
   - Verifique os códigos dos tickers.
   - Confirme o status da API do Yahoo Finance.

3. **Conflitos de Dependências**:
```bash
!pip install --force-reinstall yfinance
```

## 📌 Especificações das Etapas do Trabalho

**Metas da Semana:**

1. Conectar com o Prefect Cloud (Criar conta, gerar API Key, e executar um workflow localmente, acompanhando-o no painel do Prefect Cloud).
2. Fazer o deploy na nuvem usando os métodos `serve` ou `deploy`, com uma configuração inicial de CRON rodando diariamente.
3. Configurar o script para baixar os últimos 7 dias de dados e salvá-los no Google Drive. Implementar uma estratégia de particionamento para salvar um CSV com os dados diários.
4. Implementar saídas de console para registrar sucesso ou falha no registro dos dados (quality check).
5. Utilizar `table artifact` para registrar as três ações que mais subiram e as três que mais caíram no último dia baixado.
6. Aumentar a base de tickers baixada diariamente.

**Metas Adicionais:**

1. Implementar retentativas automáticas para tarefas que falharem, exibindo logs detalhados de erros (parâmetros `retry` e `log_print`).
2. Fazer o deploy utilizando `blocks` (para armazenar dados confidenciais, como API keys) e `variables` (para armazenar a lista de tickers).
3. Caso não tenha implementado algum item anterior, como `artifacts table`, ou tenha tido erro no deploy, corrigir nesta semana.

Não se esqueça de fazer o upload do seu notebook ou arquivo `.py` para contar sua presença na aula.

## 🤝 Contribuição
```plaintext
1. Faça um fork do repositório
2. Crie um branch de feature (git checkout -b feature/melhoria)
3. Commit suas mudanças (git commit -am 'Adicionar nova funcionalidade')
4. Envie para o branch (git push origin feature/melhoria)
5. Crie um Pull Request
```

## 📄 Licença
Licença MIT - Consulte [LICENSE](https://opensource.org/licenses/MIT) para mais detalhes.

