import requests
import json
import os
import datetime
from typing import Dict, Any


TRANSACTION_PATTERNS = {
    
    "withdraw()": {
        "risk": "high",
        "message": "🚨 CRITICAL: Withdraw function called - check for reentrancy protection"
    },
    "transfer(": {
        "risk": "medium",
        "message": "⚠️ WARNING: Transfer function called - verify recipient"
    },
    
    "0x3ccfd60b": {  
        "risk": "high",
        "message": "🚨 CRITICAL: Withdraw function signature detected"
    },
    "0xa9059cbb": {  
        "risk": "medium",
        "message": "⚠️ WARNING: ERC20 transfer detected"
    },
    "0x00000000": {
        "risk": "high",
        "message": "🚨 CRITICAL: Zero address reference detected"
    }
}

def analyze_with_ollama(tx_data: Dict[str, Any], model: str = "codellama:7b") -> str:
    """
    Enhanced transaction analyzer with hybrid approach
    """
    
    quick_result = quick_transaction_analysis(tx_data)
    if quick_result["risk"] == "high":
        return quick_result["message"]
    
    
    try:
        prompt = f"""Analyze this blockchain transaction for security risks:
        
Transaction Hash: {tx_data.get('tx_hash', 'unknown')}
From: {tx_data.get('from_address', 'unknown')}
Value: {tx_data.get('value', 0)} ETH
Function: {tx_data.get('decoded_function', 'unknown')}
Input Data: {tx_data.get('input_data', '')}

Potential risks to check:
1. Reentrancy attempts
2. Unauthorized access
3. Unexpected value transfers
4. Suspicious input patterns
5. Known attack signatures

Provide:
- Risk level (High/Medium/Low)
- Specific concerns
- Recommended actions"""
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2}
            },
            timeout=10
        )
        
        ai_response = response.json().get("response", "")
        return f"📊 AI Analysis:\n{ai_response}" if ai_response else quick_result["message"]
    
    except Exception as e:
        print(f"⚠️ Ollama analysis failed: {str(e)}")
        return quick_result["message"]

def quick_transaction_analysis(tx_data: Dict[str, Any]) -> Dict[str, str]:
    """Instant transaction pattern matching"""
    input_data = tx_data.get('input_data', '').lower()
    func_name = tx_data.get('decoded_function', '').lower()
    
    for pattern, info in TRANSACTION_PATTERNS.items():
        pattern_lower = pattern.lower()
        if pattern_lower in input_data or pattern_lower in func_name:
            return info
    
    return {
        "risk": "low",
        "message": "✅ No immediate risks detected via pattern matching"
    }

def save_transaction_report(tx_hash: str, analysis: str):
    """Save transaction analysis results"""
    os.makedirs("tx_reports", exist_ok=True)
    filename = f"tx_reports/{tx_hash}_analysis.json"
    with open(filename, "w") as f:
        json.dump({
            "tx_hash": tx_hash,
            "timestamp": datetime.datetime.now().isoformat(),
            "analysis": analysis
        }, f, indent=2)
    return filename

if __name__ == "__main__":
    
    test_tx = {
        'tx_hash': '0x123...',
        'decoded_function': 'withdraw()',
        'input_data': '0x3ccfd60b000000...',
        'value': '1.5',
        'from_address': '0xabc...'
    }
    
    print("🔍 Testing transaction analysis...")
    result = analyze_with_ollama(test_tx)
    print(result)