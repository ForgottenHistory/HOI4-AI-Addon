#!/usr/bin/env python3
"""
Focus Service
Centralized national focus handling and formatting
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
from .utils import has_dynamic_text, truncate_description


class FocusFormatStyle(Enum):
    """Focus formatting styles for different contexts"""
    BRIEF = "brief"           # Just current focus name
    STANDARD = "standard"     # Focus + progress
    DETAILED = "detailed"     # Focus + progress + description  
    VERBOSE = "verbose"       # Everything including recent completions


@dataclass
class FocusInfo:
    """Data transfer object for focus information"""
    tag: str
    country_name: str
    current_focus_id: Optional[str]
    current_focus_name: Optional[str]
    current_focus_description: Optional[str]
    progress: float
    completed_count: int
    completed_focus_ids: List[str]
    completed_focus_names: List[str]
    is_paused: bool
    recent_completed_names: List[str]  # Last few completed focuses


class FocusService:
    """Centralized service for focus tree operations and formatting"""
    
    def __init__(self, localizer, focus_analyzer=None):
        """
        Initialize FocusService
        
        Args:
            localizer: HOI4Localizer for name resolution
            focus_analyzer: Optional FocusAnalyzer for legacy support
        """
        self.localizer = localizer
        self.focus_analyzer = focus_analyzer
    
    def get_focus_info(self, tag: str, country_data: Dict[str, Any], 
                      country_name: Optional[str] = None) -> Optional[FocusInfo]:
        """
        Get comprehensive focus information for a country
        
        Args:
            tag: Country tag
            country_data: Country data dictionary
            country_name: Optional country name (will be resolved if not provided)
            
        Returns:
            FocusInfo object or None if no focus data
        """
        focus_data = country_data.get('focus')
        if not focus_data:
            return None
        
        # Get country name if not provided
        if not country_name:
            ruling_party = country_data.get('politics', {}).get('ruling_party')
            country_name = self.localizer.get_country_name(tag, ruling_party)
        
        # Extract focus information
        current_focus_id = focus_data.get('current')
        progress = focus_data.get('progress', 0.0)
        completed_ids = focus_data.get('completed', [])
        is_paused = focus_data.get('paused', 'no') != 'no'
        
        # Localize current focus
        current_focus_name = None
        current_focus_description = None
        if current_focus_id:
            localized_name = self.localizer.get_localized_text(current_focus_id)
            # Only use if no dynamic text
            if not has_dynamic_text(localized_name):
                current_focus_name = localized_name
                description = self._get_focus_description(current_focus_id)
                if not has_dynamic_text(description):
                    current_focus_description = description
                else:
                    current_focus_name = None  # Filter out if description has dynamic text
            
            if not current_focus_name:
                current_focus_id = None  # Clear ID if we can't use it
        
        # Localize completed focuses (filter out dynamic text)
        completed_focus_names = []
        for focus_id in completed_ids:
            focus_name = self.localizer.get_localized_text(focus_id)
            if not has_dynamic_text(focus_name):
                completed_focus_names.append(focus_name)
        
        # Get recent completed (last 3)
        recent_completed_names = completed_focus_names[-3:] if completed_focus_names else []
        
        return FocusInfo(
            tag=tag,
            country_name=country_name,
            current_focus_id=current_focus_id,
            current_focus_name=current_focus_name,
            current_focus_description=current_focus_description,
            progress=progress,
            completed_count=len(completed_ids),
            completed_focus_ids=completed_ids,
            completed_focus_names=completed_focus_names,
            is_paused=is_paused,
            recent_completed_names=recent_completed_names
        )
    
    def get_focus_info_from_analysis(self, focus_analysis) -> Optional[FocusInfo]:
        """
        Convert legacy FocusAnalysis object to FocusInfo
        
        Args:
            focus_analysis: FocusAnalysis object from focus_analyzer
            
        Returns:
            FocusInfo object
        """
        if not focus_analysis:
            return None
        
        # Get description for current focus
        description = None
        if focus_analysis.current_focus and self.focus_analyzer:
            description = self.focus_analyzer.get_focus_description(
                focus_analysis.current_focus, truncate=False
            )
        
        return FocusInfo(
            tag=focus_analysis.tag,
            country_name=focus_analysis.name,
            current_focus_id=focus_analysis.current_focus,
            current_focus_name=focus_analysis.current_focus_name,
            current_focus_description=description,
            progress=focus_analysis.progress,
            completed_count=focus_analysis.completed_count,
            completed_focus_ids=focus_analysis.completed_focuses,
            completed_focus_names=focus_analysis.completed_focus_names,
            is_paused=focus_analysis.is_paused,
            recent_completed_names=focus_analysis.completed_focus_names[-3:] if focus_analysis.completed_focus_names else []
        )
    
    def format_focus_status(self, focus: FocusInfo, style: FocusFormatStyle = FocusFormatStyle.STANDARD) -> str:
        """
        Format focus information for display
        
        Args:
            focus: FocusInfo object
            style: Formatting style to use
            
        Returns:
            Formatted focus status string
        """
        if not focus.current_focus_name and focus.completed_count == 0:
            return "No focus activity"
        
        if style == FocusFormatStyle.BRIEF:
            return focus.current_focus_name or "No active focus"
        
        elif style == FocusFormatStyle.STANDARD:
            lines = []
            if focus.current_focus_name:
                status = "PAUSED" if focus.is_paused else f"{focus.progress:.1f}% complete"
                lines.append(f"Current: {focus.current_focus_name} ({status})")
            
            if focus.completed_count > 0:
                lines.append(f"Completed: {focus.completed_count} focuses")
            
            return " | ".join(lines) if lines else "No focus activity"
        
        elif style == FocusFormatStyle.DETAILED:
            lines = []
            if focus.current_focus_name:
                status = "PAUSED" if focus.is_paused else f"{focus.progress:.1f}% complete"
                lines.append(f"Current: {focus.current_focus_name} ({status})")
                
                if focus.current_focus_description:
                    # Truncate description for detailed mode  
                    desc = truncate_description(focus.current_focus_description, truncate=True, max_length=150)
                    lines.append(f"  - {desc}")
            
            if focus.completed_count > 0:
                lines.append(f"Completed: {focus.completed_count} focuses")
                if focus.recent_completed_names:
                    lines.append(f"Recent: {', '.join(focus.recent_completed_names)}")
            
            return '\n    '.join(lines) if lines else "No focus activity"
        
        elif style == FocusFormatStyle.VERBOSE:
            lines = []
            if focus.current_focus_name:
                status = "PAUSED" if focus.is_paused else f"{focus.progress:.1f}% complete"
                lines.append(f"Current: {focus.current_focus_name} ({status})")
                
                if focus.current_focus_description:
                    # Full description for verbose mode
                    lines.append(f"  - {focus.current_focus_description}")
            
            if focus.completed_count > 0:
                lines.append(f"Completed: {focus.completed_count} focuses")
                if focus.recent_completed_names:
                    lines.append(f"Recent: {', '.join(focus.recent_completed_names)}")
            
            return '\n    '.join(lines) if lines else "No focus activity"
        
        return "No focus activity"
    
    def get_active_focuses(self, countries_data: List[Dict[str, Any]]) -> List[FocusInfo]:
        """
        Get countries currently working on focuses
        
        Args:
            countries_data: List of country data dictionaries with 'tag' and 'data' keys
            
        Returns:
            List of FocusInfo objects for countries with active focuses
        """
        active_focuses = []
        
        for country in countries_data:
            focus_info = self.get_focus_info(country['tag'], country['data'])
            if focus_info and focus_info.current_focus_name and not focus_info.is_paused:
                active_focuses.append(focus_info)
        
        # Sort by progress (highest first)
        return sorted(active_focuses, key=lambda x: x.progress, reverse=True)
    
    def get_focus_leaders(self, countries_data: List[Dict[str, Any]], min_completed: int = 3) -> List[FocusInfo]:
        """
        Get countries with most completed focuses
        
        Args:
            countries_data: List of country data dictionaries
            min_completed: Minimum completed focuses to include
            
        Returns:
            List of FocusInfo objects sorted by completion count
        """
        focus_leaders = []
        
        for country in countries_data:
            focus_info = self.get_focus_info(country['tag'], country['data'])
            if focus_info and focus_info.completed_count >= min_completed:
                focus_leaders.append(focus_info)
        
        # Sort by completed count, then by progress
        return sorted(focus_leaders, key=lambda x: (x.completed_count, x.progress), reverse=True)
    
    def _get_focus_description(self, focus_id: str) -> str:
        """Get focus description from localization"""
        desc_key = f"{focus_id}_desc"
        description = self.localizer.get_localized_text(desc_key)
        
        # If we got back the same key, no description was found
        if description == desc_key:
            return ""
        
        if description:
            # Clean up newlines
            description = description.replace('\\n', ' ').strip()
        
        return description
    
    def extract_focus_events(self, focus: FocusInfo) -> List[str]:
        """
        Extract newsworthy events from focus information
        
        Args:
            focus: FocusInfo object
            
        Returns:
            List of event strings suitable for news generation
        """
        events = []
        
        # Current focus events
        if focus.current_focus_name:
            if focus.progress > 80:
                events.append(f"{focus.country_name} nears completion of '{focus.current_focus_name}' policy ({focus.progress:.0f}% complete)")
            elif focus.progress > 50:
                events.append(f"{focus.country_name} makes significant progress on '{focus.current_focus_name}' ({focus.progress:.0f}% complete)")
            else:
                events.append(f"{focus.country_name} pursuing '{focus.current_focus_name}' policy ({focus.progress:.0f}% complete)")
        
        # Recent completions
        for focus_name in focus.recent_completed_names:
            events.append(f"{focus.country_name} completed major policy initiative: '{focus_name}'")
        
        return events