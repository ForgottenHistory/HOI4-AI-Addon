#!/usr/bin/env python3
"""
Base Generator Class
Abstract base class for all AI report generators
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseGenerator(ABC):
    """Base class for all AI report generators"""
    
    @abstractmethod
    def generate_prompt(self, game_data: Dict[str, Any], **kwargs) -> str:
        """Generate the prompt for this report type"""
        pass
    
    @abstractmethod
    def get_max_tokens(self) -> int:
        """Get maximum tokens for this report type"""
        pass