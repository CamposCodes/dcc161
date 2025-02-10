import yfinance as yf
from datetime import datetime, timedelta
from prefect import flow, task, variables
from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule
from prefect.artifacts import create_table_artifact
from prefect.filesystems import LocalFileSystem
from prefect.blocks.system import Secret
import pandas as pd
import os
import matplotlib.pyplot as plt

# ==============================================
# BLOCKS E VARIÁVEIS DE CONFIGURAÇÃO
# ==============================================
def configure_blocks_and_variables():
    # Carregar tickers da variável do Prefect (configurar via UI)
    tickers = variables.get("tickers", default=[
        "ABEV3.SA", "ALPA4.SA", "AMER3.SA", "ARZZ3.SA", "ASAI3.SA", "AZUL4.SA",
        # ... (lista completa de tickers)
        "WEGE3.SA", "YDUQ3.SA"
    ])
    
    # Configurar armazenamento local (bloco salvo via UI/CLI)
    storage = LocalFileSystem.load("stock-data")
    
    return tickers, storage

# ==============================================
# TASKS COM RETRY E LOGGING
# ==============================================
@task(retries=3, retry_delay_seconds=30, log_prints=True)
def download_stock_data(tickers):
    data = {}
    for ticker in tickers:
        try:
            df = yf.download(ticker, period="7d", interval="1d")
            if not df.empty:
                data[ticker] = df
                print(f"✅ Dados de {ticker} baixados | Registros: {len(df)}")
            else:
                print(f"⚠️  Dados vazios para {ticker}")
        except Exception as e:
            print(f"⛔ Falha crítica no download de {ticker}: {str(e)}")
            raise
    return data

@task(retries=2, log_prints=True)
def calculate_indicators(data):
    for ticker, df in data.items():
        try:
            df['SMA_50'] = df['Close'].rolling(window=50).mean().round(2)
            df['Volatility'] = df['Close'].pct_change().std().round(4)
            print(f"📊 Indicadores calculados para {ticker}")
        except Exception as e:
            print(f"❌ Erro no cálculo de indicadores para {ticker}: {str(e)}")
            raise
    return data

@task(log_prints=True)
def quality_check(data):
    for ticker, df in data.items():
        if df.empty:
            raise ValueError(f"🚨 Dados vazios para {ticker}")
        if df.isnull().values.any():
            print(f"⚠️  Dados incompletos para {ticker}")
    print("✅ Verificação de qualidade concluída")
    return data

# ==============================================
# PARTICIONAMENTO E ARMAZENAMENTO
# ==============================================
@task(log_prints=True)
def save_partitioned_data(data, storage):
    for ticker, df in data.items():
        try:
            # Particionamento por data
            for date in df.index.unique():
                daily_df = df[df.index == date]
                path = f"{ticker}/{date.date()}.csv"
                storage.write_path(path, daily_df.to_csv().encode())
                print(f"💾 Dados salvos: {path}")
        except Exception as e:
            print(f"⛔ Falha ao salvar dados de {ticker}: {str(e)}")
            raise

# ==============================================
# ARTIFACTS E RELATÓRIOS
# ==============================================
@task(log_prints=True)
def generate_report(data):
    try:
        all_data = pd.concat(data.values())
        create_table_artifact(
            key="daily-stock-report",
            table=all_data.reset_index().to_dict("records"),
            description="Relatório diário consolidado"
        )
        print("📄 Artefato de relatório gerado com sucesso")
    except Exception as e:
        print(f"⛔ Falha ao gerar relatório: {str(e)}")
        raise

@task(log_prints=True)
def record_top_movers(data):
    movers = []
    for ticker, df in data.items():
        try:
            last_day = df.iloc[-1]
            change = ((last_day['Close'] - last_day['Open']) / last_day['Open'] * 100).round(2)
            movers.append({"Ticker": ticker, "Variação (%)": change})
        except Exception as e:
            print(f"⚠️  Erro ao calcular variação para {ticker}: {str(e)}")
    
    df_movers = pd.DataFrame(movers)
    
    create_table_artifact(
        key="top-movers",
        table={
            "Top Gainers": df_movers.nlargest(3, "Variação (%)").to_dict("records"),
            "Top Losers": df_movers.nsmallest(3, "Variação (%)").to_dict("records")
        },
        description="Top 3 maiores altas e baixas"
    )
    print("📈 Artefato de movimentações gerado")

# ==============================================
# FLUXO PRINCIPAL
# ==============================================
@flow(name="Stock Analysis Pipeline", retries=2)
def stock_analysis_flow():
    # Configuração
    tickers, storage = configure_blocks_and_variables()
    
    # Execução
    raw_data = download_stock_data(tickers)
    validated_data = quality_check(raw_data)
    processed_data = calculate_indicators(validated_data)
    save_partitioned_data(processed_data, storage)
    generate_report(processed_data)
    record_top_movers(processed_data)

# ==============================================
# DEPLOYMENT E GERENCIAMENTO
# ==============================================
def deploy():
    # Configurar blocos
    Secret(value="sua-api-key").save(name="prefect-api-key", overwrite=True)
    LocalFileSystem(basepath="./data").save(name="stock-data", overwrite=True)
    
    # Criar deployment
    deployment = Deployment.build_from_flow(
        flow=stock_analysis_flow,
        name="stock-daily-analysis",
        schedule=CronSchedule(cron="0 18 * * *"),  # Diariamente às 18h
        work_pool_name="aws-ec2-pool",            # Altere para seu work pool
        parameters={"tickers": variables.get("tickers")}
    )
    deployment.apply()
    print("🚀 Deployment criado com sucesso!")

# ==============================================
# EXECUÇÃO
# ==============================================
if __name__ == "__main__":
    # Para deploy: python script.py deploy
    import sys
    if "deploy" in sys.argv:
        deploy()
    else:
        stock_analysis_flow()