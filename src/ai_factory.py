#!/usr/bin/env python3
"""
AI Service Factory - Easy configuration and setup
"""

from ai_analyst import HOI4AIService
from ai_client import AIConfig
from ai_generators import BaseGenerator

class AIServiceFactory:
    """Factory for creating configured AI services"""
    
    @staticmethod
    def create_openrouter_service(
        model: str = "moonshotai/kimi-k2-0905",
        temperature: float = 0.7
    ) -> HOI4AIService:
        """Create service with OpenRouter configuration"""
        config = AIConfig(
            api_key="",  # Will be loaded from env
            model=model,
            base_url="https://openrouter.ai/api/v1/chat/completions",
            default_temperature=temperature
        )
        return HOI4AIService(config)
    
    @staticmethod
    def create_custom_service(
        api_key: str,
        model: str,
        base_url: str,
        temperature: float = 0.7
    ) -> HOI4AIService:
        """Create service with custom configuration"""
        config = AIConfig(
            api_key=api_key,
            model=model,
            base_url=base_url,
            default_temperature=temperature
        )
        return HOI4AIService(config)
    
    @staticmethod
    def create_extended_service(custom_generators: dict[str, BaseGenerator] = None) -> HOI4AIService:
        """Create service with additional custom generators"""
        service = HOI4AIService()
        
        if custom_generators:
            for name, generator in custom_generators.items():
                service.add_generator(name, generator)
        
        return service

# Example usage and presets
class AIPresets:
    """Predefined AI service configurations"""
    
    @staticmethod
    def creative_writer(temperature: float = 0.9) -> HOI4AIService:
        """High creativity for narrative reports"""
        return AIServiceFactory.create_openrouter_service(
            temperature=temperature
        )
    
    @staticmethod
    def analytical(temperature: float = 0.3) -> HOI4AIService:
        """Low temperature for factual analysis"""
        return AIServiceFactory.create_openrouter_service(
            temperature=temperature
        )
    
    @staticmethod
    def balanced() -> HOI4AIService:
        """Balanced configuration"""
        return AIServiceFactory.create_openrouter_service()