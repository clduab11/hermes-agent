"""
HERMES Voice Context Manager with Emotion Detection
Advanced conversation state management and emotional intelligence
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class EmotionalState(Enum):
    """Detected emotional states"""

    NEUTRAL = "neutral"
    POSITIVE = "positive"
    NEGATIVE = "negative"
    FRUSTRATED = "frustrated"
    ANXIOUS = "anxious"
    SATISFIED = "satisfied"
    CONFUSED = "confused"
    URGENT = "urgent"
    CALM = "calm"
    ANGRY = "angry"


class ConversationPhase(Enum):
    """Phases of legal conversation"""

    GREETING = "greeting"
    INTAKE = "intake"
    FACT_GATHERING = "fact_gathering"
    ADVICE_SEEKING = "advice_seeking"
    SCHEDULING = "scheduling"
    CLARIFICATION = "clarification"
    CLOSING = "closing"
    EMERGENCY = "emergency"


class ContextPriority(Enum):
    """Context information priority levels"""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class EmotionMetrics:
    """Emotion detection metrics"""

    primary_emotion: EmotionalState
    confidence: float
    secondary_emotions: List[EmotionalState]
    emotional_intensity: float
    stress_indicators: List[str]
    speech_patterns: Dict[str, float]
    voice_characteristics: Dict[str, float]


@dataclass
class ConversationContext:
    """Complete conversation context"""

    session_id: str
    client_id: Optional[str]
    tenant_id: str
    conversation_phase: ConversationPhase
    emotional_state: EmotionMetrics
    intent_history: List[str]
    entities_extracted: Dict[str, Any]
    matter_context: Optional[Dict[str, Any]]
    urgency_level: int
    confidential_flags: Set[str]
    last_updated: datetime
    metadata: Dict[str, Any]


@dataclass
class ContextMemory:
    """Memory item for conversation context"""

    key: str
    value: Any
    priority: ContextPriority
    created_at: datetime
    expires_at: Optional[datetime]
    access_count: int
    metadata: Dict[str, Any]


class VoiceContextManager:
    """Advanced voice conversation context manager with emotion detection"""

    def __init__(self, redis_client=None, legal_nlp_processor=None):
        self.redis_client = redis_client
        self.legal_nlp = legal_nlp_processor
        self.active_sessions: Dict[str, ConversationContext] = {}
        self.session_memories: Dict[str, Dict[str, ContextMemory]] = {}
        self.emotion_history: Dict[str, List[EmotionMetrics]] = {}

        # Configuration
        self.max_context_items = 1000
        self.memory_ttl_hours = 24
        self.emotion_sensitivity = 0.7
        self.context_decay_rate = 0.95

        # Emotion detection patterns
        self.emotion_patterns = {
            EmotionalState.FRUSTRATED: {
                "keywords": ["frustrated", "annoyed", "irritated", "fed up", "sick of"],
                "speech_indicators": {
                    "speaking_rate": (1.2, 2.0),
                    "volume": (0.7, 1.0),
                },
                "phrase_patterns": [
                    "why is this",
                    "this is ridiculous",
                    "i cannot believe",
                ],
            },
            EmotionalState.ANXIOUS: {
                "keywords": ["worried", "concerned", "nervous", "scared", "anxious"],
                "speech_indicators": {
                    "speaking_rate": (0.5, 0.9),
                    "pitch_variance": (0.2, 1.0),
                },
                "phrase_patterns": [
                    "what if",
                    "i am worried about",
                    "this makes me nervous",
                ],
            },
            EmotionalState.URGENT: {
                "keywords": ["urgent", "emergency", "immediately", "asap", "right now"],
                "speech_indicators": {
                    "speaking_rate": (1.3, 2.5),
                    "volume": (0.8, 1.0),
                },
                "phrase_patterns": [
                    "need this now",
                    "this is urgent",
                    "emergency situation",
                ],
            },
            EmotionalState.SATISFIED: {
                "keywords": ["great", "perfect", "excellent", "wonderful", "satisfied"],
                "speech_indicators": {
                    "tone_positivity": (0.6, 1.0),
                    "speaking_rate": (0.8, 1.2),
                },
                "phrase_patterns": ["that works", "sounds good", "perfect"],
            },
            EmotionalState.CONFUSED: {
                "keywords": [
                    "confused",
                    "unclear",
                    "do not understand",
                    "what does that mean",
                ],
                "speech_indicators": {
                    "pause_frequency": (0.3, 1.0),
                    "pitch_variance": (0.1, 0.4),
                },
                "phrase_patterns": [
                    "i do not understand",
                    "can you explain",
                    "what does that mean",
                ],
            },
        }

        # Legal conversation phase indicators
        self.phase_indicators = {
            ConversationPhase.GREETING: [
                "hello",
                "hi",
                "good morning",
                "good afternoon",
            ],
            ConversationPhase.INTAKE: [
                "need help with",
                "have a legal issue",
                "looking for lawyer",
            ],
            ConversationPhase.FACT_GATHERING: [
                "what happened",
                "when did",
                "where did",
                "details",
            ],
            ConversationPhase.ADVICE_SEEKING: [
                "what should i do",
                "what are my options",
                "legal advice",
            ],
            ConversationPhase.SCHEDULING: [
                "appointment",
                "meeting",
                "when can",
                "schedule",
            ],
            ConversationPhase.EMERGENCY: [
                "emergency",
                "urgent",
                "arrested",
                "court tomorrow",
            ],
        }

    async def create_session_context(
        self,
        session_id: str,
        client_id: str = None,
        tenant_id: str = "default",
        initial_metadata: Dict[str, Any] = None,
    ) -> ConversationContext:
        """Create new conversation context for session"""

        context = ConversationContext(
            session_id=session_id,
            client_id=client_id,
            tenant_id=tenant_id,
            conversation_phase=ConversationPhase.GREETING,
            emotional_state=EmotionMetrics(
                primary_emotion=EmotionalState.NEUTRAL,
                confidence=0.5,
                secondary_emotions=[],
                emotional_intensity=0.0,
                stress_indicators=[],
                speech_patterns={},
                voice_characteristics={},
            ),
            intent_history=[],
            entities_extracted={},
            matter_context=None,
            urgency_level=1,
            confidential_flags=set(),
            last_updated=datetime.utcnow(),
            metadata=initial_metadata or {},
        )

        self.active_sessions[session_id] = context
        self.session_memories[session_id] = {}
        self.emotion_history[session_id] = []

        logger.info(f"Created voice context for session {session_id}")

        # Store in Redis if available
        if self.redis_client:
            await self.store_context_redis(context)

        return context

    async def update_conversation_context(
        self,
        session_id: str,
        text_input: str = None,
        audio_features: Dict[str, float] = None,
        extracted_entities: Dict[str, Any] = None,
        detected_intent: str = None,
        legal_entities: List = None,
    ) -> ConversationContext:
        """Update conversation context with new information"""

        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        context = self.active_sessions[session_id]

        # Update emotion detection if audio features provided
        if audio_features or text_input:
            emotion_metrics = await self.detect_emotion(
                text_input, audio_features, session_id
            )
            context.emotional_state = emotion_metrics
            self.emotion_history[session_id].append(emotion_metrics)

        # Update conversation phase
        if text_input:
            new_phase = await self.detect_conversation_phase(text_input, context)
            if new_phase != context.conversation_phase:
                logger.info(
                    f"Session {session_id} phase changed: {context.conversation_phase} -> {new_phase}"
                )
                context.conversation_phase = new_phase

        # Extract and store entities
        legal_entities_dict = {}
        if self.legal_nlp and text_input:
            legal_entities_from_nlp = await self.legal_nlp.extract_legal_entities(
                text_input
            )
            legal_entities_dict.update(legal_entities_from_nlp)

        # Add any legal entities passed directly
        if legal_entities:
            for entity in legal_entities:
                legal_entities_dict[entity.text] = {
                    "type": entity.entity_type.value,
                    "confidence": entity.confidence,
                }

        if extracted_entities:
            legal_entities_dict.update(extracted_entities)

        if legal_entities_dict:
            context.entities_extracted.update(legal_entities_dict)

        # Update intent history
        if detected_intent:
            context.intent_history.append(detected_intent)
            # Keep only last 10 intents
            context.intent_history = context.intent_history[-10:]

        # Update urgency level based on emotion and content
        context.urgency_level = await self.calculate_urgency_level(context)

        # Check for confidential content
        if text_input:
            confidential_flags = await self.detect_confidential_content(text_input)
            context.confidential_flags.update(confidential_flags)

        context.last_updated = datetime.utcnow()

        # Store updated context
        if self.redis_client:
            await self.store_context_redis(context)

        logger.debug(f"Updated context for session {session_id}")
        return context

    async def detect_emotion(
        self,
        text: str = None,
        audio_features: Dict[str, float] = None,
        session_id: str = None,
    ) -> EmotionMetrics:
        """Detect emotional state from text and audio features"""

        emotion_scores = {}
        stress_indicators = []

        # Text-based emotion detection
        if text:
            text_lower = text.lower()

            for emotion, patterns in self.emotion_patterns.items():
                score = 0.0

                # Check keywords
                for keyword in patterns["keywords"]:
                    if keyword in text_lower:
                        score += 0.3

                # Check phrase patterns
                for pattern in patterns["phrase_patterns"]:
                    if pattern in text_lower:
                        score += 0.4

                emotion_scores[emotion] = min(score, 1.0)

        # Audio-based emotion detection
        if audio_features:
            for emotion, patterns in self.emotion_patterns.items():
                if "speech_indicators" in patterns:
                    audio_score = 0.0

                    for indicator, (min_val, max_val) in patterns[
                        "speech_indicators"
                    ].items():
                        if indicator in audio_features:
                            value = audio_features[indicator]
                            if min_val <= value <= max_val:
                                audio_score += 0.2

                    if emotion in emotion_scores:
                        emotion_scores[emotion] = (
                            emotion_scores[emotion] + audio_score
                        ) / 2
                    else:
                        emotion_scores[emotion] = audio_score

        # Determine primary and secondary emotions
        if emotion_scores:
            sorted_emotions = sorted(
                emotion_scores.items(), key=lambda x: x[1], reverse=True
            )
            primary_emotion = sorted_emotions[0][0]
            primary_confidence = sorted_emotions[0][1]
            secondary_emotions = [
                emotion for emotion, score in sorted_emotions[1:3] if score > 0.3
            ]
        else:
            primary_emotion = EmotionalState.NEUTRAL
            primary_confidence = 0.5
            secondary_emotions = []

        # Calculate emotional intensity and stress indicators
        intensity = max(emotion_scores.values()) if emotion_scores else 0.0

        if audio_features:
            # Detect stress indicators from audio
            if audio_features.get("speaking_rate", 1.0) > 1.5:
                stress_indicators.append("rapid_speech")
            if audio_features.get("volume", 0.5) > 0.8:
                stress_indicators.append("elevated_volume")
            if audio_features.get("pitch_variance", 0.5) > 0.7:
                stress_indicators.append("pitch_instability")

        return EmotionMetrics(
            primary_emotion=primary_emotion,
            confidence=primary_confidence,
            secondary_emotions=secondary_emotions,
            emotional_intensity=intensity,
            stress_indicators=stress_indicators,
            speech_patterns=audio_features or {},
            voice_characteristics={},
        )

    async def detect_conversation_phase(
        self, text: str, context: ConversationContext
    ) -> ConversationPhase:
        """Detect current phase of legal conversation"""

        text_lower = text.lower()
        phase_scores = {}

        # Score each phase based on indicators
        for phase, indicators in self.phase_indicators.items():
            score = 0.0
            for indicator in indicators:
                if indicator in text_lower:
                    score += 1.0
            phase_scores[phase] = score

        # Consider emotional urgency
        if context.emotional_state.primary_emotion == EmotionalState.URGENT:
            phase_scores[ConversationPhase.EMERGENCY] += 2.0

        # Consider current phase for continuity
        if context.conversation_phase in phase_scores:
            phase_scores[context.conversation_phase] += 0.5

        # Return highest scoring phase or current if no clear indication
        if phase_scores and max(phase_scores.values()) > 0:
            return max(phase_scores.items(), key=lambda x: x[1])[0]

        return context.conversation_phase

    async def calculate_urgency_level(self, context: ConversationContext) -> int:
        """Calculate urgency level from 1 (low) to 5 (emergency)"""

        base_urgency = 1

        # Emotional factors
        if context.emotional_state.primary_emotion in [
            EmotionalState.URGENT,
            EmotionalState.FRUSTRATED,
        ]:
            base_urgency += 2
        elif context.emotional_state.primary_emotion in [
            EmotionalState.ANXIOUS,
            EmotionalState.ANGRY,
        ]:
            base_urgency += 1

        # Conversation phase factors
        if context.conversation_phase == ConversationPhase.EMERGENCY:
            base_urgency += 3
        elif context.conversation_phase in [ConversationPhase.ADVICE_SEEKING]:
            base_urgency += 1

        # Legal entity urgency indicators
        urgent_entities = ["court_date", "deadline", "arrest", "emergency"]
        for entity_type in urgent_entities:
            if entity_type in context.entities_extracted:
                base_urgency += 1
                break

        # Emotional intensity
        if context.emotional_state.emotional_intensity > 0.7:
            base_urgency += 1

        return min(base_urgency, 5)

    async def detect_confidential_content(self, text: str) -> Set[str]:
        """Detect potentially confidential content"""

        flags = set()
        text_lower = text.lower()

        # Legal confidentiality indicators
        confidential_indicators = {
            "attorney_client": [
                "attorney-client",
                "privileged",
                "confidential communication",
            ],
            "personal_info": ["social security", "ssn", "date of birth", "dob"],
            "financial": ["bank account", "credit card", "income", "assets"],
            "medical": ["medical records", "health information", "medication"],
            "litigation": ["case details", "lawsuit", "legal strategy", "settlement"],
        }

        for flag_type, indicators in confidential_indicators.items():
            for indicator in indicators:
                if indicator in text_lower:
                    flags.add(flag_type)
                    break

        return flags

    async def store_context_memory(
        self,
        session_id: str,
        key: str,
        value: Any,
        priority: ContextPriority = ContextPriority.MEDIUM,
        ttl_hours: int = None,
    ) -> None:
        """Store information in session memory"""

        if session_id not in self.session_memories:
            self.session_memories[session_id] = {}

        expires_at = None
        if ttl_hours:
            expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
        elif ttl_hours is None:
            expires_at = datetime.utcnow() + timedelta(hours=self.memory_ttl_hours)

        memory_item = ContextMemory(
            key=key,
            value=value,
            priority=priority,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            access_count=0,
            metadata={},
        )

        self.session_memories[session_id][key] = memory_item

        # Clean up expired memories
        await self.cleanup_expired_memories(session_id)

        logger.debug(f"Stored memory item '{key}' for session {session_id}")

    async def retrieve_context_memory(
        self, session_id: str, key: str = None
    ) -> Optional[Any]:
        """Retrieve information from session memory"""

        if session_id not in self.session_memories:
            return None

        memories = self.session_memories[session_id]

        if key:
            if key in memories:
                memory = memories[key]
                memory.access_count += 1
                return memory.value
            return None

        # Return all non-expired memories
        valid_memories = {}
        now = datetime.utcnow()

        for mem_key, memory in memories.items():
            if memory.expires_at is None or memory.expires_at > now:
                memory.access_count += 1
                valid_memories[mem_key] = memory.value

        return valid_memories

    async def get_contextual_suggestions(
        self, session_id: str, current_text: str = None
    ) -> List[Dict[str, Any]]:
        """Generate contextual suggestions based on conversation state"""

        if session_id not in self.active_sessions:
            return []

        context = self.active_sessions[session_id]
        suggestions = []

        # Phase-based suggestions
        if context.conversation_phase == ConversationPhase.INTAKE:
            suggestions.append(
                {
                    "type": "question",
                    "text": "Can you tell me more about your legal matter?",
                    "priority": "high",
                }
            )
        elif context.conversation_phase == ConversationPhase.FACT_GATHERING:
            suggestions.append(
                {
                    "type": "clarification",
                    "text": "When did this incident occur?",
                    "priority": "medium",
                }
            )
        elif context.conversation_phase == ConversationPhase.SCHEDULING:
            suggestions.append(
                {
                    "type": "action",
                    "text": "I can schedule a consultation for you",
                    "priority": "high",
                }
            )

        # Emotion-based suggestions
        if context.emotional_state.primary_emotion == EmotionalState.ANXIOUS:
            suggestions.append(
                {
                    "type": "reassurance",
                    "text": "I understand this is concerning. Let me help you through this step by step.",
                    "priority": "high",
                }
            )
        elif context.emotional_state.primary_emotion == EmotionalState.FRUSTRATED:
            suggestions.append(
                {
                    "type": "de_escalation",
                    "text": "I apologize for any confusion. Let me clarify this for you.",
                    "priority": "high",
                }
            )
        elif context.emotional_state.primary_emotion == EmotionalState.URGENT:
            suggestions.append(
                {
                    "type": "urgency_response",
                    "text": "I understand this is urgent. Let me prioritize your request.",
                    "priority": "critical",
                }
            )

        # Entity-based suggestions
        if "court_date" in context.entities_extracted:
            suggestions.append(
                {
                    "type": "legal_advice",
                    "text": "I see you have a court date coming up. Would you like to schedule a consultation with an attorney?",
                    "priority": "high",
                }
            )

        return sorted(
            suggestions,
            key=lambda x: {"critical": 4, "high": 3, "medium": 2, "low": 1}[
                x["priority"]
            ],
            reverse=True,
        )

    async def cleanup_expired_memories(self, session_id: str) -> None:
        """Clean up expired memory items"""

        if session_id not in self.session_memories:
            return

        now = datetime.utcnow()
        memories = self.session_memories[session_id]
        expired_keys = []

        for key, memory in memories.items():
            if memory.expires_at and memory.expires_at <= now:
                expired_keys.append(key)

        for key in expired_keys:
            del memories[key]

        logger.debug(
            f"Cleaned up {len(expired_keys)} expired memories for session {session_id}"
        )

    async def end_session_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """End conversation context and return summary"""

        if session_id not in self.active_sessions:
            return None

        context = self.active_sessions[session_id]
        emotion_history = self.emotion_history.get(session_id, [])

        # Generate session summary
        summary = {
            "session_id": session_id,
            "duration": (datetime.utcnow() - context.last_updated).total_seconds()
            / 60,  # minutes
            "final_phase": context.conversation_phase.value,
            "final_emotion": context.emotional_state.primary_emotion.value,
            "emotion_progression": [em.primary_emotion.value for em in emotion_history],
            "urgency_level": context.urgency_level,
            "intents_discussed": context.intent_history,
            "entities_extracted": dict(context.entities_extracted),
            "confidential_flags": list(context.confidential_flags),
            "total_memories_stored": len(self.session_memories.get(session_id, {})),
        }

        # Clean up
        del self.active_sessions[session_id]
        if session_id in self.session_memories:
            del self.session_memories[session_id]
        if session_id in self.emotion_history:
            del self.emotion_history[session_id]

        # Remove from Redis if available
        if self.redis_client:
            await self.redis_client.delete(f"hermes:context:{session_id}")

        logger.info(f"Ended voice context for session {session_id}")
        return summary

    async def store_context_redis(self, context: ConversationContext) -> None:
        """Store context in Redis for persistence"""

        if not self.redis_client:
            return

        try:
            context_data = {
                "session_id": context.session_id,
                "client_id": context.client_id,
                "tenant_id": context.tenant_id,
                "conversation_phase": context.conversation_phase.value,
                "emotional_state": asdict(context.emotional_state),
                "intent_history": context.intent_history,
                "entities_extracted": context.entities_extracted,
                "matter_context": context.matter_context,
                "urgency_level": context.urgency_level,
                "confidential_flags": list(context.confidential_flags),
                "last_updated": context.last_updated.isoformat(),
                "metadata": context.metadata,
            }

            # Convert enum values to strings for JSON serialization
            emotional_state = context_data["emotional_state"]
            emotional_state["primary_emotion"] = (
                emotional_state["primary_emotion"].value
                if hasattr(emotional_state["primary_emotion"], "value")
                else str(emotional_state["primary_emotion"])
            )
            emotional_state["secondary_emotions"] = [
                e.value if hasattr(e, "value") else str(e)
                for e in emotional_state["secondary_emotions"]
            ]

            await self.redis_client.setex(
                f"hermes:context:{context.session_id}",
                24 * 3600,  # 24 hour TTL
                json.dumps(context_data, default=str),
            )

        except Exception as e:
            logger.error(f"Failed to store context in Redis: {e}")

    async def get_session_analytics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get analytics for a specific session"""

        if session_id not in self.active_sessions:
            return None

        context = self.active_sessions[session_id]
        emotion_history = self.emotion_history.get(session_id, [])

        return {
            "session_id": session_id,
            "current_phase": context.conversation_phase.value,
            "emotional_progression": [
                em.primary_emotion.value for em in emotion_history
            ],
            "average_emotional_intensity": (
                sum(em.emotional_intensity for em in emotion_history)
                / len(emotion_history)
                if emotion_history
                else 0
            ),
            "stress_indicators_detected": sum(
                len(em.stress_indicators) for em in emotion_history
            ),
            "urgency_level": context.urgency_level,
            "confidential_content_detected": len(context.confidential_flags),
            "entities_extracted_count": len(context.entities_extracted),
            "memory_items_stored": len(self.session_memories.get(session_id, {})),
            "session_duration_minutes": (
                datetime.utcnow() - context.last_updated
            ).total_seconds()
            / 60,
        }


# Global context manager instance
context_manager: Optional[VoiceContextManager] = None


def get_context_manager() -> VoiceContextManager:
    """Get global context manager instance"""
    global context_manager
    if context_manager is None:
        context_manager = VoiceContextManager()
    return context_manager
