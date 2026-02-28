Copy and paste this entire block into your README.md and you’re good to commit!

Markdown
# 🛡️ TradeFilter: Hybrid Algo-Discretionary Terminal

**TradeFilter** is a professional-grade trading system designed to bridge the gap between automated scanning (Chartink) and manual visual confirmation. It automates the sorting of market alerts, allowing the trader to focus only on high-probability setups.

---

## 🏗️ Architecture & Workflow

The system uses a **Decoupled Local Architecture** to ensure speed and reliability between collaborators.

1.  **Ingestion:** Real-time stock alerts are pushed from **Chartink** via **ngrok** to a local **FastAPI** listener.
2.  **Processing:** A ranking engine fetches live data via **Fyers API** and assigns a "Quality Score" to each stock.
3.  **Visualization:** A **Streamlit** dashboard displays ranked candidates with an embedded **TradingView** chart.
4.  **Database:** Data is synced through a local **SQLite** database (`trading.db`), kept private to each user.



---

## 🚀 Getting Started (Mac & Windows)

We have standardized the project on **Python 3.11.x**. Follow these steps to get up and running:

### 1. Clone the Project
Open your terminal or command prompt and run:
```bash
git clone [https://github.com/vaidyaabhi/TradeFilter.git](https://github.com/vaidyaabhi/TradeFilter.git)
cd TradeFilter
2. Run the One-Command Setup
This script automatically detects your OS, creates a venv, installs all libraries, and initializes your database:

Bash
python setup_project.py
3. Activate Your Environment
Once the setup is finished, you MUST activate the virtual environment in every new terminal window:

macOS: source venv/bin/activate

Windows: .\venv\Scripts\activate
