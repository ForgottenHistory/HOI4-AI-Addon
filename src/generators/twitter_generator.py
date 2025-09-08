#!/usr/bin/env python3
"""
Twitter Feed Generator
Generates Twitter-like social media posts from 1930s world leaders
"""

from typing import Dict, List, Any
from .base_generator import BaseGenerator

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
        
        # Recent events
        if recent_events:
            events_text = "\n".join([f"- {event}" for event in recent_events[-8:]])
            context_parts.append(f"Recent Global Events:\n{events_text}")
        
        # Current date and major powers
        context_parts.append(f"Date: {game_data['metadata']['date']}")
        
        # Major power tensions and focus activity
        major_powers = ['GER', 'SOV', 'USA', 'ENG', 'FRA', 'ITA', 'JAP']
        powers_info = []
        focus_activities = []
        
        for country in game_data.get('countries', []):
            if country['tag'] in major_powers:
                data = country['data']
                stability = data.get('stability', 0) * 100
                war_support = data.get('war_support', 0) * 100
                ruling_party = data.get('politics', {}).get('ruling_party', 'Unknown')
                
                if war_support > 60 or stability < 60:  # Only mention if notable
                    powers_info.append(f"- {country['tag']}: {ruling_party}, Stability: {stability:.0f}%, War Support: {war_support:.0f}%")
                
                # Track interesting focus activities for Twitter drama
                focus_data = data.get('focus', {})
                if focus_data.get('current'):
                    current_focus = focus_data['current']
                    progress = focus_data.get('progress', 0)
                    
                    # Look for military/aggressive focuses that would cause Twitter drama
                    military_keywords = ['military', 'army', 'war', 'expand', 'aggression', 'conquest', 'invasion', 'rearm', 'mobiliz', 'anschluss', 'lebensraum']
                    if any(keyword in current_focus.lower() for keyword in military_keywords):
                        focus_activities.append(f"- {country['tag']} pursuing {current_focus} ({progress:.0f}% complete)")
                    elif progress > 80:  # Any focus near completion is interesting
                        focus_activities.append(f"- {country['tag']} nearing completion of {current_focus} ({progress:.0f}% complete)")
        
        if powers_info:
            context_parts.append(f"Notable Power Status:\n" + "\n".join(powers_info))
        
        if focus_activities:
            context_parts.append(f"Military/Strategic Focus Activities:\n" + "\n".join(focus_activities))
        
        return "\n\n".join(context_parts)