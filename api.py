from flask import Flask, jsonify, request
from flask_cors import CORS
import time
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

from monitor import generate_ai_report_with_ollama
import threading
import json
import os

app = Flask(__name__)
CORS(app)  # Enable cross-origin requests

# In-memory storage for our demo
transactions = []
stats = {
    "protected_transactions": 0,
    "high_risk_detected": 0,
    "medium_risk": 0,
    "risk_distribution": [
        {"name": "Low Risk", "value": 0, "color": "#10B981"},
        {"name": "Medium Risk", "value": 0, "color": "#FBBF24"},
        {"name": "High Risk", "value": 0, "color": "#EF4444"},
        {"name": "Critical Risk", "value": 0, "color": "#991B1B"},
    ],
    "network_stats": {
        "current_block": 0,
        "gas_price": 0,
        "monitoring_status": "Starting...",
        "llama_ai_status": "Initializing...",
        "telegram_alerts": "Waiting..."
    }
}
analysis_results = {}

# Routes for our React frontend
@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    risk_filter = request.args.get('risk', 'all')
    if risk_filter == 'all':
        return jsonify(transactions)
    else:
        filtered = [tx for tx in transactions if tx.get('riskLevel') == risk_filter]
        return jsonify(filtered)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    return jsonify(stats)

@app.route('/api/analysis', methods=['GET'])
def get_analysis():
    return jsonify(analysis_results)

@app.route('/api/transaction_activity', methods=['GET'])
def get_transaction_activity():
    # Group transactions by hour for the chart
    hours = ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00", "24:00"]
    data = [
        {"time": hour, "transactions": len(transactions) // 7 + i, "value": round(sum([float(tx.get('value', '0').replace('ETH', '')) for tx in transactions]) / 7 + i * 0.5, 1)}
        for i, hour in enumerate(hours)
    ]
    return jsonify(data)

# Endpoint to receive transaction data from monitor.py
@app.route('/api/update_transaction', methods=['POST'])
def update_transaction():
    tx_data = request.json
    
    # Update stats based on risk level
    risk_level = tx_data.get('riskLevel', 'low').lower()
    
    # Increment appropriate counters
    if risk_level == 'high' or risk_level == 'critical':
        stats['high_risk_detected'] += 1
    elif risk_level == 'medium':
        stats['medium_risk'] += 1
    stats['protected_transactions'] += 1
    
    # Update risk distribution
    for item in stats['risk_distribution']:
        if item['name'].lower().startswith(risk_level):
            item['value'] += 1
    
    # Update network stats
    if 'blockNumber' in tx_data:
        stats['network_stats']['current_block'] = int(tx_data['blockNumber'])
    if 'gasPrice' in tx_data:
        stats['network_stats']['gas_price'] = float(tx_data['gasPrice'])
    
    stats['network_stats']['monitoring_status'] = "Active"
    stats['network_stats']['llama_ai_status'] = "Online"
    stats['network_stats']['telegram_alerts'] = "Enabled"
    
    # Add transaction to the list
    transactions.insert(0, tx_data)  # Add to beginning of list
    if len(transactions) > 100:  # Limit to 100 transactions
        transactions.pop()
    
    # Update analysis results if AI report is available
    if 'aiReport' in tx_data:
        analysis_results['latest_report'] = tx_data['aiReport']
        analysis_results['latest_transaction'] = tx_data['hash']
        analysis_results['risk_score'] = tx_data.get('riskScore', 0)
    
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
