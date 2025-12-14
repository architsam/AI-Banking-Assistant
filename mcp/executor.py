"""
Executor Module (MCP Step 3).
Executes planned steps by calling appropriate tool functions.
"""
import logging
from typing import Dict, Any, List
from tools.banking_operations import BankingOperations

logger = logging.getLogger(__name__)


class Executor:
    """Executes planned steps using tool functions."""
    
    def __init__(self, db):
        """Initialize executor with database connection."""
        self.db = db
        self.operations = BankingOperations(db)
    
    def execute_plan(self, plan: Dict) -> Dict[str, Any]:
        """
        Execute all steps in the plan.
        
        Returns:
            Combined results from all steps
        """
        steps = plan.get("steps", [])
        all_results = {}
        
        for step in steps:
            step_id = step.get("step_id")
            tool_name = step.get("tool")
            parameters = step.get("parameters", {})
            
            if not tool_name:
                logger.error(f"Step {step_id} is missing tool name. Step data: {step}")
                all_results[f"step_{step_id}"] = {
                    "success": False,
                    "error": "Tool name is missing from plan step"
                }
                continue
            
            logger.info(f"Executing step {step_id}: {tool_name}")
            
            # Execute tool function
            result = self._execute_tool(tool_name, parameters)
            all_results[f"step_{step_id}"] = result
            all_results.update(result)  # Merge main results
        
        return all_results
    
    def _execute_tool(self, tool_name: str, parameters: Dict) -> Dict[str, Any]:
        """
        Execute a specific tool function.
        
        Maps tool names to actual function calls.
        """
        # Tool name mapping to handle variations
        tool_mapping = {
            "get_balance": "get_balance",
            "account_balance_check": "get_balance",
            "check_balance": "get_balance",
            "balance_check": "get_balance",
            "transfer_money": "transfer_money",
            "transfer_funds": "transfer_money",
            "transfer": "transfer_money",
            "get_transactions": "get_transactions",
            "fetch_transactions": "get_transactions",
            "recent_transactions": "get_transactions",
            "simulate_transaction": "simulate_transaction",
            "what_if": "simulate_transaction",
            "affordability_check": "simulate_transaction",
            "get_insights": "get_insights",
            "spending_insights": "get_insights",
            "insights": "get_insights"
        }
        
        # Normalize tool name (handle None case)
        if tool_name is None:
            return {"success": False, "error": "Tool name is missing"}
        
        normalized_tool = tool_mapping.get(tool_name.lower() if isinstance(tool_name, str) else str(tool_name).lower(), tool_name)
        
        try:
            if normalized_tool == "get_balance":
                account_id = parameters.get("account_id")
                if not account_id:
                    return {"success": False, "error": "account_id required"}
                balance, error = self.operations.get_balance(account_id)
                if error:
                    return {
                        "success": False,
                        "error": error,
                        "account_id": account_id
                    }
                return {
                    "success": True,
                    "balance": balance,
                    "account_id": account_id
                }
            
            elif normalized_tool == "transfer_money":
                from_account = parameters.get("account_id") or parameters.get("from_account")
                to_account = parameters.get("recipient_account") or parameters.get("to_account")
                amount = parameters.get("amount")
                
                if not all([from_account, to_account, amount]):
                    return {"success": False, "error": "Missing required parameters"}
                
                success, message = self.operations.transfer_money(
                    from_account, to_account, amount
                )
                
                if success:
                    new_balance, _ = self.operations.get_balance(from_account)
                    return {
                        "success": True,
                        "amount": amount,
                        "from_account": from_account,
                        "to_account": to_account,
                        "new_balance": new_balance,
                        "message": message
                    }
                else:
                    return {"success": False, "error": message}
            
            elif normalized_tool == "get_transactions":
                account_id = parameters.get("account_id")
                limit = parameters.get("limit", 10)
                
                if not account_id:
                    # Try to get first available account as fallback
                    account_id = self._get_default_account_id()
                    if not account_id:
                        return {"success": False, "error": "account_id required. Please specify an account (e.g., 'account 1')"}
                
                transactions = self.operations.get_recent_transactions(account_id, limit)
                return {
                    "success": True,
                    "transactions": transactions,
                    "account_id": account_id
                }
            
            elif normalized_tool == "simulate_transaction":
                account_id = parameters.get("account_id")
                amount = parameters.get("amount")
                
                if not all([account_id, amount]):
                    return {"success": False, "error": "Missing required parameters"}
                
                result = self.operations.simulate_transaction(account_id, amount)
                return {
                    "success": True,
                    **result
                }
            
            elif normalized_tool == "get_insights":
                account_id = parameters.get("account_id")
                time_period = parameters.get("time_period", 30)
                
                if not account_id:
                    # Try to get first available account as fallback
                    account_id = self._get_default_account_id()
                    if not account_id:
                        return {"success": False, "error": "account_id required. Please specify an account (e.g., 'account 7')"}
                
                # Parse time_period - extract number from string like "10 days" or just use number
                days = self._parse_time_period(time_period)
                
                insights = self.operations.get_insights(account_id, days)
                return {
                    "success": True,
                    "summary": insights,
                    "account_id": account_id
                }
            
            else:
                return {"success": False, "error": f"Unknown tool: {tool_name} (normalized: {normalized_tool})"}
                
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {"success": False, "error": str(e)}
    
    def _parse_time_period(self, time_period) -> int:
        """Parse time period string to extract number of days."""
        import re
        
        if isinstance(time_period, (int, float)):
            return int(time_period)
        
        if isinstance(time_period, str):
            # Extract number from string like "10 days", "30", "7 days", etc.
            match = re.search(r'(\d+)', str(time_period))
            if match:
                return int(match.group(1))
        
        # Default to 30 days if parsing fails
        logger.warning(f"Could not parse time_period: {time_period}, defaulting to 30 days")
        return 30
    
    def _get_default_account_id(self):
        """Get the first available account ID as default."""
        try:
            # Query database for first account
            conn = self.db._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM accounts LIMIT 1")
            result = cursor.fetchone()
            conn.close()
            if result:
                return result['id'] if isinstance(result, dict) else result[0]
        except Exception as e:
            logger.error(f"Error getting default account: {e}")
        return None

