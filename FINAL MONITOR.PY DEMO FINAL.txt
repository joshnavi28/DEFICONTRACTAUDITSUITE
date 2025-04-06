import time
import requests
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
import os
import random


load_dotenv()

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
INFURA_URL = os.getenv("INFURA_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


w3 = Web3(Web3.HTTPProvider(INFURA_URL))

if w3.is_connected():
    print(f"✅ Connected to Ethereum (Chain ID: {w3.eth.chain_id})")
else:
    raise ConnectionError("❌ Failed to connect to Ethereum node.")



def generate_ai_report_with_ollama(tx_info):
    prompt = f"""
You are an AI security analyst. Analyze the following Ethereum transaction and generate a markdown-style risk report.

Include:
1. ⚠️ Risk Level and a score out of 100
2. 📝 A brief summary
3. 📊 3-5 bullet points of technical analysis
4. 💡 3-5 bullet points of security recommendations

Transaction Details:
- From: {tx_info['from']}
- To: {tx_info['to']}
- Value: {tx_info['value']} ETH
- Gas Price: {tx_info['gas_price']} Gwei
- Recipient Tx Count: {tx_info['recipient_tx_count']}
- Data Field: {tx_info['data']}
- Block: {tx_info['block']}
"""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama2",
                "prompt": prompt,
                "stream": False
            }
        )
        result = response.json()
        return result.get("response", "").strip()
    except Exception as e:
        return f"❌ AI report generation failed: {e}"



def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"❌ Telegram error: {e}")



def get_live_gas_price():
    try:
        url = f"https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey={ETHERSCAN_API_KEY}"
        response = requests.get(url)
        data = response.json()
        if data["status"] == "1":
            avg_gas = float(data["result"]["ProposeGasPrice"])
            return avg_gas
        else:
            print("⚠️ Etherscan error:", data["result"])
            return 20.0
    except Exception as e:
        print(f"⚠️ Error fetching gas price: {e}")
        return 20.0



def monitor_transactions():
    print("🔍 Monitoring transactions...\n")
    processed_blocks = set()

    while True:
        try:
            latest_block = w3.eth.block_number
            if latest_block not in processed_blocks:
                print(f"\n\n🔨 New Block: {latest_block}")
                avg_gas_price = get_live_gas_price()

                block = w3.eth.get_block(latest_block, full_transactions=True)

                for tx in block.transactions:
                    if tx.to:
                        time.sleep(2)  # ⏳ Simulate AI thinking delay

                        tx_hash = tx.hash.hex()
                        to_addr = tx.to
                        from_addr = tx['from']
                        gas_price = tx.gasPrice / 1e9
                        value = tx.value / 1e18
                        block_num = tx.blockNumber
                        status = "Success"
                        data_field = tx.input

                      
                        try:
                            recipient_tx_count = w3.eth.get_transaction_count(to_addr)
                        except:
                            recipient_tx_count = "N/A"

                        
                        tx_info = {
                            "from": from_addr,
                            "to": to_addr,
                            "value": f"{value:.6f}",
                            "gas_price": f"{gas_price:.2f}",
                            "recipient_tx_count": recipient_tx_count,
                            "data": data_field,
                            "block": block_num
                        }

                        
                        ai_report = generate_ai_report_with_ollama(tx_info)

                        
                        alert_msg = f"""📩 *New Transaction Detected*
🔗 *Hash:* {tx_hash}
📤 *From:* {from_addr}
📥 *To:* {to_addr}
💰 *Value:* {value:.6f} ETH
⛽ *Gas Price:* {gas_price:.2f} Gwei
📊 *Block:* {block_num}
✅ *Status:* {status}

{ai_report}
"""

                        print(alert_msg)

                        
                        if any(level in ai_report for level in ["Medium", "High", "Critical"]):
                            send_telegram_alert(alert_msg)
                            print("📡 Telegram Alert Sent! ✅")

                        time.sleep(random.uniform(5, 7))

                processed_blocks.add(latest_block)

            time.sleep(5)

        except Exception as e:
            print(f"⚠️ Network error: {e}")
            time.sleep(5)



if __name__ == "__main__":
    monitor_transactions()