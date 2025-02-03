import yfinance as yf
from datetime import datetime, timedelta
from prefect import flow, task
import pandas as pd
import os
import nest_asyncio
from prefect.server.schemas.schedules import CronSchedule
import asyncio
import matplotlib.pyplot as plt
from prefect.artifacts import create_table_artifact
from prefect.blocks.system import Secret

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
def generate_reports(data, folder_path='./reports'):
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

# Task para salvar o DataFrame localmente e criar um link de artefato
@task(retries=3, retry_delay_seconds=10, log_prints=True)
def save_data_locally(data, folder_path='./data'):
    os.makedirs(folder_path, exist_ok=True)
    links = {}
    for ticker, df in data.items():
        date_str = datetime.now().strftime('%Y-%m-%d')
        file_path = os.path.join(folder_path, f"{ticker}_stock_data_{date_str}.csv")
        df.to_csv(file_path)
        print(f"Dados de {ticker} salvos em {file_path}")
        links[ticker] = file_path

        # Simulação de criação de link de artefato
        create_table_artifact(
            key=ticker.lower().replace('.', '-'),
            table=[{"link": file_path}],
            description=ticker + " stock_data",
        )

    return links

# Task para registrar as três ações que mais subiram e as três que mais desceram no último dia baixado
@task(retries=3, retry_delay_seconds=10, log_prints=True)
def record_top_movers(data):
    changes = {}
    for ticker, df in data.items():
        try:
            # Pegar a última data disponível para cada ticker
            last_available_date = df.index[-1]
            
            # Calcular a variação usando valores escalares
            daily_change = float(df.loc[last_available_date, 'Close']) - float(df.loc[last_available_date, 'Open'])
            changes[ticker] = daily_change
            
        except (KeyError, IndexError, ValueError) as e:
            print(f"Erro ao processar {ticker}: {e}")
            continue
    # Ordenar as mudanças
    sorted_changes = sorted(changes.items(), key=lambda x: x[1], reverse=True)
    # Pegar top 3 e bottom 3
    top_gainers = sorted_changes[:3] if len(sorted_changes) >= 3 else sorted_changes
    top_losers = sorted_changes[-3:] if len(sorted_changes) >= 3 else sorted_changes[::-1]
    # Preparar dados para o artifact
    table_data = {
        "Top Gainers": [f"{ticker}: {change:.2f}" for ticker, change in top_gainers],
        "Top Losers": [f"{ticker}: {change:.2f}" for ticker, change in top_losers]
    }
    create_table_artifact(
        key="top-movers",
        table=[table_data],
        description="Top 3 gainers and losers"
    )
    print("Top movers registrados com sucesso")

# Criando o fluxo Prefect
@flow(name="stock_workflow")
def stock_workflow():
    data = download_stock_data(tickers, start_date, end_date)
    indicators = calculate_indicators(data)
    generate_reports(indicators)
    artifact_links = save_data_locally(indicators)
    record_top_movers(indicators)
    for ticker, link in artifact_links.items():
        print(f"Link para os dados de {ticker}: {link}")

# Habilitar nest_asyncio para permitir loops aninhados
nest_asyncio.apply()

# Função para criar o secret
def create_secret():
    # Criar o bloco
    secret_block = Secret(value="pnu_K4QUT5G3tDDlEpepH3jVpdG9CV5LkT3erV5U")
    
    # Salvar com o nome específico
    secret_block.save(name="prefect-cloud-api-key", overwrite=True)
    print("Bloco Secret criado com sucesso!")

# Função principal para execução
def main():
    # Criar o secret
    create_secret()

    # Configurar Prefect Cloud
    secret_block = Secret.load("prefect-cloud-api-key")
    api_key = secret_block.get()
    os.system(f"prefect cloud login -k {api_key}")

    # Executar o flow
    stock_workflow()

# Bloco de execução
if __name__ == "__main__":
    # Executar o programa
    main()


#cron adicionar e deploy