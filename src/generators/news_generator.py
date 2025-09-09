#!/usr/bin/env python3
"""
News Report Generator
Generates newspaper-style reports from recent events
"""

from typing import Dict, Any
from .base_generator import BaseGenerator

class NewsGenerator(BaseGenerator):
    """Generates newspaper-style reports"""
    
    def generate_prompt(self, game_data: Dict[str, Any], **kwargs) -> str:
        recent_events = kwargs.get('recent_events', [])
        verbose = kwargs.get('verbose', False)
        
        # If no explicit events, generate them from global data
        if not recent_events:
            recent_events = self._extract_global_events(game_data)
        
        if not recent_events:
            return "No significant developments to report."
        
        # Handle both old and new event formats
        events_text = self._format_events_for_news(recent_events[-8:], verbose=verbose)
        
        # Add context about major powers if available
        context = self._build_global_context(game_data)
        
        return f"""You are an international correspondent writing for a major newspaper in {game_data['metadata']['date']}.
Write an engaging news article based on these recent global developments:

GLOBAL SITUATION:
{context}

RECENT DEVELOPMENTS:
{events_text}

Write a compelling news article (4-5 paragraphs) that:
1. Creates a dramatic headline reflecting current tensions
2. Connects these events into a coherent geopolitical narrative
3. Explains their significance for international relations and regional stability
4. Provides historical context and references to the broader European situation
5. Maintains authentic 1930s-1940s journalism style with dramatic language
6. References specific policy changes (national focus completions) as government shifts
7. Considers the balance of power between democracies, fascist states, and communist powers

Use period-appropriate dramatic headlines and the reporting style of 1930s international correspondents. Make it feel like breaking news from that era."""
    
    def _extract_global_events(self, game_data: Dict[str, Any]) -> list:
        """Extract newsworthy events from global game data when no explicit events exist"""
        events = []
        
        # Extract events from major powers data
        major_powers = game_data.get('major_powers', [])
        for power in major_powers:
            name = power.get('name', power.get('tag', 'Unknown'))
            stability = power.get('stability', 0)
            war_support = power.get('war_support', 0)
            
            # Political tensions
            if stability < 40:
                events.append(f"{name} faces internal political crisis ({stability:.1f}% stability)")
            elif stability > 80 and war_support > 60:
                events.append(f"{name} demonstrates strong national unity amid rising tensions")
            
            # War preparations  
            if war_support > 70:
                events.append(f"Military fervor rises in {name} ({war_support:.1f}% war support)")
            elif war_support < 10:
                events.append(f"Anti-war sentiment dominates {name} domestic politics")
            
            # Focus completions
            if power.get('focus', {}).get('recent_completed'):
                for focus in power['focus']['recent_completed'][-2:]:
                    events.append(f"{name} completes major policy: '{focus}'")
        
        # Add focus activity events
        focus_leaders = game_data.get('focus_leaders', [])
        for leader in focus_leaders[:5]:  # Top 5 most active
            if hasattr(leader, 'name') and hasattr(leader, 'completed_count'):
                if leader.completed_count > 4:
                    events.append(f"{leader.name} pursues aggressive policy agenda ({leader.completed_count} major initiatives)")
        
        return events
    
    def _build_global_context(self, game_data: Dict[str, Any]) -> str:
        """Build context about the global situation"""
        context_lines = []
        context_lines.append(f"Date: {game_data['metadata']['date']}")
        
        # Major power summary
        major_powers = game_data.get('major_powers', [])
        if major_powers:
            democratic_powers = [p for p in major_powers if 'democratic' in p.get('ruling_party', '').lower()]
            fascist_powers = [p for p in major_powers if 'fascism' in p.get('ruling_party', '').lower()]
            communist_powers = [p for p in major_powers if 'communism' in p.get('ruling_party', '').lower()]
            
            context_lines.append(f"Major Powers Active: {len(major_powers)}")
            if democratic_powers:
                dem_names = [p.get('name', p.get('tag')) for p in democratic_powers]
                context_lines.append(f"Democratic Powers: {', '.join(dem_names)}")
            if fascist_powers:
                fas_names = [p.get('name', p.get('tag')) for p in fascist_powers]
                context_lines.append(f"Fascist Powers: {', '.join(fas_names)}")
            if communist_powers:
                com_names = [p.get('name', p.get('tag')) for p in communist_powers]
                context_lines.append(f"Communist Powers: {', '.join(com_names)}")
        
        return "\n".join(context_lines)
    
    def _format_events_for_news(self, events, verbose=False):
        """Format events with full descriptions for news articles"""
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
        return 1200  # Increased for richer descriptions