#!/usr/bin/env python3
"""
News Report Generator
Generates newspaper-style reports from recent events
"""

from typing import Dict, Any
from .base_generator import BaseGenerator

class NewsGenerator(BaseGenerator):
    """Generates newspaper-style reports"""
    
    def generate_prompt(self, game_data: Dict[str, Any], **kwargs) -> str:
        recent_events = kwargs.get('recent_events', [])
        if not recent_events:
            return "No significant developments to report."
        
        events_text = "\n".join([f"- {event}" for event in recent_events[-5:]])
        
        return f"""You are an international correspondent writing for a major newspaper in {game_data['metadata']['date']}.
Write an engaging news article based on these recent global developments:

RECENT DEVELOPMENTS:
{events_text}

Write a compelling news article (3-4 paragraphs) that:
1. Connects these events into a coherent narrative
2. Explains their significance for international relations
3. Provides historical context where relevant
4. Maintains the tone and style of 1930s journalism
5. References any major national focus completions as policy shifts

Use headlines and dramatic language appropriate for the era."""
    
    def get_max_tokens(self) -> int:
        return 900