#!/usr/bin/env python3
"""
Country News Generator
Generates newspaper-style reports focused on specific countries
"""

from typing import Dict, Any, List
from .base_generator import BaseGenerator

class CountryNewsGenerator(BaseGenerator):
    """Generates newspaper-style reports focused on specific countries"""
    
    def generate_prompt(self, game_data: Dict[str, Any], **kwargs) -> str:
        focus_countries = kwargs.get('focus_countries', [])
        recent_events = kwargs.get('recent_events', [])
        verbose = kwargs.get('verbose', False)
        
        if not focus_countries:
            return "No countries specified for news report."
        
        if not recent_events:
            return "No significant developments to report."
        
        # Build country context
        country_names = [c['name'] for c in focus_countries]
        country_context = self._build_country_context(focus_countries)
        events_text = self._format_events_for_country_news(recent_events[-8:], verbose=verbose)  # More events for country focus
        
        # Determine if this is a single country or multi-country report
        if len(focus_countries) == 1:
            country = focus_countries[0]
            report_type = f"focused on {country['name']}"
            headline_suggestion = f"involving {country['name']}"
        else:
            report_type = f"covering {', '.join(country_names[:3])}"
            if len(country_names) > 3:
                report_type += f" and {len(country_names) - 3} other nations"
            headline_suggestion = "involving multiple major powers"
        
        return f"""You are an international correspondent writing for a major newspaper in {game_data['metadata']['date']}.
Write an engaging news article {report_type} based on these recent developments:

COUNTRY FOCUS:
{country_context}

RECENT DEVELOPMENTS:
{events_text}

Write a compelling news article (4-5 paragraphs) that:
1. Creates a dramatic headline appropriate for developments {headline_suggestion}
2. Connects these events into a coherent geopolitical narrative
3. Explains the significance for international relations and regional stability
4. Provides historical context and references to previous developments
5. Maintains authentic 1930s-1940s journalism style with dramatic language
6. References specific policy changes (national focus completions) as government shifts
7. Analyzes the political implications of stability and war support changes
8. Considers the broader European/world situation in context

Use period-appropriate language, dramatic headlines, and the reporting style of 1930s international correspondents. Include dateline and byline. Make it feel like breaking news from that era."""
    
    def _build_country_context(self, focus_countries: List[Dict[str, Any]]) -> str:
        """Build detailed context about the focus countries"""
        context_lines = []
        
        for country in focus_countries:
            tag = country['tag']
            name = country['name']
            political = country['political']
            focus = country['focus']
            
            # Basic political situation
            stability_desc = self._describe_stability(political.stability)
            war_support_desc = self._describe_war_support(political.war_support)
            
            context_lines.append(f"{name} ({tag}):")
            context_lines.append(f"  - Political Situation: {stability_desc}, {war_support_desc}")
            context_lines.append(f"  - Ruling Party: {political.ruling_party}")
            context_lines.append(f"  - Political Power: {political.political_power:.0f}")
            
            # Party dynamics
            if political.party_support:
                sorted_parties = sorted(political.party_support.items(), key=lambda x: x[1], reverse=True)
                party_info = ", ".join([f"{party} ({support:.1f}%)" for party, support in sorted_parties[:3]])
                context_lines.append(f"  - Party Support: {party_info}")
            
            # Focus tree progress
            if focus and focus.current_focus:
                context_lines.append(f"  - Current Policy: {focus.current_focus_name} ({focus.progress:.0f}% complete)")
            
            if focus and focus.completed_focus_names:
                recent_focuses = focus.completed_focus_names[-2:]  # Last 2 for context
                focus_list = ", ".join(recent_focuses)
                context_lines.append(f"  - Recent Policies: {focus_list}")
            
            # Special status
            if country['is_player']:
                context_lines.append(f"  - Status: Player nation taking active decisions")
            if country['is_major_power']:
                context_lines.append(f"  - Status: Major world power")
            
            context_lines.append("")  # Blank line between countries
        
        return "\n".join(context_lines)
    
    def _describe_stability(self, stability: float) -> str:
        """Convert stability percentage to descriptive text"""
        if stability >= 80:
            return f"High stability ({stability:.1f}% - strong internal unity)"
        elif stability >= 60:
            return f"Moderate stability ({stability:.1f}% - manageable tensions)"
        elif stability >= 40:
            return f"Low stability ({stability:.1f}% - growing unrest)"
        else:
            return f"Critical instability ({stability:.1f}% - severe internal crisis)"
    
    def _describe_war_support(self, war_support: float) -> str:
        """Convert war support percentage to descriptive text"""
        if war_support >= 80:
            return f"High war support ({war_support:.1f}% - population ready for conflict)"
        elif war_support >= 60:
            return f"Moderate war support ({war_support:.1f}% - cautious but supportive)"
        elif war_support >= 40:
            return f"Low war support ({war_support:.1f}% - war-weary population)"
        else:
            return f"Minimal war support ({war_support:.1f}% - strong anti-war sentiment)"
    
    def _format_events_for_country_news(self, events, verbose=False):
        """Format events with full descriptions for country news articles"""
        if not events:
            return ""
        
        if isinstance(events, list) and len(events) > 0 and isinstance(events[0], dict):
            # New format with descriptions
            formatted = []
            for event in events:
                formatted.append(f"- {event['title']}")
                if event.get('description'):
                    desc = event['description']
                    # Only truncate if not verbose
                    if not verbose and len(desc) > 200:
                        desc = desc[:200] + "..."
                    formatted.append(f"  Details: {desc}")
            return "\n".join(formatted)
        else:
            # Old format (backwards compatibility)
            return "\n".join([f"- {event}" for event in events])
    
    def get_max_tokens(self) -> int:
        return 1400  # Increased for richer descriptions