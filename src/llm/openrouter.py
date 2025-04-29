"""
OpenRouter API client module.

This module provides functionality to interact with the OpenRouter API
to generate shell commands from natural language requests.
"""

import os
import time
from typing import Dict, Any, Optional, List, Tuple

import requests
from dotenv import load_dotenv


class OpenRouterError(Exception):
    """Base exception for OpenRouter API errors."""
    pass


class RateLimitError(OpenRouterError):
    """Exception raised when API rate limit is reached."""
    pass


class AuthenticationError(OpenRouterError):
    """Exception raised when API authentication fails."""
    pass


class OpenRouterClient:
    """
    Client for interacting with the OpenRouter API.
    
    This client handles API requests to the OpenRouter service using
    the specified Mistral model.
    """
    
    # OpenRouter API endpoint
    BASE_URL = "https://openrouter.ai/api/v1"
    
    # Default model to use
    DEFAULT_MODEL = "mistralai/mistral-small-3.1-24b-instruct:free"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize the OpenRouter client.
        
        Args:
            api_key: The OpenRouter API key. If None, loads from environment.
            model: The model identifier to use for requests.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retry attempts on failure.
            retry_delay: Base delay between retries in seconds.
        """
        # Load environment variables if api_key not provided
        if api_key is None:
            load_dotenv()
            api_key = os.getenv("OPENROUTER_API_KEY")
        
        if not api_key:
            raise AuthenticationError(
                "OpenRouter API key not found. Please set OPENROUTER_API_KEY "
                "in the .env file or provide it as a parameter."
            )
        
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get the required headers for API requests.
        
        Returns:
            Dictionary of headers for API requests.
        """
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://localai-terminal-assistant",  # Required by OpenRouter
            "X-Title": "Terminal AI Assistant"  # Optional but recommended
        }
    
    def generate_command(self, prompt: str) -> Tuple[bool, str]:
        """
        Generate a shell command from a natural language prompt.
        
        Args:
            prompt: The natural language prompt describing the command to generate.
            
        Returns:
            A tuple containing:
            - Success flag (True if successful, False otherwise)
            - The generated command or error message
        """
        url = f"{self.BASE_URL}/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,  # Lower temperature for more deterministic outputs
            "max_tokens": 200,    # Limit token count for faster responses
        }
        
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers=self._get_headers(),
                    timeout=self.timeout
                )
                
                # Handle different response status codes
                if response.status_code == 200:
                    return self._parse_command_response(response.json())
                elif response.status_code == 401:
                    raise AuthenticationError("Invalid API key")
                elif response.status_code == 429:
                    # Rate limit error - exponential backoff
                    retry_after = int(response.headers.get("Retry-After", str(2 ** attempt)))
                    time.sleep(retry_after)
                    continue
                else:
                    # Other errors
                    error_msg = f"API error: {response.status_code} - {response.text}"
                    return False, error_msg
                    
            except requests.exceptions.Timeout:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                return False, "Request timed out"
                
            except requests.exceptions.RequestException as e:
                return False, f"Request error: {str(e)}"
                
            except Exception as e:
                return False, f"Unexpected error: {str(e)}"
        
        return False, "Max retries exceeded"
    
    def _parse_command_response(self, response_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Parse the API response to extract the generated command.
        
        Args:
            response_data: The JSON response from the API.
            
        Returns:
            A tuple containing:
            - Success flag (True if successful, False otherwise)
            - The generated command or error message
        """
        try:
            # Extract the command from the response
            if "choices" in response_data and response_data["choices"]:
                choice = response_data["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    command = choice["message"]["content"].strip()
                    return True, command
            
            # If we couldn't parse the response
            return False, "Failed to parse command from response"
            
        except Exception as e:
            return False, f"Error parsing response: {str(e)}"

