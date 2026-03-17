from groq import Groq
from typing import Generator, Optional


class GroqClient:
    def __init__(self, api_key: str):
        """
        Initialize Groq client with API key.
        
        Args:
            api_key: Groq API key for authentication
        """
        self.client = Groq(api_key=api_key)
    
    def complete(self, system_prompt: str, user_prompt: str, model: str, temperature: float, max_tokens: int = 1500) -> str:
        """
        Generate a complete response from Groq model.
        
        Args:
            system_prompt: System prompt for role conditioning
            user_prompt: User prompt with context
            model: Model name to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            
        Returns:
            Complete response text as string
            
        Raises:
            RuntimeError: If API call fails
        """
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise RuntimeError(f"Groq API error: {str(e)}")
    
    def stream_complete(self, system_prompt: str, user_prompt: str, model: str, temperature: float, max_tokens: int = 1500) -> Generator[str, None, None]:
        """
        Generate a streaming response from Groq model.
        
        Args:
            system_prompt: System prompt for role conditioning
            user_prompt: User prompt with context
            model: Model name to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            
        Yields:
            Response text chunks as strings
            
        Raises:
            RuntimeError: If API call fails
        """
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response_stream = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            for chunk in response_stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            raise RuntimeError(f"Groq API error: {str(e)}")
