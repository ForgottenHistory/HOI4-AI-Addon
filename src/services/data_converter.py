#!/usr/bin/env python3
"""
Phase 4: Data Format Conversion Utilities
Converts legacy data formats to standardized Phase 4 format
"""

from typing import Dict, List, Any, Optional, Union
from .data_format import (
    StandardizedGameData, StandardizedCountry, StandardizedPolitical,
    StandardizedFocus, StandardizedEvent, StandardizedMetadata,
    PoliticalSystem, EventSeverity,
    normalize_political_system, classify_event_severity, categorize_event
)
from .utils import get_major_power_tags, is_major_power


class DataConverter:
    """Converts legacy data formats to Phase 4 standardized format"""
    
    def __init__(self, localizer=None):
        self.localizer = localizer
        self.major_power_tags = set(get_major_power_tags())
    
    def convert_to_standardized(self, legacy_data: Dict[str, Any], **kwargs) -> StandardizedGameData:
        """
        Convert legacy game_data format to standardized format
        
        Args:
            legacy_data: Original game_data dictionary
            **kwargs: Additional parameters like recent_events, focus_countries, player_analysis
        
        Returns:
            StandardizedGameData object
        """
        # Convert metadata
        metadata = self._convert_metadata(legacy_data.get('metadata', {}))
        
        # Convert countries
        countries = self._convert_countries(legacy_data.get('countries', []))
        
        # Convert events
        events = self._convert_events(legacy_data.get('events', []))
        recent_events = self._convert_events(kwargs.get('recent_events', []))
        
        # Convert major powers (can come from different sources)
        major_powers = self._convert_major_powers(legacy_data, countries)
        
        # Handle generator-specific data
        focus_countries = self._convert_focus_countries(kwargs.get('focus_countries', []))
        player_analysis = self._convert_player_analysis(kwargs.get('player_analysis'))
        
        # Determine scope
        scope = legacy_data.get('scope', 'global')
        if focus_countries:
            scope = 'country'
        
        return StandardizedGameData(
            metadata=metadata,
            countries=countries,
            events=events,
            major_powers=major_powers,
            recent_events=recent_events,
            focus_countries=focus_countries,
            player_analysis=player_analysis,
            scope=scope
        )
    
    def _convert_metadata(self, metadata_dict: Dict[str, Any]) -> StandardizedMetadata:
        """Convert legacy metadata to standardized format"""
        return StandardizedMetadata(
            date=metadata_dict.get('date', '1936.1.1'),
            player_tag=metadata_dict.get('player') or metadata_dict.get('player_tag'),
            game_version=metadata_dict.get('game_version'),
            mod_version=metadata_dict.get('mod_version'),
            difficulty=metadata_dict.get('difficulty'),
            ironman=metadata_dict.get('ironman', False)
        )
    
    def _convert_countries(self, countries_list: List[Dict[str, Any]]) -> List[StandardizedCountry]:
        """Convert legacy countries list to standardized format"""
        standardized = []
        
        for country_dict in countries_list:
            if isinstance(country_dict, dict):
                standardized_country = self._convert_single_country(country_dict)
                if standardized_country:
                    standardized.append(standardized_country)
        
        return standardized
    
    def _convert_single_country(self, country_dict: Dict[str, Any]) -> Optional[StandardizedCountry]:
        """Convert a single country dictionary to standardized format"""
        # Handle different legacy formats
        tag = country_dict.get('tag')
        if not tag:
            return None
        
        # Get country name (with localization support)
        name = self._get_country_name(tag, country_dict)
        
        # Convert political data
        political = self._convert_political_data(country_dict)
        
        # Convert focus data
        focus = self._convert_focus_data(country_dict)
        
        # Determine special status
        is_player = country_dict.get('is_player', False)
        is_major_power_flag = country_dict.get('is_major_power', is_major_power(tag))
        
        return StandardizedCountry(
            tag=tag,
            name=name,
            political=political,
            focus=focus,
            is_player=is_player,
            is_major_power=is_major_power_flag,
            manpower=country_dict.get('manpower'),
            factories=country_dict.get('factories')
        )
    
    def _convert_political_data(self, country_dict: Dict[str, Any]) -> StandardizedPolitical:
        """Convert political data from various legacy formats"""
        # Handle nested 'data' structure or direct structure
        data_source = country_dict.get('data', country_dict)
        political_source = country_dict.get('political', data_source)
        
        # Extract stability (handle both 0-1 and 0-100 formats)
        stability = self._normalize_percentage(
            political_source.get('stability') or data_source.get('stability', 50)
        )
        
        # Extract war support
        war_support = self._normalize_percentage(
            political_source.get('war_support') or data_source.get('war_support', 50)
        )
        
        # Extract political power
        political_power = political_source.get('political_power') or data_source.get('political_power', 100)
        
        # Extract ruling party
        ruling_party = (
            political_source.get('ruling_party') or 
            data_source.get('politics', {}).get('ruling_party') or
            'Unknown'
        )
        
        # Normalize political system
        political_system = normalize_political_system(ruling_party)
        
        # Extract party support
        party_support = political_source.get('party_support', {})
        
        # Extract national ideas
        national_ideas = political_source.get('national_ideas', [])
        
        return StandardizedPolitical(
            stability=stability,
            war_support=war_support,
            political_power=political_power,
            ruling_party=ruling_party,
            political_system=political_system,
            party_support=party_support,
            national_ideas=national_ideas
        )
    
    def _convert_focus_data(self, country_dict: Dict[str, Any]) -> Optional[StandardizedFocus]:
        """Convert focus data from various legacy formats"""
        focus_source = country_dict.get('focus') or country_dict.get('focus_analysis')
        if not focus_source:
            return None
        
        return StandardizedFocus(
            current_focus=focus_source.get('current_focus'),
            current_focus_name=focus_source.get('current_focus_name'),
            current_focus_description=focus_source.get('current_focus_description'),
            progress=focus_source.get('progress', 0.0),
            is_paused=focus_source.get('is_paused', False),
            completed_count=focus_source.get('completed_count', 0),
            completed_focuses=focus_source.get('completed_focuses', []),
            completed_focus_names=focus_source.get('completed_focus_names', []),
            available_focuses=focus_source.get('available_focuses', [])
        )
    
    def _convert_events(self, events_data: Union[List[str], List[Dict[str, Any]]]) -> List[StandardizedEvent]:
        """Convert events from various legacy formats"""
        if not events_data:
            return []
        
        standardized = []
        
        for event in events_data:
            if isinstance(event, str):
                # Old string format
                std_event = StandardizedEvent(
                    title=event,
                    description="",
                    severity=classify_event_severity(event),
                    category=categorize_event(event)
                )
            elif isinstance(event, dict):
                # New dictionary format
                std_event = StandardizedEvent(
                    title=event.get('title', ''),
                    description=event.get('description', ''),
                    severity=EventSeverity(event.get('severity', 'moderate')),
                    country_tags=event.get('country_tags', []),
                    timestamp=event.get('timestamp'),
                    category=event.get('category', categorize_event(
                        event.get('title', ''), 
                        event.get('description', '')
                    ))
                )
            else:
                continue  # Skip invalid events
            
            standardized.append(std_event)
        
        return standardized
    
    def _convert_major_powers(self, legacy_data: Dict[str, Any], countries: List[StandardizedCountry]) -> List[StandardizedCountry]:
        """Extract and convert major powers from various sources"""
        # First, try explicit major_powers list
        if 'major_powers' in legacy_data:
            major_powers_data = legacy_data['major_powers']
            if isinstance(major_powers_data, list) and major_powers_data:
                if isinstance(major_powers_data[0], dict):
                    # List of country dictionaries
                    return self._convert_countries(major_powers_data)
                else:
                    # List of tags, find in countries
                    return [country for country in countries if country.tag in major_powers_data]
        
        # Otherwise, filter countries by major power status
        return [country for country in countries if country.is_major_power]
    
    def _convert_focus_countries(self, focus_countries_data: List[Dict[str, Any]]) -> List[StandardizedCountry]:
        """Convert focus_countries parameter to standardized format"""
        if not focus_countries_data:
            return []
        
        return self._convert_countries(focus_countries_data)
    
    def _convert_player_analysis(self, player_analysis_data: Optional[Dict[str, Any]]) -> Optional[StandardizedCountry]:
        """Convert player_analysis parameter to standardized format"""
        if not player_analysis_data:
            return None
        
        return self._convert_single_country(player_analysis_data)
    
    def _get_country_name(self, tag: str, country_dict: Dict[str, Any]) -> str:
        """Get localized country name with fallbacks"""
        # Try localization first
        if self.localizer:
            name = self.localizer.get_country_name(tag)
            if name and name != tag:
                return name
        
        # Fall back to data in country dict
        name = country_dict.get('name')
        if name:
            return name
        
        # Final fallback to tag
        return tag
    
    def _normalize_percentage(self, value: Union[int, float]) -> float:
        """Normalize percentage to 0-100 range"""
        if value is None:
            return 50.0  # Default value
        
        float_val = float(value)
        
        # If value is between 0-1, assume it's a ratio and convert to percentage
        if 0 <= float_val <= 1:
            return float_val * 100
        
        # If already in percentage range, use as-is
        elif 0 <= float_val <= 100:
            return float_val
        
        # Clamp to valid range
        else:
            return max(0, min(100, float_val))


