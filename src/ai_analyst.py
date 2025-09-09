#!/usr/bin/env python3
"""
Streamlined HOI4 AI Analyst Service
Main orchestrator for AI-powered game analysis
"""

from typing import Dict, Any
from ai_client import AIClient, AIConfig
from generators import (
    IntelligenceGenerator, 
    AdviserGenerator, 
    NewsGenerator, 
    CountryNewsGenerator,
    CitizenInterviewGenerator,
    TwitterGenerator
)

class HOI4AIService:
    """Main AI service that coordinates generators and client"""
    
    def __init__(self, ai_config: AIConfig = None):
        # Initialize AI client with logging enabled
        self.client = AIClient(ai_config, log_prompts=True)
        
        # Register all available generators
        self.generators = {
            'intelligence': IntelligenceGenerator(),
            'adviser': AdviserGenerator(),
            'news': NewsGenerator(),
            'country_news': CountryNewsGenerator(),
            'citizen_interviews': CitizenInterviewGenerator(),
            'twitter': TwitterGenerator(),
        }
    
    def generate_report(self, report_type: str, game_data: Dict[str, Any], **kwargs) -> str:
        """Generate a report using the specified generator"""
        if report_type not in self.generators:
            available = ", ".join(self.generators.keys())
            return f"Unknown report type: {report_type}. Available: {available}"
        
        # Get the appropriate generator
        generator = self.generators[report_type]
        
        # Generate the prompt
        prompt = generator.generate_prompt(game_data, **kwargs)
        
        # Make the API call
        return self.client.generate_text(
            prompt=prompt,
            max_tokens=generator.get_max_tokens(),
            report_type=report_type
        )
    
    def add_generator(self, name: str, generator):
        """Add a custom generator (for extensibility)"""
        self.generators[name] = generator
    
    def get_available_reports(self) -> list[str]:
        """Get list of available report types"""
        return list(self.generators.keys())
    
    def set_ai_config(self, config: AIConfig):
        """Update AI configuration"""
        self.client = AIClient(config, log_prompts=True)