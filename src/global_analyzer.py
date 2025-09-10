#!/usr/bin/env python3
"""
Global Analyzer - Handles world-wide analysis and global scope reports
Focuses on major powers, worldwide events, diplomatic situation, etc.
"""

from typing import Dict, Any
from game_data_loader import GameDataLoader
from localization import HOI4Localizer
from political_analyzer import PoliticalAnalyzer
from focus_analyzer import FocusAnalyzer
from event_analyzer import EventAnalyzer
from ai_analyst import HOI4AIService
# Import services for consolidated functionality
import sys
import os
sys.path.append(os.path.dirname(__file__))
from services import ServiceContainer
from services.utils import get_major_power_tags, has_dynamic_text

class GlobalAnalyzer:
    """
    Handles analysis with global scope:
    - World situation reports
    - Major power analysis  
    - Diplomatic intelligence
    - Global news and events
    """
    
    def __init__(self, data_loader: GameDataLoader, localizer: HOI4Localizer, 
                 ai_service: HOI4AIService):
        self.data_loader = data_loader
        self.localizer = localizer
        self.ai_service = ai_service
        
        # Initialize component analyzers
        self.political_analyzer = PoliticalAnalyzer(localizer)
        self.focus_analyzer = FocusAnalyzer(localizer)
        self.event_analyzer = EventAnalyzer(localizer)
        
        # Initialize service container for consolidated functionality
        self.services = ServiceContainer.create_from_existing_components(
            localizer=localizer,
            game_data_loader=data_loader,
            event_analyzer=self.event_analyzer,
            focus_analyzer=self.focus_analyzer,
            political_analyzer=self.political_analyzer
        )
    
    def generate_report(self, generator_type: str, verbose: bool = False) -> str:
        """Generate global scope reports"""
        if not self.data_loader.is_loaded():
            return "Error: No game data loaded"
        
        # Validate generator type
        global_generators = ['intelligence', 'news', 'twitter', 'adviser']
        if generator_type not in global_generators:
            available = self.ai_service.get_available_reports()
            return f"Error: '{generator_type}' is not a global generator. Available global generators: {', '.join(global_generators)}"
        
        # Prepare global game data
        game_data = self._prepare_global_data()
        
        # Handle special cases
        if generator_type == 'adviser':
            return self._generate_adviser_report(game_data)
        
        # Standard global reports
        kwargs = {}
        if generator_type in ['news', 'twitter']:
            # Use the rich event data with descriptions
            kwargs['recent_events'] = game_data['recent_events']
        
        return self.ai_service.generate_report(generator_type, game_data, verbose=verbose, **kwargs)
    
    def _prepare_global_data(self) -> Dict[str, Any]:
        """Prepare global game data for AI generation"""
        metadata = self.data_loader.get_metadata()
        
        # Analyze major powers with focus descriptions
        major_powers = self._analyze_major_powers_with_descriptions()
        
        # Get global events with descriptions
        events = self.data_loader.get_events()
        recent_events_with_descriptions = self._prepare_events_with_descriptions(events)
        
        # Get focus activity
        countries = self.data_loader.get_countries()
        focus_leaders = self.focus_analyzer.get_focus_leaders(countries, min_completed=3)
        
        return {
            'metadata': metadata,
            'major_powers': major_powers,
            'recent_events': recent_events_with_descriptions[-10:],  # Last 10 events
            'focus_leaders': focus_leaders[:10],   # Top 10 active nations
            'total_countries': len(countries),
            'scope': 'global'
        }
    
    def _analyze_major_powers(self) -> list[Dict[str, Any]]:
        """Analyze all major powers for global context"""
        major_tags = list(get_major_power_tags())
        major_powers = []
        
        for tag in major_tags:
            country_data = self.data_loader.get_country(tag)
            if country_data:
                political = self.political_analyzer.analyze_country(tag, country_data)
                focus = self.focus_analyzer.analyze_country_focus(tag, country_data)
                
                power_analysis = {
                    'tag': tag,
                    'name': political.name,
                    'stability': political.stability,
                    'war_support': political.war_support,
                    'ruling_party': political.ruling_party,
                    'political_power': political.political_power,
                    'party_support': political.party_support,
                    'national_ideas': political.national_ideas
                }
                
                if focus:
                    power_analysis['focus'] = {
                        'current_focus': focus.current_focus_name,
                        'progress': focus.progress,
                        'completed_count': focus.completed_count,
                        'recent_completed': focus.completed_focus_names[-3:] if focus.completed_focus_names else []
                    }
                
                major_powers.append(power_analysis)
        
        return major_powers
    
    def _analyze_major_powers_with_descriptions(self) -> list[Dict[str, Any]]:
        """Analyze all major powers with focus descriptions for AI generation"""
        major_tags = list(get_major_power_tags())
        major_powers = []
        
        for tag in major_tags:
            country_data = self.data_loader.get_country(tag)
            if country_data:
                political = self.political_analyzer.analyze_country(tag, country_data)
                focus = self.focus_analyzer.analyze_country_focus(tag, country_data)
                
                power_analysis = {
                    'tag': tag,
                    'name': political.name,
                    'stability': political.stability,
                    'war_support': political.war_support,
                    'ruling_party': political.ruling_party,
                    'political_power': political.political_power,
                    'party_support': political.party_support,
                    'national_ideas': political.national_ideas
                }
                
                if focus:
                    power_analysis['focus'] = {
                        'current_focus': focus.current_focus_name,
                        'current_focus_description': self.focus_analyzer.get_focus_description(focus.current_focus, truncate=False) if focus.current_focus else "",
                        'progress': focus.progress,
                        'completed_count': focus.completed_count,
                        'recent_completed': focus.completed_focus_names[-3:] if focus.completed_focus_names else []
                    }
                
                major_powers.append(power_analysis)
        
        return major_powers
    
    def _prepare_events_with_descriptions(self, events: list[str]) -> list[Dict[str, str]]:
        """Prepare events with descriptions for AI generation"""
        events_with_descriptions = []
        clean_events_with_raw = self.event_analyzer.get_clean_events_with_raw(events)
        
        for clean_event, raw_event in clean_events_with_raw:
            description = self.event_analyzer._get_event_description(raw_event, truncate=False)
            
            event_data = {
                'title': clean_event,
                'description': description if description and not has_dynamic_text(description) else ""
            }
            events_with_descriptions.append(event_data)
        
        return events_with_descriptions
    
    def _generate_adviser_report(self, game_data: Dict[str, Any]) -> str:
        """Generate player-specific adviser report"""
        player_tag = self.data_loader.get_player_tag()
        country_data = self.data_loader.get_country(player_tag)
        
        if not country_data:
            return "Error: No player data available for adviser report"
        
        # Analyze player country in detail
        political = self.political_analyzer.analyze_country(player_tag, country_data)
        focus = self.focus_analyzer.analyze_country_focus(player_tag, country_data)
        
        # Prepare player-specific data
        player_analysis = {
            'tag': political.tag,
            'name': political.name,
            'stability': political.stability,
            'war_support': political.war_support,
            'ruling_party': political.ruling_party,
            'political_power': political.political_power,
            'party_support': political.party_support,
            'national_ideas': political.national_ideas
        }
        
        if focus:
            player_analysis['focus_analysis'] = {
                'current_focus': focus.current_focus_name,
                'progress': focus.progress,
                'completed_count': focus.completed_count,
                'recent_completed': focus.completed_focus_names[-3:] if focus.completed_focus_names else []
            }
        
        return self.ai_service.generate_report('adviser', game_data, player_analysis=player_analysis)
    
    def print_summary(self, verbose: bool = False):
        """Print comprehensive world situation summary"""
        if not self.data_loader.is_loaded():
            print("No data loaded")
            return
        
        metadata = self.data_loader.get_metadata()
        
        print("\n" + "="*60)
        print("🌍 HOI4 WORLD SITUATION REPORT")
        print("="*60)
        
        print(f"📅 Date: {metadata['date']}")
        player_name = self.localizer.get_country_name(metadata['player']) if hasattr(self.localizer, 'get_country_name') else metadata['player']
        print(f"🎮 Player Nation: {player_name} ({metadata['player']})")
        
        # Recent events
        self._print_events_section(verbose=verbose)
        
        # Major powers
        self._print_major_powers_section(verbose=verbose)
        
        print("="*60)
    
    def _print_events_section(self, verbose: bool = False):
        """Print recent global events section"""
        events = self.data_loader.get_events()
        
        print(f"\n📰 RECENT GLOBAL EVENTS:")
        clean_events_with_raw = self.event_analyzer.get_clean_events_with_raw(events)
        if clean_events_with_raw:
            for i, (clean_event, raw_event) in enumerate(clean_events_with_raw[-10:], 1):
                print(f"  {i:2}. {clean_event}")
                
                # Get event description (truncated for regular mode, full for verbose)
                description = self.event_analyzer._get_event_description(raw_event, truncate=not verbose)
                if description and not has_dynamic_text(description):
                    print(f"      {description}")
                if verbose:
                    print()  # Extra line between events in verbose mode
        else:
            print("  No major events to report")
    
    def _print_major_powers_section(self, verbose: bool = False):
        """Print major powers status section"""
        print(f"\n🏛️ MAJOR POWER STATUS:")
        major_tags = list(get_major_power_tags())
        
        for tag in major_tags:
            country_data = self.data_loader.get_country(tag)
            if country_data:
                # Political analysis
                political = self.political_analyzer.analyze_country(tag, country_data)
                print(f"  {self.political_analyzer.format_summary_line(political)}")
                
                # Focus analysis
                focus = self.focus_analyzer.analyze_country_focus(tag, country_data)
                if focus:
                    if verbose:
                        focus_summary = self.focus_analyzer.format_focus_summary_verbose(focus)
                        print(f"    🎯 Focus: {focus_summary}")
                    else:
                        # Regular mode now shows descriptions (truncated)
                        focus_summary = self.focus_analyzer.format_focus_summary(focus, show_description=True)
                        print(f"    🎯 Focus: {focus_summary}")
                
                if verbose:
                    print()  # Extra spacing in verbose mode
    