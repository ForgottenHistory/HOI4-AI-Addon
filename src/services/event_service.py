#!/usr/bin/env python3
"""
Event Service
Centralized event handling and formatting for consistent access across generators
"""

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
from .utils import has_dynamic_text, clean_text_for_display


class EventFormatStyle(Enum):
    """Event formatting styles for different generator types"""
    STANDARD = "standard"      # Basic title + description format
    INTELLIGENCE = "intelligence"  # Intelligence briefing format
    NEWS = "news"             # Newspaper article format
    COUNTRY_NEWS = "country_news"  # Country-specific news format
    TWITTER = "twitter"       # Social media format


@dataclass
class EventInfo:
    """Data transfer object for event information"""
    id: Optional[str]
    title: str
    description: str
    date: Optional[str] = None
    country: Optional[str] = None
    raw_event_id: Optional[str] = None


class EventService:
    """Centralized service for event handling and formatting"""
    
    def __init__(self, event_analyzer=None):
        """
        Initialize EventService
        Args:
            event_analyzer: Optional EventAnalyzer for legacy support
        """
        self.event_analyzer = event_analyzer
    
    def get_events_from_game_data(self, game_data: Dict[str, Any], limit: int = 8) -> List[EventInfo]:
        """
        Extract events from game_data in any format and return standardized EventInfo objects
        
        Args:
            game_data: Game data dictionary
            limit: Maximum number of events to return
            
        Returns:
            List of EventInfo objects
        """
        events = []
        
        # Try new format first: game_data['metadata']['recent_events']
        if game_data.get('metadata', {}).get('recent_events'):
            raw_events = game_data['metadata']['recent_events'][-limit:]
            for event in raw_events:
                if isinstance(event, dict):
                    events.append(EventInfo(
                        id=event.get('id'),
                        title=event.get('title', 'Unknown Event'),
                        description=event.get('description', ''),
                        date=event.get('date'),
                        country=event.get('country')
                    ))
                else:
                    # Handle string format in recent_events
                    events.append(EventInfo(
                        id=None,
                        title=str(event),
                        description='',
                        raw_event_id=str(event)
                    ))
        
        # Try game_data['recent_events'] format
        elif game_data.get('recent_events'):
            raw_events = game_data['recent_events'][-limit:]
            for event in raw_events:
                if isinstance(event, dict):
                    events.append(EventInfo(
                        id=event.get('id'),
                        title=event.get('title', 'Unknown Event'),
                        description=event.get('description', ''),
                        date=event.get('date'),
                        country=event.get('country')
                    ))
                else:
                    events.append(EventInfo(
                        id=None,
                        title=str(event),
                        description='',
                        raw_event_id=str(event)
                    ))
        
        # Try legacy game_data['events'] format  
        elif game_data.get('events'):
            raw_events = game_data['events'][-limit:]
            for event in raw_events:
                if isinstance(event, dict):
                    events.append(EventInfo(
                        id=event.get('id'),
                        title=event.get('title', 'Unknown Event'),
                        description=event.get('description', ''),
                        date=event.get('date'),
                        country=event.get('country')
                    ))
                else:
                    # Legacy string format - use event analyzer if available
                    title = str(event)
                    description = ''
                    
                    if self.event_analyzer:
                        # Get localized title
                        localized_title = self.event_analyzer.localizer.get_event_name(event)
                        if localized_title != event and not has_dynamic_text(localized_title):
                            title = localized_title
                            # Get description
                            description = self.event_analyzer._get_event_description(event, truncate=False)
                    
                    events.append(EventInfo(
                        id=None,
                        title=title,
                        description=description,
                        raw_event_id=str(event)
                    ))
        
        return events
    
    def format_events(self, events: List[EventInfo], style: EventFormatStyle = EventFormatStyle.STANDARD, 
                     verbose: bool = False) -> str:
        """
        Format events according to the specified style
        
        Args:
            events: List of EventInfo objects
            style: Formatting style to use
            verbose: Whether to use verbose formatting (full descriptions)
            
        Returns:
            Formatted string ready for generator use
        """
        if not events:
            return ""
        
        if style == EventFormatStyle.STANDARD:
            return self._format_standard(events, verbose)
        elif style == EventFormatStyle.INTELLIGENCE:
            return self._format_intelligence(events, verbose)
        elif style == EventFormatStyle.NEWS:
            return self._format_news(events, verbose)
        elif style == EventFormatStyle.COUNTRY_NEWS:
            return self._format_country_news(events, verbose)
        elif style == EventFormatStyle.TWITTER:
            return self._format_twitter(events, verbose)
        else:
            return self._format_standard(events, verbose)
    
    def _format_standard(self, events: List[EventInfo], verbose: bool) -> str:
        """Standard event formatting - title + description"""
        formatted = []
        for event in events:
            formatted.append(f"- {event.title}")
            if event.description:
                desc = event.description
                if not verbose and len(desc) > 150:
                    desc = desc[:150] + "..."
                formatted.append(f"  {desc}")
        return "\n".join(formatted)
    
    def _format_intelligence(self, events: List[EventInfo], verbose: bool) -> str:
        """Intelligence briefing format - title + analysis"""
        formatted = []
        for event in events:
            formatted.append(f"- {event.title}")
            if event.description:
                desc = event.description
                if not verbose and len(desc) > 150:
                    desc = desc[:150] + "..."
                formatted.append(f"    Analysis: {desc}")
        return "\n".join(formatted)
    
    def _format_news(self, events: List[EventInfo], verbose: bool) -> str:
        """News article format - title + details"""
        formatted = []
        for event in events:
            formatted.append(f"- {event.title}")
            if event.description:
                desc = event.description
                if not verbose and len(desc) > 200:
                    desc = desc[:200] + "..."
                formatted.append(f"  Details: {desc}")
        return "\n".join(formatted)
    
    def _format_country_news(self, events: List[EventInfo], verbose: bool) -> str:
        """Country news format - emphasizes local relevance"""
        formatted = []
        for event in events:
            formatted.append(f"- {event.title}")
            if event.description:
                desc = event.description
                if not verbose and len(desc) > 180:
                    desc = desc[:180] + "..."
                formatted.append(f"  Impact: {desc}")
        return "\n".join(formatted)
    
    def _format_twitter(self, events: List[EventInfo], verbose: bool) -> str:
        """Twitter format - title + context"""
        formatted = []
        for event in events:
            formatted.append(f"- {event.title}")
            if event.description:
                desc = event.description
                # Twitter format never truncates for better context
                formatted.append(f"  Context: {desc}")
        return "\n".join(formatted)
    
    def get_events_for_kwargs(self, game_data: Dict[str, Any], recent_events: Optional[List] = None, 
                             limit: int = 8) -> List[EventInfo]:
        """
        Get events handling both explicit recent_events kwargs and game_data formats
        This bridges the gap between old generator patterns and new service
        
        Args:
            game_data: Game data dictionary
            recent_events: Explicit recent events from kwargs
            limit: Maximum number of events
            
        Returns:
            List of EventInfo objects
        """
        if recent_events:
            # Handle explicit recent_events from kwargs
            events = []
            for event in recent_events[-limit:]:
                if isinstance(event, dict):
                    events.append(EventInfo(
                        id=event.get('id'),
                        title=event.get('title', 'Unknown Event'),
                        description=event.get('description', ''),
                        date=event.get('date'),
                        country=event.get('country')
                    ))
                else:
                    events.append(EventInfo(
                        id=None,
                        title=str(event),
                        description='',
                        raw_event_id=str(event)
                    ))
            return events
        else:
            # Fall back to game_data extraction
            return self.get_events_from_game_data(game_data, limit)
    
