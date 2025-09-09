#!/usr/bin/env python3
"""
HOI4 News Service - Generates AI-powered news reports for specific countries
Usage: python news_service.py <country_tag> [additional_tags...]
"""

import sys
import os
from pathlib import Path

# Load environment variables from .env file
def load_env_file(filepath='.env'):
    """Load environment variables from .env file"""
    env_path = Path(filepath)
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# Load .env file if it exists
load_env_file()
from game_data_loader import GameDataLoader
from localization import HOI4Localizer
from political_analyzer import PoliticalAnalyzer
from focus_analyzer import FocusAnalyzer
from event_analyzer import EventAnalyzer
from ai_analyst import HOI4AIService

class CountryNewsService:
    """Generates AI news reports focused on specific countries"""
    
    def __init__(self, json_path: str = "game_data.json"):
        # Initialize components
        self.data_loader = GameDataLoader(json_path)
        self.localizer = HOI4Localizer()
        self.localization_available = False
        
        # Try to load localization
        print("Loading HOI4 localization...")
        try:
            if self.localizer.localization_path.exists():
                self.localizer.load_all_files()
                self.localization_available = len(self.localizer.translations) > 0
                if self.localization_available:
                    print("Localization loaded successfully!")
                else:
                    print("No translations found, using country tags as fallback")
            else:
                print("HOI4 localization files not found, using tags as fallback")
        except Exception as e:
            print(f"Localization loading failed: {e}")
            print("Using country tags as fallback")
        
        # Initialize analyzers
        self.political_analyzer = PoliticalAnalyzer(self.localizer)
        self.focus_analyzer = FocusAnalyzer(self.localizer)
        self.event_analyzer = EventAnalyzer(self.localizer)
        
        # Initialize AI service
        self.ai_service = HOI4AIService()
        
        # Ensure output directory exists
        Path("news_reports").mkdir(exist_ok=True)
    
    def load_data(self) -> bool:
        """Load game data"""
        success = self.data_loader.load_data()
        if success:
            metadata = self.data_loader.get_metadata()
            player_tag = metadata['player']
            if self.localization_available:
                player_name = self.localizer.get_country_name(player_tag)
            else:
                player_name = player_tag
            print(f"Game loaded - Player: {player_name} ({player_tag}), Date: {metadata['date']}")
        return success
    
    def generate_news_report(self, country_tags: list[str], generator_type: str = 'country_news') -> str:
        """Generate a news report focused on the specified countries"""
        if not self.data_loader.is_loaded():
            return "Error: No game data loaded"
        
        metadata = self.data_loader.get_metadata()
        countries = self.data_loader.get_countries()
        
        # Validate country tags and collect country data
        valid_countries = []
        for tag in country_tags:
            tag = tag.upper()
            country_data = self.data_loader.get_country(tag)
            if country_data:
                valid_countries.append((tag, country_data))
            else:
                print(f"Warning: Country '{tag}' not found in game data")
        
        if not valid_countries:
            available_tags = sorted([c['tag'] for c in countries])[:20]
            return f"Error: No valid countries found. Available tags (first 20): {', '.join(available_tags)}"
        
        # Analyze each country to gather news-worthy events
        recent_events = []
        country_summaries = []
        
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
            
            # Create country summary for context
            country_summary = {
                'tag': tag,
                'name': country_name,
                'political': political,
                'focus': focus,
                'is_player': tag == metadata.get('player'),
                'is_major_power': tag in ['GER', 'SOV', 'USA', 'ENG', 'FRA', 'ITA', 'JAP']
            }
            country_summaries.append(country_summary)
            
            # Extract news-worthy events
            events = self._extract_newsworthy_events(country_summary, metadata)
            recent_events.extend(events)
        
        # Prepare game data for AI generation
        game_data = {
            'metadata': metadata,
            'focus_countries': country_summaries,
            'player_tag': metadata.get('player'),
        }
        
        # Generate the news report using the specified generator
        print(f"Generating news report for: {', '.join([c['name'] for c in country_summaries])}")
        print(f"Using generator: {generator_type}")
        report = self.ai_service.generate_report(
            report_type=generator_type,
            game_data=game_data,
            recent_events=recent_events,
            focus_countries=country_summaries
        )
        
        return report
    
    def _extract_newsworthy_events(self, country_summary: dict, metadata: dict) -> list[str]:
        """Extract newsworthy events from country analysis"""
        events = []
        tag = country_summary['tag']
        name = country_summary['name']
        political = country_summary['political']
        focus = country_summary['focus']
        
        # Political developments
        if political.stability < 30:
            events.append(f"{name} faces severe internal instability ({political.stability:.1f}% stability)")
        elif political.stability > 80 and political.war_support > 70:
            events.append(f"{name} shows strong national unity with {political.stability:.1f}% stability")
        
        if political.war_support > 80:
            events.append(f"War fervor rises in {name} ({political.war_support:.1f}% war support)")
        elif political.war_support < 20:
            events.append(f"Anti-war sentiment grows in {name} ({political.war_support:.1f}% war support)")
        
        # Focus tree developments
        if focus and focus.current_focus:
            events.append(f"{name} pursuing '{focus.current_focus_name}' policy ({focus.progress:.0f}% complete)")
        
        if focus and focus.completed_focus_names:
            # Recent focus completions (last 3)
            recent_focuses = focus.completed_focus_names[-3:]
            for focus_name in recent_focuses:
                events.append(f"{name} completed policy: '{focus_name}'")
        
        # Political power situation
        if political.political_power > 500:
            events.append(f"{name} government consolidates power ({political.political_power:.0f} political power)")
        elif political.political_power < 50:
            events.append(f"{name} government struggles with limited political capital")
        
        # Party dynamics
        if political.party_support:
            sorted_parties = sorted(political.party_support.items(), key=lambda x: x[1], reverse=True)
            if len(sorted_parties) > 1:
                top_party = sorted_parties[0]
                second_party = sorted_parties[1]
                if top_party[1] - second_party[1] < 10:  # Close political race
                    events.append(f"Political tensions rise in {name} as {top_party[0]} ({top_party[1]:.1f}%) faces challenge from {second_party[0]} ({second_party[1]:.1f}%)")
        
        # Special status events
        if country_summary['is_player']:
            events.append(f"{name} takes decisive action on the world stage")
        
        if country_summary['is_major_power']:
            events.append(f"Great power {name} shapes international affairs")
        
        return events
    
    def save_report(self, report: str, country_tags: list[str], metadata: dict):
        """Save the news report to a file"""
        # Create filename
        tags_str = "_".join(country_tags)
        date_str = metadata['date'].replace('.', '_')
        filename = f"news_reports/news_{tags_str}_{date_str}.txt"
        
        # Create full report content
        full_report = []
        full_report.append("=" * 70)
        full_report.append("HOI4 AI NEWS REPORT")
        full_report.append("=" * 70)
        full_report.append(f"Generated: {metadata.get('generated_at', 'Unknown')}")
        full_report.append(f"Game Date: {metadata['date']}")
        full_report.append(f"Focus Countries: {', '.join(country_tags)}")
        full_report.append("=" * 70)
        full_report.append("")
        full_report.append(report)
        full_report.append("")
        full_report.append("=" * 70)
        full_report.append("End of Report")
        full_report.append("=" * 70)
        
        # Write to file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("\n".join(full_report))
        
        return filename
    
    def list_available_generators(self):
        """List all available report generators"""
        available = self.ai_service.get_available_reports()
        print("Available generators:")
        for gen in available:
            print(f"  - {gen}")
        return available

