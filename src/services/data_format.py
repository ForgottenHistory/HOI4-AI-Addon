#!/usr/bin/env python3
"""
Phase 4: Standardized Data Format Schema
Defines consistent data structures for all generators and analyzers
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum


class EventSeverity(Enum):
    """Standardized event severity levels"""
    LOW = "low"
    MODERATE = "moderate" 
    HIGH = "high"
    CRITICAL = "critical"


class PoliticalSystem(Enum):
    """Standardized political system types"""
    DEMOCRATIC = "democratic"
    FASCIST = "fascist"
    COMMUNIST = "communist"
    NEUTRALITY = "neutrality"
    MONARCHIST = "monarchist"


@dataclass
class StandardizedEvent:
    """Standardized event format for all generators"""
    title: str
    description: str = ""
    severity: EventSeverity = EventSeverity.MODERATE
    country_tags: List[str] = field(default_factory=list)
    timestamp: Optional[str] = None
    category: str = "general"  # political, military, economic, diplomatic
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backwards compatibility"""
        return {
            'title': self.title,
            'description': self.description,
            'severity': self.severity.value,
            'country_tags': self.country_tags,
            'timestamp': self.timestamp,
            'category': self.category
        }


@dataclass
class StandardizedPolitical:
    """Standardized political information"""
    stability: float  # 0-100 percentage
    war_support: float  # 0-100 percentage
    political_power: float
    ruling_party: str
    political_system: PoliticalSystem
    party_support: Dict[str, float] = field(default_factory=dict)  # party -> percentage
    national_ideas: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backwards compatibility"""
        return {
            'stability': self.stability,
            'war_support': self.war_support,
            'political_power': self.political_power,
            'ruling_party': self.ruling_party,
            'political_system': self.political_system.value,
            'party_support': self.party_support,
            'national_ideas': self.national_ideas
        }


@dataclass
class StandardizedFocus:
    """Standardized focus tree information"""
    current_focus: Optional[str] = None
    current_focus_name: Optional[str] = None  # Localized name
    current_focus_description: Optional[str] = None
    progress: float = 0.0  # 0-100 percentage
    is_paused: bool = False
    completed_count: int = 0
    completed_focuses: List[str] = field(default_factory=list)  # IDs
    completed_focus_names: List[str] = field(default_factory=list)  # Localized names
    available_focuses: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backwards compatibility"""
        return {
            'current_focus': self.current_focus,
            'current_focus_name': self.current_focus_name,
            'current_focus_description': self.current_focus_description,
            'progress': self.progress,
            'is_paused': self.is_paused,
            'completed_count': self.completed_count,
            'completed_focuses': self.completed_focuses,
            'completed_focus_names': self.completed_focus_names,
            'available_focuses': self.available_focuses
        }


@dataclass
class StandardizedCountry:
    """Standardized country information for all generators"""
    tag: str
    name: str  # Localized name
    political: StandardizedPolitical
    focus: Optional[StandardizedFocus] = None
    is_player: bool = False
    is_major_power: bool = False
    # Economic indicators (for future expansion)
    manpower: Optional[float] = None
    factories: Optional[Dict[str, int]] = None  # civilian, military, naval
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backwards compatibility"""
        result = {
            'tag': self.tag,
            'name': self.name,
            'political': self.political.to_dict() if isinstance(self.political, StandardizedPolitical) else self.political,
            'is_player': self.is_player,
            'is_major_power': self.is_major_power
        }
        
        if self.focus:
            result['focus'] = self.focus.to_dict() if isinstance(self.focus, StandardizedFocus) else self.focus
        
        if self.manpower is not None:
            result['manpower'] = self.manpower
        
        if self.factories:
            result['factories'] = self.factories
            
        return result


@dataclass
class StandardizedMetadata:
    """Standardized metadata for all game data"""
    date: str
    player_tag: Optional[str] = None
    game_version: Optional[str] = None
    mod_version: Optional[str] = None
    difficulty: Optional[str] = None
    ironman: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backwards compatibility"""
        return {
            'date': self.date,
            'player': self.player_tag,  # Legacy field name
            'player_tag': self.player_tag,
            'game_version': self.game_version,
            'mod_version': self.mod_version,
            'difficulty': self.difficulty,
            'ironman': self.ironman
        }


