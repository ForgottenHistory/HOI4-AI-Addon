#!/usr/bin/env python3
"""
AI API Client - Handles communication with AI services
"""

import os
import requests
from typing import Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

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
    
    def __init__(self, config: Optional[AIConfig] = None, log_prompts: bool = True):
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
        
        self.log_prompts = log_prompts
        self.log_dir = Path("ai_logs")
        if self.log_prompts:
            self.log_dir.mkdir(exist_ok=True)
    
    def generate_text(self, prompt: str, max_tokens: int = 1000, temperature: Optional[float] = None, report_type: str = "unknown") -> str:
        """Generate text using the AI API"""
        
        # Log the prompt
        if self.log_prompts:
            self._log_prompt(prompt, report_type)
        
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
            generated_text = result['choices'][0]['message']['content'].strip()
            
            # Log the response
            if self.log_prompts:
                self._log_response(generated_text, report_type)
            
            return generated_text
            
        except requests.exceptions.Timeout:
            return "AI Generation Error: Request timed out"
        except requests.exceptions.RequestException as e:
            return f"AI Generation Error: Network error - {e}"
        except KeyError as e:
            return f"AI Generation Error: Unexpected response format - {e}"
        except Exception as e:
            return f"AI Generation Error: {e}"
    
    def _log_prompt(self, prompt: str, report_type: str):
        """Log the prompt to a file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{report_type}_prompt.txt"
        log_path = self.log_dir / filename
        
        try:
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(f"=== AI PROMPT LOG ===\n")
                f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Report Type: {report_type}\n")
                f.write(f"Model: {self.config.model}\n")
                f.write(f"Max Tokens: (will be set by generator)\n")
                f.write(f"Temperature: {self.config.default_temperature}\n")
                f.write(f"{'='*50}\n\n")
                f.write(prompt)
                f.write(f"\n\n{'='*50}\n")
        except Exception as e:
            print(f"Warning: Failed to log prompt: {e}")
    
    def _log_response(self, response: str, report_type: str):
        """Log the AI response to the same file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{report_type}_prompt.txt"
        log_path = self.log_dir / filename
        
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(f"=== AI RESPONSE ===\n\n")
                f.write(response)
                f.write(f"\n\n{'='*50}\n")
        except Exception as e:
            print(f"Warning: Failed to log response: {e}")