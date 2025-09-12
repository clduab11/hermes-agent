"""
Legal NLP Processing for HERMES Voice Pipeline
Copyright (c) 2025 Parallax Analytics LLC. All rights reserved.

Provides legal-domain specific natural language processing:
- Legal entity extraction (contracts, parties, dates, amounts)
- Legal concept recognition (liability, damages, jurisdiction)
- Compliance and risk assessment
- Legal disclaimer injection
- Multi-jurisdiction support
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class LegalEntityType(str, Enum):
    """Types of legal entities that can be extracted."""
    PERSON = "person"
    ORGANIZATION = "organization"
    CONTRACT = "contract"
    CASE_CITATION = "case_citation"
    STATUTE = "statute"
    REGULATION = "regulation"
    DATE = "date"
    MONETARY_AMOUNT = "monetary_amount"
    JURISDICTION = "jurisdiction"
    LEGAL_CONCEPT = "legal_concept"
    DEADLINE = "deadline"
    LIABILITY = "liability"
    DAMAGES = "damages"
    PENALTY = "penalty"


class LegalRiskLevel(str, Enum):
    """Risk levels for legal content."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LegalJurisdiction(str, Enum):
    """Supported legal jurisdictions."""
    FEDERAL = "federal"
    CALIFORNIA = "california"
    NEW_YORK = "new_york"
    TEXAS = "texas"
    FLORIDA = "florida"
    GENERIC_US = "generic_us"
    INTERNATIONAL = "international"


@dataclass
class LegalEntity:
    """Represents an extracted legal entity."""
    text: str
    entity_type: LegalEntityType
    confidence: float
    start_pos: int
    end_pos: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    jurisdiction: Optional[LegalJurisdiction] = None


@dataclass
class LegalConcept:
    """Represents a legal concept or principle."""
    concept: str
    definition: str
    relevance: float
    risk_level: LegalRiskLevel
    requires_attorney: bool = False
    compliance_notes: List[str] = field(default_factory=list)


@dataclass
class LegalAnalysis:
    """Complete legal analysis of text."""
    original_text: str
    entities: List[LegalEntity]
    concepts: List[LegalConcept]
    overall_risk: LegalRiskLevel
    compliance_score: float
    requires_human_review: bool
    disclaimers: List[str]
    recommendations: List[str]
    analyzed_at: datetime = field(default_factory=datetime.utcnow)


