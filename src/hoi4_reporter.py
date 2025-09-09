#!/usr/bin/env python3
"""
HOI4 Reporter - Unified interface for all HOI4 analysis and report generation
Handles both global scope (world analysis) and local scope (country-specific) operations
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
from ai_analyst import HOI4AIService

# Import analyzers
from global_analyzer import GlobalAnalyzer
from country_analyzer import CountryAnalyzer

class HOI4Reporter:
    """
    Unified interface for HOI4 analysis and report generation
    
    Handles two main scopes:
    - Global: World situation, major powers, diplomatic overview
    - Country: Specific country analysis, citizen perspectives, local news
    """
    
    def __init__(self, json_path: str = "game_data.json"):
        # Core components
        self.data_loader = GameDataLoader(json_path)
        self.localizer = HOI4Localizer()
        self._ai_service = None  # Initialized lazily when needed
        
        # Load localization
        print("Loading HOI4 localization...")
        try:
            # Try to load from both project locale and game paths
            if self.localizer.project_locale_path.exists() or self.localizer.game_localization_path.exists():
                self.localizer.load_all_files()
                self.localization_available = len(self.localizer.translations) > 0
                if self.localization_available:
                    print("Localization loaded successfully!")
                else:
                    print("No translations found, using country tags as fallback")
            else:
                print("No localization files found in project or game folders, using tags as fallback")
                self.localization_available = False
        except Exception as e:
            print(f"Localization loading failed: {e}")
            print("Using country tags as fallback")
            self.localization_available = False
        
        # Initialize analyzers lazily (AI service will be created when needed)
        self._global_analyzer = None
        self._country_analyzer = None
        
        # Ensure output directories exist
        Path("reports").mkdir(exist_ok=True)
        Path("reports/global").mkdir(exist_ok=True)
        Path("reports/countries").mkdir(exist_ok=True)
    
    def get_ai_service(self, debug_mode: bool = False):
        """Get AI service with optional debug mode"""
        if self._ai_service is None or debug_mode != getattr(self._ai_service, 'debug_mode', False):
            self._ai_service = HOI4AIService(debug_mode=debug_mode)
        return self._ai_service
    
    @property
    def ai_service(self):
        """Lazy initialization of AI service"""
        return self.get_ai_service()
    
    @property 
    def global_analyzer(self):
        """Lazy initialization of global analyzer"""
        if self._global_analyzer is None:
            self._global_analyzer = GlobalAnalyzer(
                self.data_loader, self.localizer, self.ai_service
            )
        return self._global_analyzer
    
    @property
    def country_analyzer(self):
        """Lazy initialization of country analyzer"""
        if self._country_analyzer is None:
            self._country_analyzer = CountryAnalyzer(
                self.data_loader, self.localizer, self.ai_service
            )
        return self._country_analyzer
    
    def load_data(self) -> bool:
        """Load game data and display basic info"""
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
    
    def list_generators(self):
        """List all available report generators"""
        print("Available report generators:")
        print("\n📊 GLOBAL SCOPE (world situation):")
        global_generators = ['intelligence', 'news', 'twitter']
        for gen in global_generators:
            print(f"  - {gen}")
        
        print("\n🏛️ COUNTRY SCOPE (specific countries):")  
        country_generators = ['country_news', 'citizen_interviews', 'leader_speech']
        for gen in country_generators:
            print(f"  - {gen}")
        
        print("\n📋 SPECIALIZED:")
        specialized = ['adviser']  # Player-specific
        for gen in specialized:
            print(f"  - {gen}")
        
        return global_generators + country_generators + specialized
    
    def generate_global_report(self, generator_type: str, output_file: bool = True, debug: bool = False, verbose: bool = False) -> str:
        """
        Generate reports with global scope (world situation)
        
        Args:
            generator_type: Type of report ('intelligence', 'news', 'twitter', 'adviser')
            output_file: Whether to save report to file
        """
        if not self.data_loader.is_loaded():
            return "Error: No game data loaded"
        
        print(f"🌍 Generating global {generator_type} report...")
        if debug:
            print("🐛 Debug mode enabled - showing prompt only")
        
        # Get global analyzer with debug-enabled AI service
        if debug:
            # Create a new analyzer with debug mode
            debug_ai_service = self.get_ai_service(debug_mode=True)
            from global_analyzer import GlobalAnalyzer
            debug_analyzer = GlobalAnalyzer(self.data_loader, self.localizer, debug_ai_service)
            report = debug_analyzer.generate_report(generator_type, verbose=verbose)
        else:
            # Delegate to global analyzer
            report = self.global_analyzer.generate_report(generator_type, verbose=verbose)
        
        if output_file and not report.startswith("Error:"):
            filename = self._save_global_report(report, generator_type)
            print(f"📁 Report saved to: {filename}")
        
        return report
    
    def generate_country_report(self, country_tags: list[str], generator_type: str, 
                              output_file: bool = True) -> str:
        """
        Generate reports with country scope (specific countries)
        
        Args:
            country_tags: List of country tags to analyze
            generator_type: Type of report ('country_news', 'citizen_interviews')
            output_file: Whether to save report to file
        """
        if not self.data_loader.is_loaded():
            return "Error: No game data loaded"
        
        if not country_tags:
            return "Error: No countries specified"
        
        print(f"🏛️ Generating {generator_type} report for: {', '.join(country_tags)}")
        
        # Delegate to country analyzer
        report = self.country_analyzer.generate_report(country_tags, generator_type)
        
        if output_file and not report.startswith("Error:"):
            filename = self._save_country_report(report, country_tags, generator_type)
            print(f"📁 Report saved to: {filename}")
        
        return report
    
    def _save_global_report(self, report: str, generator_type: str) -> str:
        """Save global report to file"""
        metadata = self.data_loader.get_metadata()
        date_str = metadata['date'].replace('.', '_')
        filename = f"reports/global/{generator_type}_{date_str}.txt"
        
        # Create full report content
        full_report = []
        full_report.append("=" * 70)
        full_report.append(f"HOI4 GLOBAL {generator_type.upper()} REPORT")
        full_report.append("=" * 70)
        full_report.append(f"Generated: {metadata.get('generated_at', 'Unknown')}")
        full_report.append(f"Game Date: {metadata['date']}")
        full_report.append(f"Scope: Global Analysis")
        full_report.append("=" * 70)
        full_report.append("")
        full_report.append(report)
        full_report.append("")
        full_report.append("=" * 70)
        full_report.append("End of Report")
        full_report.append("=" * 70)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("\n".join(full_report))
        
        return filename
    
    def _save_country_report(self, report: str, country_tags: list[str], 
                           generator_type: str) -> str:
        """Save country report to file"""
        metadata = self.data_loader.get_metadata()
        tags_str = "_".join(country_tags)
        date_str = metadata['date'].replace('.', '_')
        filename = f"reports/countries/{generator_type}_{tags_str}_{date_str}.txt"
        
        # Create full report content
        full_report = []
        full_report.append("=" * 70)
        full_report.append(f"HOI4 COUNTRY {generator_type.upper()} REPORT")
        full_report.append("=" * 70)
        full_report.append(f"Generated: {metadata.get('generated_at', 'Unknown')}")
        full_report.append(f"Game Date: {metadata['date']}")
        full_report.append(f"Focus Countries: {', '.join(country_tags)}")
        full_report.append(f"Scope: Country Analysis")
        full_report.append("=" * 70)
        full_report.append("")
        full_report.append(report)
        full_report.append("")
        full_report.append("=" * 70)
        full_report.append("End of Report")
        full_report.append("=" * 70)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("\n".join(full_report))
        
        return filename
    
    def print_world_summary(self, verbose: bool = False):
        """Print comprehensive world situation summary (delegates to global analyzer)"""
        self.global_analyzer.print_summary(verbose=verbose)
    
    def print_country_details(self, country_tag: str):
        """Print detailed country analysis (delegates to country analyzer)"""
        self.country_analyzer.print_details(country_tag)

def main():
    """Main CLI interface"""
    if len(sys.argv) < 2:
        print("HOI4 Reporter - Unified Analysis Interface")
        print("=" * 50)
        print()
        print("Usage:")
        print("  python hoi4_reporter.py --list-generators")
        print("  python hoi4_reporter.py --global <generator> [--debug]")
        print("  python hoi4_reporter.py --countries <tags> --generator <type>")
        print("  python hoi4_reporter.py --summary [--verbose]")
        print()
        print("Examples:")
        print("  python hoi4_reporter.py --global intelligence")
        print("  python hoi4_reporter.py --global twitter --debug")
        print("  python hoi4_reporter.py --countries GER SOV --generator citizen_interviews") 
        print("  python hoi4_reporter.py --countries USA --generator country_news")
        print("  python hoi4_reporter.py --summary")
        print("  python hoi4_reporter.py --summary --verbose")
        sys.exit(1)
    
    # Initialize reporter
    reporter = HOI4Reporter()
    
    if not reporter.load_data():
        print("Failed to load game data. Make sure game_data.json exists.")
        sys.exit(1)
    
    # Handle commands
    args = sys.argv[1:]
    
    if '--list-generators' in args:
        reporter.list_generators()
        
    elif '--summary' in args:
        verbose = '--verbose' in args
        reporter.print_world_summary(verbose=verbose)
        
    elif '--global' in args:
        try:
            generator_idx = args.index('--global') + 1
            if generator_idx >= len(args):
                print("Error: --global requires a generator type")
                sys.exit(1)
            
            generator_type = args[generator_idx]
            debug = '--debug' in args
            verbose = '--verbose' in args
            print(f"\n🌍 Generating global {generator_type} report...")
            if verbose:
                print("🔍 Verbose mode enabled - full descriptions")
            if not debug:
                print("This may take a moment...")
            
            report = reporter.generate_global_report(generator_type, debug=debug, verbose=verbose)
            
            if report.startswith("Error:"):
                print(f"\n{report}")
                sys.exit(1)
            
            print(f"\n{'='*60}")
            print(f"GLOBAL {generator_type.upper()} REPORT")
            print(f"{'='*60}")
            print(report)
            print(f"{'='*60}")
            
        except ValueError:
            print("Error: Invalid --global usage")
            sys.exit(1)
            
    elif '--countries' in args:
        try:
            countries_idx = args.index('--countries') + 1
            generator_idx = args.index('--generator') + 1
            
            # Extract country tags
            country_tags = []
            for i in range(countries_idx, len(args)):
                if args[i].startswith('--'):
                    break
                country_tags.append(args[i].upper())
            
            if not country_tags:
                print("Error: --countries requires at least one country tag")
                sys.exit(1)
                
            if generator_idx >= len(args):
                print("Error: --generator is required for country analysis")
                sys.exit(1)
            
            generator_type = args[generator_idx]
            
            print(f"\n🏛️ Generating {generator_type} report for: {', '.join(country_tags)}")
            print("This may take a moment...")
            
            report = reporter.generate_country_report(country_tags, generator_type)
            
            if report.startswith("Error:"):
                print(f"\n{report}")
                sys.exit(1)
            
            print(f"\n{'='*60}")
            print(f"COUNTRY {generator_type.upper()} REPORT")
            print(f"{'='*60}")
            print(report)
            print(f"{'='*60}")
            
        except ValueError:
            print("Error: Invalid --countries usage")
            sys.exit(1)
    
    else:
        print("Error: Unknown command. Use --help for usage information.")
        sys.exit(1)

if __name__ == "__main__":
    main()