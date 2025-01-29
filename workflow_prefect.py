import yfinance as yf
from datetime import datetime, timedelta
from prefect import flow, task
import pandas as pd
from google.colab import drive
import os
import nest_asyncio
from prefect.server.schemas.schedules import CronSchedule
import asyncio
import matplotlib.pyplot as plt
from prefect.deployments import Deployment
from prefect.infrastructure import Process
from prefect.client import get_client
from prefect.artifacts import create_table_artifact
from prefect.blocks.system import Secret
from prefect.variables import set_variable, get_variable

# Conectar ao Google Drive
drive.mount('/content/drive')

# Definir variáveis de data e tickers
end_date = datetime.now()
start_date = end_date - timedelta(days=7)
tickers = [
    "ABEV3.SA", "ALPA4.SA", "AMER3.SA", "ARZZ3.SA", "ASAI3.SA", "AZUL4.SA",
    "B3SA3.SA", "BBAS3.SA", "BBDC3.SA", "BBDC4.SA", "BBSE3.SA", "BEEF3.SA",
    "BPAC11.SA", "BPAN4.SA", "BRAP4.SA", "BRFS3.SA", "BRKM5.SA", "BRML3.SA",
    "CASH3.SA", "CCRO3.SA", "CIEL3.SA", "CMIG4.SA", "CMIN3.SA", "COGN3.SA",
    "CPFE3.SA", "CPLE6.SA", "CRFB3.SA", "CSAN3.SA", "CSNA3.SA", "CVCB3.SA",
    "CYRE3.SA", "DXCO3.SA", "ECOR3.SA", "EGIE3.SA", "ELET3.SA", "ELET6.SA",
    "EMBR3.SA", "ENBR3.SA", "ENGI11.SA", "ENEV3.SA", "EQTL3.SA", "EZTC3.SA",
    "FLRY3.SA", "GGBR4.SA", "GOAU4.SA", "GOLL4.SA", "HAPV3.SA", "HGTX3.SA",
    "HYPE3.SA", "IGTI11.SA", "IRBR3.SA", "ITSA4.SA", "ITUB4.SA", "JBSS3.SA",
    "JHSF3.SA", "KLBN11.SA", "LAME4.SA", "LCAM3.SA", "LIGT3.SA", "LINX3.SA",
    "LREN3.SA", "MGLU3.SA", "MOVI3.SA", "MRFG3.SA", "MRVE3.SA", "MULT3.SA",
    "MYPK3.SA", "NTCO3.SA", "PCAR3.SA", "PETR3.SA", "PETR4.SA", "POSI3.SA",
    "PRIO3.SA", "QUAL3.SA", "RADL3.SA", "RAIL3.SA", "RENT3.SA", "RRRP3.SA",
    "SANB11.SA", "SBSP3.SA", "SULA11.SA", "SUZB3.SA", "TAEE11.SA", "TIMS3.SA",
    "TOTS3.SA", "UGPA3.SA", "USIM5.SA", "VALE3.SA", "VBBR3.SA", "VIVT3.SA",
    "VVAR3.SA", "WEGE3.SA", "YDUQ3.SA"
]

# Salvar a lista de tickers como variável Prefect
set_variable("tickers", tickers)

# Task para baixar dados
@task(retries=3, retry_delay_seconds=10, log_prints=True)
def download_stock_data(tickers, start_date, end_date):
    data = {}
    for ticker in tickers:
        try:
            df = yf.download(ticker, start=start_date, end=end_date)
            data[ticker] = df
            print(f"Dados de {ticker} baixados com sucesso")
        except Exception as e:
            print(f"Falha ao baixar dados de {ticker}: {e}")
    return data

# Task para calcular indicadores financeiros básicos
@task(retries=3, retry_delay_seconds=10, log_prints=True)
def calculate_indicators(data):
    indicators = {}
    for ticker, df in data.items():
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['Volatility'] = df['Close'].rolling(window=50).std()
        indicators[ticker] = df
        print(f"Indicadores calculados para {ticker}")
    return indicators

