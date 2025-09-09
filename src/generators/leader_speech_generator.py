#!/usr/bin/env python3
"""
Country Leader Speech Generator
Generates speeches from national leaders based on their country's situation and ideology
"""

from typing import Dict, Any, List
from .base_generator import BaseGenerator

class LeaderSpeechGenerator(BaseGenerator):
    """Generates speeches from country leaders addressing their nation"""
    
    def generate_prompt(self, game_data: Dict[str, Any], **kwargs) -> str:
        focus_countries = kwargs.get('focus_countries', [])
        
        if not focus_countries:
            return "No country specified for leader speech."
        
        # Focus on the primary country for the speech
        primary_country = focus_countries[0]
        country_name = primary_country['name']
        tag = primary_country['tag']
        political = primary_country['political']
        focus = primary_country['focus']
        
        # Determine leader characteristics and speech context
        leader_context = self._build_leader_context(primary_country, game_data)
        speech_occasion = self._determine_speech_occasion(primary_country)
        rhetorical_style = self._get_rhetorical_style(primary_country)
        
        return f"""You are writing a speech delivered by the leader of {country_name} in {game_data['metadata']['date']}.

LEADER & COUNTRY CONTEXT:
{leader_context}

SPEECH OCCASION:
{speech_occasion}

RHETORICAL STYLE:
{rhetorical_style}

Write a compelling leader's speech (600-800 words) that:

1. **Opening**: Addresses the nation with appropriate formality for the political system
2. **Current Situation**: References the country's stability, challenges, and recent policy changes
3. **Vision/Goals**: Outlines the leader's agenda and national priorities
4. **Call to Action**: Mobilizes citizens around shared values and objectives
5. **Closing**: Ends with a memorable phrase or rallying cry

IMPORTANT REQUIREMENTS:
- Use language and rhetoric appropriate to the leader's ideology and time period
- Reference specific current policies from the focus tree progress
- Address the country's stability and war support levels naturally
- Include period-appropriate concerns (economic, military, social)
- Maintain authentic historical voice without offensive content
- Balance inspiration with realistic acknowledgment of challenges
- Use rhetorical devices common to 1930s-1940s political oratory

The speech should sound like it could have been delivered by an actual leader of that country and ideology in that era."""
    
    def _build_leader_context(self, country: Dict[str, Any], game_data: Dict[str, Any]) -> str:
        """Build context about the leader and country situation"""
        tag = country['tag']
        name = country['name']
        political = country['political']
        focus = country['focus']
        
        context_lines = []
        context_lines.append(f"Country: {name} ({tag})")
        context_lines.append(f"Date: {game_data['metadata']['date']}")
        context_lines.append(f"Government Type: {political.ruling_party}")
        context_lines.append(f"National Stability: {political.stability:.1f}%")
        context_lines.append(f"Public War Support: {political.war_support:.1f}%")
        context_lines.append(f"Government Authority: {political.political_power:.0f} political power")
        
        # Political dynamics
        if political.party_support:
            sorted_parties = sorted(political.party_support.items(), key=lambda x: x[1], reverse=True)
            context_lines.append(f"Political Support: {sorted_parties[0][0]} leads with {sorted_parties[0][1]:.1f}%")
            if len(sorted_parties) > 1:
                context_lines.append(f"Main Opposition: {sorted_parties[1][0]} ({sorted_parties[1][1]:.1f}%)")
        
        # Current policies
        if focus and focus.current_focus:
            context_lines.append(f"Current National Priority: {focus.current_focus_name}")
            context_lines.append(f"Policy Progress: {focus.progress:.0f}% complete")
        
        # Recent achievements
        if focus and focus.completed_focus_names:
            recent_policies = focus.completed_focus_names[-2:]
            context_lines.append(f"Recent Policy Successes: {', '.join(recent_policies)}")
        
        # Special status
        if country['is_player']:
            context_lines.append("Status: Player nation - active on world stage")
        if country['is_major_power']:
            context_lines.append("Status: Major world power with global influence")
        
        return "\n".join(context_lines)
    
    def _determine_speech_occasion(self, country: Dict[str, Any]) -> str:
        """Determine the appropriate occasion for the speech"""
        political = country['political']
        focus = country['focus']
        
        # Base occasion on current situation
        if political.stability < 30:
            return "Emergency address to the nation during a time of severe internal crisis"
        elif political.stability < 50:
            return "Address to parliament/party congress during political tensions"
        elif political.war_support > 70:
            return "Rally speech to prepare the nation for potential military action"
        elif focus and focus.current_focus and focus.progress > 80:
            return "Public ceremony announcing the completion of a major national policy"
        elif political.political_power > 500:
            return "State of the nation address celebrating governmental achievements"
        else:
            return "Regular radio address to the citizens updating them on national progress"
    
    def _get_rhetorical_style(self, country: Dict[str, Any]) -> str:
        """Determine the rhetorical style based on ideology and situation"""
        tag = country['tag']
        political = country['political']
        ruling_party = political.ruling_party.lower()
        
        style_notes = []
        
        # Ideological style
        if 'fascism' in ruling_party or 'fascist' in ruling_party:
            style_notes.extend([
                "Dramatic, passionate rhetoric with appeals to national greatness",
                "References to historical glory and destiny",
                "Strong leader persona with calls for unity behind the state",
                "Emphasis on action, strength, and national renewal"
            ])
        elif 'communism' in ruling_party or 'communist' in ruling_party:
            style_notes.extend([
                "Revolutionary language focused on class struggle and progress", 
                "Appeals to worker solidarity and socialist construction",
                "References to enemies of the people and party vigilance",
                "Emphasis on collective achievement and ideological purity"
            ])
        elif 'democratic' in ruling_party:
            style_notes.extend([
                "Reasoned, measured tone appealing to democratic values",
                "References to constitutional principles and civic duty",
                "Acknowledgment of different viewpoints and debate",
                "Emphasis on freedom, rights, and representative government"
            ])
        else:  # Neutrality/other
            style_notes.extend([
                "Pragmatic, non-ideological focus on practical governance",
                "Appeals to tradition, stability, and national interest",
                "Moderate tone avoiding extreme positions",
                "Emphasis on competent administration and national development"
            ])
        
        # Country-specific additions
        if tag == 'USA':
            style_notes.append("References to American exceptionalism and constitutional heritage")
        elif tag == 'GER':
            style_notes.append("Appeals to German efficiency, order, and cultural achievement")
        elif tag == 'SOV':
            style_notes.append("Marxist-Leninist terminology and references to socialist construction")
        elif tag == 'ENG':
            style_notes.append("References to British imperial tradition and parliamentary democracy")
        elif tag == 'FRA':
            style_notes.append("Appeals to French republican values and cultural leadership")
        elif tag == 'ITA':
            style_notes.append("References to Roman heritage and Mediterranean destiny")
        elif tag == 'JAP':
            style_notes.append("Appeals to Japanese honor, emperor, and Asian leadership")
        
        # Situational modifiers
        if political.stability < 40:
            style_notes.append("Urgent tone addressing national crisis and need for sacrifice")
        elif political.war_support > 60:
            style_notes.append("Martial language preparing citizens for potential conflict")
        
        return "\n".join([f"- {note}" for note in style_notes])
    
    def get_max_tokens(self) -> int:
        return 1400  # Longer for full speeches