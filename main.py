"""
Main CLI Interface for Banking Agent.
Implements the complete MCP pipeline.
"""
import sys
import logging
from database import BankingDatabase
from mcp.intent_parser import IntentParser
from mcp.planner import Planner
from mcp.executor import Executor
from mcp.validator import Validator
from mcp.responder import Responder
from utils.logger import setup_logger

# Setup logging
logger = setup_logger("banking_agent", level="INFO")


class BankingAgent:
    """Main Banking Agent implementing MCP architecture."""
    
    def __init__(self):
        """Initialize all MCP components."""
        logger.info("Initializing Banking Agent...")
        
        # Initialize database
        self.db = BankingDatabase()
        
        # Initialize MCP components
        self.intent_parser = IntentParser()
        self.planner = Planner()
        self.executor = Executor(self.db)
        self.validator = Validator()
        self.responder = Responder()
        
        logger.info("Banking Agent initialized successfully")
    
    def process_query(self, user_query: str) -> str:
        """
        Process user query through complete MCP pipeline.
        
        MCP Flow:
        1. Intent Parser → Extract intent and entities
        2. Planner → Generate execution plan
        3. Executor → Execute planned steps
        4. Validator → Validate results
        5. Responder → Format response
        """
        logger.info(f"Processing query: {user_query}")
        
        # Step 1: Intent Parsing
        logger.info("MCP Step 1: Intent Parsing")
        parsed = self.intent_parser.parse(user_query)
        intent = parsed.get("intent", "unknown")
        entities = parsed.get("entities", {})
        
        if parsed.get("confidence", 0) < 0.5:
            return "I'm not sure I understand. Could you rephrase your banking query?"
        
        # Step 2: Planning
        logger.info("MCP Step 2: Planning")
        plan = self.planner.plan(intent, entities)
        
        # Step 3: Execution
        logger.info("MCP Step 3: Execution")
        execution_results = self.executor.execute_plan(plan)
        
        # Step 4: Validation (if required)
        if plan.get("requires_validation", False):
            logger.info("MCP Step 4: Validation")
            for step in plan.get("steps", []):
                step_id = step.get("step_id")
                step_result = execution_results.get(f"step_{step_id}", {})
                is_valid, message = self.validator.validate(step_result, step)
                if not is_valid:
                    logger.warning(f"Validation failed: {message}")
                    execution_results["validation_error"] = message
        
        # Step 5: Response Generation
        logger.info("MCP Step 5: Response Generation")
        response = self.responder.respond(execution_results, intent)
        
        return response
    
    def setup_demo_data(self):
        """Create demo data for testing."""
        logger.info("Setting up demo data...")
        
        # Create demo user
        user_id = self.db.create_user("John Doe", "password123")
        
        # Create demo accounts
        account1 = self.db.create_account(user_id, initial_balance=5000.0)
        account2 = self.db.create_account(user_id, initial_balance=2000.0)
        
        logger.info(f"Demo setup complete. User ID: {user_id}, Accounts: {account1}, {account2}")
        print(f"\n✅ Demo data created!")
        print(f"   User: John Doe (ID: {user_id})")
        print(f"   Account 1: ${5000.0:.2f} (ID: {account1})")
        print(f"   Account 2: ${2000.0:.2f} (ID: {account2})\n")


def main():
    """Main CLI entry point."""
    print("=" * 60)
    print("🏦 Banking Agent - AI-Powered Banking Assistant")
    print("=" * 60)
    print("\nCommands:")
    print("  'setup' - Create demo data")
    print("  'quit' or 'exit' - Exit the agent")
    print("\nAsk me anything about banking!\n")
    
    agent = BankingAgent()
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if user_input.lower() == 'setup':
                agent.setup_demo_data()
                continue
            
            # Process query through MCP pipeline
            response = agent.process_query(user_input)
            print(f"\nAgent: {response}\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            print(f"\n❌ Error: {str(e)}\n")


if __name__ == "__main__":
    main()

