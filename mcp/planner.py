"""
Planner Module (MCP Step 2).
Generates step-by-step execution plans based on intent.
"""
import json
import logging
from groq import Groq
import config

logger = logging.getLogger(__name__)


class Planner:
    """Generates execution plans from parsed intent."""
    
    def __init__(self):
        self.client = Groq(api_key=config.GROQ_API_KEY)
        self.model = config.GROQ_MODEL
    
    def plan(self, intent: str, entities: dict) -> dict:
        """
        Generate execution plan from intent and entities.
        
        Returns:
            {
                "steps": [{"step_id": int, "action": str, "tool": str, "parameters": dict}],
                "requires_validation": bool
            }
        """
        models_to_try = [self.model] + config.GROQ_FALLBACK_MODELS
        
        for model in models_to_try:
            try:
                prompt = config.PLANNING_PROMPT.format(
                    intent=intent,
                    entities=json.dumps(entities)
                )
                
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a precise planner. Always return valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                
                plan = json.loads(response.choices[0].message.content)
                
                # Validate and fix plan structure
                plan = self._validate_and_fix_plan(plan, intent, entities)
                
                logger.info(f"Generated plan with {len(plan.get('steps', []))} steps (using model: {model})")
                
                # Update model if fallback was used
                if model != self.model:
                    self.model = model
                    logger.info(f"Switched to model: {model}")
                
                return plan
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse plan as JSON: {e}")
                continue
            except Exception as e:
                error_msg = str(e)
                # If model is decommissioned, try next model
                if "decommissioned" in error_msg.lower() or "model" in error_msg.lower():
                    logger.warning(f"Model {model} failed: {error_msg}. Trying next model...")
                    continue
                logger.error(f"Planning failed with model {model}: {e}")
                continue
        
        # All models failed, use fallback plan
        logger.warning("All models failed for planning, using fallback plan")
        return self._fallback_plan(intent, entities)
    
    def _validate_and_fix_plan(self, plan: dict, intent: str, entities: dict) -> dict:
        """Validate plan structure and fix missing tool names."""
        intent_to_tool = {
            "check_balance": "get_balance",
            "transfer": "transfer_money",
            "transactions": "get_transactions",
            "what_if": "simulate_transaction",
            "insights": "get_insights"
        }
        
        steps = plan.get("steps", [])
        if not steps:
            logger.warning("Plan has no steps, using fallback")
            return self._fallback_plan(intent, entities)
        
        # Fix any steps missing tool names
        for step in steps:
            if not step.get("tool"):
                # Try to infer from action or intent
                action = step.get("action", intent)
                tool = intent_to_tool.get(action, intent_to_tool.get(intent, "get_balance"))
                step["tool"] = tool
                logger.warning(f"Fixed missing tool name in step {step.get('step_id')}, set to: {tool}")
        
        return plan
    
    def _fallback_plan(self, intent: str, entities: dict) -> dict:
        """Generate a simple fallback plan if LLM fails."""
        intent_to_tool = {
            "check_balance": "get_balance",
            "transfer": "transfer_money",
            "transactions": "get_transactions",
            "what_if": "simulate_transaction",
            "insights": "get_insights"
        }
        
        tool = intent_to_tool.get(intent, "unknown")
        
        return {
            "steps": [
                {
                    "step_id": 1,
                    "action": intent,
                    "tool": tool,
                    "parameters": entities,
                    "description": f"Execute {intent}"
                }
            ],
            "requires_validation": intent in ["transfer", "what_if"]
        }

