"""
Validator Module (MCP Step 4).
Validates execution results and business constraints.
"""
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class Validator:
    """Validates execution results and constraints."""
    
    def validate(self, step_result: Dict[str, Any], step_plan: Dict) -> tuple[bool, str]:
        """
        Validate step execution result.
        
        Returns:
            (is_valid: bool, message: str)
        """
        action = step_plan.get("action", "")
        
        # Check if execution was successful
        if not step_result.get("success", False):
            return False, step_result.get("error", "Execution failed")
        
        # Action-specific validation
        if action == "transfer":
            return self._validate_transfer(step_result)
        elif action == "what_if":
            return self._validate_simulation(step_result)
        elif action == "check_balance":
            return self._validate_balance(step_result)
        
        # Default: accept if success is True
        return True, "Validation passed"
    
    def _validate_transfer(self, result: Dict) -> tuple[bool, str]:
        """Validate transfer operation."""
        if result.get("success"):
            amount = result.get("amount", 0)
            return True, f"Transfer of ${amount:.2f} validated successfully"
        return False, result.get("error", "Transfer validation failed")
    
    def _validate_simulation(self, result: Dict) -> tuple[bool, str]:
        """Validate simulation result."""
        if result.get("affordable", False):
            return True, "Simulation shows transaction is affordable"
        return False, "Simulation shows transaction is not affordable"
    
    def _validate_balance(self, result: Dict) -> tuple[bool, str]:
        """Validate balance check result."""
        balance = result.get("balance")
        if balance is not None and balance >= 0:
            return True, "Balance check valid"
        return False, "Invalid balance result"

