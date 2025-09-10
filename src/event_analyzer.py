#!/usr/bin/env python3
"""
HOI4 Event Analysis
Processes and filters game events for clean display
"""

from typing import List
# Import shared utilities to replace duplicate functions
import sys
import os
sys.path.append(os.path.dirname(__file__))
from services.utils import has_dynamic_text, truncate_description

class EventAnalyzer:
    """Analyzes and filters game events"""
    
    def __init__(self, localizer):
        self.localizer = localizer
    
    def get_clean_events(self, raw_events: List[str]) -> List[str]:
        """Get list of events with localized names, filtering out dynamic text"""
        clean_events = []
        
        for event in raw_events:
            # Try to get localized title
            localized_title = self.localizer.get_event_name(event)
            
            # Try to get localized description
            localized_desc = self._get_event_description(event)
            
            # Only include if we found proper localization and no dynamic text
            if (localized_title != event and 
                not has_dynamic_text(localized_title) and
                not has_dynamic_text(localized_desc)):
                clean_events.append(localized_title)
        
        return clean_events
    
    def get_clean_events_with_raw(self, raw_events: List[str]) -> List[tuple[str, str]]:
        """Get list of events with localized names paired with raw event IDs, filtering out dynamic text"""
        clean_events_with_raw = []
        
        for event in raw_events:
            # Try to get localized title
            localized_title = self.localizer.get_event_name(event)
            
            # Try to get localized description
            localized_desc = self._get_event_description(event)
            
            # Only include if we found proper localization and no dynamic text
            if (localized_title != event and 
                not has_dynamic_text(localized_title) and
                not has_dynamic_text(localized_desc)):
                clean_events_with_raw.append((localized_title, event))
        
        return clean_events_with_raw
    
    def _get_event_description(self, event_id: str, truncate: bool = False) -> str:
        """Get event description, return empty string if not found"""
        desc_key = f"{event_id}.d"
        description = ""
        
        if desc_key in self.localizer.translations:
            description = self.localizer.translations[desc_key]
        else:
            desc_key = f"{event_id}.desc"
            if desc_key in self.localizer.translations:
                description = self.localizer.translations[desc_key]
        
        if description:
            # Use shared utility for consistent text processing
            description = truncate_description(description, truncate=truncate, max_length=200)
        
        return description

    # Legacy compatibility: redirect to shared utility
    def _has_dynamic_text(self, text: str) -> bool:
        """Legacy method - use services.utils.has_dynamic_text instead"""
        return has_dynamic_text(text)