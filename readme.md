# 📈 Stock Data Pipeline with Prefect

[![Prefect](https://img.shields.io/badge/prefect-2.0+-blue.svg)](https://www.prefect.io/)
[![yfinance](https://img.shields.io/badge/yfinance-0.2.37-green.svg)](https://pypi.org/project/yfinance/)
[![Google Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/)

An automated pipeline for collecting, analyzing, and reporting Brazilian stock market data using Prefect workflow orchestration.

## 🌟 Features

- **Automated Data Collection**: Daily download of stock data from Yahoo Finance
- **Technical Indicators**: Calculation of SMA-50 and volatility
- **Visual Reports**: Generation of interactive price charts
- **Cloud Integration**: Automatic storage in Google Drive
- **Smart Alerts**: Identification of top gainers/losers
- **Scheduled Execution**: Daily automated runs with Prefect Cloud

## 🚀 Quick Start

### Installation
```bash
!pip install -U prefect yfinance nest_asyncio matplotlib
```

### Configuration
1. **Google Drive Mounting**:
```python
from google.colab import drive
drive.mount('/content/drive')
```

2. **Prefect Cloud Setup**:
```python
from prefect.blocks.system import Secret
secret_block = Secret.load("prefect-cloud-api-key")
```

## 📊 Workflow Overview

### Pipeline Structure
1. **Data Acquisition** (`download_stock_data`)
   - Fetches historical data for 100+ Brazilian stocks
   - Automatic retries for failed downloads

2. **Technical Analysis** (`calculate_indicators`)
   - Calculates:
     - 50-day Simple Moving Average (SMA)
     - 50-day Volatility

3. **Visual Reporting** (`generate_reports`)
   - Generates interactive charts with:
     - Price trends
     - SMA overlay
     - Volatility bands

4. **Cloud Storage** (`upload_to_drive_and_create_link`)
   - Saves data to Google Drive:
   ```plaintext
   /My Drive/stock_data/[TICKER]_stock_data_[DATE].csv
   ```

5. **Market Insights** (`record_top_movers`)
   - Identifies top 3 performers/decliners
   - Creates Prefect artifacts for tracking

## ⚙️ Prefect Cloud Integration

### Deployment Setup
```python
deployment = Deployment.build_from_flow(
    flow=stock_workflow,
    name="stock-data-daily",
    schedule=CronSchedule(cron="0 0 * * *"),  # Midnight UTC
    infrastructure=Process(),
    tags=["br-stocks", "daily-analysis"]
)
```

### Monitoring
- Track runs in Prefect Cloud UI
- View artifact links for generated reports
- Monitor task success rates

## 📈 Example Outputs

### Top Movers Table
| Top Gainers         | Top Losers          |
|---------------------|---------------------|
| PETR4: +2.45%       | BBDC4: -1.87%       |
| VALE3: +1.92%       | ITUB4: -1.23%       |
| MGLU3: +1.15%       | BBAS3: -0.98%       |

### Sample Report
![Price Chart](https://via.placeholder.com/800x400.png?text=Stock+Price+Chart+Example)

## 🔧 Customization

### Modify Tickers List
```python
tickers = [
    "PETR4.SA", 
    "VALE3.SA",
    # Add/remove tickers as needed
]
```

### Adjust Analysis Period
```python
start_date = end_date - timedelta(days=30)  # Change to 30-day window
```

### Add New Indicators
```python
df['RSI'] = ta.rsi(df['Close'], window=14)
```

## 🛠 Troubleshooting

**Common Issues**:
1. **Authentication Errors**:
   - Verify Prefect API key
   - Check Google Drive permissions

2. **Data Download Failures**:
   - Verify ticker symbols
   - Check Yahoo Finance API status

3. **Dependency Conflicts**:
```bash
!pip install --force-reinstall yfinance
```

## 🤝 Contributing
```plaintext
1. Fork the repository
2. Create feature branch (git checkout -b feature/improvement)
3. Commit changes (git commit -am 'Add new feature')
4. Push to branch (git push origin feature/improvement)
5. Create Pull Request
```

## 📄 License
MIT License - See [LICENSE](https://opensource.org/licenses/MIT) for details

---

**Powered by**:  
![Prefect](https://prefect.io/img/logos/prefect-logo-mark.svg)  
![Yahoo Finance](https://logos-world.net/wp-content/uploads/2021/02/Yahoo-Finance-Logo.png)