# Task para gerar relatórios simples em formato de gráficos
@task(retries=3, retry_delay_seconds=10, log_prints=True)
def generate_reports(data, folder_path='/content/drive/My Drive/stock_reports'):
    os.makedirs(folder_path, exist_ok=True)
    for ticker, df in data.items():
        plt.figure(figsize=(10, 5))
        plt.plot(df['Close'], label='Close Price')
        plt.plot(df['SMA_50'], label='50-Day SMA')
        plt.title(f'{ticker} Stock Price and 50-Day SMA')
        plt.legend()
        report_path = os.path.join(folder_path, f"{ticker}_report.png")
        plt.savefig(report_path)
        plt.close()
        print(f"Relatório de {ticker} salvo em {report_path}")

# Task para salvar o DataFrame no Google Drive e criar um link de artefato
@task(retries=3, retry_delay_seconds=10, log_prints=True)
def upload_to_drive_and_create_link(data, folder_path='/content/drive/My Drive/stock_data'):
    os.makedirs(folder_path, exist_ok=True)
    links = {}
    for ticker, df in data.items():
        date_str = datetime.now().strftime('%Y-%m-%d')
        file_path = os.path.join(folder_path, f"{ticker}_stock_data_{date_str}.csv")
        df.to_csv(file_path)
        print(f"Dados de {ticker} salvos em {file_path}")
        links[ticker] = file_path

        # Simulação de criação de link de artefato
        create_link_artifact(
            key=ticker.lower(),
            link=file_path,
            description=ticker + " stock_data",
        )

    return links

# Task para registrar as três ações que mais subiram e as três que mais desceram no último dia baixado
@task(retries=3, retry_delay_seconds=10, log_prints=True)
def record_top_movers(data):
    last_day = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    changes = {}
    for ticker, df in data.items():
        if last_day in df.index:
            changes[ticker] = df.loc[last_day]['Close'] - df.loc[last_day]['Open']
    sorted_changes = sorted(changes.items(), key=lambda x: x[1], reverse=True)
    top_gainers = sorted_changes[:3]
    top_losers = sorted_changes[-3:]

    table_data = {
        "Top Gainers": [f"{ticker}: {change:.2f}" for ticker, change in top_gainers],
        "Top Losers": [f"{ticker}: {change:.2f}" for ticker, change in top_losers]
    }
    create_table_artifact(
        key="top_movers",
        table=table_data,
        description="Top 3 gainers and losers"
    )
    print("Top movers registrados com sucesso")

# Criando o fluxo Prefect
@flow(name="stock_workflow")
def stock_workflow():
    tickers = get_variable("tickers")
    data = download_stock_data(tickers, start_date, end_date)
    indicators = calculate_indicators(data)
    generate_reports(indicators)
    artifact_links = upload_to_drive_and_create_link(indicators)
    record_top_movers(indicators)
    for ticker, link in artifact_links.items():
        print(f"Link para os dados de {ticker}: {link}")

# Habilitar nest_asyncio para permitir loops aninhados
nest_asyncio.apply()

# Função principal para execução
async def main():
    # Configurar Prefect Cloud
    secret_block = Secret.load("prefect-cloud-api-key")
    os.system(f"prefect cloud login -k {secret_block.get()}")

    # Fazer o deploy com CRON
    deployment = Deployment.build_from_flow(
        flow=stock_workflow,
        name="stock-data-daily",
        schedule=CronSchedule(cron="0 0 * * *"),  # Executa diariamente à meia-noite
        infrastructure=Process(),
        tags=["stocks", "daily"]
    )
    deployment.apply()

    # Executar o flow
    await stock_workflow()

# Bloco de execução
if __name__ == "__main__":
    # Executar o programa
    asyncio.run(main())

# Instale as dependencias
!pip install -U prefect yfinance nest_asyncio matplotlib
