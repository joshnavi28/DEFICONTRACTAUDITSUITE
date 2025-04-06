import streamlit as st
import json
import os
import time
from datetime import datetime


st.set_page_config(page_title="🧠 Ethereum AI Risk Dashboard", layout="wide", initial_sidebar_state="expanded")


st.markdown("<h1 style='color:#00ffcc;'>🧠 Live Ethereum Transaction Monitoring (AI Risk Analysis)</h1>", unsafe_allow_html=True)


refresh_interval = st.selectbox("⏱️ Refresh every (seconds):", [2, 5, 10, 20], index=0)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
tx_store_path = os.path.join(BASE_DIR, "scripts", "tx_data_store.json")


def load_transactions():
    try:
        with open(tx_store_path, "r") as f:
            data = json.load(f)
            return data.get("transactions", [])
    except Exception as e:
        st.warning(f"⚠️ Could not load transaction data: {e}")
        return []


placeholder = st.empty()

while True:
    with placeholder.container():
        transactions = load_transactions()

        if not transactions:
            st.info("🕵️ No transactions detected yet...")
        else:
            for tx in reversed(transactions[-20:]):  
                risk = tx.get("risk_level", "Unknown").capitalize()
                color = {"Low": "#00ff88", "Medium": "#ffaa00", "High": "#ff4444"}.get(risk, "#cccccc")

                st.markdown(f"""
                <div style="padding:15px; margin-bottom:10px; border:1px solid {color}; border-radius:8px; background-color:#111111;">
                    <h4 style="color:{color}; margin:0;">🔹 Transaction Hash: {tx.get('hash', 'N/A')}</h4>
                    <p style="margin:2px 0; color:#cccccc;">From: {tx.get('from')}</p>
                    <p style="margin:2px 0; color:#cccccc;">To: {tx.get('to')}</p>
                    <p style="margin:2px 0; color:#cccccc;">Value: {tx.get('value')} ETH</p>
                    <p style="margin:2px 0; color:#cccccc;">Gas Price: {tx.get('gas_price')} Gwei</p>
                    <p style="margin:2px 0; color:{color};">🧠 Risk Level: <strong>{risk}</strong></p>
                    <p style="margin:2px 0; color:#999999;"><i>{tx.get('ai_summary', 'AI analysis not available.')}</i></p>
                    <a style="color:#0099ff;" href="https://etherscan.io/tx/{tx.get('hash')}" target="_blank">🔗 View on Etherscan</a>
                </div>
                """, unsafe_allow_html=True)

    time.sleep(refresh_interval)
