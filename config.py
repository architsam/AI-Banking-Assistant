"""
Configuration file for the Banking Agent.
Contains API keys, database settings, and LLM configuration.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Groq API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"  # Primary model
# Fallback models (tried in order if primary fails)
GROQ_FALLBACK_MODELS = [
    "llama-3.1-8b-instant",  # Fast alternative
    "mixtral-8x7b-32768",    # Alternative model
    "gemma2-9b-it"           # Another alternative
]

# Database Configuration
DATABASE_PATH = "banking.db"

# LLM Prompt Templates
INTENT_PARSING_PROMPT = """You are an intent parser for a banking assistant. 
Parse the user's query and extract:
1. Intent (check_balance, transfer, transactions, what_if, insights)
2. Entities (account_id, amount, recipient_account, time_period)

IMPORTANT: Extract account_id from phrases like "account 1", "account 7", "account one", etc.
Extract time_period from phrases like "10 days", "30 days", "last week", etc. (return as string with number and "days")

User query: {query}

Return ONLY valid JSON in this format:
{{
    "intent": "intent_name",
    "entities": {{
        "account_id": null or number (extract from "account X" patterns),
        "amount": null or number,
        "recipient_account": null or number,
        "time_period": null or string (e.g., "10 days", "30 days")
    }},
    "confidence": 0.0-1.0
}}
"""

PLANNING_PROMPT = """You are a planner for a banking assistant.
Given the intent and entities, create a step-by-step execution plan.

Intent: {intent}
Entities: {entities}

AVAILABLE TOOLS (use EXACTLY these names):
- "get_balance" - Check account balance (requires: account_id)
- "transfer_money" - Transfer money between accounts (requires: account_id/from_account, recipient_account/to_account, amount)
- "get_transactions" - Get recent transactions (requires: account_id, optional: limit)
- "simulate_transaction" - Check if transaction is affordable (requires: account_id, amount)
- "get_insights" - Get spending insights (requires: account_id, optional: time_period/days)

Return ONLY valid JSON in this format:
{{
    "steps": [
        {{
            "step_id": 1,
            "action": "action_name",
            "tool": "tool_function_name",
            "parameters": {{}},
            "description": "what this step does"
        }}
    ],
    "requires_validation": true/false
}}

IMPORTANT: Use ONLY the exact tool names listed above. Do not invent new tool names.
"""

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FILE = "banking_agent.log"

