#!/usr/bin/env python3
"""
Intelligence Report Generator V2
Generates formal diplomatic intelligence briefings using the new service architecture
"""

from typing import Dict, Any
from .base_generator import BaseGenerator

# Import services with absolute imports for testing compatibility
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from services import ServiceContainer
from services.event_service import EventFormatStyle
from services.focus_service import FocusFormatStyle


class IntelligenceGeneratorV2(BaseGenerator):
    """Generates diplomatic intelligence briefings using service architecture"""
    
    def __init__(self, services: ServiceContainer):
        """
        Initialize with service container
        
        Args:
            services: ServiceContainer instance providing access to all services
        """
        self.services = services
    
    def generate_prompt(self, game_data: Dict[str, Any], **kwargs) -> str:
        verbose = kwargs.get('verbose', False)
        recent_events = kwargs.get('recent_events', [])
        
        # Use services to build context instead of manual parsing
        context = self._build_world_context_v2(game_data, recent_events, verbose=verbose)
        
        return f"""You are a diplomatic intelligence analyst in {game_data['metadata']['date']}. 
Analyze the current world situation and write a brief, engaging intelligence report.

CURRENT SITUATION:
{context}

Write a concise intelligence briefing (3-4 paragraphs) covering:
1. Most significant global developments
2. Rising tensions and potential flashpoints  
3. Key power dynamics between major nations
4. Strategic implications for world stability
5. Notable national focus activities and their implications

Write in the style of a 1930s diplomatic cable - serious but engaging."""
    
    def get_max_tokens(self) -> int:
        return 1300  # Increased for richer descriptions
    
    def _build_world_context_v2(self, game_data: Dict[str, Any], recent_events: list, verbose: bool = False) -> str:
        """Build world context using the new service architecture"""
        context_parts = []
        
        # Get events using EventService
        events = self.services.event_service.get_events_for_kwargs(
            game_data, recent_events, limit=5
        )
        
        if events:
            events_text = self.services.event_service.format_events(
                events, EventFormatStyle.INTELLIGENCE, verbose
            )
            context_parts.append(f"Recent Global Events:\n{events_text}")
        
        # Get major powers using CountryService
        major_powers = self.services.country_service.get_major_powers_info(game_data)
        
        if major_powers:
            powers_info = []
            for power in major_powers:
                # Use consistent country info formatting
                info = (f"- {power.display_name} ({power.tag}): {power.ruling_party} government, "
                       f"{power.stability:.0f}% stability, {power.war_support:.0f}% war support")
                
                # Get focus information using FocusService
                focus_info = self.services.focus_service.get_focus_info(
                    power.tag, power.raw_data, power.name
                )
                
                if focus_info and focus_info.current_focus_name:
                    info += f", pursuing {focus_info.current_focus_name} ({focus_info.progress:.0f}% complete)"
                    
                    # Add focus description for intelligence context
                    if focus_info.current_focus_description:
                        description = focus_info.current_focus_description
                        if not verbose and len(description) > 120:
                            description = description[:120] + "..."
                        info += f"\n    Policy: {description}"
                
                if focus_info and focus_info.completed_count > 0:
                    info += f"\n    Completed initiatives: {focus_info.completed_count}"
                
                powers_info.append(info)
            
            if powers_info:
                context_parts.append(f"Major Powers Analysis:\n" + "\n".join(powers_info))
        
        return "\n\n".join(context_parts)
    
    def compare_with_legacy(self, game_data: Dict[str, Any], **kwargs) -> Dict[str, str]:
        """
        Compare output with legacy implementation
        
        Returns:
            Dictionary with 'v1' and 'v2' prompts for comparison
        """
        # Import legacy generator
        from .intelligence_generator import IntelligenceGenerator
        legacy_gen = IntelligenceGenerator()
        
        # Generate both versions
        v1_prompt = legacy_gen.generate_prompt(game_data, **kwargs)
        v2_prompt = self.generate_prompt(game_data, **kwargs)
        
        return {
            'v1': v1_prompt,
            'v2': v2_prompt
        }


# Legacy compatibility: create a function to easily upgrade existing code
def create_intelligence_generator_with_services(localizer, game_data_loader=None, 
                                              event_analyzer=None, focus_analyzer=None) -> IntelligenceGeneratorV2:
    """
    Factory function to create IntelligenceGeneratorV2 with legacy components
    
    This allows existing code to gradually migrate to the service architecture
    """
    services = ServiceContainer.create_from_existing_components(
        localizer=localizer,
        game_data_loader=game_data_loader,
        event_analyzer=event_analyzer,
        focus_analyzer=focus_analyzer
    )
    
    return IntelligenceGeneratorV2(services)