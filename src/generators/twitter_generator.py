#!/usr/bin/env python3
"""
Twitter Feed Generator
Generates Twitter-like social media posts from 1930s world leaders
"""

from typing import Dict, List, Any
from .base_generator import BaseGenerator
# Import shared utilities
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from services.utils import get_major_power_tags

class TwitterGenerator(BaseGenerator):
    """Generates Twitter-like social media posts from 1930s world leaders"""
    
    def generate_prompt(self, game_data: Dict[str, Any], **kwargs) -> str:
        context = self._build_twitter_context(game_data, kwargs.get('recent_events', []))
        
        return f"""You are generating a social media feed from an alternate 1936 where Twitter exists. 
Create tweets from various world leaders, diplomats, and journalists reacting to current events.

CURRENT WORLD SITUATION:
{context}

Generate 8-12 realistic tweets (280 chars max each) from different personas:
- World leaders (Hitler, Stalin, FDR, Churchill, etc.)
- Diplomats and foreign ministers  
- Journalists and war correspondents
- Political commentators

Format each tweet as:
@username: [tweet content] 
[timestamp - like 2h ago, 4h ago, etc.]

Make them authentic to 1930s personalities but in modern Twitter style:
- Use period-appropriate language and concerns
- Include some replies/arguments between leaders
- Add realistic hashtags (#SpanishCrisis #Anschluss etc.)
- Show different political perspectives
- Reference national focus activities as policy announcements
- Keep the tone serious but occasionally dramatic

Make it feel like real political Twitter discourse from 1936."""
    
    def get_max_tokens(self) -> int:
        return 1200
    
    def _build_twitter_context(self, game_data: Dict[str, Any], recent_events: List[str]) -> str:
        context_parts = []
        
        # Recent events with descriptions
        if recent_events:
            if isinstance(recent_events, list) and len(recent_events) > 0 and isinstance(recent_events[0], dict):
                # New format with descriptions
                events_text = []
                for event in recent_events[-8:]:
                    events_text.append(f"- {event['title']}")
                    if event.get('description'):
                        # Full description, no truncation
                        desc = event['description']
                        events_text.append(f"  Context: {desc}")
                context_parts.append(f"Recent Global Events:\n" + "\n".join(events_text))
            else:
                # Old format (backwards compatibility)
                events_text = "\n".join([f"- {event}" for event in recent_events[-8:]])
                context_parts.append(f"Recent Global Events:\n{events_text}")
        
        # Current date
        context_parts.append(f"Date: {game_data['metadata']['date']}")
        
        # Major power information with focus descriptions
        if 'major_powers' in game_data:
            powers_info = []
            focus_activities = []
            
            for power in game_data['major_powers']:
                stability = power.get('stability', 0)
                war_support = power.get('war_support', 0)
                ruling_party = power.get('ruling_party', 'Unknown')
                
                if war_support > 60 or stability < 60:  # Only mention if notable (values are already percentages)
                    powers_info.append(f"- {power['name']} ({power['tag']}): {ruling_party}, Stability: {stability:.0f}%, War Support: {war_support:.0f}%")
                
                # All focus activities with full descriptions 
                focus_data = power.get('focus', {})
                if focus_data and focus_data.get('current_focus'):
                    current_focus = focus_data['current_focus']
                    description = focus_data.get('current_focus_description', '')
                    progress = focus_data.get('progress', 0)
                    
                    # Show all focuses, not just military ones
                    activity = f"- {power['name']} pursuing {current_focus} ({progress:.0f}% complete)"
                    if description:  # Add full description if available
                        activity += f"\n  Policy: {description}"
                    focus_activities.append(activity)
            
            if powers_info:
                context_parts.append(f"Notable Power Status:\n" + "\n".join(powers_info))
            
            if focus_activities:
                context_parts.append(f"Current Focus Activities:\n" + "\n".join(focus_activities))
        else:
            # Fallback to old format
            major_powers = list(get_major_power_tags())
            powers_info = []
            focus_activities = []
            
            for country in game_data.get('countries', []):
                if country['tag'] in major_powers:
                    data = country['data']
                    stability = data.get('stability', 0) * 100
                    war_support = data.get('war_support', 0) * 100
                    ruling_party = data.get('politics', {}).get('ruling_party', 'Unknown')
                    
                    if war_support > 60 or stability < 60:
                        powers_info.append(f"- {country['tag']}: {ruling_party}, Stability: {stability:.0f}%, War Support: {war_support:.0f}%")
        
        return "\n\n".join(context_parts)