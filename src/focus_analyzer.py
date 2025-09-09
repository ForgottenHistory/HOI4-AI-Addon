#!/usr/bin/env python3
"""
HOI4 Focus Tree Analysis
Analyzes national focus progress and completed focuses
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class FocusAnalysis:
    """Container for focus analysis results"""
    tag: str
    name: str
    current_focus: Optional[str]
    current_focus_name: Optional[str]
    progress: float
    completed_count: int
    completed_focuses: List[str]
    completed_focus_names: List[str]
    is_paused: bool

class FocusAnalyzer:
    """Analyzes focus tree data for countries"""
    
    def __init__(self, localizer):
        self.localizer = localizer
    
    def analyze_country_focus(self, tag: str, country_data: Dict[str, Any]) -> Optional[FocusAnalysis]:
        """Analyze focus situation for a single country"""
        focus_data = country_data.get('focus')
        if not focus_data:
            return None
        
        # Extract basic focus info
        current_focus = focus_data.get('current')
        progress = focus_data.get('progress', 0.0)
        completed = focus_data.get('completed', [])
        is_paused = focus_data.get('paused', 'no') != 'no'
        
        # Get ideology for proper country name
        politics = country_data.get('politics', {})
        ruling_party = politics.get('ruling_party', 'Unknown')
        
        # Localize focus names and filter out dynamic text
        current_focus_name = None
        if current_focus:
            localized_name = self.localizer.get_localized_text(current_focus)
            # Only use the focus if it doesn't have dynamic text
            if not self._has_dynamic_text(localized_name):
                current_focus_name = localized_name
                # Also check description for dynamic text
                description = self.get_focus_description(current_focus, truncate=False)
                if self._has_dynamic_text(description):
                    current_focus_name = None  # Filter out if description has dynamic text
            else:
                current_focus = None  # Clear the raw focus ID too
        
        completed_focus_names = []
        for focus in completed:
            focus_name = self.localizer.get_localized_text(focus)
            # Only include completed focuses without dynamic text
            if not self._has_dynamic_text(focus_name):
                completed_focus_names.append(focus_name)
        
        return FocusAnalysis(
            tag=tag,
            name=self.localizer.get_country_name(tag, ruling_party),
            current_focus=current_focus,
            current_focus_name=current_focus_name,
            progress=progress,
            completed_count=len(completed),
            completed_focuses=completed,
            completed_focus_names=completed_focus_names,
            is_paused=is_paused
        )
    
    def get_focus_leaders(self, countries_data: List[Dict[str, Any]], min_completed: int = 5) -> List[FocusAnalysis]:
        """Get countries with most completed focuses"""
        focus_analyses = []
        
        for country in countries_data:
            analysis = self.analyze_country_focus(country['tag'], country['data'])
            if analysis and analysis.completed_count >= min_completed:
                focus_analyses.append(analysis)
        
        # Sort by completed count, then by progress
        return sorted(focus_analyses, key=lambda x: (x.completed_count, x.progress), reverse=True)
    
    def get_active_focuses(self, countries_data: List[Dict[str, Any]]) -> List[FocusAnalysis]:
        """Get countries currently working on focuses"""
        active_focuses = []
        
        for country in countries_data:
            analysis = self.analyze_country_focus(country['tag'], country['data'])
            if analysis and analysis.current_focus and not analysis.is_paused:
                active_focuses.append(analysis)
        
        # Sort by progress (highest first)
        return sorted(active_focuses, key=lambda x: x.progress, reverse=True)
    
    def format_focus_summary(self, analysis: FocusAnalysis, show_completed: bool = False, show_description: bool = False) -> str:
        """Format focus analysis for display"""
        lines = []
        
        if analysis.current_focus:
            status = "PAUSED" if analysis.is_paused else f"{analysis.progress:.1f}% complete"
            lines.append(f"Current: {analysis.current_focus_name} ({status})")
            
            if show_description:
                # Add truncated description for regular mode
                description = self.get_focus_description(analysis.current_focus, truncate=True)
                if description:
                    lines.append(f"  → {description}")
        
        if analysis.completed_count > 0:
            lines.append(f"Completed: {analysis.completed_count} focuses")
            
            if show_completed and analysis.completed_focus_names:
                # Filter out completed focuses with dynamic text
                clean_completed = [focus for focus in analysis.completed_focus_names[-3:] if not self._has_dynamic_text(focus)]
                if clean_completed:
                    lines.append(f"Recent: {', '.join(clean_completed)}")
        
        if show_description:
            return '\n    '.join(lines) if lines else "No focus activity"
        else:
            return ' | '.join(lines) if lines else "No focus activity"
    
    def get_focus_description(self, focus_id: str, truncate: bool = False) -> str:
        """Get focus description from localization"""
        desc_key = f"{focus_id}_desc"
        description = self.localizer.get_localized_text(desc_key)
        
        # If we got back the same key, no description was found
        if description == desc_key:
            return ""
        
        if description and truncate:
            # Clean up and truncate for regular mode
            description = description.replace('\\n', ' ').strip()
            if len(description) > 150:
                description = description[:150] + "..."
        elif description:
            # Just clean up newlines for verbose mode
            description = description.replace('\\n', ' ').strip()
        
        return description
    
    def format_focus_summary_verbose(self, analysis: FocusAnalysis) -> str:
        """Format focus analysis for verbose display with full descriptions"""
        lines = []
        
        if analysis.current_focus:
            status = "PAUSED" if analysis.is_paused else f"{analysis.progress:.1f}% complete"
            lines.append(f"Current: {analysis.current_focus_name} ({status})")
            
            # Add full description for current focus (no truncation)
            description = self.get_focus_description(analysis.current_focus, truncate=False)
            if description:
                lines.append(f"  → {description}")
        
        if analysis.completed_count > 0:
            lines.append(f"Completed: {analysis.completed_count} focuses")
            
            if analysis.completed_focus_names:
                # Filter out completed focuses with dynamic text
                clean_completed = [focus for focus in analysis.completed_focus_names[-3:] if not self._has_dynamic_text(focus)]
                if clean_completed:
                    lines.append(f"Recent: {', '.join(clean_completed)}")
        
        return '\n    '.join(lines) if lines else "No focus activity"
    
    def _has_dynamic_text(self, text: str) -> bool:
        """Check if text contains dynamic placeholders (any square brackets)"""
        if not text:
            return False
        return '[' in text and ']' in text