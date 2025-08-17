#!/usr/bin/env python3
"""
Oracle GenAI Client Module
Provides a clean interface for Oracle Generative AI API calls
"""

import json
import logging
from typing import Dict, Any, Optional
import oci
from oci.generative_ai_inference import GenerativeAiInferenceClient

logger = logging.getLogger(__name__)

class OracleGenAIClient:
    """Oracle Generative AI client wrapper"""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize the GenAI client
        
        Args:
            config_file: Path to OCI config file (defaults to ~/.oci/config)
        """
        try:
            if config_file:
                self.config = oci.config.from_file(config_file)
            else:
                self.config = oci.config.from_file()
            
            self.compartment_id = self.config.get("tenancy")
            self.client = GenerativeAiInferenceClient(
                config=self.config,
                service_endpoint="https://inference.generativeai.us-chicago-1.oci.oraclecloud.com",
                retry_strategy=oci.retry.NoneRetryStrategy(),
                timeout=(10, 240)
            )
            logger.info("Oracle GenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Oracle GenAI client: {e}")
            raise
    
    def chat(self, 
             prompt: str, 
             model_name: str = "xai.grok-4", 
             temperature: float = 0.0,
             max_tokens: int = 300) -> Dict[str, Any]:
        """Make a chat completion request to Oracle GenAI
        
        Args:
            prompt: The prompt to send to the model
            model_name: Model ID (default: xai.grok-4)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dict containing response data or error information
        """
        try:
            logger.info(f"Making GenAI request with model: {model_name}, temp: {temperature}")
            logger.debug(f"Prompt preview: {prompt[:200]}...")
            
            # Prepare the request
            content = oci.generative_ai_inference.models.TextContent(text=prompt, type="TEXT")
            message = oci.generative_ai_inference.models.Message(role="USER", content=[content])
            
            # Determine API format based on model
            if model_name.startswith("cohere"):
                api_format = oci.generative_ai_inference.models.BaseChatRequest.API_FORMAT_COHERE
                chat_request = oci.generative_ai_inference.models.CohereChatRequest(
                    api_format=api_format,
                    message=prompt,  # Cohere uses 'message' not 'messages'
                    max_tokens=max_tokens,
                    temperature=temperature
                )
            else:
                # Generic format for other models (Grok, Llama, etc.)
                api_format = oci.generative_ai_inference.models.BaseChatRequest.API_FORMAT_GENERIC
                chat_request = oci.generative_ai_inference.models.GenericChatRequest(
                    api_format=api_format,
                    messages=[message],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
            
            chat_details = oci.generative_ai_inference.models.ChatDetails(
                serving_mode=oci.generative_ai_inference.models.OnDemandServingMode(model_id=model_name),
                chat_request=chat_request,
                compartment_id=self.compartment_id
            )
            
            # Make the API call
            response = self.client.chat(chat_details)
            
            # Process response
            result = self._process_response(response)
            logger.info(f"GenAI request completed successfully. Response length: {len(result.get('text', ''))}")
            return result
            
        except Exception as e:
            logger.error(f"GenAI API call failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "raw_response": None
            }
    
    def _process_response(self, response) -> Dict[str, Any]:
        """Process the API response and extract relevant information
        
        Args:
            response: Raw API response object
            
        Returns:
            Processed response dictionary
        """
        try:
            logger.debug(f"Response status: {response.status}")
            
            chat_response = response.data.chat_response
            
            # Handle Cohere response format
            if hasattr(chat_response, 'text'):
                # Cohere format - direct text attribute
                text_content = chat_response.text
                logger.debug(f"Extracted Cohere text: '{text_content}'")
                
                return {
                    "success": True,
                    "text": text_content,
                    "raw_response": response.data,
                    "finish_reason": getattr(chat_response, 'finish_reason', None)
                }
            
            # Handle Generic response format (Grok, Llama, etc.)
            elif hasattr(chat_response, 'choices'):
                # Check if response has choices
                if not chat_response.choices:
                    logger.warning("No choices in API response")
                    return {
                        "success": False,
                        "error": "no_choices",
                        "text": "",
                        "raw_response": response.data
                    }
                
                # Get the first choice
                choice = chat_response.choices[0]
                
                # Check if choice has content
                if not choice.message.content:
                    logger.warning("No content in response message")
                    return {
                        "success": False,
                        "error": "no_content", 
                        "text": "",
                        "raw_response": response.data
                    }
                
                # Extract text content
                text_content = choice.message.content[0].text
                logger.debug(f"Extracted Generic text: '{text_content}'")
                
                return {
                    "success": True,
                    "text": text_content,
                    "raw_response": response.data,
                    "finish_reason": getattr(choice, 'finish_reason', None)
                }
            
            else:
                logger.error("Unknown response format - no 'text' or 'choices' attribute")
                return {
                    "success": False,
                    "error": "unknown_response_format",
                    "text": "",
                    "raw_response": response.data
                }
            
        except Exception as e:
            logger.error(f"Failed to process API response: {e}")
            return {
                "success": False,
                "error": f"response_processing_failed: {e}",
                "text": "",
                "raw_response": getattr(response, 'data', None)
            }
    
    def chat_json(self, 
                  prompt: str, 
                  model_name: str = "xai.grok-4",
                  temperature: float = 0.0,
                  max_tokens: int = 300,
                  retry_on_invalid_json: bool = True) -> Dict[str, Any]:
        """Make a chat request expecting JSON response
        
        Args:
            prompt: The prompt to send (should request JSON format)
            model_name: Model ID
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            retry_on_invalid_json: Whether to retry with JSON formatting prompt if parsing fails
            
        Returns:
            Dict containing parsed JSON or error information
        """
        # Make the initial request
        response = self.chat(prompt, model_name, temperature, max_tokens)
        
        if not response["success"]:
            return response
        
        text = response["text"]
        
        # Try to parse as JSON
        try:
            parsed_json = json.loads(text.strip())
            logger.info("Successfully parsed JSON response")
            return {
                "success": True,
                "json": parsed_json,
                "raw_text": text,
                "raw_response": response["raw_response"]
            }
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON: {e}")
            
            if retry_on_invalid_json and text.strip():
                logger.info("Retrying with JSON formatting prompt")
                return self._retry_json_formatting(text, model_name, temperature)
            
            return {
                "success": False,
                "error": f"json_parse_failed: {e}",
                "raw_text": text,
                "raw_response": response["raw_response"]
            }
    
    def _retry_json_formatting(self, raw_text: str, model_name: str, temperature: float) -> Dict[str, Any]:
        """Retry with a JSON formatting prompt"""
        format_prompt = f"""
