"""
Responder Module (MCP Step 5).
Formats execution results into natural language responses.
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class Responder:
    """Formats results into user-friendly responses."""
    
    def respond(self, execution_results: Dict[str, Any], intent: str) -> str:
        """
        Generate natural language response from execution results.
        
        Args:
            execution_results: Combined results from all executed steps
            intent: Original user intent
        
        Returns:
            Formatted response string
        """
        if intent == "check_balance":
            return self._format_balance_response(execution_results)
        elif intent == "transfer":
            return self._format_transfer_response(execution_results)
        elif intent == "transactions":
            return self._format_transactions_response(execution_results)
        elif intent == "what_if":
            return self._format_simulation_response(execution_results)
        elif intent == "insights":
            return self._format_insights_response(execution_results)
        else:
            return self._format_generic_response(execution_results)
    
    def _format_balance_response(self, results: Dict) -> str:
        """Format balance check response."""
        balance = results.get("balance")
        account_id = results.get("account_id", "N/A")
        error = results.get("error")
        
        if error:
            if "not found" in error.lower():
                return f"❌ Account {account_id} not found. Please run 'setup' to create demo accounts first."
            return f"❌ {error}"
        
        if balance is not None:
            return f"Your account {account_id} balance is ${balance:.2f}"
        return "Unable to retrieve balance. Please check the account ID or run 'setup' to create demo accounts."
    
    def _format_transfer_response(self, results: Dict) -> str:
        """Format transfer response."""
        if results.get("success"):
            amount = results.get("amount", 0)
            from_acc = results.get("from_account")
            to_acc = results.get("to_account")
            new_balance = results.get("new_balance")
            
            response = f"✅ Transfer successful!\n"
            response += f"Transferred ${amount:.2f} from account {from_acc} to account {to_acc}.\n"
            if new_balance is not None:
                response += f"Your new balance is ${new_balance:.2f}"
            return response
        else:
            return f"❌ Transfer failed: {results.get('error', 'Unknown error')}"
    
    def _format_transactions_response(self, results: Dict) -> str:
        """Format transactions list response."""
        transactions = results.get("transactions", [])
        
        if not transactions:
            return "No recent transactions found."
        
        response = f"📋 Recent transactions ({len(transactions)}):\n\n"
        for txn in transactions:
            txn_type = txn.get("type", "").upper()
            amount = txn.get("amount", 0)
            timestamp = txn.get("timestamp", "")[:10]  # Just date
            response += f"  {txn_type}: ${amount:.2f} on {timestamp}\n"
        
        return response
    
    def _format_simulation_response(self, results: Dict) -> str:
        """Format what-if simulation response."""
        affordable = results.get("affordable", False)
        current_balance = results.get("current_balance", 0)
        amount = results.get("amount", 0)
        projected_balance = results.get("projected_balance", 0)
        
        response = f"💡 Affordability Check:\n"
        response += f"Current balance: ${current_balance:.2f}\n"
        response += f"Transaction amount: ${amount:.2f}\n"
        response += f"Projected balance: ${projected_balance:.2f}\n\n"
        
        if affordable:
            response += "✅ This transaction is affordable!"
        else:
            response += "❌ This transaction would result in insufficient funds."
        
        return response
    
    def _format_insights_response(self, results: Dict) -> str:
        """Format insights response."""
        summary = results.get("summary", {})
        
        if not summary:
            return "No insights available for this account."
        
        response = "📊 Spending Insights (Last 30 days):\n\n"
        
        total_debits = summary.get("debit", {}).get("total", 0) or 0
        total_credits = summary.get("credit", {}).get("total", 0) or 0
        
        response += f"Total Spent: ${abs(total_debits):.2f}\n"
        response += f"Total Received: ${total_credits:.2f}\n"
        response += f"Net Change: ${total_credits + total_debits:.2f}\n"
        
        if total_debits > 0:
            avg_spending = abs(total_debits) / 30
            response += f"\n💡 Average daily spending: ${avg_spending:.2f}"
        
        return response
    
    def _format_generic_response(self, results: Dict) -> str:
        """Format generic response."""
        if results.get("success"):
            return "✅ Operation completed successfully."
        return f"❌ Operation failed: {results.get('error', 'Unknown error')}"

