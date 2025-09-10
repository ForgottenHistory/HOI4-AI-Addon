#!/usr/bin/env python3
"""
Service Container
Dependency injection container for managing service instances
"""

from typing import Optional
from .event_service import EventService
from .country_service import CountryService
from .focus_service import FocusService


class ServiceContainer:
    """
    Container for managing service dependencies and providing centralized access
    """
    
    def __init__(self, localizer, game_data_loader=None, event_analyzer=None, 
                 focus_analyzer=None, political_analyzer=None):
        """
        Initialize service container with core dependencies
        
        Args:
            localizer: HOI4Localizer instance (required)
            game_data_loader: GameDataLoader instance (optional)
            event_analyzer: EventAnalyzer instance (for legacy support)
            focus_analyzer: FocusAnalyzer instance (for legacy support)  
            political_analyzer: PoliticalAnalyzer instance (for legacy support)
        """
        # Store dependencies
        self._localizer = localizer
        self._game_data_loader = game_data_loader
        self._event_analyzer = event_analyzer
        self._focus_analyzer = focus_analyzer
        self._political_analyzer = political_analyzer
        
        # Service instances (lazy loaded)
        self._event_service: Optional[EventService] = None
        self._country_service: Optional[CountryService] = None
        self._focus_service: Optional[FocusService] = None
    
    @property
    def event_service(self) -> EventService:
        """Get EventService instance (lazy loaded)"""
        if self._event_service is None:
            self._event_service = EventService(event_analyzer=self._event_analyzer)
        return self._event_service
    
    @property
    def country_service(self) -> CountryService:
        """Get CountryService instance (lazy loaded)"""
        if self._country_service is None:
            self._country_service = CountryService(
                localizer=self._localizer,
                game_data_loader=self._game_data_loader,
                political_analyzer=self._political_analyzer
            )
        return self._country_service
    
    @property
    def focus_service(self) -> FocusService:
        """Get FocusService instance (lazy loaded)"""
        if self._focus_service is None:
            self._focus_service = FocusService(
                localizer=self._localizer,
                focus_analyzer=self._focus_analyzer
            )
        return self._focus_service
    
    @classmethod
    def create_from_existing_components(cls, localizer, game_data_loader=None, 
                                      event_analyzer=None, focus_analyzer=None, 
                                      political_analyzer=None) -> 'ServiceContainer':
        """
        Factory method to create container from existing component instances
        
        This method is designed for gradual migration - it allows existing code
        to continue using their analyzer instances while providing access to
        the new service layer.
        
        Args:
            localizer: HOI4Localizer instance
            game_data_loader: Optional GameDataLoader instance
            event_analyzer: Optional EventAnalyzer instance
            focus_analyzer: Optional FocusAnalyzer instance
            political_analyzer: Optional PoliticalAnalyzer instance
            
        Returns:
            ServiceContainer instance
        """
        return cls(
            localizer=localizer,
            game_data_loader=game_data_loader,
            event_analyzer=event_analyzer,
            focus_analyzer=focus_analyzer,
            political_analyzer=political_analyzer
        )
    
    @classmethod
    def create_minimal(cls, localizer) -> 'ServiceContainer':
        """
        Create minimal service container with just localizer
        
        Args:
            localizer: HOI4Localizer instance
            
        Returns:
            ServiceContainer instance with minimal dependencies
        """
        return cls(localizer=localizer)
    
    def get_all_services(self) -> tuple:
        """
        Get all service instances as tuple for unpacking
        
        Returns:
            Tuple of (event_service, country_service, focus_service)
        """
        return (self.event_service, self.country_service, self.focus_service)
    
    def inject_into_generator(self, generator_instance):
        """
        Inject services into a generator instance
        
        This method adds service properties to existing generator instances
        for gradual migration support.
        
        Args:
            generator_instance: Generator instance to inject services into
        """
        generator_instance.event_service = self.event_service
        generator_instance.country_service = self.country_service
        generator_instance.focus_service = self.focus_service
        generator_instance.services = self
    
    def create_enhanced_base_generator_mixin(self):
        """
        Create a mixin class that can be added to BaseGenerator
        
        Returns:
            Mixin class with service access methods
        """
        services = self
        
        class ServiceMixin:
            """Mixin to add service access to generators"""
            
            def get_events(self, game_data, recent_events=None, limit=8):
                """Get events using EventService"""
                return services.event_service.get_events_for_kwargs(
                    game_data, recent_events, limit
                )
            
            def format_events(self, events, style='standard', verbose=False):
                """Format events using EventService"""
                from .event_service import EventFormatStyle
                style_enum = getattr(EventFormatStyle, style.upper(), EventFormatStyle.STANDARD)
                return services.event_service.format_events(events, style_enum, verbose)
            
            def get_country_info(self, tag, game_data, country_data=None):
                """Get country info using CountryService"""
                return services.country_service.get_country_info(tag, game_data, country_data)
            
            def get_countries_info(self, tags, game_data):
                """Get multiple countries info using CountryService"""
                return services.country_service.get_countries_info(tags, game_data)
            
            def get_focus_info(self, tag, country_data, country_name=None):
                """Get focus info using FocusService"""
                return services.focus_service.get_focus_info(tag, country_data, country_name)
            
            def format_focus_status(self, focus_info, style='standard'):
                """Format focus status using FocusService"""
                from .focus_service import FocusFormatStyle
                style_enum = getattr(FocusFormatStyle, style.upper(), FocusFormatStyle.STANDARD)
                return services.focus_service.format_focus_status(focus_info, style_enum)
        
        return ServiceMixin