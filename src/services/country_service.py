#!/usr/bin/env python3
"""
Country Service  
Centralized country information retrieval and formatting
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from .utils import is_major_power, get_major_power_tags, format_percentage


@dataclass
class CountryInfo:
    """Data transfer object for country information"""
    tag: str
    name: str
    display_name: str  # Name with ideology/context
    ideology: str
    ruling_party: str
    stability: float
    war_support: float
    political_power: float
    is_major: bool
    is_player: bool
    raw_data: Dict[str, Any]  # Original country data for advanced access


class CountryService:
    """Centralized service for country data access and formatting"""
    
    def __init__(self, localizer, game_data_loader=None, political_analyzer=None):
        """
        Initialize CountryService
        
        Args:
            localizer: HOI4Localizer instance for name resolution
            game_data_loader: Optional GameDataLoader for direct data access
            political_analyzer: Optional PoliticalAnalyzer for legacy support
        """
        self.localizer = localizer
        self.game_data_loader = game_data_loader
        self.political_analyzer = political_analyzer
        
        # Major power tags from shared utilities
        self.major_power_tags = get_major_power_tags()
    
    def get_country_info(self, tag: str, game_data: Optional[Dict[str, Any]] = None, 
                        country_data: Optional[Dict[str, Any]] = None) -> Optional[CountryInfo]:
        """
        Get comprehensive country information
        
        Args:
            tag: Country tag (e.g., 'GER', 'USA')
            game_data: Optional game data dict (for player detection)
            country_data: Optional specific country data dict
            
        Returns:
            CountryInfo object or None if country not found
        """
        # Get country data if not provided
        if not country_data:
            if self.game_data_loader:
                country_data = self.game_data_loader.get_country(tag)
            elif game_data and 'countries' in game_data:
                for country in game_data['countries']:
                    if country['tag'] == tag:
                        country_data = country['data']
                        break
            
            if not country_data:
                return None
        
        # Extract basic political info
        politics = country_data.get('politics', {})
        ruling_party = politics.get('ruling_party', 'Unknown')
        
        # Get country names
        basic_name = self.get_country_name(tag)
        display_name = self.get_country_name(tag, ruling_party)
        
        # Determine if player
        is_player = False
        if game_data:
            player_tag = game_data.get('metadata', {}).get('player') or game_data.get('player_tag')
            is_player = (tag == player_tag)
        
        # Check if major power
        is_major = is_major_power(tag)
        if not is_major and country_data.get('major', False):
            is_major = True
        
        return CountryInfo(
            tag=tag,
            name=basic_name,
            display_name=display_name,
            ideology=ruling_party,
            ruling_party=ruling_party,
            stability=country_data.get('stability', 0) * 100,
            war_support=country_data.get('war_support', 0) * 100,
            political_power=politics.get('political_power', 0),
            is_major=is_major,
            is_player=is_player,
            raw_data=country_data
        )
    
    def get_countries_info(self, tags: List[str], game_data: Dict[str, Any]) -> List[CountryInfo]:
        """
        Get information for multiple countries
        
        Args:
            tags: List of country tags
            game_data: Game data dictionary
            
        Returns:
            List of CountryInfo objects (excludes countries not found)
        """
        countries = []
        for tag in tags:
            country_info = self.get_country_info(tag, game_data)
            if country_info:
                countries.append(country_info)
        return countries
    
    def get_major_powers_info(self, game_data: Dict[str, Any]) -> List[CountryInfo]:
        """
        Get information for all major powers in the game
        
        Args:
            game_data: Game data dictionary
            
        Returns:
            List of CountryInfo objects for major powers
        """
        major_powers = []
        
        # Check if game_data has processed major_powers
        if 'major_powers' in game_data:
            for power in game_data['major_powers']:
                tag = power.get('tag')
                if tag:
                    # Create country info from major_powers data
                    country_info = CountryInfo(
                        tag=tag,
                        name=power.get('name', tag),
                        display_name=power.get('name', tag),
                        ideology=power.get('ruling_party', 'Unknown'),
                        ruling_party=power.get('ruling_party', 'Unknown'),
                        stability=power.get('stability', 0),  # Already as percentage
                        war_support=power.get('war_support', 0),  # Already as percentage  
                        political_power=0,  # Not available in major_powers format
                        is_major=True,
                        is_player=(tag == game_data.get('metadata', {}).get('player')),
                        raw_data=power
                    )
                    major_powers.append(country_info)
        else:
            # Fall back to scanning all countries
            countries = game_data.get('countries', [])
            for country in countries:
                tag = country['tag']
                if tag in self.major_power_tags:
                    country_info = self.get_country_info(tag, game_data, country['data'])
                    if country_info:
                        major_powers.append(country_info)
        
        return major_powers
    
    def get_country_name(self, tag: str, ideology: Optional[str] = None) -> str:
        """
        Get country name with consistent fallback handling
        
        Args:
            tag: Country tag
            ideology: Optional ideology for ideological country names
            
        Returns:
            Localized country name or cleaned tag as fallback
        """
        return self.localizer.get_country_name(tag, ideology)
    
    def format_country_summary(self, country: CountryInfo, style: str = 'standard') -> str:
        """
        Format country information for display
        
        Args:
            country: CountryInfo object
            style: Format style ('standard', 'brief', 'detailed')
            
        Returns:
            Formatted country summary string
        """
        if style == 'brief':
            return f"{country.display_name} ({country.tag})"
        elif style == 'detailed':
            lines = [
                f"{country.display_name} ({country.tag})",
                f"  Government: {country.ruling_party}",
                f"  Stability: {country.stability:.1f}%",
                f"  War Support: {country.war_support:.1f}%",
                f"  Political Power: {country.political_power:.0f}"
            ]
            if country.is_player:
                lines.append("  Status: Player Nation")
            if country.is_major:
                lines.append("  Status: Major Power")
            return "\n".join(lines)
        else:  # standard
            status_flags = []
            if country.is_player:
                status_flags.append("Player")
            if country.is_major:
                status_flags.append("Major")
            
            status_str = f" [{', '.join(status_flags)}]" if status_flags else ""
            return (f"{country.display_name:15} | {country.ruling_party:12} | "
                   f"Stability: {country.stability:5.1f}% | "
                   f"War Support: {country.war_support:5.1f}%{status_str}")
    
    def get_countries_by_ideology(self, countries: List[CountryInfo]) -> Dict[str, List[CountryInfo]]:
        """
        Group countries by their ruling ideology
        
        Args:
            countries: List of CountryInfo objects
            
        Returns:
            Dictionary mapping ideology names to country lists
        """
        by_ideology = {}
        for country in countries:
            ideology = country.ideology.lower()
            if 'democratic' in ideology:
                key = 'Democratic'
            elif 'fascism' in ideology or 'fascist' in ideology:
                key = 'Fascist'
            elif 'communism' in ideology or 'communist' in ideology:
                key = 'Communist'
            else:
                key = 'Other'
            
            if key not in by_ideology:
                by_ideology[key] = []
            by_ideology[key].append(country)
        
        return by_ideology
    
    def find_country_by_name(self, name: str, game_data: Dict[str, Any]) -> Optional[CountryInfo]:
        """
        Find country by localized name (fuzzy matching)
        
        Args:
            name: Country name to search for
            game_data: Game data dictionary
            
        Returns:
            CountryInfo if found, None otherwise
        """
        countries = game_data.get('countries', [])
        name_lower = name.lower()
        
        for country in countries:
            tag = country['tag']
            country_name = self.get_country_name(tag).lower()
            
            if name_lower in country_name or country_name in name_lower:
                return self.get_country_info(tag, game_data, country['data'])
        
        return None