class LegalNLPProcessor:
    """Main processor for legal NLP tasks."""
    
    def __init__(self, jurisdiction: LegalJurisdiction = LegalJurisdiction.GENERIC_US):
        self.jurisdiction = jurisdiction
        self.legal_patterns = self._load_legal_patterns()
        self.prohibited_phrases = self._load_prohibited_phrases()
        self.legal_concepts_db = self._load_legal_concepts()
        self.compliance_thresholds = {
            "min_confidence": 0.85,
            "high_risk_threshold": 0.7,
            "attorney_review_threshold": 0.6
        }
    
    def analyze_text(self, text: str) -> LegalAnalysis:
        """Perform comprehensive legal analysis of text."""
        try:
            # Extract legal entities
            entities = self._extract_legal_entities(text)
            
            # Identify legal concepts
            concepts = self._identify_legal_concepts(text, entities)
            
            # Assess risk level
            risk_level = self._assess_risk_level(text, entities, concepts)
            
            # Calculate compliance score
            compliance_score = self._calculate_compliance_score(text, entities, concepts)
            
            # Determine if human review is needed
            requires_review = self._requires_human_review(risk_level, compliance_score)
            
            # Generate disclaimers
            disclaimers = self._generate_disclaimers(concepts, risk_level)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(entities, concepts, risk_level)
            
            analysis = LegalAnalysis(
                original_text=text,
                entities=entities,
                concepts=concepts,
                overall_risk=risk_level,
                compliance_score=compliance_score,
                requires_human_review=requires_review,
                disclaimers=disclaimers,
                recommendations=recommendations
            )
            
            logger.debug(f"Legal analysis completed: {len(entities)} entities, {len(concepts)} concepts, risk={risk_level}")
            return analysis
            
        except Exception as e:
            logger.error(f"Legal NLP analysis failed: {e}")
            # Return safe fallback analysis
            return self._create_fallback_analysis(text)
    
    def _extract_legal_entities(self, text: str) -> List[LegalEntity]:
        """Extract legal entities from text using patterns and rules."""
        entities = []
        
        try:
            # Extract monetary amounts
            money_pattern = r'\$[\d,]+(?:\.\d{2})?|\b\d+(?:,\d{3})*(?:\.\d{2})?\s*dollars?'
            for match in re.finditer(money_pattern, text, re.IGNORECASE):
                entities.append(LegalEntity(
                    text=match.group(),
                    entity_type=LegalEntityType.MONETARY_AMOUNT,
                    confidence=0.9,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    metadata={"amount": self._parse_monetary_amount(match.group())}
                ))
            
            # Extract dates
            date_patterns = [
                r'\b\d{1,2}/\d{1,2}/\d{4}\b',  # MM/DD/YYYY
                r'\b\d{4}-\d{2}-\d{2}\b',      # YYYY-MM-DD
                r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
            ]
            
            for pattern in date_patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    entities.append(LegalEntity(
                        text=match.group(),
                        entity_type=LegalEntityType.DATE,
                        confidence=0.85,
                        start_pos=match.start(),
                        end_pos=match.end()
                    ))
            
            # Extract case citations
            citation_pattern = r'\b\d+\s+[A-Z][a-z.]+\s+\d+(?:\s*\([A-Z][a-z.]*\s+\d{4}\))?'
            for match in re.finditer(citation_pattern, text):
                entities.append(LegalEntity(
                    text=match.group(),
                    entity_type=LegalEntityType.CASE_CITATION,
                    confidence=0.8,
                    start_pos=match.start(),
                    end_pos=match.end()
                ))
            
            # Extract contract-related terms
            contract_terms = [
                'agreement', 'contract', 'lease', 'deed', 'will', 'testament',
                'settlement', 'covenant', 'warrant', 'indemnification'
            ]
            
            for term in contract_terms:
                pattern = rf'\b{term}(?:s)?\b'
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    entities.append(LegalEntity(
                        text=match.group(),
                        entity_type=LegalEntityType.CONTRACT,
                        confidence=0.75,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        metadata={"term_type": term}
                    ))
            
            # Extract jurisdiction indicators
            jurisdictions = {
                'federal': ['federal', 'constitutional', 'supreme court', 'circuit court'],
                'california': ['california', 'ca state', 'cal. code'],
                'new_york': ['new york', 'ny state', 'n.y.']
            }
            
            for jurisdiction, indicators in jurisdictions.items():
                for indicator in indicators:
                    pattern = rf'\b{re.escape(indicator)}\b'
                    for match in re.finditer(pattern, text, re.IGNORECASE):
                        entities.append(LegalEntity(
                            text=match.group(),
                            entity_type=LegalEntityType.JURISDICTION,
                            confidence=0.7,
                            start_pos=match.start(),
                            end_pos=match.end(),
                            jurisdiction=LegalJurisdiction(jurisdiction),
                            metadata={"indicator": indicator}
                        ))
            
            # Extract legal concepts
            legal_concept_terms = [
                'negligence', 'liability', 'damages', 'breach', 'tort', 'fiduciary',
                'consideration', 'capacity', 'duress', 'fraud', 'statute of limitations',
                'due process', 'equal protection', 'habeas corpus', 'probable cause'
            ]
            
            for term in legal_concept_terms:
                pattern = rf'\b{term}\b'
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    entities.append(LegalEntity(
                        text=match.group(),
                        entity_type=LegalEntityType.LEGAL_CONCEPT,
                        confidence=0.8,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        metadata={"concept_category": self._categorize_legal_concept(term)}
                    ))
            
            # Sort entities by position
            entities.sort(key=lambda e: e.start_pos)
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
        
        return entities
    
    def _identify_legal_concepts(self, text: str, entities: List[LegalEntity]) -> List[LegalConcept]:
        """Identify legal concepts based on text and extracted entities."""
        concepts = []
        
        try:
            # Analyze for contract law concepts
            if any(e.entity_type == LegalEntityType.CONTRACT for e in entities):
                concepts.extend(self._analyze_contract_concepts(text, entities))
            
            # Analyze for tort law concepts
            tort_indicators = ['negligence', 'liability', 'damages', 'injury', 'duty', 'breach']
            if any(indicator in text.lower() for indicator in tort_indicators):
                concepts.extend(self._analyze_tort_concepts(text, entities))
            
            # Analyze for procedural concepts
            procedural_indicators = ['filing', 'deadline', 'statute of limitations', 'discovery', 'motion']
            if any(indicator in text.lower() for indicator in procedural_indicators):
                concepts.extend(self._analyze_procedural_concepts(text, entities))
            
            # Analyze for compliance concepts
            compliance_indicators = ['regulation', 'compliance', 'violation', 'penalty', 'fine']
            if any(indicator in text.lower() for indicator in compliance_indicators):
                concepts.extend(self._analyze_compliance_concepts(text, entities))
            
        except Exception as e:
            logger.error(f"Concept identification failed: {e}")
        
        return concepts
    
    def _analyze_contract_concepts(self, text: str, entities: List[LegalEntity]) -> List[LegalConcept]:
        """Analyze contract-related legal concepts."""
        concepts = []
        
        # Check for offer and acceptance
        if re.search(r'\b(?:offer|propose|accept|agree)\b', text, re.IGNORECASE):
            concepts.append(LegalConcept(
                concept="Contract Formation",
                definition="The process of creating a legally binding agreement",
                relevance=0.8,
                risk_level=LegalRiskLevel.MEDIUM,
                requires_attorney=True,
                compliance_notes=["Ensure all elements of contract formation are present"]
            ))
        
        # Check for consideration
        monetary_entities = [e for e in entities if e.entity_type == LegalEntityType.MONETARY_AMOUNT]
        if monetary_entities or re.search(r'\b(?:consideration|payment|exchange)\b', text, re.IGNORECASE):
            concepts.append(LegalConcept(
                concept="Consideration",
                definition="Something of value exchanged between parties",
                relevance=0.9,
                risk_level=LegalRiskLevel.LOW,
                compliance_notes=["Verify adequate consideration exists"]
            ))
        
        return concepts
    
    def _analyze_tort_concepts(self, text: str, entities: List[LegalEntity]) -> List[LegalConcept]:
        """Analyze tort law concepts."""
        concepts = []
        
        if re.search(r'\bnegligence\b', text, re.IGNORECASE):
            concepts.append(LegalConcept(
                concept="Negligence",
                definition="Failure to exercise reasonable care",
                relevance=0.95,
                risk_level=LegalRiskLevel.HIGH,
                requires_attorney=True,
                compliance_notes=[
                    "Assess duty, breach, causation, and damages",
                    "Consider comparative negligence rules"
                ]
            ))
        
        if re.search(r'\b(?:damages|compensation|injury)\b', text, re.IGNORECASE):
            concepts.append(LegalConcept(
                concept="Damages",
                definition="Monetary compensation for harm or loss",
                relevance=0.85,
                risk_level=LegalRiskLevel.MEDIUM,
                compliance_notes=["Determine type and measure of damages"]
            ))
        
        return concepts
    
    def _analyze_procedural_concepts(self, text: str, entities: List[LegalEntity]) -> List[LegalConcept]:
        """Analyze procedural law concepts."""
        concepts = []
        
        if re.search(r'\b(?:deadline|statute of limitations|time limit)\b', text, re.IGNORECASE):
            concepts.append(LegalConcept(
                concept="Statute of Limitations",
                definition="Time limit for filing legal claims",
                relevance=0.9,
                risk_level=LegalRiskLevel.CRITICAL,
                requires_attorney=True,
                compliance_notes=[
                    "Verify applicable statute of limitations",
                    "Check for any tolling provisions"
                ]
            ))
        
        return concepts
    
    def _analyze_compliance_concepts(self, text: str, entities: List[LegalEntity]) -> List[LegalConcept]:
        """Analyze compliance-related concepts."""
        concepts = []
        
        if re.search(r'\b(?:regulation|compliance|violation)\b', text, re.IGNORECASE):
            concepts.append(LegalConcept(
                concept="Regulatory Compliance",
                definition="Adherence to laws and regulations",
                relevance=0.8,
                risk_level=LegalRiskLevel.HIGH,
                requires_attorney=True,
                compliance_notes=["Review applicable regulations and compliance requirements"]
            ))
        
        return concepts
    
    def _assess_risk_level(self, text: str, entities: List[LegalEntity], concepts: List[LegalConcept]) -> LegalRiskLevel:
        """Assess overall risk level of the legal content."""
        try:
            risk_factors = []
            
            # Check for prohibited phrases
            for phrase in self.prohibited_phrases:
                if phrase.lower() in text.lower():
                    risk_factors.append(("prohibited_phrase", 0.9))
            
            # Check for high-risk concepts
            for concept in concepts:
                if concept.risk_level == LegalRiskLevel.CRITICAL:
                    risk_factors.append(("critical_concept", 0.95))
                elif concept.risk_level == LegalRiskLevel.HIGH:
                    risk_factors.append(("high_risk_concept", 0.8))
            
            # Check for legal advice indicators
            advice_indicators = [
                'you should', 'i recommend', 'my advice', 'legal opinion',
                'you must', 'required to', 'shall', 'obligation'
            ]
            for indicator in advice_indicators:
                if indicator in text.lower():
                    risk_factors.append(("advice_indicator", 0.7))
            
            # Calculate overall risk
            if not risk_factors:
                return LegalRiskLevel.LOW
            
            max_risk = max(risk_factors, key=lambda x: x[1])[1]
            
            if max_risk >= 0.9:
                return LegalRiskLevel.CRITICAL
            elif max_risk >= 0.7:
                return LegalRiskLevel.HIGH
            elif max_risk >= 0.5:
                return LegalRiskLevel.MEDIUM
            else:
                return LegalRiskLevel.LOW
                
        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
            return LegalRiskLevel.HIGH  # Default to high risk on error
    
    def _calculate_compliance_score(self, text: str, entities: List[LegalEntity], concepts: List[LegalConcept]) -> float:
        """Calculate compliance score (0-100)."""
        try:
            score = 100.0
            
            # Deduct points for prohibited content
            for phrase in self.prohibited_phrases:
                if phrase.lower() in text.lower():
                    score -= 20
            
            # Deduct points for high-risk concepts without disclaimers
            high_risk_concepts = [c for c in concepts if c.risk_level in [LegalRiskLevel.HIGH, LegalRiskLevel.CRITICAL]]
            if high_risk_concepts and 'disclaimer' not in text.lower():
                score -= 15 * len(high_risk_concepts)
            
            # Deduct points for potential legal advice
            if re.search(r'\b(?:you should|i recommend|my advice|legal opinion)\b', text, re.IGNORECASE):
                score -= 25
            
            # Bonus points for proper disclaimers
            if 'not legal advice' in text.lower() or 'consult an attorney' in text.lower():
                score += 10
            
            return max(0.0, min(100.0, score))
            
        except Exception as e:
            logger.error(f"Compliance score calculation failed: {e}")
            return 50.0  # Default to medium compliance on error
    
    def _requires_human_review(self, risk_level: LegalRiskLevel, compliance_score: float) -> bool:
        """Determine if human review is required."""
        if risk_level in [LegalRiskLevel.HIGH, LegalRiskLevel.CRITICAL]:
            return True
        
        if compliance_score < self.compliance_thresholds["attorney_review_threshold"] * 100:
            return True
        
        return False
    
    def _generate_disclaimers(self, concepts: List[LegalConcept], risk_level: LegalRiskLevel) -> List[str]:
        """Generate appropriate legal disclaimers."""
        disclaimers = []
        
        # Always include general disclaimer
        disclaimers.append(
            "This information is provided for general informational purposes only and "
            "does not constitute legal advice. Please consult with a qualified attorney "
            "for advice regarding your specific situation."
        )
        
        # Add specific disclaimers based on risk level
        if risk_level in [LegalRiskLevel.HIGH, LegalRiskLevel.CRITICAL]:
            disclaimers.append(
                "IMPORTANT: This matter involves complex legal issues that require "
                "immediate attention from a licensed attorney."
            )
        
        # Add concept-specific disclaimers
        concept_types = {c.concept for c in concepts}
        
        if "Statute of Limitations" in concept_types:
            disclaimers.append(
                "Time limits for legal action vary by jurisdiction and case type. "
                "Consult an attorney immediately to protect your rights."
            )
        
        if "Negligence" in concept_types:
            disclaimers.append(
                "Negligence claims involve complex legal standards and requirements. "
                "Professional legal evaluation is strongly recommended."
            )
        
        return disclaimers
    
    def _generate_recommendations(self, entities: List[LegalEntity], concepts: List[LegalConcept], risk_level: LegalRiskLevel) -> List[str]:
        """Generate recommendations based on legal analysis."""
        recommendations = []
        
        if risk_level in [LegalRiskLevel.HIGH, LegalRiskLevel.CRITICAL]:
            recommendations.append("Consult with a qualified attorney immediately")
        
        # Time-sensitive recommendations
        time_sensitive_entities = [e for e in entities if e.entity_type in [LegalEntityType.DATE, LegalEntityType.DEADLINE]]
        if time_sensitive_entities:
            recommendations.append("Review all dates and deadlines with legal counsel")
        
        # Monetary recommendations
        monetary_entities = [e for e in entities if e.entity_type == LegalEntityType.MONETARY_AMOUNT]
        if monetary_entities:
            recommendations.append("Have all financial terms reviewed by an attorney")
        
        # Concept-specific recommendations
        for concept in concepts:
            if concept.requires_attorney:
                recommendations.append(f"Seek legal advice regarding {concept.concept.lower()}")
        
        return list(set(recommendations))  # Remove duplicates
    
    def _create_fallback_analysis(self, text: str) -> LegalAnalysis:
        """Create safe fallback analysis when processing fails."""
        return LegalAnalysis(
            original_text=text,
            entities=[],
            concepts=[],
            overall_risk=LegalRiskLevel.HIGH,  # Default to high risk for safety
            compliance_score=50.0,
            requires_human_review=True,
            disclaimers=[
                "This information could not be properly analyzed. Please consult "
                "with a qualified attorney for any legal matters."
            ],
            recommendations=["Consult with a qualified attorney immediately"]
        )
    
    def _load_legal_patterns(self) -> Dict[str, List[str]]:
        """Load legal pattern matching rules."""
        return {
            "contract_terms": [
                "agreement", "contract", "covenant", "terms", "conditions",
                "offer", "acceptance", "consideration", "capacity", "legality"
            ],
            "tort_terms": [
                "negligence", "liability", "damages", "duty", "breach",
                "causation", "injury", "harm", "fault"
            ],
            "procedural_terms": [
                "filing", "deadline", "statute of limitations", "discovery",
                "motion", "hearing", "trial", "appeal"
            ]
        }
    
    def _load_prohibited_phrases(self) -> List[str]:
        """Load phrases that should trigger high-risk assessment."""
        return [
            "this is legal advice",
            "i am your attorney",
            "attorney-client relationship",
            "you will win",
            "guaranteed outcome",
            "you should sue",
            "you have a strong case",
            "you will recover"
        ]
    
    def _load_legal_concepts(self) -> Dict[str, Dict[str, Any]]:
        """Load database of legal concepts and their definitions."""
        return {
            "negligence": {
                "definition": "Failure to exercise reasonable care",
                "elements": ["duty", "breach", "causation", "damages"],
                "risk_level": "high"
            },
            "contract": {
                "definition": "Legally binding agreement between parties",
                "elements": ["offer", "acceptance", "consideration", "capacity", "legality"],
                "risk_level": "medium"
            }
        }
    
    def _parse_monetary_amount(self, amount_text: str) -> float:
        """Parse monetary amount from text."""
        try:
            # Remove currency symbols and commas
            cleaned = re.sub(r'[$,]', '', amount_text)
            # Extract numeric value
            match = re.search(r'[\d.]+', cleaned)
            if match:
                return float(match.group())
        except:
            pass
        return 0.0
    
    def _categorize_legal_concept(self, term: str) -> str:
        """Categorize a legal concept term."""
        categories = {
            "contract": ["consideration", "capacity", "offer", "acceptance"],
            "tort": ["negligence", "liability", "damages", "duty", "breach"],
            "constitutional": ["due process", "equal protection", "habeas corpus"],
            "criminal": ["probable cause", "miranda rights", "search warrant"]
        }
        
        for category, terms in categories.items():
            if term.lower() in terms:
                return category
        
        return "general"


# Global processor instance
legal_nlp = LegalNLPProcessor()