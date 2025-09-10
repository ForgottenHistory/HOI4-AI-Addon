#!/usr/bin/env python3
"""
Data Transfer Objects (DTOs)
Common data structures used across the service layer
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

# Re-export DTOs from individual service files for convenience
from .event_service import EventInfo, EventFormatStyle
from .country_service import CountryInfo
from .focus_service import FocusInfo, FocusFormatStyle


@dataclass 
class GameContext:
    """Comprehensive game context combining all major data sources"""
    metadata: Dict[str, Any]
    player_tag: Optional[str]
    date: str
    events: List[EventInfo]
    major_powers: List[CountryInfo]
    all_countries: List[CountryInfo]
    active_focuses: List[FocusInfo]
    focus_leaders: List[FocusInfo]
    
    def get_country(self, tag: str) -> Optional[CountryInfo]:
        """Get specific country by tag"""
        for country in self.all_countries:
            if country.tag == tag:
                return country
        return None
    
    def get_major_powers_by_ideology(self) -> Dict[str, List[CountryInfo]]:
        """Group major powers by ideology"""
        ideologies = {}
        for power in self.major_powers:
            ideology = power.ideology.lower()
            if 'democratic' in ideology:
                key = 'Democratic'
            elif 'fascism' in ideology or 'fascist' in ideology:
                key = 'Fascist'
            elif 'communism' in ideology or 'communist' in ideology:
                key = 'Communist'
            else:
                key = 'Other'
            
            if key not in ideologies:
                ideologies[key] = []
            ideologies[key].append(power)
        
        return ideologies
    
    def get_player_country(self) -> Optional[CountryInfo]:
        """Get player country info"""
        if self.player_tag:
            return self.get_country(self.player_tag)
        return None


@dataclass
class GeneratorContext:
    """Context data specifically prepared for generator use"""
    game_context: GameContext
    recent_events: List[EventInfo]
    focus_countries: List[CountryInfo]  # Countries specifically relevant to this generator
    scope: str  # 'global', 'country', 'region', etc.
    generator_specific_data: Dict[str, Any]  # Additional data specific to the generator type
    
    def get_events_formatted(self, style: EventFormatStyle = EventFormatStyle.STANDARD, 
                           verbose: bool = False, limit: int = 8) -> str:
        """Get formatted events for this context"""
        from .event_service import EventService
        event_service = EventService()
        events_to_format = self.recent_events[-limit:] if self.recent_events else []
        return event_service.format_events(events_to_format, style, verbose)
    
    def get_country_summaries(self, style: str = 'standard') -> List[str]:
        """Get formatted country summaries"""
        summaries = []
        for country in self.focus_countries:
            # This would need CountryService but we avoid circular imports
            summaries.append(f"{country.display_name} ({country.tag})")
        return summaries


class AnalysisScope(Enum):
    """Scope levels for analysis and generation"""
    GLOBAL = "global"           # World-wide perspective
    REGIONAL = "regional"       # Regional/continental focus  
    COUNTRY = "country"         # Single country focus
    LOCAL = "local"             # Sub-national/local perspective
    COMPARATIVE = "comparative"  # Comparing multiple entities


@dataclass
class AnalysisRequest:
    """Request object for analysis operations"""
    scope: AnalysisScope
    target_countries: List[str]  # Country tags
    focus_areas: List[str]       # Areas of focus (politics, military, economy, etc.)
    time_period: Optional[str]   # Specific time period if relevant
    depth: str                   # 'brief', 'standard', 'detailed', 'comprehensive'
    include_context: bool = True # Whether to include contextual information
    filter_sensitive: bool = True # Whether to filter out sensitive/dynamic content
    
    def is_single_country(self) -> bool:
        """Check if this is a single country analysis"""
        return len(self.target_countries) == 1
    
    def is_major_powers_focus(self) -> bool:
        """Check if analysis focuses on major powers"""
        major_tags = {'GER', 'SOV', 'USA', 'ENG', 'FRA', 'ITA', 'JAP'}
        return any(tag in major_tags for tag in self.target_countries)


# Utility functions for working with DTOs

def create_game_context_from_data(game_data: Dict[str, Any], event_service, 
                                 country_service, focus_service) -> GameContext:
    """
    Factory function to create GameContext from raw game data
    
    Args:
        game_data: Raw game data dictionary
        event_service: EventService instance
        country_service: CountryService instance  
        focus_service: FocusService instance
        
    Returns:
        GameContext object
    """
    metadata = game_data.get('metadata', {})
    player_tag = metadata.get('player')
    date = metadata.get('date', 'Unknown')
    
    # Extract events
    events = event_service.get_events_from_game_data(game_data)
    
    # Extract major powers
    major_powers = country_service.get_major_powers_info(game_data)
    
    # Get all countries (sample for performance)
    all_countries = []
    countries_data = game_data.get('countries', [])[:50]  # Limit for performance
    for country in countries_data:
        country_info = country_service.get_country_info(
            country['tag'], game_data, country['data']
        )
        if country_info:
            all_countries.append(country_info)
    
    # Get focus information
    active_focuses = focus_service.get_active_focuses(countries_data)
    focus_leaders = focus_service.get_focus_leaders(countries_data)
    
    return GameContext(
        metadata=metadata,
        player_tag=player_tag,
        date=date,
        events=events,
        major_powers=major_powers,
        all_countries=all_countries,
        active_focuses=active_focuses,
        focus_leaders=focus_leaders
    )


def create_generator_context(game_context: GameContext, target_countries: List[str] = None,
                           scope: str = 'global', recent_events_limit: int = 8,
                           **generator_data) -> GeneratorContext:
    """
    Create generator context from game context
    
    Args:
        game_context: GameContext object
        target_countries: Optional list of country tags to focus on
        scope: Analysis scope
        recent_events_limit: Number of recent events to include
        **generator_data: Additional generator-specific data
        
    Returns:
        GeneratorContext object
    """
    # Get recent events
    recent_events = game_context.events[-recent_events_limit:] if game_context.events else []
    
    # Get focus countries
    focus_countries = []
    if target_countries:
        for tag in target_countries:
            country = game_context.get_country(tag)
            if country:
                focus_countries.append(country)
    else:
        # Default to major powers for global scope
        focus_countries = game_context.major_powers
    
    return GeneratorContext(
        game_context=game_context,
        recent_events=recent_events,
        focus_countries=focus_countries,
        scope=scope,
        generator_specific_data=generator_data
    )


# Export all DTOs and enums for convenience
__all__ = [
    'EventInfo', 'EventFormatStyle',
    'CountryInfo', 
    'FocusInfo', 'FocusFormatStyle',
    'GameContext', 'GeneratorContext', 
    'AnalysisScope', 'AnalysisRequest',
    'create_game_context_from_data', 'create_generator_context'
]