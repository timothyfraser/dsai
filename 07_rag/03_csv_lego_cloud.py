# 03_csv_lego_cloud.py
# Example RAG workflow using a LEGO inventory CSV + Ollama Cloud
# Based on 03_csv.py
# Tim Fraser
#
# This script demonstrates a simple RAG flow:
# 1) Search a local CSV inventory
# 2) Pass matching rows as JSON to an LLM
# 3) Ask the model to produce a clear business-style answer

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import os        # for file path operations
import json      # for JSON formatting
import pandas as pd  # for reading CSV files and filtering data
import requests  # for Ollama Cloud API requests
from dotenv import load_dotenv  # for loading OLLAMA_API_KEY from .env

## 0.2 Working Directory #################################

# Set working directory to this script's folder so relative paths work consistently.
script_dir = os.path.dirname(os.path.abspath(__name__))
os.chdir(script_dir)

# Load environment variables from repo .env (if present).
load_dotenv()

## 0.3 Configuration #################################

MODEL = "gpt-oss:20b-cloud"  # Ollama Cloud model
PORT = 11434
OLLAMA_HOST = f"http://localhost:{PORT}"  # kept for parity with local scripts
DOCUMENT = "data/lego_inventory.csv"  # path to the inventory CSV
OLLAMA_CLOUD_URL = "https://ollama.com/api/chat"
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")

if not OLLAMA_API_KEY:
    raise ValueError("OLLAMA_API_KEY not found in .env file. Please set it before running.")

# 1. SEARCH FUNCTION ###################################

def search_inventory(query, document):
    """
    Search LEGO inventory rows using a keyword across common fields.

    Parameters:
    -----------
    query : str
        Search term supplied by the user.
    document : str
        Path to the CSV file.

    Returns:
    --------
    str
        JSON string of matching rows (list of dicts).
    """

    df = pd.read_csv(document)

    # Search multiple text-friendly columns for better retrieval coverage.
    mask = (
        df["set_name"].astype(str).str.contains(query, case=False, na=False)
        | df["theme"].astype(str).str.contains(query, case=False, na=False)
        | df["supplier"].astype(str).str.contains(query, case=False, na=False)
        | df["warehouse_location"].astype(str).str.contains(query, case=False, na=False)
    )

    filtered_df = df[mask]
    result_dict = filtered_df.to_dict(orient="records")
    result_json = json.dumps(result_dict, indent=2)
    return result_json

# 2. OLLAMA CLOUD CHAT ###################################

def chat_cloud(role, task, model=MODEL):
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": role},
            {"role": "user", "content": task}
        ],
        "stream": False
    }

    response = requests.post(
        OLLAMA_CLOUD_URL,
        headers={
            "Authorization": f"Bearer {OLLAMA_API_KEY}",
            "Content-Type": "application/json"
        },
        json=body,
        timeout=60
    )
    response.raise_for_status()
    data = response.json()
    return data["message"]["content"]

# 3. RAG QUERY WORKFLOW ###################################

# Example user query for retrieval:
user_query = "Star Wars"

print("Testing search function...")
retrieved_json = search_inventory(user_query, DOCUMENT)
print("Search result preview:")
print(retrieved_json[:300] + "..." if len(retrieved_json) > 300 else retrieved_json)
print()

# System prompt (role): instructs how to process inventory JSON context.
role = (
    "You are an inventory analyst for a LEGO retailer. "
    "You will receive: (1) a user question, and (2) JSON rows from a CSV inventory search. "
    "Use only the provided JSON rows as evidence. "
    "If there are no rows, clearly say no matching inventory was found. "
    "Return markdown with: "
    "1) a short title, "
    "2) 3-5 bullet insights (stock risk, high-value sets, reorder candidates), and "
    "3) a compact table with columns: set_name, theme, stock_quantity, reorder_level, price_usd."
)

task = f"User question: {user_query}\n\nInventory JSON:\n{retrieved_json}"
answer = chat_cloud(role=role, task=task, model=MODEL)

print("🧱 LEGO Inventory RAG Result:")
print(answer)

