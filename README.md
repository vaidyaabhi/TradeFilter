# 🛡️ TradeFilter: Hybrid Algo-Discretionary Terminal

**TradeFilter** is a professional-grade trading system designed to bridge the gap between cloud-based scanning and manual visual confirmation. It automates the "grunt work" of sorting and ranking market alerts, allowing you to focus only on the high-probability setups.

---

## 🏗️ Architecture & Workflow

The system uses a **Decoupled Local Architecture** to ensure speed, security, and reliability.

1.  **Ingestion:** Real-time stock alerts are pushed from **Chartink** via **ngrok** tunnels to a local **FastAPI** listener.
2.  **Processing (The Brain):** A ranking engine fetches live data (Volume, Price) via the **Fyers API** and assigns a "Quality Score" to each stock.
3.  **Unified UI:** A **Streamlit** dashboard displays the ranked candidates with an embedded **TradingView** chart for manual approval.
4.  **Execution (Prosimumlator):** Once a trade is confirmed by the user, the engine handles position sizing, entry, and live SL/TP monitoring.



---

## 🛠️ Tech Stack

* **Backend:** FastAPI (High-performance Webhook Listener)
* **Frontend:** Streamlit (Real-time Dashboard)
* **Database:** SQLite with SQLAlchemy (Shared Local State)
* **Tunneling:** ngrok (Cloud-to-Local Bridge)
* **API:** Fyers API v3 (Market Data & Execution)

---

## 🧑‍💻 Setup for Collaborators

To ensure no "Local Machine Dependency" issues, follow these steps:

### 1. Clone the Repository
```bash
git clone [https://github.com/vaidyaabhi/TradeFilter.git](https://github.com/vaidyaabhi/TradeFilter.git)
cd TradeFilter
