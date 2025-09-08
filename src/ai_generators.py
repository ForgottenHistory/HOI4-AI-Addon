#!/usr/bin/env python3
"""
AI Report Generators - Individual generators for different report types
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

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
                
                powers_info.append(f"- {country['tag']}: {ruling_party} government, {stability:.0f}% stability, {war_support:.0f}% war support")
        
        if powers_info:
            context_parts.append(f"Major Powers Status:\n" + "\n".join(powers_info))
        
        return "\n\n".join(context_parts)

class AdviserGenerator(BaseGenerator):
    """Generates strategic advice for the player's country"""
    
    def generate_prompt(self, game_data: Dict[str, Any], **kwargs) -> str:
        player_analysis = kwargs.get('player_analysis')
        if not player_analysis:
            return "No player data available for analysis."
        
        context = self._build_player_context(game_data, player_analysis)
        
        return f"""You are a senior advisor to the government of {player_analysis.get('name', 'Unknown')} in {game_data['metadata']['date']}.
Provide strategic counsel to your leadership.

CURRENT DOMESTIC SITUATION:
{context}

Provide a strategic assessment (2-3 paragraphs) covering:
1. Current domestic political stability and challenges
2. Strategic position relative to major powers
3. Key opportunities and threats on the horizon
4. Recommended focus areas for national development

Write as a trusted advisor speaking directly to leadership."""
    
    def get_max_tokens(self) -> int:
        return 800
    
    def _build_player_context(self, game_data: Dict[str, Any], player_analysis: Dict[str, Any]) -> str:
        context_parts = []
        
        context_parts.append(f"Government: {player_analysis.get('ruling_party', 'Unknown')}")
        context_parts.append(f"Stability: {player_analysis.get('stability', 0):.1f}%")
        context_parts.append(f"War Support: {player_analysis.get('war_support', 0):.1f}%")
        context_parts.append(f"Political Power: {player_analysis.get('political_power', 'Unknown')}")
        
        if player_analysis.get('party_support'):
            party_text = ", ".join([f"{party}: {support:.1f}%" 
                                  for party, support in player_analysis['party_support'].items()])
            context_parts.append(f"Party Support: {party_text}")
        
        if player_analysis.get('national_ideas'):
            ideas_text = ", ".join(player_analysis['national_ideas'][:5])
            context_parts.append(f"Key National Characteristics: {ideas_text}")
        
        # Focus information
        if player_analysis.get('focus_analysis'):
            focus = player_analysis['focus_analysis']
            if focus.get('current_focus'):
                context_parts.append(f"Current Focus: {focus['current_focus']} ({focus.get('progress', 0):.0f}% complete)")
            if focus.get('completed_count', 0) > 0:
                context_parts.append(f"Completed Focuses: {focus['completed_count']}")
        
        return "\n".join(context_parts)

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

Use headlines and dramatic language appropriate for the era."""
    
    def get_max_tokens(self) -> int:
        return 900

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
        
        # Major power tensions
        major_powers = ['GER', 'SOV', 'USA', 'ENG', 'FRA', 'ITA', 'JAP']
        powers_info = []
        
        for country in game_data.get('countries', []):
            if country['tag'] in major_powers:
                data = country['data']
                stability = data.get('stability', 0) * 100
                war_support = data.get('war_support', 0) * 100
                ruling_party = data.get('politics', {}).get('ruling_party', 'Unknown')
                
                if war_support > 60 or stability < 60:  # Only mention if notable
                    powers_info.append(f"- {country['tag']}: {ruling_party}, Stability: {stability:.0f}%, War Support: {war_support:.0f}%")
        
        if powers_info:
            context_parts.append(f"Notable Power Status:\n" + "\n".join(powers_info))
        
        return "\n\n".join(context_parts)