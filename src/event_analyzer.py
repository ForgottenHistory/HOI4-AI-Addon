#!/usr/bin/env python3
"""
HOI4 Event Analysis
Processes and filters game events for clean display
"""

from typing import List

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
                not self._has_dynamic_text(localized_title) and
                not self._has_dynamic_text(localized_desc)):
                clean_events.append(localized_title)
        
        return clean_events
    
    def _get_event_description(self, event_id: str) -> str:
        """Get event description, return empty string if not found"""
        desc_key = f"{event_id}.d"
        if desc_key in self.localizer.translations:
            return self.localizer.translations[desc_key]
        
        desc_key = f"{event_id}.desc"
        if desc_key in self.localizer.translations:
            return self.localizer.translations[desc_key]
        
        return ""

    def _has_dynamic_text(self, text: str) -> bool:
        """Check if text contains dynamic placeholders like [FROM.GetName]"""
        if not text:
            return False
            
        if '[' in text and ']' in text:
            return True
        
        dynamic_patterns = ['ROOT.', 'FROM.', 'THIS.', 'PREV.', '.Get']
        return any(pattern in text for pattern in dynamic_patterns)