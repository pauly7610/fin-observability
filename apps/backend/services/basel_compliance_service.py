import logging
from sqlalchemy.orm import Session
from ..models import Transaction
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class BaselComplianceService:
    """
    Calculates Basel III Liquidity Coverage Ratio (LCR) and compliance status.
    """
    def __init__(self, lcr_threshold: float = 1.0):
        self.lcr_threshold = lcr_threshold

    def calculate_lcr(self, db: Session, lookback_days: int = 30) -> dict:
        """
        Calculate the LCR over the last N days.
        LCR = High Quality Liquid Assets (HQLA) / Total Net Cash Outflows over 30 days
        For MVP, assume HQLA = sum of positive balances in meta, outflows = sum of negative amounts.
        """
        since = datetime.utcnow() - timedelta(days=lookback_days)
        transactions = db.query(Transaction).filter(Transaction.timestamp >= since).all()
        hqla = 0.0
        outflows = 0.0
        for tx in transactions:
            meta = tx.meta or {}
            # MVP: treat 'balance' in meta as HQLA if positive
            hqla_val = meta.get('balance', 0.0)
            if hqla_val > 0:
                hqla += hqla_val
            # treat negative transaction amounts as outflows
            if tx.amount < 0:
                outflows += abs(tx.amount)
        lcr = hqla / outflows if outflows > 0 else float('inf')
        compliant = lcr >= self.lcr_threshold
        return {
            'lcr': lcr,
            'hqla': hqla,
            'outflows': outflows,
            'compliant': compliant,
            'threshold': self.lcr_threshold,
            'lookback_days': lookback_days
        }
