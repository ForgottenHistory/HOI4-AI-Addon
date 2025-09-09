#!/usr/bin/env python3
"""
Citizen Interview Generator
Generates interviews with ordinary citizens about their country's current situation
"""

from typing import Dict, Any, List
from .base_generator import BaseGenerator

class CitizenInterviewGenerator(BaseGenerator):
    """Generates interviews with citizens from different walks of life"""
    
    def generate_prompt(self, game_data: Dict[str, Any], **kwargs) -> str:
        focus_countries = kwargs.get('focus_countries', [])
        recent_events = kwargs.get('recent_events', [])
        
        if not focus_countries:
            return "No countries specified for citizen interviews."
        
        # Focus on the primary country for interviews
        primary_country = focus_countries[0]
        country_name = primary_country['name']
        tag = primary_country['tag']
        political = primary_country['political']
        focus = primary_country['focus']
        
        # Build context about the country's situation
        situation_context = self._build_situation_context(primary_country, recent_events, game_data)
        citizen_types = self._get_citizen_types(primary_country, game_data)
        
        return f"""You are a journalist conducting interviews with ordinary citizens in {country_name} in {game_data['metadata']['date']}. 
Create authentic interviews with 4-5 different people from various walks of life about their country's current situation.

COUNTRY SITUATION:
{situation_context}

INTERVIEW SUBJECTS TO INCLUDE:
{citizen_types}

Create interviews in this format:
- Start with a brief introduction setting the scene
- Interview 4-5 citizens with different perspectives
- Each interview should be 2-3 exchanges (question/answer pairs)
- Show how political events affect ordinary people's daily lives
- Capture period-appropriate language, concerns, and attitudes
- Include diverse viewpoints reflecting different social classes and political leanings
- End with a brief journalist's reflection

Guidelines:
1. Make citizens sound authentic to their time period and social position
2. Show how macro political events (stability, war support, policies) affect daily life
3. Include references to recent government policies or focus tree completions
4. Reflect the country's political tensions in citizen responses
5. Use period-appropriate concerns (food prices, jobs, military service, etc.)
6. Show varying levels of political awareness and engagement
7. Include both supporters and critics of the current government
8. Make it feel like real people talking, not political speeches

The tone should be journalistic but intimate - like a radio documentary or newspaper feature story from the era."""
    
    def _build_situation_context(self, country: Dict[str, Any], recent_events: List[str], game_data: Dict[str, Any]) -> str:
        """Build context about the country's current situation"""
        political = country['political']
        focus = country['focus']
        
        context = []
        context.append(f"Country: {country['name']} ({country['tag']})")
        context.append(f"Date: {game_data['metadata']['date']}")
        context.append(f"Government Stability: {political.stability:.1f}%")
        context.append(f"Public War Support: {political.war_support:.1f}%")
        context.append(f"Ruling Party: {political.ruling_party}")
        
        # Political dynamics
        if political.party_support:
            sorted_parties = sorted(political.party_support.items(), key=lambda x: x[1], reverse=True)
            context.append(f"Political Support: {sorted_parties[0][0]} ({sorted_parties[0][1]:.1f}%)")
            if len(sorted_parties) > 1:
                context.append(f"Main Opposition: {sorted_parties[1][0]} ({sorted_parties[1][1]:.1f}%)")
        
        # Current policies
        if focus and focus.current_focus:
            context.append(f"Current Government Priority: {focus.current_focus_name}")
        
        # Recent developments
        if recent_events:
            context.append("Recent Developments:")
            for event in recent_events[-3:]:  # Last 3 events for context
                context.append(f"  - {event}")
        
        return "\n".join(context)
    
    def _get_citizen_types(self, country: Dict[str, Any], game_data: Dict[str, Any]) -> str:
        """Suggest types of citizens to interview based on country and era"""
        tag = country['tag']
        political = country['political']
        date = game_data['metadata']['date']
        
        # Base citizen types for 1930s-1940s era
        citizen_types = []
        
        # Economic situations determine citizen concerns
        if political.stability < 50:
            citizen_types.extend([
                "A factory worker concerned about job security and political unrest",
                "A shopkeeper worried about civil disorder affecting business"
            ])
        else:
            citizen_types.extend([
                "A factory worker discussing working conditions and government policies",
                "A local merchant commenting on economic conditions"
            ])
        
        # War support affects military-related perspectives
        if political.war_support > 60:
            citizen_types.append("A young man of military age discussing potential service")
        else:
            citizen_types.append("A mother worried about her sons and war preparations")
        
        # Country-specific citizen types
        if tag in ['GER', 'ITA']:  # Fascist countries
            citizen_types.extend([
                "A party member enthusiastic about recent government changes",
                "An elderly person comparing current times to the past"
            ])
        elif tag in ['SOV']:  # Communist country
            citizen_types.extend([
                "A collective farm worker discussing agricultural policies",
                "A party official explaining recent purges or policy changes"
            ])
        elif tag in ['USA', 'ENG', 'FRA']:  # Democracies
            citizen_types.extend([
                "A middle-class citizen discussing democratic values and foreign threats",
                "A veteran of the Great War sharing thoughts on current tensions"
            ])
        else:  # Other countries
            citizen_types.extend([
                "A farmer discussing how national politics affect rural life",
                "A teacher or intellectual commenting on cultural and political changes"
            ])
        
        # Add universal types
        citizen_types.extend([
            "An elderly person who remembers life before the current regime",
            "A housewife managing family concerns amid political changes"
        ])
        
        return "\n".join([f"- {citizen_type}" for citizen_type in citizen_types[:5]])  # Limit to 5
    
    def get_max_tokens(self) -> int:
        return 1500  # Longer for multiple interviews