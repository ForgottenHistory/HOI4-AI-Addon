#!/usr/bin/env python3
"""
HOI4 Political Situation Analysis
Analyzes country politics, stability, and party support
"""

from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class PoliticalAnalysis:
    """Container for political analysis results"""
    tag: str
    name: str
    stability: float
    war_support: float
    ruling_party: str
    political_power: float
    elections_allowed: bool
    party_support: Dict[str, float]
    national_ideas: list[str]

class PoliticalAnalyzer:
    """Analyzes political situations for countries"""
    
    def __init__(self, localizer):
        self.localizer = localizer
    
    def analyze_country(self, tag: str, country_data: Dict[str, Any]) -> PoliticalAnalysis:
        """Analyze political situation for a country"""
        politics = country_data.get('politics', {})
        
        # Basic political data
        ruling_party = politics.get('ruling_party', 'Unknown')
        analysis = PoliticalAnalysis(
            tag=tag,
            name=self.localizer.get_country_name(tag, ruling_party),
            stability=country_data.get('stability', 0) * 100,
            war_support=country_data.get('war_support', 0) * 100,
            ruling_party=ruling_party,
            political_power=politics.get('political_power', 0),
            elections_allowed=politics.get('elections_allowed', False),
            party_support={},
            national_ideas=[]
        )
        
        # Party support with localized names
        if politics.get('parties'):
            for party_type, party_data in politics['parties'].items():
                if party_data and party_data.get('popularity') is not None:
                    party_name = self.localizer.get_localized_text(party_type)
                    analysis.party_support[party_name] = party_data['popularity']
        
        # National ideas with localized names
        if politics.get('ideas'):
            for idea in politics['ideas']:
                localized_idea = self.localizer.get_idea_name(idea)
                analysis.national_ideas.append(localized_idea)
        
        return analysis
    
    def format_summary_line(self, analysis: PoliticalAnalysis) -> str:
        """Format political analysis for summary display"""
        return (f"{analysis.name:15} | "
                f"{analysis.ruling_party:12} | "
                f"Stability: {analysis.stability:5.1f}% | "
                f"War Support: {analysis.war_support:5.1f}%")
    
    def format_detailed_report(self, analysis: PoliticalAnalysis) -> str:
        """Format detailed political analysis"""
        lines = [
            f"Government: {analysis.ruling_party}",
            f"Political Power: {analysis.political_power}",
            f"Elections Allowed: {analysis.elections_allowed}",
            f"Stability: {analysis.stability:.1f}%",
            f"War Support: {analysis.war_support:.1f}%"
        ]
        
        if analysis.party_support:
            lines.append("\nParty Support:")
            for party, support in analysis.party_support.items():
                lines.append(f"  {party:15}: {support:5.1f}%")
        
        if analysis.national_ideas:
            lines.append("\nNational Ideas:")
            for idea in analysis.national_ideas:
                lines.append(f"  • {idea}")
        
        return '\n'.join(lines)