class LegacyCompatibilityWrapper:
    """
    Wraps StandardizedGameData to provide legacy dictionary interface
    This allows generators to gradually migrate to the new format
    """
    
    def __init__(self, standardized_data: StandardizedGameData):
        self.standardized = standardized_data
        self._dict_cache = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert back to legacy dictionary format"""
        if self._dict_cache is None:
            self._dict_cache = self.standardized.to_dict()
        return self._dict_cache
    
    def __getitem__(self, key: str) -> Any:
        """Dictionary-style access for backwards compatibility"""
        return self.to_dict()[key]
    
    def __contains__(self, key: str) -> bool:
        """Dictionary-style membership test"""
        return key in self.to_dict()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Dictionary-style get method"""
        return self.to_dict().get(key, default)
    
    def keys(self):
        """Dictionary-style keys method"""
        return self.to_dict().keys()
    
    def items(self):
        """Dictionary-style items method"""
        return self.to_dict().items()
    
    def values(self):
        """Dictionary-style values method"""
        return self.to_dict().values()


# Convenience function for easy conversion
def convert_legacy_data(game_data: Dict[str, Any], localizer=None, **kwargs) -> StandardizedGameData:
    """
    Convenience function to convert legacy data to standardized format
    
    Args:
        game_data: Legacy game_data dictionary
        localizer: Optional localizer for country names
        **kwargs: Additional parameters (recent_events, focus_countries, etc.)
    
    Returns:
        StandardizedGameData object
    """
    converter = DataConverter(localizer)
    return converter.convert_to_standardized(game_data, **kwargs)


def create_legacy_wrapper(game_data: Dict[str, Any], localizer=None, **kwargs) -> LegacyCompatibilityWrapper:
    """
    Create a legacy-compatible wrapper around standardized data
    
    Args:
        game_data: Legacy game_data dictionary  
        localizer: Optional localizer for country names
        **kwargs: Additional parameters (recent_events, focus_countries, etc.)
    
    Returns:
        LegacyCompatibilityWrapper that behaves like a dictionary
    """
    standardized = convert_legacy_data(game_data, localizer, **kwargs)
    return LegacyCompatibilityWrapper(standardized)