#!/usr/bin/env python3
"""
HOI4 Game Data Analyzer with Localization
Reads JSON output from Rust extractor and processes game data
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any
from localization import HOI4Localizer

class HOI4Analyzer:
    def __init__(self, json_path: str = "game_data.json"):
        self.json_path = json_path
        self.data = None
        self.localizer = HOI4Localizer()
        
        # Load localization on startup
        print("Loading HOI4 localization...")
        self.localizer.load_all_files()
        print("Localization ready!\n")
    
    def extract_data(self) -> bool:
        """Run Rust extractor to generate JSON data"""
        try:
            print("Running Rust data extractor...")
            result = subprocess.run(["cargo", "run"], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Rust extractor failed: {result.stderr}")
                return False
            
            print("Rust extraction completed successfully")
            return True
            
        except Exception as e:
            print(f"Error running Rust extractor: {e}")
            return False
    
    def load_data(self) -> bool:
        """Load JSON data from file"""
        try:
            if not Path(self.json_path).exists():
                print(f"Data file {self.json_path} not found. Running extractor...")
                if not self.extract_data():
                    return False
            
            with open(self.json_path, 'r') as f:
                self.data = json.load(f)
            
            print(f"Loaded data for {self.data['metadata']['date']}")
            print(f"Player: {self.localizer.get_country_name(self.data['metadata']['player'])}")
            print(f"Events: {len(self.data['events'])}")
            print(f"Active countries: {len(self.data['countries'])}")
            
            return True
            
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
    
    def get_country(self, tag: str) -> Dict[str, Any] | None:
        """Get country data by tag"""
        if not self.data:
            return None
        
        for country in self.data['countries']:
            if country['tag'] == tag:
                return country['data']
        return None
    
    def analyze_political_situation(self, tag: str) -> Dict[str, Any]:
        """Analyze political situation for a country"""
        country = self.get_country(tag)
        if not country or not country.get('politics'):
            return {}
        
        politics = country['politics']
        analysis = {
            'tag': tag,
            'name': self.localizer.get_country_name(tag),
            'stability': country.get('stability', 0) * 100,
            'war_support': country.get('war_support', 0) * 100,
            'ruling_party': politics.get('ruling_party'),
            'political_power': politics.get('political_power'),
            'elections_allowed': politics.get('elections_allowed', False)
        }
        
        # Party support with localized names
        if politics.get('parties'):
            parties = politics['parties']
            analysis['party_support'] = {}
            
            for party_type, party_data in parties.items():
                if party_data and party_data.get('popularity') is not None:
                    party_name = self.localizer.get_localized_text(party_type)
                    analysis['party_support'][party_name] = party_data['popularity']
        
        # National ideas with localized names
        if politics.get('ideas'):
            analysis['national_ideas'] = []
            for idea in politics['ideas']:
                localized_idea = self.localizer.get_idea_name(idea)
                analysis['national_ideas'].append(localized_idea)
        
        return analysis
    
    def get_localized_events(self) -> List[str]:
        """Get list of recent events with localized names, filtering out hidden events"""
        if not self.data:
            return []
        
        localized_events = []
        for event in self.data['events']:
            # Try to get localized name
            localized_name = self.localizer.get_event_name(event)
            
            # Only include if we found a proper localization (not the original event ID)
            if localized_name != event:
                localized_events.append(localized_name)
        
        return localized_events
    
    def print_summary(self):
        """Print a human-readable summary of the current game state"""
        if not self.data:
            print("No data loaded")
            return
        
        print("\n" + "="*50)
        print("HOI4 WORLD SITUATION REPORT")
        print("="*50)
        
        print(f"Date: {self.data['metadata']['date']}")
        player_name = self.localizer.get_country_name(self.data['metadata']['player'])
        print(f"Player Nation: {player_name}")
        
        # Get visible events only
        visible_events = self.get_localized_events()
        
        print(f"\nRECENT GLOBAL EVENTS:")
        if visible_events:
            for i, event in enumerate(visible_events[-10:], 1):  # Last 10 visible events
                print(f"  {i:2}. {event}")
        else:
            print("  No major events to report")
        
        print(f"\nMAJOR POWER STATUS:")
        # Sort countries by political power or use a predefined major power list
        major_tags = ['GER', 'SOV', 'USA', 'ENG', 'FRA', 'ITA', 'JAP']
        
        for tag in major_tags:
            analysis = self.analyze_political_situation(tag)
            if analysis:
                ideas_str = ", ".join(analysis.get('national_ideas', [])[:3])
                if len(analysis.get('national_ideas', [])) > 3:
                    ideas_str += "..."
                
                print(f"  {analysis['name']:15} | "
                      f"{analysis['ruling_party']:12} | "
                      f"Stability: {analysis['stability']:5.1f}% | "
                      f"War Support: {analysis['war_support']:5.1f}%")
                if ideas_str:
                    print(f"    Ideas: {ideas_str}")

def main():
    analyzer = HOI4Analyzer()
    
    if not analyzer.load_data():
        print("Failed to load game data")
        sys.exit(1)
    
    analyzer.print_summary()
    
    # Detailed analysis of player country
    player_tag = analyzer.data['metadata']['player']
    player_analysis = analyzer.analyze_political_situation(player_tag)
    
    if player_analysis:
        print(f"\n" + "="*50)
        print(f"DETAILED {player_analysis['name'].upper()} ANALYSIS")
        print("="*50)
        
        print(f"Government: {player_analysis['ruling_party']}")
        print(f"Political Power: {player_analysis.get('political_power', 'Unknown')}")
        print(f"Elections Allowed: {player_analysis['elections_allowed']}")
        
        if 'party_support' in player_analysis:
            print(f"\nParty Support:")
            for party, support in player_analysis['party_support'].items():
                print(f"  {party:15}: {support:5.1f}%")
        
        if 'national_ideas' in player_analysis:
            print(f"\nNational Ideas:")
            for idea in player_analysis['national_ideas']:
                print(f"  • {idea}")

if __name__ == "__main__":
    main()