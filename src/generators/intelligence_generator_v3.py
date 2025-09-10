#!/usr/bin/env python3
"""
Phase 4: Intelligence Generator V3
Demonstration of Phase 4 standardized data format capabilities
"""

from typing import Dict, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from generators.standardized_base_generator import StandardizedBaseGenerator
from services.data_format import StandardizedGameData, EventSeverity, PoliticalSystem


class IntelligenceGeneratorV3(StandardizedBaseGenerator):
    """
    Phase 4 Intelligence Generator using standardized data format
    
    Key improvements over V2:
    - Uses standardized data structures
    - Rich helper methods for data access
    - Automatic event categorization and severity filtering
    - Enhanced political analysis
    - Better focus tree integration
    """
    
    def generate_prompt(self, game_data: StandardizedGameData, **kwargs) -> str:
        verbose = kwargs.get('verbose', False)
        
        # Build enhanced world context using standardized data
        context = self._build_enhanced_world_context(game_data, verbose=verbose)
        
        return f"""You are a diplomatic intelligence analyst in {game_data.metadata.date}. 
Analyze the current world situation and write a comprehensive intelligence briefing.

CURRENT GLOBAL SITUATION:
{context}

Write a detailed intelligence briefing (4-5 paragraphs) covering:

1. **Critical Developments**: Most urgent global developments requiring immediate attention
2. **Political Instability**: Countries experiencing internal turmoil and potential flashpoints  
3. **Military Preparations**: Nations showing signs of war readiness and mobilization
4. **Strategic Alliances**: Key power dynamics and shifting relationships between major nations
5. **Policy Implications**: How current national focus activities affect global balance
6. **Intelligence Assessment**: Strategic implications for world stability and security

Write in the style of a classified intelligence assessment - analytical, precise, but engaging.
Include threat assessments and strategic recommendations where appropriate."""
    
    def get_max_tokens(self) -> int:
        return 1500  # Enhanced for richer analysis
    
    def _build_enhanced_world_context(self, game_data: StandardizedGameData, verbose: bool = False) -> str:
        """Build rich world context using Phase 4 standardized data"""
        context_sections = []
        
        # Critical events analysis
        critical_events = self.get_events_by_severity(game_data, EventSeverity.CRITICAL)
        high_events = self.get_events_by_severity(game_data, EventSeverity.HIGH)
        
        if critical_events or high_events:
            urgent_events = critical_events + high_events[-3:]  # Most recent high-severity
            events_text = self.format_event_list(urgent_events, 
                                               include_descriptions=verbose,
                                               max_description_length=200 if verbose else 120)
            context_sections.append(f"URGENT DEVELOPMENTS:\n{events_text}")
        
        # Political instability analysis
        unstable_countries = self.get_unstable_countries(game_data, threshold=40.0)
        if unstable_countries:
            instability_analysis = self._analyze_political_instability(unstable_countries)
            context_sections.append(f"POLITICAL INSTABILITY ANALYSIS:\n{instability_analysis}")
        
        # Military readiness assessment
        war_ready_countries = self.get_war_ready_countries(game_data, threshold=70.0)
        if war_ready_countries:
            military_analysis = self._analyze_military_readiness(war_ready_countries)
            context_sections.append(f"MILITARY READINESS ASSESSMENT:\n{military_analysis}")
        
        # Major powers comprehensive analysis
        major_powers_analysis = self._analyze_major_powers(game_data, verbose=verbose)
        context_sections.append(f"MAJOR POWERS ANALYSIS:\n{major_powers_analysis}")
        
        # Ideological balance assessment
        ideology_analysis = self._analyze_ideological_balance(game_data)
        context_sections.append(f"GLOBAL IDEOLOGICAL BALANCE:\n{ideology_analysis}")
        
        # Focus tree intelligence (policy changes)
        focus_intelligence = self._analyze_focus_activities(game_data, verbose=verbose)
        if focus_intelligence:
            context_sections.append(f"POLICY INTELLIGENCE:\n{focus_intelligence}")
        
        return "\n\n".join(context_sections)
    
    def _analyze_political_instability(self, unstable_countries) -> str:
        """Analyze countries with political instability"""
        analysis = []
        
        for country in unstable_countries[:5]:  # Top 5 most unstable
            stability = country.political.stability
            war_support = country.political.war_support
            
            risk_level = "CRITICAL" if stability < 20 else "HIGH" if stability < 35 else "MODERATE"
            
            line = f"- {country.name}: {risk_level} RISK ({stability:.1f}% stability)"
            
            # Additional risk factors
            risk_factors = []
            if war_support < 20:
                risk_factors.append("strong anti-war sentiment")
            elif war_support > 80:
                risk_factors.append("high militarization risk")
            
            if country.political.political_power < 50:
                risk_factors.append("governmental paralysis")
            
            if risk_factors:
                line += f" - {', '.join(risk_factors)}"
            
            # Party competition analysis
            if country.political.party_support:
                sorted_parties = sorted(country.political.party_support.items(), 
                                      key=lambda x: x[1], reverse=True)
                if len(sorted_parties) > 1:
                    margin = sorted_parties[0][1] - sorted_parties[1][1]
                    if margin < 10:
                        line += f" - Political deadlock ({sorted_parties[0][0]} vs {sorted_parties[1][0]})"
            
            analysis.append(line)
        
        return "\n".join(analysis)
    
    def _analyze_military_readiness(self, war_ready_countries) -> str:
        """Analyze countries showing military readiness"""
        analysis = []
        
        for country in war_ready_countries[:5]:  # Top 5 most war-ready
            war_support = country.political.war_support
            stability = country.political.stability
            
            threat_level = "HIGH" if war_support > 85 else "ELEVATED" if war_support > 75 else "MODERATE"
            
            line = f"- {country.name}: {threat_level} THREAT ({war_support:.1f}% war support)"
            
            # Capability assessment
            capability_factors = []
            if stability > 70:
                capability_factors.append("stable government")
            if country.political.political_power > 300:
                capability_factors.append("strong state capacity")
            if country.is_major_power:
                capability_factors.append("major power resources")
            
            if capability_factors:
                line += f" - Capabilities: {', '.join(capability_factors)}"
            
            # Focus context
            if country.focus and country.focus.current_focus:
                focus_name = country.focus.current_focus_name or country.focus.current_focus
                if any(term in focus_name.lower() for term in ['military', 'army', 'war', 'rearm']):
                    line += f" - Military focus: {focus_name}"
            
            analysis.append(line)
        
        return "\n".join(analysis)
    
    def _analyze_major_powers(self, game_data: StandardizedGameData, verbose: bool = False) -> str:
        """Enhanced major powers analysis using standardized data"""
        major_powers = self.get_major_powers(game_data)
        if not major_powers:
            return "No major powers data available."
        
        analysis = []
        
        for power in major_powers:
            pol = power.political
            focus = power.focus
            
            # Basic assessment
            stability_desc = self.describe_stability(pol.stability)
            war_support_desc = self.describe_war_support(pol.war_support)
            
            line = f"- {power.name} ({power.tag}): {pol.political_system.value} regime, {stability_desc}, {war_support_desc}"
            
            # Enhanced focus analysis
            if focus and focus.current_focus:
                progress_desc = f"{focus.progress:.0f}% complete"
                if focus.is_paused:
                    progress_desc += " (PAUSED)"
                
                line += f"\n  Current Policy: {focus.current_focus_name} ({progress_desc})"
                
                # Add focus description for intelligence context
                if verbose and focus.current_focus_description:
                    desc = focus.current_focus_description
                    if len(desc) > 150:
                        desc = desc[:150] + "..."
                    line += f"\n    Intelligence: {desc}"
            
            # Recent policy completions
            if focus and focus.completed_focus_names:
                recent_count = min(3, len(focus.completed_focus_names))
                recent_focuses = focus.completed_focus_names[-recent_count:]
                line += f"\n  Recent Policies: {', '.join(recent_focuses)}"
            
            # Political dynamics
            if pol.party_support and len(pol.party_support) > 1:
                sorted_parties = sorted(pol.party_support.items(), key=lambda x: x[1], reverse=True)
                if sorted_parties[0][1] - sorted_parties[1][1] < 15:
                    line += f"\n  Political Competition: {sorted_parties[0][0]} vs {sorted_parties[1][0]}"
            
            # Special intelligence notes
            intel_notes = []
            if power.is_player:
                intel_notes.append("PLAYER NATION - direct decision-making observed")
            if pol.political_power > 500:
                intel_notes.append("high state capacity")
            elif pol.political_power < 100:
                intel_notes.append("limited governmental effectiveness")
            
            if intel_notes:
                line += f"\n  Intelligence Notes: {', '.join(intel_notes)}"
            
            analysis.append(line)
        
        return "\n".join(analysis)
    
    def _analyze_ideological_balance(self, game_data: StandardizedGameData) -> str:
        """Analyze global ideological balance"""
        major_powers = self.get_major_powers(game_data)
        
        # Count by ideology
        ideology_counts = {}
        ideology_powers = {}
        
        for power in major_powers:
            ideology = power.political.political_system
            if ideology not in ideology_counts:
                ideology_counts[ideology] = 0
                ideology_powers[ideology] = []
            
            ideology_counts[ideology] += 1
            ideology_powers[ideology].append(power.name)
        
        analysis = []
        analysis.append(f"Total Major Powers: {len(major_powers)}")
        
        # Detailed breakdown
        for ideology, count in sorted(ideology_counts.items(), key=lambda x: x[1], reverse=True):
            power_names = ideology_powers[ideology][:3]  # Top 3
            name_list = ", ".join(power_names)
            if len(ideology_powers[ideology]) > 3:
                name_list += f" (+{len(ideology_powers[ideology]) - 3} others)"
            
            analysis.append(f"{ideology.value.title()}: {count} powers ({name_list})")
        
        # Strategic balance assessment
        if len(ideology_counts) > 2:
            analysis.append("Assessment: Multi-polar ideological competition - high tension potential")
        elif PoliticalSystem.FASCIST in ideology_counts and PoliticalSystem.DEMOCRATIC in ideology_counts:
            analysis.append("Assessment: Fascist-Democratic confrontation axis - conflict likely")
        elif PoliticalSystem.COMMUNIST in ideology_counts:
            analysis.append("Assessment: Communist expansion concerns - ideological struggle ongoing")
        
        return "\n".join(analysis)
    
    def _analyze_focus_activities(self, game_data: StandardizedGameData, verbose: bool = False) -> str:
        """Analyze current focus tree activities for intelligence insights"""
        countries_with_focus = self.get_countries_with_active_focus(game_data)
        if not countries_with_focus:
            return ""
        
        # Categorize focuses by type
        military_focuses = []
        diplomatic_focuses = []
        economic_focuses = []
        political_focuses = []
        
        for country in countries_with_focus:
            if not country.focus or not country.focus.current_focus:
                continue
            
            focus_name = (country.focus.current_focus_name or country.focus.current_focus).lower()
            focus_desc = country.focus.current_focus_description or ""
            
            focus_info = {
                'country': country.name,
                'focus': country.focus.current_focus_name or country.focus.current_focus,
                'progress': country.focus.progress,
                'description': focus_desc[:100] + "..." if len(focus_desc) > 100 and not verbose else focus_desc
            }
            
            # Categorize by keywords
            if any(term in focus_name for term in ['military', 'army', 'navy', 'air', 'rearm', 'mobiliz']):
                military_focuses.append(focus_info)
            elif any(term in focus_name for term in ['diplomatic', 'alliance', 'treaty', 'foreign']):
                diplomatic_focuses.append(focus_info)
            elif any(term in focus_name for term in ['economic', 'industry', 'trade', 'infrastructure']):
                economic_focuses.append(focus_info)
            else:
                political_focuses.append(focus_info)
        
        analysis = []
        
        # Military intelligence
        if military_focuses:
            analysis.append("MILITARY PREPARATIONS:")
            for focus in military_focuses[:4]:  # Top 4
                line = f"  {focus['country']}: {focus['focus']} ({focus['progress']:.0f}%)"
                if verbose and focus['description']:
                    line += f" - {focus['description']}"
                analysis.append(line)
        
        # Diplomatic intelligence
        if diplomatic_focuses:
            analysis.append("DIPLOMATIC INITIATIVES:")
            for focus in diplomatic_focuses[:3]:
                line = f"  {focus['country']}: {focus['focus']} ({focus['progress']:.0f}%)"
                if verbose and focus['description']:
                    line += f" - {focus['description']}"
                analysis.append(line)
        
        # Economic intelligence (if significant)
        if len(economic_focuses) >= 2:
            analysis.append("ECONOMIC MOBILIZATION:")
            for focus in economic_focuses[:3]:
                line = f"  {focus['country']}: {focus['focus']} ({focus['progress']:.0f}%)"
                analysis.append(line)
        
        return "\n".join(analysis) if analysis else ""