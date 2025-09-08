#!/usr/bin/env python3
"""
Strategic Adviser Generator
Generates strategic advice for the player's country
"""

from typing import Dict, Any
from .base_generator import BaseGenerator

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
5. Assessment of current focus tree progress and strategic priorities

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
                if focus.get('recent_completed'):
                    recent = ", ".join(focus['recent_completed'])
                    context_parts.append(f"Recent Completed Focuses: {recent}")
        
        return "\n".join(context_parts)