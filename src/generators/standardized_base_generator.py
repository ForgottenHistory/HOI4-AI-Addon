#!/usr/bin/env python3
"""
Phase 4: Standardized Base Generator
Enhanced base generator using Phase 4 standardized data formats
"""

from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

# Import Phase 4 components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.data_format import (
    StandardizedGameData, StandardizedCountry, StandardizedEvent, 
    StandardizedPolitical, StandardizedFocus, EventSeverity, PoliticalSystem
)
from services.data_converter import convert_legacy_data, create_legacy_wrapper
from services import ServiceContainer


class StandardizedBaseGenerator(ABC):
    """
    Phase 4 Enhanced base generator with standardized data format support
    
    Provides:
    - Automatic data format conversion
    - Rich helper methods for data access
    - Service integration
    - Backwards compatibility
    """
    
    def __init__(self, services: Optional[ServiceContainer] = None):
        self.services = services
    
    @abstractmethod
    def generate_prompt(self, game_data: StandardizedGameData, **kwargs) -> str:
        """
        Generate prompt using standardized data format
        
        Args:
            game_data: StandardizedGameData object with consistent structure
            **kwargs: Additional generator-specific parameters
            
        Returns:
            Generated prompt string
        """
        pass
    
    @abstractmethod
    def get_max_tokens(self) -> int:
        """Return maximum tokens for this generator"""
        pass
    
    def generate_with_legacy_data(self, legacy_data: Dict[str, Any], localizer=None, **kwargs) -> str:
        """
        Generate prompt from legacy data format (backwards compatibility)
        
        Args:
            legacy_data: Legacy game_data dictionary
            localizer: Optional localizer for country names
            **kwargs: Additional parameters (recent_events, focus_countries, etc.)
            
        Returns:
            Generated prompt string
        """
        # Convert to standardized format
        standardized_data = convert_legacy_data(legacy_data, localizer, **kwargs)
        
        # Call the new standardized method
        return self.generate_prompt(standardized_data, **kwargs)
    
    # === Helper Methods for Common Data Access Patterns ===
    
    def get_major_powers(self, game_data: StandardizedGameData) -> List[StandardizedCountry]:
        """Get list of major power countries"""
        return game_data.major_powers
    
    def get_country_by_tag(self, game_data: StandardizedGameData, tag: str) -> Optional[StandardizedCountry]:
        """Get country by tag with fallback search"""
        return game_data.get_country_by_tag(tag)
    
    def get_player_country(self, game_data: StandardizedGameData) -> Optional[StandardizedCountry]:
        """Get the player's country"""
        if game_data.metadata.player_tag:
            return game_data.get_country_by_tag(game_data.metadata.player_tag)
        return None
    
    def get_recent_events(self, game_data: StandardizedGameData, limit: int = 10) -> List[StandardizedEvent]:
        """Get recent events with optional limit"""
        return game_data.recent_events[-limit:] if game_data.recent_events else []
    
    def get_events_by_severity(self, game_data: StandardizedGameData, 
                              severity: EventSeverity) -> List[StandardizedEvent]:
        """Get events filtered by severity level"""
        return [event for event in game_data.events if event.severity == severity]
    
    def get_events_by_category(self, game_data: StandardizedGameData, 
                              category: str) -> List[StandardizedEvent]:
        """Get events filtered by category"""
        return game_data.get_events_by_category(category)
    
    def get_events_involving_country(self, game_data: StandardizedGameData, 
                                   tag: str) -> List[StandardizedEvent]:
        """Get events involving a specific country"""
        return game_data.get_events_by_country(tag)
    
    def get_countries_by_ideology(self, game_data: StandardizedGameData, 
                                 ideology: PoliticalSystem) -> List[StandardizedCountry]:
        """Get countries filtered by political ideology"""
        return [country for country in game_data.countries 
                if country.political.political_system == ideology]
    
    def get_unstable_countries(self, game_data: StandardizedGameData, 
                              threshold: float = 50.0) -> List[StandardizedCountry]:
        """Get countries with stability below threshold"""
        return [country for country in game_data.countries 
                if country.political.stability < threshold]
    
    def get_war_ready_countries(self, game_data: StandardizedGameData, 
                               threshold: float = 60.0) -> List[StandardizedCountry]:
        """Get countries with war support above threshold"""
        return [country for country in game_data.countries 
                if country.political.war_support > threshold]
    
    def get_countries_with_active_focus(self, game_data: StandardizedGameData) -> List[StandardizedCountry]:
        """Get countries currently pursuing a focus"""
        return [country for country in game_data.countries 
                if country.focus and country.focus.current_focus]
    
    # === Formatting Helper Methods ===
    
    def format_event_list(self, events: List[StandardizedEvent], 
                         include_descriptions: bool = True,
                         max_description_length: int = 150) -> str:
        """Format a list of events for display"""
        if not events:
            return "No events to report."
        
        formatted = []
        for event in events:
            line = f"- {event.title}"
            
            if include_descriptions and event.description:
                desc = event.description
                if len(desc) > max_description_length:
                    desc = desc[:max_description_length] + "..."
                line += f"\n  {desc}"
            
            formatted.append(line)
        
        return "\n".join(formatted)
    
    def format_country_summary(self, country: StandardizedCountry, 
                             include_focus: bool = True) -> str:
        """Format a country summary for display"""
        lines = [f"{country.name} ({country.tag}):"]
        
        # Political situation
        pol = country.political
        lines.append(f"  Government: {pol.ruling_party} ({pol.political_system.value})")
        lines.append(f"  Stability: {pol.stability:.1f}%, War Support: {pol.war_support:.1f}%")
        lines.append(f"  Political Power: {pol.political_power:.0f}")
        
        # Focus information
        if include_focus and country.focus and country.focus.current_focus:
            focus = country.focus
            lines.append(f"  Current Focus: {focus.current_focus_name} ({focus.progress:.0f}% complete)")
        
        # Special status
        status_flags = []
        if country.is_player:
            status_flags.append("Player Nation")
        if country.is_major_power:
            status_flags.append("Major Power")
        
        if status_flags:
            lines.append(f"  Status: {', '.join(status_flags)}")
        
        return "\n".join(lines)
    
    def format_major_powers_summary(self, game_data: StandardizedGameData) -> str:
        """Format summary of all major powers"""
        major_powers = self.get_major_powers(game_data)
        if not major_powers:
            return "No major powers data available."
        
        summaries = []
        for power in major_powers:
            summaries.append(self.format_country_summary(power, include_focus=False))
        
        return "\n\n".join(summaries)
    
    def format_political_landscape(self, game_data: StandardizedGameData) -> str:
        """Format overview of global political landscape"""
        lines = [f"Global Political Situation ({game_data.metadata.date}):"]
        
        # Count by ideology
        ideology_counts = {}
        for country in game_data.major_powers:
            ideology = country.political.political_system
            ideology_counts[ideology] = ideology_counts.get(ideology, 0) + 1
        
        for ideology, count in ideology_counts.items():
            lines.append(f"  {ideology.value.title()} Powers: {count}")
        
        # Stability overview
        unstable = self.get_unstable_countries(game_data, 40.0)
        if unstable:
            unstable_names = [c.name for c in unstable[:3]]
            lines.append(f"  Countries with Low Stability: {', '.join(unstable_names)}")
            if len(unstable) > 3:
                lines.append(f"    ...and {len(unstable) - 3} others")
        
        # War readiness
        war_ready = self.get_war_ready_countries(game_data, 70.0)
        if war_ready:
            ready_names = [c.name for c in war_ready[:3]]
            lines.append(f"  War-Ready Nations: {', '.join(ready_names)}")
            if len(war_ready) > 3:
                lines.append(f"    ...and {len(war_ready) - 3} others")
        
        return "\n".join(lines)
    
    def describe_stability(self, stability: float) -> str:
        """Convert stability percentage to descriptive text"""
        if stability >= 80:
            return f"very stable ({stability:.1f}%)"
        elif stability >= 60:
            return f"stable ({stability:.1f}%)"
        elif stability >= 40:
            return f"unstable ({stability:.1f}%)"
        else:
            return f"highly unstable ({stability:.1f}%)"
    
    def describe_war_support(self, war_support: float) -> str:
        """Convert war support percentage to descriptive text"""
        if war_support >= 80:
            return f"strong war support ({war_support:.1f}%)"
        elif war_support >= 60:
            return f"moderate war support ({war_support:.1f}%)"
        elif war_support >= 40:
            return f"limited war support ({war_support:.1f}%)"
        else:
            return f"war-weary population ({war_support:.1f}%)"
    
    # === Service Integration Methods ===
    
    def get_formatted_events(self, game_data: StandardizedGameData, 
                           format_style: str = "STANDARD", limit: int = 10) -> str:
        """Get formatted events using service layer if available"""
        if self.services:
            events = self.get_recent_events(game_data, limit)
            # Convert to legacy format for service compatibility
            event_dicts = [event.to_dict() for event in events]
            return self.services.event_service.format_events(event_dicts, format_style)
        else:
            # Fallback to built-in formatting
            events = self.get_recent_events(game_data, limit)
            return self.format_event_list(events)
    
    def get_country_info(self, game_data: StandardizedGameData, tag: str) -> Optional[Dict[str, Any]]:
        """Get country info using service layer if available"""
        if self.services:
            return self.services.country_service.get_country_info(tag)
        else:
            # Fallback to direct access
            country = self.get_country_by_tag(game_data, tag)
            return country.to_dict() if country else None
    
    def get_focus_info(self, game_data: StandardizedGameData, tag: str) -> Optional[Dict[str, Any]]:
        """Get focus info using service layer if available"""  
        if self.services:
            return self.services.focus_service.get_focus_info(tag)
        else:
            # Fallback to direct access
            country = self.get_country_by_tag(game_data, tag)
            return country.focus.to_dict() if country and country.focus else None
    
    # === Legacy Compatibility ===
    
    def _ensure_standardized_data(self, game_data: Any, localizer=None, **kwargs) -> StandardizedGameData:
        """
        Ensure data is in standardized format, converting if necessary
        """
        if isinstance(game_data, StandardizedGameData):
            return game_data
        elif isinstance(game_data, dict):
            return convert_legacy_data(game_data, localizer, **kwargs)
        else:
            raise ValueError(f"Unsupported game_data type: {type(game_data)}")