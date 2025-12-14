"""
Database module for SQLite operations.
Handles schema creation, user management, and transaction logging.
"""
import sqlite3
import logging
from datetime import datetime
from typing import Optional, List, Dict, Tuple

logger = logging.getLogger(__name__)


class BankingDatabase:
    """Manages all database operations for the banking system."""
    
    def __init__(self, db_path: str = "banking.db"):
        self.db_path = db_path
        self._init_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Create and return a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    
    def _init_database(self):
        """Initialize database schema if it doesn't exist."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                password TEXT NOT NULL
            )
        """)
        
        # Create accounts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                balance REAL NOT NULL DEFAULT 0.0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Create transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (account_id) REFERENCES accounts(id)
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    def create_user(self, name: str, password: str) -> int:
        """Create a new user and return user_id."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, password) VALUES (?, ?)",
            (name, password)
        )
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        logger.info(f"Created user: {name} (ID: {user_id})")
        return user_id
    
    def create_account(self, user_id: int, initial_balance: float = 0.0) -> int:
        """Create a new account for a user and return account_id."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO accounts (user_id, balance) VALUES (?, ?)",
            (user_id, initial_balance)
        )
        account_id = cursor.lastrowid
        conn.commit()
        conn.close()
        logger.info(f"Created account {account_id} for user {user_id}")
        return account_id
    
    def get_account_balance(self, account_id: int) -> Optional[float]:
        """Get balance for a given account_id."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT balance FROM accounts WHERE id = ?",
            (account_id,)
        )
        result = cursor.fetchone()
        conn.close()
        if result:
            return result['balance']
        return None
    
    def get_user_accounts(self, user_id: int) -> List[Dict]:
        """Get all accounts for a user."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, balance FROM accounts WHERE user_id = ?",
            (user_id,)
        )
        accounts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return accounts
    
    def transfer_money(
        self, 
        from_account_id: int, 
        to_account_id: int, 
        amount: float
    ) -> Tuple[bool, str]:
        """
        Transfer money between accounts.
        Returns (success: bool, message: str)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if both accounts exist
            cursor.execute("SELECT balance FROM accounts WHERE id = ?", (from_account_id,))
            from_account = cursor.fetchone()
            if not from_account:
                return False, f"Source account {from_account_id} not found"
            
            cursor.execute("SELECT balance FROM accounts WHERE id = ?", (to_account_id,))
            to_account = cursor.fetchone()
            if not to_account:
                return False, f"Destination account {to_account_id} not found"
            
            # Check sufficient balance
            if from_account['balance'] < amount:
                return False, f"Insufficient balance. Available: ${from_account['balance']:.2f}"
            
            # Perform transfer
            new_from_balance = from_account['balance'] - amount
            new_to_balance = to_account['balance'] + amount
            
            cursor.execute(
                "UPDATE accounts SET balance = ? WHERE id = ?",
                (new_from_balance, from_account_id)
            )
            cursor.execute(
                "UPDATE accounts SET balance = ? WHERE id = ?",
                (new_to_balance, to_account_id)
            )
            
            # Log transactions
            timestamp = datetime.now().isoformat()
            cursor.execute(
                """INSERT INTO transactions (account_id, type, amount, timestamp)
                   VALUES (?, ?, ?, ?)""",
                (from_account_id, "debit", amount, timestamp)
            )
            cursor.execute(
                """INSERT INTO transactions (account_id, type, amount, timestamp)
                   VALUES (?, ?, ?, ?)""",
                (to_account_id, "credit", amount, timestamp)
            )
            
            conn.commit()
            conn.close()
            logger.info(f"Transfer: ${amount:.2f} from {from_account_id} to {to_account_id}")
            return True, f"Successfully transferred ${amount:.2f}"
            
        except Exception as e:
            conn.rollback()
            conn.close()
            logger.error(f"Transfer failed: {str(e)}")
            return False, f"Transfer failed: {str(e)}"
    
    def get_recent_transactions(
        self, 
        account_id: int, 
        limit: int = 10
    ) -> List[Dict]:
        """Get recent transactions for an account."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, type, amount, timestamp 
               FROM transactions 
               WHERE account_id = ? 
               ORDER BY timestamp DESC 
               LIMIT ?""",
            (account_id, limit)
        )
        transactions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return transactions
    
    def get_transaction_summary(
        self, 
        account_id: int, 
        days: int = 30
    ) -> Dict:
        """Get transaction summary for insights."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Calculate date threshold
        from datetime import datetime, timedelta
        threshold = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute(
            """SELECT type, SUM(amount) as total, COUNT(*) as count
               FROM transactions 
               WHERE account_id = ? AND timestamp >= ?
               GROUP BY type""",
            (account_id, threshold)
        )
        
        summary = {}
        for row in cursor.fetchall():
            summary[row['type']] = {
                'total': row['total'],
                'count': row['count']
            }
        
        conn.close()
        return summary

