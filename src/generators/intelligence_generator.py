#!/usr/bin/env python3
"""
Intelligence Report Generator
Generates formal diplomatic intelligence briefings
"""

from typing import Dict, Any
from .base_generator import BaseGenerator
# Import shared utilities
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from services.utils import get_major_power_tags

class IntelligenceGenerator(BaseGenerator):
    """Generates diplomatic intelligence briefings"""
    
    def generate_prompt(self, game_data: Dict[str, Any], **kwargs) -> str:
        verbose = kwargs.get('verbose', False)
        context = self._build_world_context(game_data, verbose=verbose)
        
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
        return 1300  # Increased for richer descriptions
    
    def _build_world_context(self, game_data: Dict[str, Any], verbose: bool = False) -> str:
        context_parts = []
        
        # Handle both event formats
        if game_data.get('recent_events'):
            recent_events = game_data['recent_events'][-5:]
            events_text = self._format_events_for_intelligence(recent_events, verbose=verbose)
            context_parts.append(f"Recent Global Events:\n{events_text}")
        elif game_data.get('events'):
            # Fallback to old format
            recent_events = game_data['events'][-5:]
            events_text = "\n".join([f"- {event}" for event in recent_events])
            context_parts.append(f"Recent Global Events:\n{events_text}")
        
        # Use rich major powers data if available
        if game_data.get('major_powers'):
            powers_info = []
            for power in game_data['major_powers']:
                stability = power.get('stability', 0)
                war_support = power.get('war_support', 0)
                ruling_party = power.get('ruling_party', 'Unknown')
                
                info = f"- {power['name']} ({power['tag']}): {ruling_party} government, {stability:.0f}% stability, {war_support:.0f}% war support"
                
                # Add detailed focus information
                focus_data = power.get('focus', {})
                if focus_data.get('current_focus'):
                    current_focus = focus_data['current_focus']
                    progress = focus_data.get('progress', 0)
                    info += f", pursuing {current_focus} ({progress:.0f}% complete)"
                    
                    # Add focus description for intelligence context
                    description = focus_data.get('current_focus_description', '')
                    if description:
                        # Truncate only if not verbose
                        if not verbose and len(description) > 120:
                            description = description[:120] + "..."
                        info += f"\n    Policy: {description}"
                
                completed_count = focus_data.get('completed_count', 0)
                if completed_count > 0:
                    info += f"\n    Completed initiatives: {completed_count}"
                
                powers_info.append(info)
            
            if powers_info:
                context_parts.append(f"Major Powers Analysis:\n" + "\n".join(powers_info))
        else:
            # Fallback to old format
            major_powers = list(get_major_power_tags())
            powers_info = []
            
            for country in game_data.get('countries', []):
                if country['tag'] in major_powers:
                    data = country['data']
                    stability = data.get('stability', 0) * 100
                    war_support = data.get('war_support', 0) * 100
                    ruling_party = data.get('politics', {}).get('ruling_party', 'Unknown')
                    
                    info = f"- {country['tag']}: {ruling_party} government, {stability:.0f}% stability, {war_support:.0f}% war support"
                    powers_info.append(info)
            
            if powers_info:
                context_parts.append(f"Major Powers Status:\n" + "\n".join(powers_info))
        
        return "\n\n".join(context_parts)
    
    def _format_events_for_intelligence(self, events, verbose=False):
        """Format events with context for intelligence briefings"""
        if not events:
            return ""
        
        if isinstance(events, list) and len(events) > 0 and isinstance(events[0], dict):
            # New format with descriptions
            formatted = []
            for event in events:
                formatted.append(f"- {event['title']}")
                if event.get('description'):
                    desc = event['description']
                    if not verbose and len(desc) > 150:
                        desc = desc[:150] + "..."
                    formatted.append(f"    Analysis: {desc}")
            return "\n".join(formatted)
        else:
            # Old format
            return "\n".join([f"- {event}" for event in events])