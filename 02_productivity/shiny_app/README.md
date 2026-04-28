# 📌 READ

## FDA Adverse Event Reporter (Shiny App)

🕒 *Estimated Time: 5 minutes to run*

---

This app queries the **openFDA Drug Event API** (FAERS) and displays adverse event reports in a table. You set query parameters in the sidebar, click **Fetch data**, and view a summary plus a filterable results grid. Optional: download results as CSV, clear results, or use an API key for higher rate limits.

---

## 📋 Overview

- **Purpose**: Fetch and display U.S. FDA drug adverse event reports (FAERS) in a Shiny for Python web app.
- **Data source**: [**openFDA Drug Event API**](https://open.fda.gov/apis/drug/event/): adverse event and medication error reports submitted to FDA. **No API key required** for basic use; key recommended for higher rate limits.
- **Features**: Sidebar controls (record limit, date range), loading state, summary stats, filterable data table, Download CSV, and Clear results.

---

### 🖥️ Screenshots

The app in the browser: sidebar with query parameters and Fetch data, main area with header, summary stats, and results table.

![App in browser](https://github.com/williammanno/dsai/raw/main/02_productivity/shiny_app/IMG_7982.png)

---

## 🔧 Installation

From the repo root or from this folder:

```bash
cd 02_productivity/shiny_app
pip install -r requirements.txt
```

**Dependencies** (in [`requirements.txt`](requirements.txt)): `shiny`, `pandas`, `requests`, `python-dotenv`.

---

## ▶️ How to Run

```bash
shiny run app.py
```

The terminal will show something like `Uvicorn running on http://127.0.0.1:8000`. **Open that URL in your browser** — the app does not open a window automatically.

---

## 🔑 API Requirements

- **Endpoint**: `https://api.fda.gov/drug/event.json` (GET).
- **API key**: Optional. Without a key, rate limits are lower; with a key, you get higher limits.
  - Get a key: [**openFDA API Key**](https://open.fda.gov/apis/authentication/). **Register for API key.**
  - Create a file named `FDA.env` in this folder, in `02_productivity/`, or in the repo root:

  ```
  FDA_API_KEY=your_openfda_api_key_here
  ```

  The app looks for `FDA.env` or `.env` in those locations and loads `FDA_API_KEY` automatically.

---

## 📖 Usage

- **Number of records**: 1–1000 (default 50). Controls how many rows the API returns.
- **Date from / Date to**: YYYYMMDD (e.g. `20230101`, `20241231`). Restricts reports by FDA receive date. Leave both set for a range; empty = no date filter.
- **Fetch data**: Runs the query. A loading state appears, then the summary and table update. Errors show in the summary area.
- **Clear results**: Resets the app to the initial state (no table, no summary).
- **Download CSV**: After a successful fetch, use this to download the current table as `fda_adverse_events.csv`.

---

## 📁 Files

- [`app.py`](app.py) — Shiny UI and server logic.
- [`api_client.py`](api_client.py) — FDA API client and helpers (`get_fda_events`, `record_to_row`).
- [`requirements.txt`](requirements.txt) — Python dependencies.

---

![](../../docs/images/icons.png)

---

← 🏠 [Back to Top](#READ)
