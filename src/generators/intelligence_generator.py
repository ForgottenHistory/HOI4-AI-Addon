#!/usr/bin/env python3
"""
Intelligence Report Generator
Generates formal diplomatic intelligence briefings
"""

from typing import Dict, Any
from .base_generator import BaseGenerator

class IntelligenceGenerator(BaseGenerator):
    """Generates diplomatic intelligence briefings"""
    
    def generate_prompt(self, game_data: Dict[str, Any], **kwargs) -> str:
        context = self._build_world_context(game_data)
        
        return f"""You are a diplomatic intelligence analyst in {game_data['metadata']['date']}. 
Analyze the current world situation and write a brief, engaging intelligence report.

CURRENT SITUATION:
{context}

Write a concise intelligence briefing (3-4 paragraphs) covering:
1. Most significant global developments
2. Rising tensions and potential flashpoints  
3. Key power dynamics between major nations
4. Strategic implications for world stability
5. Notable national focus activities and their implications

Write in the style of a 1930s diplomatic cable - serious but engaging."""
    
    def get_max_tokens(self) -> int:
        return 1000
    
    def _build_world_context(self, game_data: Dict[str, Any]) -> str:
        context_parts = []
        
        if game_data.get('events'):
            recent_events = game_data['events'][-5:]
            events_text = "\n".join([f"- {event}" for event in recent_events])
            context_parts.append(f"Recent Global Events:\n{events_text}")
        
        major_powers = ['GER', 'SOV', 'USA', 'ENG', 'FRA', 'ITA', 'JAP']
        powers_info = []
        
        for country in game_data.get('countries', []):
            if country['tag'] in major_powers:
                data = country['data']
                stability = data.get('stability', 0) * 100
                war_support = data.get('war_support', 0) * 100
                ruling_party = data.get('politics', {}).get('ruling_party', 'Unknown')
                
                info = f"- {country['tag']}: {ruling_party} government, {stability:.0f}% stability, {war_support:.0f}% war support"
                
                # Add focus information if available
                focus_data = data.get('focus', {})
                if focus_data.get('current'):
                    current_focus = focus_data['current']
                    progress = focus_data.get('progress', 0)
                    info += f", focusing on {current_focus} ({progress:.0f}% complete)"
                
                completed_count = len(focus_data.get('completed', []))
                if completed_count > 0:
                    info += f", {completed_count} focuses completed"
                
                powers_info.append(info)
        
        if powers_info:
            context_parts.append(f"Major Powers Status:\n" + "\n".join(powers_info))
        
        return "\n\n".join(context_parts)