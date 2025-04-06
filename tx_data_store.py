from backend.models import TransactionData
from datetime import datetime

from typing import List
from threading import Lock

class TxDataStore:
    def __init__(self):
        self.transactions: List[dict] = []
        self.lock = Lock()

    def add_transaction(self, tx_data: dict):
        with self.lock:
            self.transactions.insert(0, tx_data)
            if len(self.transactions) > 20:  
                self.transactions.pop()

    def get_transactions(self) -> List[dict]:
        with self.lock:
            return self.transactions.copy()

tx_store = TxDataStore()

