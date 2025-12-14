"""
Intent Parser Module (MCP Step 1).
Uses LLM to extract intent and entities from user queries.
"""
import json
import logging
from groq import Groq
import config

logger = logging.getLogger(__name__)


class IntentParser:
    """Parses user intent and extracts entities using LLM."""
    
    def __init__(self):
        self.client = Groq(api_key=config.GROQ_API_KEY)
        self.model = config.GROQ_MODEL
    
    def parse(self, user_query: str) -> dict:
        """
        Parse user query to extract intent and entities.
        
        Returns:
            {
                "intent": str,
                "entities": dict,
                "confidence": float
            }
        """
        models_to_try = [self.model] + config.GROQ_FALLBACK_MODELS
        
        for model in models_to_try:
            try:
                prompt = config.INTENT_PARSING_PROMPT.format(query=user_query)
                
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a precise intent parser. Always return valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,  # Low temperature for consistent parsing
                    response_format={"type": "json_object"}
                )
                
                result = json.loads(response.choices[0].message.content)
                logger.info(f"Parsed intent: {result.get('intent')} with confidence {result.get('confidence', 0)} (using model: {model})")
                
                # Update model if fallback was used
                if model != self.model:
                    self.model = model
                    logger.info(f"Switched to model: {model}")
                
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                continue
            except Exception as e:
                error_msg = str(e)
                # If model is decommissioned, try next model
                if "decommissioned" in error_msg.lower() or "model" in error_msg.lower():
                    logger.warning(f"Model {model} failed: {error_msg}. Trying next model...")
                    continue
                logger.error(f"Intent parsing failed with model {model}: {e}")
                continue
        
        # All models failed
        logger.error("All models failed for intent parsing")
        return {
            "intent": "unknown",
            "entities": {},
            "confidence": 0.0
        }

