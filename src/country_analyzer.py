#!/usr/bin/env python3
"""
Country Analyzer - Handles country-specific analysis and local scope reports
Focuses on individual countries, citizen perspectives, local news, etc.
"""

from typing import Dict, Any, List
from game_data_loader import GameDataLoader
from localization import HOI4Localizer
from political_analyzer import PoliticalAnalyzer
from focus_analyzer import FocusAnalyzer
from event_analyzer import EventAnalyzer
from ai_analyst import HOI4AIService

class CountryAnalyzer:
    """
    Handles analysis with country/local scope:
    - Country-specific news reports
    - Citizen interviews and perspectives
    - Local political analysis
    - Regional focus
    """
    
    def __init__(self, data_loader: GameDataLoader, localizer: HOI4Localizer, 
                 ai_service: HOI4AIService):
        self.data_loader = data_loader
        self.localizer = localizer
        self.ai_service = ai_service
        self.localization_available = len(localizer.translations) > 0 if hasattr(localizer, 'translations') else False
        
        # Initialize component analyzers
        self.political_analyzer = PoliticalAnalyzer(localizer)
        self.focus_analyzer = FocusAnalyzer(localizer)
        self.event_analyzer = EventAnalyzer(localizer)
    
    def generate_report(self, country_tags: List[str], generator_type: str) -> str:
        """Generate country-specific reports"""
        if not self.data_loader.is_loaded():
            return "Error: No game data loaded"
        
        # Validate generator type
        country_generators = ['country_news', 'citizen_interviews', 'leader_speech']
        if generator_type not in country_generators:
            available = self.ai_service.get_available_reports()
            country_available = [g for g in available if g in country_generators]
            return f"Error: '{generator_type}' is not a country generator. Available country generators: {', '.join(country_available)}"
        
        # Validate and analyze countries
        valid_countries = []
        for tag in country_tags:
            tag = tag.upper()
            country_data = self.data_loader.get_country(tag)
            if country_data:
                valid_countries.append((tag, country_data))
            else:
                print(f"⚠️  Warning: Country '{tag}' not found in game data")
        
        if not valid_countries:
            countries = self.data_loader.get_countries()
            available_tags = sorted([c['tag'] for c in countries])[:20]
            return f"Error: No valid countries found. Available tags (first 20): {', '.join(available_tags)}"
        
        # Prepare country data for AI generation
        game_data, country_summaries, recent_events = self._prepare_country_data(valid_countries)
        
        # Generate the report
        return self.ai_service.generate_report(
            generator_type,
            game_data,
            recent_events=recent_events,
            focus_countries=country_summaries
        )
    
    def _prepare_country_data(self, valid_countries: List[tuple]) -> tuple:
        """Prepare country-specific data for AI generation"""
        metadata = self.data_loader.get_metadata()
        
        # Analyze each country
        country_summaries = []
        all_events = []
        
        for tag, country_data in valid_countries:
            # Get country name
            if self.localization_available:
                country_name = self.localizer.get_country_name(tag)
                if not country_name or country_name == tag:
                    country_name = country_data.get('name', tag)
            else:
                country_name = tag
            
            # Analyze country
            political = self.political_analyzer.analyze_country(tag, country_data)
            focus = self.focus_analyzer.analyze_country_focus(tag, country_data)
            
            # Create country summary
            country_summary = {
                'tag': tag,
                'name': country_name,
                'political': political,
                'focus': focus,
                'is_player': tag == metadata.get('player'),
                'is_major_power': tag in ['GER', 'SOV', 'USA', 'ENG', 'FRA', 'ITA', 'JAP']
            }
            country_summaries.append(country_summary)
            
            # Extract newsworthy events for this country
            events = self._extract_country_events(country_summary, metadata)
            all_events.extend(events)
        
        # Prepare game data structure
        game_data = {
            'metadata': metadata,
            'focus_countries': country_summaries,
            'player_tag': metadata.get('player'),
            'scope': 'country'
        }
        
        return game_data, country_summaries, all_events
    
    def _extract_country_events(self, country_summary: Dict[str, Any], 
                               metadata: Dict[str, Any]) -> List[str]:
        """Extract newsworthy events from country analysis"""
        events = []
        tag = country_summary['tag']
        name = country_summary['name']
        political = country_summary['political']
        focus = country_summary['focus']
        
        # Political stability events
        if political.stability < 30:
            events.append(f"{name} faces severe internal instability ({political.stability:.1f}% stability)")
        elif political.stability > 85:
            events.append(f"{name} shows exceptional national unity ({political.stability:.1f}% stability)")
        elif political.stability < 50:
            events.append(f"Political tensions rise in {name} ({political.stability:.1f}% stability)")
        
        # War support events  
        if political.war_support > 80:
            events.append(f"War fervor reaches peak in {name} ({political.war_support:.1f}% war support)")
        elif political.war_support < 20:
            events.append(f"Anti-war sentiment dominates {name} ({political.war_support:.1f}% war support)")
        elif political.war_support > 60:
            events.append(f"Citizens rally behind potential conflict in {name} ({political.war_support:.1f}% war support)")
        
        # Focus tree developments
        if focus and focus.current_focus:
            progress_desc = "nearing completion" if focus.progress > 80 else f"{focus.progress:.0f}% complete"
            events.append(f"{name} pursuing '{focus.current_focus_name}' policy ({progress_desc})")
        
        # Recent focus completions
        if focus and focus.completed_focus_names:
            recent_focuses = focus.completed_focus_names[-2:]  # Last 2 completed
            for focus_name in recent_focuses:
                events.append(f"{name} completed major policy initiative: '{focus_name}'")
        
        # Political power dynamics
        if political.political_power > 600:
            events.append(f"{name} government consolidates unprecedented power ({political.political_power:.0f} political power)")
        elif political.political_power < 30:
            events.append(f"{name} government paralyzed by lack of political capital ({political.political_power:.0f} political power)")
        
        # Party competition
        if political.party_support and len(political.party_support) > 1:
            sorted_parties = sorted(political.party_support.items(), key=lambda x: x[1], reverse=True)
            top_party = sorted_parties[0]
            second_party = sorted_parties[1]
            
            if top_party[1] - second_party[1] < 15:  # Close political competition
                events.append(f"Political deadlock threatens {name} as {top_party[0]} ({top_party[1]:.1f}%) narrowly leads {second_party[0]} ({second_party[1]:.1f}%)")
            elif top_party[1] > 70:  # Dominant party
                events.append(f"{top_party[0]} achieves political dominance in {name} ({top_party[1]:.1f}% support)")
        
        # Special status events
        if country_summary['is_player']:
            events.append(f"{name} takes decisive action as player nation shapes world events")
        
        if country_summary['is_major_power']:
            events.append(f"Great power {name} influences international balance")
        
        # Economic/social indicators (inferred from political power and stability)
        if political.stability > 70 and political.political_power > 200:
            events.append(f"{name} experiences period of domestic prosperity and government effectiveness")
        elif political.stability < 40 and political.political_power < 100:
            events.append(f"{name} struggles with economic hardship and governmental crisis")
        
        return events
    
    def print_details(self, country_tag: str):
        """Print detailed analysis of a specific country"""
        if not self.data_loader.is_loaded():
            print("No data loaded")
            return
        
        country_tag = country_tag.upper()
        country_data = self.data_loader.get_country(country_tag)
        
        if not country_data:
            print(f"❌ Country '{country_tag}' not found")
            countries = self.data_loader.get_countries()
            available_tags = sorted([c['tag'] for c in countries])[:15]
            print(f"Available country tags (first 15): {', '.join(available_tags)}")
            return
        
        # Get country name
        if self.localization_available:
            country_name = self.localizer.get_country_name(country_tag)
            if not country_name or country_name == country_tag:
                country_name = country_data.get('name', country_tag)
        else:
            country_name = country_tag
        
        # Analyze country
        political = self.political_analyzer.analyze_country(country_tag, country_data)
        focus = self.focus_analyzer.analyze_country_focus(country_tag, country_data)
        
        print(f"\n" + "="*60)
        print(f"🏛️ DETAILED COUNTRY ANALYSIS: {country_name.upper()}")
        print(f"Country Tag: {country_tag}")
        
        metadata = self.data_loader.get_metadata()
        print(f"Date: {metadata['date']}")
        
        # Check if player or major power
        if country_tag == metadata.get('player'):
            print("Status: 🎮 PLAYER NATION")
        if country_tag in ['GER', 'SOV', 'USA', 'ENG', 'FRA', 'ITA', 'JAP']:
            print("Status: 🌟 MAJOR POWER")
        
        print("="*60)
        
        # Political situation
        print(f"\n📊 POLITICAL SITUATION:")
        print(f"  Stability: {political.stability:.1f}%")
        print(f"  War Support: {political.war_support:.1f}%")
        print(f"  Political Power: {political.political_power:.0f}")
        print(f"  Ruling Party: {political.ruling_party}")
        
        # Party support breakdown
        if political.party_support:
            print(f"\n🗳️ PARTY SUPPORT:")
            sorted_parties = sorted(political.party_support.items(), key=lambda x: x[1], reverse=True)
            for party, support in sorted_parties:
                print(f"  {party}: {support:.1f}%")
        
        # National ideas
        if political.national_ideas:
            print(f"\n💡 NATIONAL IDEAS:")
            for idea in political.national_ideas[:8]:  # Show first 8
                print(f"  • {idea}")
        
        # Focus tree progress
        if focus:
            print(f"\n🎯 FOCUS TREE PROGRESS:")
            print(f"  Completed Focuses: {focus.completed_count}")
            
            if focus.current_focus:
                status = f"{focus.progress:.1f}% complete" if not focus.is_paused else "⏸️ PAUSED"
                print(f"  Current Focus: {focus.current_focus_name} ({status})")
            else:
                print("  Current Focus: None active")
            
            if focus.completed_focus_names:
                recent_count = min(8, len(focus.completed_focus_names))
                print(f"  Recent Completed ({recent_count}):")
                for focus_name in focus.completed_focus_names[-recent_count:]:
                    print(f"    • {focus_name}")
        else:
            print(f"\n🎯 FOCUS TREE PROGRESS:")
            print("  No focus tree activity detected")
        
        print("\n" + "="*60)