def main():
    if len(sys.argv) < 2:
        print("Usage: python news_service.py <country_tag> [additional_tags...] [--generator=TYPE]")
        print("Example: python news_service.py GER SOV")
        print("Example: python news_service.py USA --generator=country_news")
        print("Example: python news_service.py --list-generators")
        sys.exit(1)
    
    # Handle special commands
    if '--list-generators' in sys.argv:
        service = CountryNewsService()
        service.list_available_generators()
        sys.exit(0)
    
    # Parse command line arguments
    country_tags = []
    generator_type = 'country_news'  # Default to country news generator
    
    for arg in sys.argv[1:]:
        if arg.startswith('--generator='):
            generator_type = arg.split('=')[1]
        elif not arg.startswith('--'):
            country_tags.append(arg.upper())
    
    # Initialize service
    service = CountryNewsService()
    
    if not service.load_data():
        print("Failed to load game data. Make sure game_data.json exists.")
        sys.exit(1)
    
    # Validate generator type
    available_generators = service.ai_service.get_available_reports()
    if generator_type not in available_generators:
        print(f"Error: Unknown generator '{generator_type}'")
        print(f"Available generators: {', '.join(available_generators)}")
        sys.exit(1)
    
    # Generate report
    print(f"\nGenerating news report for: {', '.join(country_tags)}")
    print("This may take a moment...")
    
    report = service.generate_news_report(country_tags, generator_type)
    
    if report.startswith("Error:"):
        print(f"\n{report}")
        sys.exit(1)
    
    # Save report
    metadata = service.data_loader.get_metadata()
    filename = service.save_report(report, country_tags, metadata)
    
    # Display results
    print(f"\n{'='*50}")
    print("NEWS REPORT GENERATED")
    print(f"{'='*50}")
    print(report)
    print(f"\n{'='*50}")
    print(f"Report saved to: {filename}")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()