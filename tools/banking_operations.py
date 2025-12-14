"""
Banking Operations Tool Functions.
Contains all executable banking operations.
"""
import logging
from typing import Dict, List, Tuple, Optional
from database import BankingDatabase

logger = logging.getLogger(__name__)


class BankingOperations:
    """Collection of banking operation tools."""
    
    def __init__(self, db: BankingDatabase):
        """Initialize with database connection."""
        self.db = db
    
    def get_balance(self, account_id: int) -> Tuple[Optional[float], Optional[str]]:
        """
        Get account balance.
        Returns: (balance, error_message)
        """
        balance = self.db.get_account_balance(account_id)
        if balance is None:
            logger.warning(f"Account {account_id} not found")
            return None, f"Account {account_id} not found"
        return balance, None
    
    def transfer_money(
        self, 
        from_account_id: int, 
        to_account_id: int, 
        amount: float
    ) -> Tuple[bool, str]:
        """
        Transfer money between accounts.
        
        Returns:
            (success: bool, message: str)
        """
        # Validate amount
        if amount <= 0:
            return False, "Amount must be positive"
        
        if amount > 1000000:  # Safety limit
            return False, "Amount exceeds maximum transfer limit"
        
        return self.db.transfer_money(from_account_id, to_account_id, amount)
    
    def get_recent_transactions(
        self, 
        account_id: int, 
        limit: int = 10
    ) -> List[Dict]:
        """Get recent transactions for an account."""
        return self.db.get_recent_transactions(account_id, limit)
    
    def simulate_transaction(self, account_id: int, amount: float) -> Dict:
        """
        Simulate a transaction to check affordability.
        
        Returns:
            {
                "affordable": bool,
                "current_balance": float,
                "projected_balance": float,
                "amount": float
            }
        """
        current_balance, error = self.get_balance(account_id)
        if error:
            return {
                "affordable": False,
                "current_balance": 0.0,
                "projected_balance": -amount,
                "amount": amount,
                "error": error
            }
        projected_balance = current_balance - amount
        
        return {
            "affordable": projected_balance >= 0,
            "current_balance": current_balance,
            "projected_balance": projected_balance,
            "amount": amount
        }
    
    def get_insights(self, account_id: int, days: int = 30) -> Dict:
        """
        Get spending insights for an account.
        
        Returns:
            Transaction summary with totals and counts
        """
        return self.db.get_transaction_summary(account_id, days)

