#!/usr/bin/env python3
"""
AI API Client - Handles communication with AI services
"""

import os
import requests
from typing import Optional
from dataclasses import dataclass

@dataclass
class AIConfig:
    """Configuration for AI API calls"""
    api_key: str
    model: str
    base_url: str
    default_temperature: float = 0.7
    timeout: int = 30

class AIClient:
    """Generic AI API client"""
    
    def __init__(self, config: Optional[AIConfig] = None):
        if config:
            self.config = config
        else:
            # Default OpenRouter configuration
            api_key = os.getenv('OPENROUTER_API_KEY')
            if not api_key:
                raise ValueError("OPENROUTER_API_KEY environment variable not found")
            
            self.config = AIConfig(
                api_key=api_key,
                model="moonshotai/kimi-k2-0905",
                base_url="https://openrouter.ai/api/v1/chat/completions"
            )
    
    def generate_text(self, prompt: str, max_tokens: int = 1000, temperature: Optional[float] = None) -> str:
        """Generate text using the AI API"""
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        
        data = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature or self.config.default_temperature
        }
        
        try:
            response = requests.post(
                self.config.base_url, 
                headers=headers, 
                json=data, 
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
            
        except requests.exceptions.Timeout:
            return "AI Generation Error: Request timed out"
        except requests.exceptions.RequestException as e:
            return f"AI Generation Error: Network error - {e}"
        except KeyError as e:
            return f"AI Generation Error: Unexpected response format - {e}"
        except Exception as e:
            return f"AI Generation Error: {e}"