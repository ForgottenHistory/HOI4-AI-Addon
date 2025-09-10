#!/usr/bin/env python3
"""
Enhanced Base Generator
Next-generation base class for AI report generators with service injection
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from ..services import ServiceContainer, EventFormatStyle, FocusFormatStyle
from ..services.data_types import EventInfo, CountryInfo, FocusInfo, create_game_context_from_data


class EnhancedBaseGenerator(ABC):
    """Enhanced base class with service integration for all AI report generators"""
    
    def __init__(self, services: ServiceContainer):
        """
        Initialize generator with service container
        
        Args:
            services: ServiceContainer providing access to all services
        """
        self.services = services
        
    @abstractmethod
    def generate_prompt(self, game_data: Dict[str, Any], **kwargs) -> str:
        """Generate the prompt for this report type"""
        pass
    
    @abstractmethod
    def get_max_tokens(self) -> int:
        """Get maximum tokens for this report type"""
        pass
    
    # Service convenience methods
    
    def get_events(self, game_data: Dict[str, Any], recent_events: Optional[List] = None, 
                   limit: int = 8) -> List[EventInfo]:
        """Get events using EventService"""
        return self.services.event_service.get_events_for_kwargs(
            game_data, recent_events, limit
        )
    
    def format_events(self, events: List[EventInfo], style: str = 'standard', 
                     verbose: bool = False) -> str:
        """Format events using EventService"""
        style_enum = getattr(EventFormatStyle, style.upper(), EventFormatStyle.STANDARD)
        return self.services.event_service.format_events(events, style_enum, verbose)
    
    def get_country_info(self, tag: str, game_data: Dict[str, Any], 
                        country_data: Optional[Dict[str, Any]] = None) -> Optional[CountryInfo]:
        """Get country info using CountryService"""
        return self.services.country_service.get_country_info(tag, game_data, country_data)
    
    def get_major_powers(self, game_data: Dict[str, Any]) -> List[CountryInfo]:
        """Get major powers using CountryService"""
        return self.services.country_service.get_major_powers_info(game_data)
    
    def get_focus_info(self, tag: str, country_data: Dict[str, Any], 
                      country_name: Optional[str] = None) -> Optional[FocusInfo]:
        """Get focus info using FocusService"""
        return self.services.focus_service.get_focus_info(tag, country_data, country_name)
    
    def format_focus_status(self, focus_info: FocusInfo, style: str = 'standard') -> str:
        """Format focus status using FocusService"""
        style_enum = getattr(FocusFormatStyle, style.upper(), FocusFormatStyle.STANDARD)
        return self.services.focus_service.format_focus_status(focus_info, style_enum)
    
    def get_country_name(self, tag: str, ideology: Optional[str] = None) -> str:
        """Get country name using CountryService"""
        return self.services.country_service.get_country_name(tag, ideology)
    
    # High-level context builders
    
    def build_event_context(self, game_data: Dict[str, Any], recent_events: Optional[List] = None,
                           style: str = 'standard', limit: int = 8, verbose: bool = False) -> str:
        """Build formatted event context"""
        events = self.get_events(game_data, recent_events, limit)
        if not events:
            return "No significant recent developments."
        return self.format_events(events, style, verbose)
    
    def build_major_powers_context(self, game_data: Dict[str, Any], 
                                  include_focus: bool = True, verbose: bool = False) -> str:
        """Build formatted major powers context"""
        major_powers = self.get_major_powers(game_data)
        if not major_powers:
            return "No major power data available."
        
        context_lines = []
        for power in major_powers:
            line = (f"- {power.display_name} ({power.tag}): {power.ruling_party} government, "
                   f"{power.stability:.0f}% stability, {power.war_support:.0f}% war support")
            
            if include_focus:
                focus_info = self.get_focus_info(power.tag, power.raw_data, power.name)
                if focus_info and focus_info.current_focus_name:
                    line += f", pursuing {focus_info.current_focus_name} ({focus_info.progress:.0f}% complete)"
                    
                    if verbose and focus_info.current_focus_description:
                        description = focus_info.current_focus_description
                        if not verbose and len(description) > 150:
                            description = description[:150] + "..."
                        line += f"\n  Policy: {description}"
            
            context_lines.append(line)
        
        return "\n".join(context_lines)
    
    def build_comprehensive_context(self, game_data: Dict[str, Any], 
                                  recent_events: Optional[List] = None,
                                  event_style: str = 'standard',
                                  include_focus: bool = True,
                                  verbose: bool = False) -> Dict[str, str]:
        """Build comprehensive context with all major components"""
        context = {}
        
        # Date and metadata
        metadata = game_data.get('metadata', {})
        context['date'] = metadata.get('date', 'Unknown')
        context['player'] = metadata.get('player', 'Unknown')
        
        # Events
        context['events'] = self.build_event_context(
            game_data, recent_events, event_style, verbose=verbose
        )
        
        # Major powers
        context['major_powers'] = self.build_major_powers_context(
            game_data, include_focus, verbose
        )
        
        return context
    
    def create_game_context(self, game_data: Dict[str, Any]):
        """Create comprehensive game context using services"""
        return create_game_context_from_data(
            game_data,
            self.services.event_service,
            self.services.country_service,
            self.services.focus_service
        )


class LegacyCompatibleGenerator(EnhancedBaseGenerator):
    """
    Compatibility layer for generators that need to work with both old and new systems
    """
    
    def __init__(self, services: ServiceContainer = None, localizer=None, 
                 game_data_loader=None, event_analyzer=None, focus_analyzer=None):
        """
        Initialize with either services or legacy components
        
        Args:
            services: ServiceContainer (preferred)
            localizer: Legacy HOI4Localizer 
            game_data_loader: Legacy GameDataLoader
            event_analyzer: Legacy EventAnalyzer
            focus_analyzer: Legacy FocusAnalyzer
        """
        if services:
            super().__init__(services)
        elif localizer:
            # Create services from legacy components
            services = ServiceContainer.create_from_existing_components(
                localizer=localizer,
                game_data_loader=game_data_loader,
                event_analyzer=event_analyzer,
                focus_analyzer=focus_analyzer
            )
            super().__init__(services)
        else:
            raise ValueError("Must provide either services or localizer")


# Migration helper functions

def migrate_generator_to_services(generator_class, services: ServiceContainer):
    """
    Helper to inject services into an existing generator class
    
    Args:
        generator_class: Existing generator class
        services: ServiceContainer to inject
        
    Returns:
        Enhanced generator instance with service access
    """
    # Create instance
    instance = generator_class()
    
    # Inject services
    services.inject_into_generator(instance)
    
    return instance


def create_enhanced_generator_factory(generator_class):
    """
    Create factory function for enhanced generator creation
    
    Args:
        generator_class: Generator class to enhance
        
    Returns:
        Factory function that creates enhanced generators
    """
    def factory(services: ServiceContainer):
        """Factory function"""
        if issubclass(generator_class, EnhancedBaseGenerator):
            return generator_class(services)
        else:
            return migrate_generator_to_services(generator_class, services)
    
    return factory