You will receive some model output that should have been JSON but isn't. Convert it to EXACT valid JSON.

Rules:
- Output ONLY a single JSON object on one line. No markdown, no prose, no code fences.
- Use double quotes for all keys and string values.
- If fields are too long, truncate reasonably but keep valid JSON.

Raw content:
<<<BEGIN>>>
{raw_text}
<<<END>>>
"""
        
        response = self.chat(format_prompt, model_name, temperature, max_tokens=200)
        
        if not response["success"]:
            return {
                "success": False,
                "error": "json_retry_failed",
                "raw_text": raw_text,
                "retry_response": response
            }
        
        try:
            parsed_json = json.loads(response["text"].strip())
            logger.info("Successfully parsed JSON after retry")
            return {
                "success": True,
                "json": parsed_json,
                "raw_text": raw_text,
                "retry_text": response["text"],
                "raw_response": response["raw_response"]
            }
        except json.JSONDecodeError as e:
            logger.error(f"JSON retry also failed: {e}")
            return {
                "success": False,
                "error": f"json_retry_parse_failed: {e}",
                "raw_text": raw_text,
                "retry_text": response["text"],
                "raw_response": response["raw_response"]
            }


# Convenience function for simple usage
def chat_with_genai(prompt: str, 
                   model_name: str = "xai.grok-4",
                   temperature: float = 0.0,
                   max_tokens: int = 300) -> str:
    """Simple function to get text response from GenAI
    
    Args:
        prompt: The prompt to send
        model_name: Model ID
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        
    Returns:
        Response text or empty string on error
    """
    try:
        client = OracleGenAIClient()
        response = client.chat(prompt, model_name, temperature, max_tokens)
        return response.get("text", "")
    except Exception as e:
        logger.error(f"Simple GenAI call failed: {e}")
        return ""


# Convenience function for JSON responses
def chat_json_with_genai(prompt: str,
                        model_name: str = "xai.grok-4", 
                        temperature: float = 0.0,
                        max_tokens: int = 300) -> Optional[Dict[str, Any]]:
    """Simple function to get JSON response from GenAI
    
    Args:
        prompt: The prompt to send (should request JSON)
        model_name: Model ID
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        
    Returns:
        Parsed JSON dict or None on error
    """
    try:
        client = OracleGenAIClient()
        response = client.chat_json(prompt, model_name, temperature, max_tokens)
        return response.get("json") if response["success"] else None
    except Exception as e:
        logger.error(f"Simple JSON GenAI call failed: {e}")
        return None
