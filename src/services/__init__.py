#!/usr/bin/env python3
"""
Services Package
Centralized services for consistent data access and processing
"""

from .event_service import EventService, EventInfo
from .country_service import CountryService, CountryInfo
from .focus_service import FocusService
from .service_container import ServiceContainer
from . import utils

# Phase 4: Standardized Data Format Components
from .data_format import (
    StandardizedGameData, StandardizedCountry, StandardizedPolitical,
    StandardizedFocus, StandardizedEvent, StandardizedMetadata,
    PoliticalSystem, EventSeverity
)
from .data_converter import (
    DataConverter, LegacyCompatibilityWrapper,
    convert_legacy_data, create_legacy_wrapper
)

__all__ = [
    # Phase 1-3 Services
    'EventService', 'EventInfo',
    'CountryService', 'CountryInfo', 
    'FocusService',
    'ServiceContainer',
    'utils',
    
    # Phase 4 Standardized Data Format
    'StandardizedGameData', 'StandardizedCountry', 'StandardizedPolitical',
    'StandardizedFocus', 'StandardizedEvent', 'StandardizedMetadata',
    'PoliticalSystem', 'EventSeverity',
    
    # Phase 4 Data Conversion
    'DataConverter', 'LegacyCompatibilityWrapper',
    'convert_legacy_data', 'create_legacy_wrapper'
]