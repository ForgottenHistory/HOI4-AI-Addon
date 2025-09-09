#!/usr/bin/env python3
"""
HOI4 Country-Specific Analyzer - Analyzes each country individually
Writes detailed analysis for each country to separate files in ./countries/
"""

import sys
import os
from pathlib import Path
from localization import HOI4Localizer
from game_data_loader import GameDataLoader
from political_analyzer import PoliticalAnalyzer
from focus_analyzer import FocusAnalyzer
from event_analyzer import EventAnalyzer

class HOI4CountryAnalyzer:
    def __init__(self, json_path: str = "game_data.json"):
        # Initialize components
        self.data_loader = GameDataLoader(json_path)
        self.localizer = HOI4Localizer()
        self.localization_available = False
        
        # Try to load localization (gracefully handle failure)
        print("Attempting to load HOI4 localization...")
        try:
            if self.localizer.localization_path.exists():
                self.localizer.load_all_files()
                self.localization_available = len(self.localizer.translations) > 0
                if self.localization_available:
                    print("Localization ready!\n")
                else:
                    print("No translations loaded, using IDs as fallback\n")
            else:
                print("HOI4 localization files not found, using IDs as fallback\n")
        except Exception as e:
            print(f"Failed to load localization: {e}")
            print("Using IDs as fallback\n")
        
        # Initialize analyzers
        self.political_analyzer = PoliticalAnalyzer(self.localizer)
        self.focus_analyzer = FocusAnalyzer(self.localizer)
        self.event_analyzer = EventAnalyzer(self.localizer)
        
        # Ensure countries directory exists
        Path("countries").mkdir(exist_ok=True)
    
    def load_data(self) -> bool:
        """Load game data"""
        success = self.data_loader.load_data()
        if success:
            metadata = self.data_loader.get_metadata()
            player_tag = metadata['player']
            if self.localization_available:
                player_name = self.localizer.get_country_name(player_tag)
            else:
                player_name = player_tag  # Use tag as fallback
            print(f"Player: {player_name} ({player_tag})")
        return success
    
    def analyze_all_countries(self):
        """Analyze all countries and write individual files"""
        if not self.data_loader.is_loaded():
            print("No data loaded")
            return
        
        countries = self.data_loader.get_countries()
        metadata = self.data_loader.get_metadata()
        
        print(f"\nAnalyzing {len(countries)} countries...")
        print("="*50)
        
        analyzed_count = 0
        skipped_count = 0
        
        for country in countries:
            tag = country['tag']
            country_data = country['data']
            
            try:
                self.analyze_country(tag, country_data, metadata)
                analyzed_count += 1
                
                # Progress indicator
                if analyzed_count % 10 == 0:
                    print(f"Progress: {analyzed_count}/{len(countries)} countries analyzed")
                    
            except Exception as e:
                print(f"Error analyzing {tag}: {e}")
                skipped_count += 1
        
        print(f"\nAnalysis complete!")
        print(f"Countries analyzed: {analyzed_count}")
        print(f"Countries skipped: {skipped_count}")
        print(f"Files written to: ./countries/")
    
    def analyze_country(self, tag: str, country_data: dict, metadata: dict):
        """Analyze a single country and write to file"""
        
        # Get country name (fallback to tag if not found)
        if self.localization_available:
            country_name = self.localizer.get_country_name(tag)
            if not country_name or country_name == tag:
                country_name = country_data.get('name', tag)
        else:
            # Use tag as country name when no localization available
            country_name = tag
        
        # Skip if country has no meaningful data
        if not self._has_meaningful_data(country_data):
            return
        
        # Perform analysis
        political = self.political_analyzer.analyze_country(tag, country_data)
        focus = self.focus_analyzer.analyze_country_focus(tag, country_data)
        
        # Generate report content
        report_content = self._generate_country_report(political, focus, metadata, tag)
        
        # Write to file (sanitize filename)
        safe_filename = self._sanitize_filename(f"{tag}_{country_name}")
        file_path = f"countries/{safe_filename}.txt"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
    
    def _has_meaningful_data(self, country_data: dict) -> bool:
        """Check if country has meaningful data to analyze"""
        # Skip countries with no political power or very basic data
        if not country_data.get('politics'):
            return False
        
        politics = country_data['politics']
        
        # Must have some political power or be involved in the world
        has_political_power = politics.get('political_power', 0) > 0
        has_stability = politics.get('stability', 0) > 0
        has_war_support = politics.get('war_support', 0) > 0
        has_parties = bool(politics.get('parties'))
        
        return has_political_power or has_stability or has_war_support or has_parties
    
    def _generate_country_report(self, political, focus, metadata: dict, tag: str) -> str:
        """Generate detailed country analysis report"""
        lines = []
        
        # Header
        lines.append("="*60)
        lines.append(f"HOI4 COUNTRY ANALYSIS: {political.name}")
        lines.append(f"Country Tag: {tag}")
        lines.append(f"Date: {metadata['date']}")
        lines.append(f"Analysis Generated: {metadata.get('generated_at', 'Unknown')}")
        lines.append("="*60)
        lines.append("")
        
        # Political Analysis
        lines.append("POLITICAL SITUATION:")
        lines.append("-" * 20)
        lines.append(f"Stability: {political.stability:.1f}%")
        lines.append(f"War Support: {political.war_support:.1f}%")
        lines.append(f"Political Power: {political.political_power:.0f}")
        lines.append(f"Ruling Party: {political.ruling_party}")
        lines.append("")
        
        # Party Support
        if political.party_support:
            lines.append("PARTY SUPPORT:")
            lines.append("-" * 13)
            for party, support in political.party_support.items():
                lines.append(f"  {party}: {support:.1f}%")
            lines.append("")
        
        # National Ideas
        if political.national_ideas:
            lines.append("NATIONAL IDEAS:")
            lines.append("-" * 15)
            for idea in political.national_ideas:
                lines.append(f"  • {idea}")
            lines.append("")
        
        # Focus Tree Analysis
        if focus:
            lines.append("FOCUS TREE PROGRESS:")
            lines.append("-" * 20)
            lines.append(f"Completed Focuses: {focus.completed_count}")
            
            if focus.current_focus:
                status = f"{focus.progress:.1f}% complete" if not focus.is_paused else "PAUSED"
                lines.append(f"Current Focus: {focus.current_focus_name} ({status})")
            else:
                lines.append("Current Focus: None")
            
            lines.append("")
            
            # Recent completed focuses
            if focus.completed_focus_names:
                recent_count = min(10, len(focus.completed_focus_names))
                lines.append(f"RECENT COMPLETED FOCUSES (Last {recent_count}):")
                lines.append("-" * 35)
                for focus_name in focus.completed_focus_names[-recent_count:]:
                    lines.append(f"  • {focus_name}")
                lines.append("")
        else:
            lines.append("FOCUS TREE PROGRESS:")
            lines.append("-" * 20)
            lines.append("No focus tree activity detected")
            lines.append("")
        
        # Additional country-specific data
        lines.append("ADDITIONAL INFORMATION:")
        lines.append("-" * 23)
        
        # Check if this is the player country
        player_tag = metadata.get('player')
        if tag == player_tag:
            lines.append("Status: PLAYER NATION")
        
        # Check for major power status
        major_powers = ['GER', 'SOV', 'USA', 'ENG', 'FRA', 'ITA', 'JAP']
        if tag in major_powers:
            lines.append("Status: MAJOR POWER")
        
        lines.append("")
        lines.append("="*60)
        lines.append("End of Report")
        lines.append("="*60)
        
        return "\n".join(lines)
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for cross-platform compatibility"""
        # Replace or remove problematic characters
        replacements = {
            '<': '',
            '>': '',
            ':': '-',
            '"': '',
            '/': '_',
            '\\': '_',
            '|': '_',
            '?': '',
            '*': '',
            ' ': '_'
        }
        
        for old, new in replacements.items():
            filename = filename.replace(old, new)
        
        # Remove any consecutive underscores and limit length
        filename = '_'.join(filter(None, filename.split('_')))
        return filename[:100]  # Limit filename length
    
    def analyze_specific_country(self, country_tag: str):
        """Analyze a specific country by tag"""
        if not self.data_loader.is_loaded():
            print("No data loaded")
            return
        
        # Use the existing get_country method which handles the lookup
        country_data = self.data_loader.get_country(country_tag)
        
        if not country_data:
            print(f"Country '{country_tag}' not found in data")
            countries = self.data_loader.get_countries()
            available_tags = sorted([c['tag'] for c in countries])[:20]  # Show first 20
            print(f"Available country tags (first 20): {', '.join(available_tags)}")
            return
        
        metadata = self.data_loader.get_metadata()
        
        print(f"Analyzing {country_tag}...")
        
        try:
            self.analyze_country(country_tag, country_data, metadata)
            if self.localization_available:
                country_name = self.localizer.get_country_name(country_tag)
            else:
                country_name = country_tag
            safe_filename = self._sanitize_filename(f"{country_tag}_{country_name}")
            print(f"Analysis complete! Written to: countries/{safe_filename}.txt")
        except Exception as e:
            print(f"Error analyzing {country_tag}: {e}")

def main():
    analyzer = HOI4CountryAnalyzer()
    
    if not analyzer.load_data():
        print("Failed to load game data")
        sys.exit(1)
    
    # Check command line arguments
    if len(sys.argv) > 1:
        # Analyze specific country
        country_tag = sys.argv[1].upper()
        analyzer.analyze_specific_country(country_tag)
    else:
        # Analyze all countries
        analyzer.analyze_all_countries()

if __name__ == "__main__":
    main()