@dataclass  
class StandardizedGameData:
    """Master standardized data structure for all generators"""
    metadata: StandardizedMetadata
    countries: List[StandardizedCountry] = field(default_factory=list)
    events: List[StandardizedEvent] = field(default_factory=list)
    major_powers: List[StandardizedCountry] = field(default_factory=list)  # Subset of countries
    recent_events: List[StandardizedEvent] = field(default_factory=list)  # Last N events
    
    # Generator-specific data (optional)
    focus_countries: List[StandardizedCountry] = field(default_factory=list)  # For country-focused generators
    player_analysis: Optional[StandardizedCountry] = None  # For adviser generator
    scope: str = "global"  # global, country, regional
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to legacy dictionary format for backwards compatibility"""
        result = {
            'metadata': self.metadata.to_dict() if isinstance(self.metadata, StandardizedMetadata) else self.metadata,
            'countries': [c.to_dict() if isinstance(c, StandardizedCountry) else c for c in self.countries],
            'events': [e.to_dict() if isinstance(e, StandardizedEvent) else e for e in self.events],
            'major_powers': [c.to_dict() if isinstance(c, StandardizedCountry) else c for c in self.major_powers],
            'recent_events': [e.to_dict() if isinstance(e, StandardizedEvent) else e for e in self.recent_events],
            'scope': self.scope
        }
        
        # Add generator-specific fields only if they have data
        if self.focus_countries:
            result['focus_countries'] = [c.to_dict() if isinstance(c, StandardizedCountry) else c for c in self.focus_countries]
        
        if self.player_analysis:
            result['player_analysis'] = self.player_analysis.to_dict() if isinstance(self.player_analysis, StandardizedCountry) else self.player_analysis
        
        return result
    
    def get_country_by_tag(self, tag: str) -> Optional[StandardizedCountry]:
        """Get a country by tag from any list"""
        tag = tag.upper()
        
        # Check focus countries first (most specific)
        for country in self.focus_countries:
            if country.tag == tag:
                return country
        
        # Check major powers
        for country in self.major_powers:
            if country.tag == tag:
                return country
        
        # Check all countries
        for country in self.countries:
            if country.tag == tag:
                return country
        
        return None
    
    def get_major_power_tags(self) -> List[str]:
        """Get list of major power tags"""
        return [country.tag for country in self.major_powers]
    
    def get_events_by_country(self, tag: str) -> List[StandardizedEvent]:
        """Get events involving a specific country"""
        tag = tag.upper()
        return [event for event in self.events if tag in event.country_tags]
    
    def get_events_by_category(self, category: str) -> List[StandardizedEvent]:
        """Get events by category"""
        return [event for event in self.events if event.category == category]


# Utility functions for data conversion
def normalize_political_system(party_name: str) -> PoliticalSystem:
    """Convert party name to standardized political system"""
    party_lower = party_name.lower()
    
    if any(term in party_lower for term in ['fascism', 'fascist', 'nazi', 'nationalist']):
        return PoliticalSystem.FASCIST
    elif any(term in party_lower for term in ['communism', 'communist', 'socialist', 'marxist']):
        return PoliticalSystem.COMMUNIST
    elif any(term in party_lower for term in ['democratic', 'liberal', 'republic']):
        return PoliticalSystem.DEMOCRATIC
    elif any(term in party_lower for term in ['monarchist', 'monarchy', 'royalist']):
        return PoliticalSystem.MONARCHIST
    else:
        return PoliticalSystem.NEUTRALITY


def classify_event_severity(title: str, description: str = "") -> EventSeverity:
    """Classify event severity based on content"""
    text = (title + " " + description).lower()
    
    if any(term in text for term in ['war', 'invasion', 'coup', 'revolution', 'crisis', 'collapse']):
        return EventSeverity.CRITICAL
    elif any(term in text for term in ['tension', 'conflict', 'mobilization', 'sanctions']):
        return EventSeverity.HIGH
    elif any(term in text for term in ['policy', 'election', 'negotiation', 'agreement']):
        return EventSeverity.MODERATE
    else:
        return EventSeverity.LOW


def categorize_event(title: str, description: str = "") -> str:
    """Categorize event based on content"""
    text = (title + " " + description).lower()
    
    if any(term in text for term in ['military', 'army', 'navy', 'war', 'battle', 'invasion']):
        return "military"
    elif any(term in text for term in ['diplomatic', 'treaty', 'ambassador', 'negotiation']):
        return "diplomatic"  
    elif any(term in text for term in ['economic', 'trade', 'factory', 'production', 'industrial']):
        return "economic"
    elif any(term in text for term in ['political', 'party', 'election', 'government', 'policy']):
        return "political"
    else:
        return "general"