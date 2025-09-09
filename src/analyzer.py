#!/usr/bin/env python3
"""
HOI4 Main Analyzer - Orchestrates all analysis components
"""

import sys
from localization import HOI4Localizer
from game_data_loader import GameDataLoader
from political_analyzer import PoliticalAnalyzer
from focus_analyzer import FocusAnalyzer
from event_analyzer import EventAnalyzer
from ai_analyst import HOI4AIService

class HOI4Analyzer:
    def __init__(self, json_path: str = "game_data.json"):
        # Initialize components
        self.data_loader = GameDataLoader(json_path)
        self.localizer = HOI4Localizer()
        
        # Load localization
        print("Loading HOI4 localization...")
        self.localizer.load_all_files()
        print("Localization ready!\n")
        
        # Initialize analyzers
        self.political_analyzer = PoliticalAnalyzer(self.localizer)
        self.focus_analyzer = FocusAnalyzer(self.localizer)
        self.event_analyzer = EventAnalyzer(self.localizer)
    
    def load_data(self) -> bool:
        """Load game data"""
        success = self.data_loader.load_data()
        if success:
            metadata = self.data_loader.get_metadata()
            player_name = self.localizer.get_country_name(metadata['player'])
            print(f"Player: {player_name}")
        return success
    
    def print_summary(self):
        """Print comprehensive world situation summary"""
        if not self.data_loader.is_loaded():
            print("No data loaded")
            return
        
        metadata = self.data_loader.get_metadata()
        
        print("\n" + "="*50)
        print("HOI4 WORLD SITUATION REPORT")
        print("="*50)
        
        print(f"Date: {metadata['date']}")
        player_name = self.localizer.get_country_name(metadata['player'])
        print(f"Player Nation: {player_name}")
        
        # Recent events
        self._print_events_section()
        
        # Major powers
        self._print_major_powers_section()
        
        # Focus activity
        self._print_focus_section()
    
    def _print_events_section(self):
        """Print recent events section"""
        events = self.data_loader.get_events()
        clean_events = self.event_analyzer.get_clean_events(events)
        
        print(f"\nRECENT GLOBAL EVENTS:")
        if clean_events:
            for i, event in enumerate(clean_events[-10:], 1):
                print(f"  {i:2}. {event}")
        else:
            print("  No major events to report")
    
    def _print_major_powers_section(self):
        """Print major powers status section"""
        print(f"\nMAJOR POWER STATUS:")
        major_tags = ['GER', 'SOV', 'USA', 'ENG', 'FRA', 'ITA', 'JAP']
        
        for tag in major_tags:
            country_data = self.data_loader.get_country(tag)
            if country_data:
                # Political analysis
                political = self.political_analyzer.analyze_country(tag, country_data)
                print(f"  {self.political_analyzer.format_summary_line(political)}")
                
                # Focus analysis
                focus = self.focus_analyzer.analyze_country_focus(tag, country_data)
                if focus:
                    focus_summary = self.focus_analyzer.format_focus_summary(focus)
                    print(f"    Focus: {focus_summary}")
    
    def _print_focus_section(self):
        """Print focus activity section"""
        print(f"\nFOCUS TREE PROGRESS:")
        countries = self.data_loader.get_countries()
        focus_leaders = self.focus_analyzer.get_focus_leaders(countries, min_completed=3)
        
        if focus_leaders:
            print("  Most Active Nations:")
            for analysis in focus_leaders[:5]:
                print(f"    {analysis.name:15} | {analysis.completed_count} completed")
                if analysis.current_focus:
                    status = f"{analysis.progress:.0f}%" if not analysis.is_paused else "PAUSED"
                    print(f"      → {analysis.current_focus_name} ({status})")
        else:
            print("  No significant focus activity")
    
    def print_player_details(self):
        """Print detailed analysis of player country"""
        player_tag = self.data_loader.get_player_tag()
        country_data = self.data_loader.get_country(player_tag)
        
        if not country_data:
            print("No player data available")
            return
        
        political = self.political_analyzer.analyze_country(player_tag, country_data)
        
        print(f"\n" + "="*50)
        print(f"DETAILED {political.name.upper()} ANALYSIS")
        print("="*50)
        
        # Political details
        print(self.political_analyzer.format_detailed_report(political))
        
        # Focus details
        focus = self.focus_analyzer.analyze_country_focus(player_tag, country_data)
        if focus:
            print(f"\nFocus Tree Progress:")
            print(f"  Completed Focuses: {focus.completed_count}")
            if focus.current_focus:
                status = f"{focus.progress:.1f}% complete" if not focus.is_paused else "PAUSED"
                print(f"  Current Focus: {focus.current_focus_name} ({status})")
            
            if focus.completed_focus_names:
                recent = focus.completed_focus_names[-5:]
                print(f"  Recent Completed: {', '.join(recent)}")
    
    def generate_ai_report(self, report_type: str = 'intelligence'):
        """Generate AI analysis report"""
        if not self.data_loader.is_loaded():
            print("No data loaded for AI analysis")
            return
        
        try:
            ai_service = HOI4AIService()
            data = self.data_loader.data
            
            if report_type == 'adviser':
                # Enhanced player data for adviser report
                player_tag = self.data_loader.get_player_tag()
                country_data = self.data_loader.get_country(player_tag)
                
                if country_data:
                    political = self.political_analyzer.analyze_country(player_tag, country_data)
                    focus = self.focus_analyzer.analyze_country_focus(player_tag, country_data)
                    
                    # Convert to dict for AI service
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
                    
                    print(f"\n🏛️ AI STRATEGIC ASSESSMENT - {political.name.upper()}")
                    print("="*60)
                    report = ai_service.generate_report('adviser', data, player_analysis=player_analysis)
                    print(report)
                    return
            
            # Handle other report types
            if report_type in ['news', 'twitter']:
                events = self.data_loader.get_events()
                recent_events = self.event_analyzer.get_clean_events(events)
                kwargs = {'recent_events': recent_events}
            else:
                kwargs = {}
            
            # Print appropriate header
            headers = {
                'intelligence': "🌍 AI WORLD INTELLIGENCE BRIEFING",
                'news': "📰 AI GENERATED NEWS REPORT", 
                'twitter': "🐦 AI TWITTER FEED - 1936 EDITION"
            }
            
            print(f"\n{headers.get(report_type, 'AI REPORT')}")
            print("="*60)
            
            report = ai_service.generate_report(report_type, data, **kwargs)
            print(report)
            
        except Exception as e:
            print(f"AI analysis failed: {e}")
            print("Make sure your OPENROUTER_API_KEY is set correctly")
    
    def generate_all_reports(self):
        """Generate all available AI reports"""
        report_types = ['intelligence', 'adviser', 'news', 'twitter']
        
        for report_type in report_types:
            print(f"\n{'='*60}")
            print(f"🤖 GENERATING {report_type.upper()} REPORT...")
            print('='*60)
            
            try:
                self.generate_ai_report(report_type)
            except Exception as e:
                print(f"Failed to generate {report_type} report: {e}")
            
            print()  # Add spacing between reports

def main():
    analyzer = HOI4Analyzer()
    
    if not analyzer.load_data():
        print("Failed to load game data")
        sys.exit(1)
    
    analyzer.print_summary()
    analyzer.print_player_details()
    
    # Generate AI analysis
    # print("\n" + "="*50)
    # print("🤖 GENERATING AI ANALYSIS...")
    # print("="*50)
    
    # Choose one of these options:
    
    # Option 1: Generate all reports
    # analyzer.generate_all_reports()
    
    # Option 2: Generate single report (comment out line above, uncomment one below)
    # analyzer.generate_ai_report('intelligence')  # Diplomatic briefing
    # analyzer.generate_ai_report('adviser')       # Strategic advice
    # analyzer.generate_ai_report('news')         # Newspaper article  
    # analyzer.generate_ai_report('twitter')      # Twitter feed

if __name__ == "__main__":
    main()