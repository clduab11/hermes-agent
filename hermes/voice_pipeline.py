"""
Core voice pipeline integrating STT, LLM processing, and TTS.
"""

import asyncio
import logging
import secrets
import time
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Literal, Optional, TypedDict
from uuid import uuid4

import openai
from pydantic import BaseModel

from .config import settings
from .event_streaming import EventStreamingService, EventType, VoiceEvent
from .monitoring.metrics import VOICE_PROCESSING_LATENCY
from .speech_to_text import TranscriptionResult, WhisperSTT
from .text_to_speech import KokoroTTS, SynthesisResult

logger = logging.getLogger(__name__)


class VoiceInteraction(BaseModel):
    """Complete voice interaction data."""

    session_id: str
    audio_input: bytes
    transcription: Optional[TranscriptionResult] = None
    llm_response: Optional[str] = None
    audio_output: Optional[SynthesisResult] = None
    total_processing_time: float = 0.0
    confidence_score: float = 0.0
    requires_human_transfer: bool = False


class ChatMessage(TypedDict):
    role: Literal["user", "assistant", "system"]
    content: str


class VoicePipeline:
    """
    Main voice processing pipeline orchestrating STT -> LLM -> TTS.
    """

    _HISTORY_LIMIT = 20
    _GENERAL_PREFIXES = [
        "Certainly,",
        "Of course,",
        "Sure,",
        "Absolutely,",
    ]
    _OFFER_PREFIXES = [
        "I'd be happy to help,",
    ]
    _COMPLIANCE_PREFIXES = [
        "",
    ]

    def __init__(self, event_streaming: Optional[EventStreamingService] = None):
        self.stt = WhisperSTT()
        self.tts = KokoroTTS()
        self._openai_client: Optional[openai.AsyncOpenAI] = None
        self._initialized = False
        # Maintain conversational context per session for more human-like interactions
        self._conversations: Dict[str, List[ChatMessage]] = {}
        # Event streaming for auxiliary services
        self.event_streaming = event_streaming
        self._latency_stats: Dict[str, float] = {"total": 0.0, "count": 0}

    async def initialize(self) -> None:
        """Initialize all pipeline components."""
        logger.info("Initializing HERMES voice pipeline...")

        # Initialize OpenAI client unless running in debug/demo mode where mocks are used
        if settings.demo_mode or settings.debug:
            logger.info("Skipping OpenAI client initialization (demo/debug mode)")
            self._openai_client = None
        else:
            self._openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

        # Initialize STT and TTS components
        await asyncio.gather(self.stt.initialize(), self.tts.initialize())

        self._initialized = True
        logger.info("Voice pipeline initialized successfully")

    async def process_voice_interaction(
        self, session_id: str, audio_data: bytes
    ) -> VoiceInteraction:
        """
        Process complete voice interaction: audio input -> text -> LLM -> speech output.

        Args:
            session_id: Unique session identifier
            audio_data: Raw audio input from client

        Returns:
            Complete voice interaction result
        """
        if not self._initialized:
            raise RuntimeError("Voice pipeline not initialized")

        interaction = VoiceInteraction(session_id=session_id, audio_input=audio_data)

        # Extract tenant_id from session (in production, get from JWT/auth)
        # Get tenant ID from session context or default to demo for development
        tenant_id = getattr(session_context, 'tenant_id', 'demo_tenant') if hasattr(self, 'session_context') else 'demo_tenant'
        correlation_id = str(uuid4())

        start_time = time.time()

        try:
            # Publish interaction started event
            if self.event_streaming:
                await self.event_streaming.publish_event(
                    VoiceEvent(
                        event_type=EventType.VOICE_INTERACTION_STARTED,
                        session_id=session_id,
                        tenant_id=tenant_id,
                        user_id=getattr(self, 'current_user_id', None),  # Retrieved from authenticated session
                        timestamp=datetime.now(timezone.utc),
                        data={
                            "audio_size_bytes": len(audio_data),
                            "processing_started": True,
                        },
                        metadata={"pipeline_version": "1.0"},
                        correlation_id=correlation_id,
                    )
                )

            # Step 1: Speech-to-Text
            logger.info(f"[{session_id}] Starting STT processing...")
            stt_start = time.time()
            interaction.transcription = await self.stt.transcribe_audio(audio_data)
            stt_time = time.time() - stt_start

            # Publish STT completion event
            if self.event_streaming:
                await self.event_streaming.publish_event(
                    VoiceEvent(
                        event_type=EventType.STT_PROCESSED,
                        session_id=session_id,
                        tenant_id=tenant_id,
                        user_id=None,
                        timestamp=datetime.now(timezone.utc),
                        data={
                            "transcription": {
                                "text": interaction.transcription.text,
                                "confidence": interaction.transcription.confidence,
                            },
                            "processing_time_ms": stt_time * 1000,
                            "language_detected": interaction.transcription.language_code,
                        },
                        metadata={"stt_model": "whisper"},
                        correlation_id=correlation_id,
                    )
                )

            # Check if we have meaningful speech
            if not interaction.transcription.text.strip():
                logger.warning(f"[{session_id}] No speech detected in audio")
                return interaction

            # Step 2: Confidence checking
            interaction.confidence_score = interaction.transcription.confidence

            if interaction.confidence_score < settings.confidence_threshold:
                logger.warning(
                    f"[{session_id}] Low confidence ({interaction.confidence_score:.3f}), "
                    "may require human transfer"
                )
                interaction.requires_human_transfer = True

            # Step 3: LLM Processing
            logger.info(
                f"[{session_id}] Processing with LLM: '{interaction.transcription.text[:50]}...'"
            )
            llm_start = time.time()
            interaction.llm_response = await self._process_with_llm(
                interaction.transcription.text, session_id
            )
            llm_time = time.time() - llm_start

            # Publish LLM completion event
            if self.event_streaming:
                await self.event_streaming.publish_event(
                    VoiceEvent(
                        event_type=EventType.LLM_PROCESSED,
                        session_id=session_id,
                        tenant_id=tenant_id,
                        user_id=None,
                        timestamp=datetime.now(timezone.utc),
                        data={
                            "response_text": interaction.llm_response,
                            "processing_time_ms": llm_time * 1000,
                            "input_tokens": len(interaction.transcription.text.split()),
                            "output_tokens": len(interaction.llm_response.split()),
                        },
                        metadata={"llm_model": settings.openai_model},
                        correlation_id=correlation_id,
                    )
                )

            # Step 4: Text-to-Speech
            if interaction.llm_response:
                logger.info(f"[{session_id}] Starting TTS synthesis...")
                tts_start = time.time()
                interaction.audio_output = await self.tts.synthesize_text(
                    interaction.llm_response
                )
                tts_time = time.time() - tts_start

                # Publish TTS completion event
                if self.event_streaming:
                    await self.event_streaming.publish_event(
                        VoiceEvent(
                            event_type=EventType.TTS_PROCESSED,
                            session_id=session_id,
                            tenant_id=tenant_id,
                            user_id=None,
                            timestamp=datetime.now(timezone.utc),
                            data={
                                "synthesized_text": interaction.llm_response,
                                "audio_size_bytes": len(
                                    interaction.audio_output.audio_data
                                ),
                                "processing_time_ms": tts_time * 1000,
                                "voice_used": interaction.audio_output.voice_id,
                                "duration_seconds": interaction.audio_output.duration_seconds,
                            },
                            metadata={"tts_engine": "kokoro"},
                            correlation_id=correlation_id,
                        )
                    )

            interaction.total_processing_time = time.time() - start_time
            VOICE_PROCESSING_LATENCY.observe(interaction.total_processing_time)
            self._latency_stats["total"] += interaction.total_processing_time
            self._latency_stats["count"] += 1

            # Publish interaction completion event
            if self.event_streaming:
                await self.event_streaming.publish_event(
                    VoiceEvent(
                        event_type=EventType.VOICE_INTERACTION_COMPLETED,
                        session_id=session_id,
                        tenant_id=tenant_id,
                        user_id=None,
                        timestamp=datetime.now(timezone.utc),
                        data={
                            "total_processing_time": interaction.total_processing_time,
                            "confidence_score": interaction.confidence_score,
                            "requires_human_transfer": interaction.requires_human_transfer,
                            "stt_time_ms": (
                                stt_time * 1000 if "stt_time" in locals() else 0
                            ),
                            "llm_time_ms": (
                                llm_time * 1000 if "llm_time" in locals() else 0
                            ),
                            "tts_time_ms": (
                                tts_time * 1000 if "tts_time" in locals() else 0
                            ),
                            "human_transfer_initiated": interaction.requires_human_transfer,  # Tracked via interaction state
                        },
                        metadata={
                            "performance_target_met": interaction.total_processing_time
                            < 0.1,
                            "pipeline_success": True,
                        },
                        correlation_id=correlation_id,
                    )
                )

            logger.info(
                f"[{session_id}] Voice interaction completed in "
                f"{interaction.total_processing_time:.3f}s"
            )

            return interaction

        except Exception as e:
            interaction.total_processing_time = time.time() - start_time
            VOICE_PROCESSING_LATENCY.observe(interaction.total_processing_time)
            self._latency_stats["total"] += interaction.total_processing_time
            self._latency_stats["count"] += 1

            # Publish error event
            if self.event_streaming:
                await self.event_streaming.publish_event(
                    VoiceEvent(
                        event_type=EventType.ERROR_OCCURRED,
                        session_id=session_id,
                        tenant_id=tenant_id,
                        user_id=None,
                        timestamp=datetime.now(timezone.utc),
                        data={
                            "error_message": str(e),
                            "error_type": type(e).__name__,
                            "processing_time_before_error": interaction.total_processing_time,
                        },
                        metadata={"pipeline_stage": "voice_interaction"},
                        correlation_id=correlation_id,
                    )
                )

            logger.error(f"[{session_id}] Voice processing failed: {str(e)}")
            raise

    async def _process_with_llm(self, text: str, session_id: str) -> str:
        """
        Process user input with LLM to generate response.

        Args:
            text: Transcribed user input
            session_id: Session identifier for context

        Returns:
            Generated response text
        """
        if not self._openai_client:
            raise RuntimeError("OpenAI client not initialized")

        # Check for prohibited content
        if self._contains_prohibited_content(text):
            return self._get_compliance_response()

        # Prepare system prompt for legal assistant
        system_prompt = self._build_system_prompt()

        # Retrieve and update conversational history for this session
        history = self._conversations.setdefault(session_id, [])
        history.append({"role": "user", "content": text})

        # Limit history to last 10 exchanges (20 messages)
        if len(history) > self._HISTORY_LIMIT:
            del history[: -self._HISTORY_LIMIT]

        try:
            response = await self._openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "system", "content": system_prompt}] + history,
                max_tokens=200,  # Keep responses concise for voice
                temperature=0.7,
                timeout=settings.response_timeout * 10,  # Allow more time for LLM
            )

            response_text = response.choices[0].message.content.strip()

            # Save assistant response to history
            history.append({"role": "assistant", "content": response_text})
            if len(history) > self._HISTORY_LIMIT:
                del history[: -self._HISTORY_LIMIT]

            # Post-process response
            response_text = self._post_process_response(response_text)
            response_text = self._humanize_response(response_text)

            logger.info(
                f"[{session_id}] LLM response generated: '{response_text[:50]}...'"
            )

            return response_text

        except Exception as e:
            logger.error(f"[{session_id}] LLM processing failed: {str(e)}")
            return "I apologize, but I'm experiencing technical difficulties. Please hold while I connect you with a human assistant."

    def _build_system_prompt(self) -> str:
        """Build system prompt for legal assistant."""
        return """You are HERMES, an AI voice assistant for a law firm. Your role is to:

1. Professionally greet callers and gather basic information
2. Schedule appointments and route calls appropriately  
3. Provide general information about the firm's services
4. Handle routine administrative tasks

IMPORTANT GUIDELINES:
- Never provide legal advice or interpret laws
- Keep responses concise and clear for voice interaction
- Maintain professional, empathetic tone
- If unsure about anything, offer to connect with a human attorney
- Always protect client confidentiality
- For complex legal matters, immediately transfer to human staff

LEGAL COMPLIANCE:
- All communications are subject to attorney-client privilege where applicable
- Do not discuss ongoing cases or sensitive legal matters
- Maintain strict confidentiality of all client information

Respond naturally and conversationally, as if speaking to someone on the phone."""

    def _contains_prohibited_content(self, text: str) -> bool:
        """
        Check if text contains prohibited content that requires compliance response.

        Args:
            text: User input text

        Returns:
            True if prohibited content detected
        """
        prohibited_patterns = [
            # Explicit legal advice requests
            "what should i do",
            "what should i sue for",
            "should i plead",
            "am i guilty",
            "will i go to jail",
            "what are my chances",
            # Specific case strategy
            "how to win",
            "best strategy",
            "what to say in court",
            "how to lie",
            # Inappropriate requests
            "free legal advice",
            "quick legal advice",
            "off the record",
        ]

        text_lower = text.lower()
        return any(pattern in text_lower for pattern in prohibited_patterns)

    def _get_compliance_response(self) -> str:
        """Get standard compliance response for prohibited requests."""
        return (
            "I understand you're looking for guidance, but I can't provide legal advice. "
            "Let me connect you with one of our attorneys who can properly assist you with "
            "your specific situation. Please hold while I transfer your call."
        )

    def _post_process_response(self, response: str) -> str:
        """
        Post-process LLM response for voice output.

        Args:
            response: Raw LLM response

        Returns:
            Processed response optimized for speech
        """
        # Remove markdown formatting
        response = response.replace("**", "").replace("*", "")
        response = response.replace("_", "").replace("`", "")

        # Ensure reasonable length for voice
        sentences = response.split(". ")
        if len(sentences) > 3:
            response = ". ".join(sentences[:3]) + "."

        # Add natural speech patterns
        response = response.replace(" and ", " and, ")
        response = response.replace(" but ", " but, ")

        return response.strip()

    def _requires_human_transfer(self, user_input: str, ai_response: str) -> bool:
        """
        Determine if interaction requires human transfer based on content analysis.

        Args:
            user_input: User's transcribed input
            ai_response: AI's response

        Returns:
            True if human transfer is recommended
        """
        # Check for complex legal questions
        complex_legal_indicators = [
            "lawsuit",
            "sue",
            "legal action",
            "court",
            "judge",
            "trial",
            "settlement",
            "damages",
            "liability",
            "contract dispute",
            "criminal charges",
            "divorce",
            "custody",
            "estate planning",
        ]

        user_lower = user_input.lower()
        for indicator in complex_legal_indicators:
            if indicator in user_lower:
                return True

        # Check if AI response indicates uncertainty
        uncertainty_indicators = [
            "I can't provide legal advice",
            "connect you with an attorney",
            "speak with a lawyer",
            "consult with our legal team",
        ]

        ai_lower = ai_response.lower()
        for indicator in uncertainty_indicators:
            if indicator in ai_lower:
                return True

        return False

    def _humanize_response(self, response: str) -> str:
        """Add natural-sounding prefix to make responses feel more human, with conditional logic."""

        def is_compliance_response(text: str) -> bool:
            compliance_phrases = [
                "I can't provide legal advice",
                "I am unable to",
                "I cannot",
                "I'm not able to",
                "Please hold while I transfer your call",
            ]
            return any(phrase in text for phrase in compliance_phrases)

        def is_offer_response(text: str) -> bool:
            offer_phrases = [
                "assist you",
                "help you",
                "provide",
                "do that",
                "look into",
                "arrange",
                "schedule",
                "connect you",
            ]
            return any(phrase in text for phrase in offer_phrases)

        if response:
            if is_compliance_response(response):
                prefix = secrets.choice(self._COMPLIANCE_PREFIXES)
            elif is_offer_response(response):
                prefix = secrets.choice(self._OFFER_PREFIXES + self._GENERAL_PREFIXES)
            else:
                prefix = secrets.choice(self._GENERAL_PREFIXES)

            if prefix:
                response = f"{prefix} {response}"

        return response

    async def stream_process_voice(
        self, session_id: str, audio_stream: AsyncGenerator[bytes, None]
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream processing for real-time voice interaction.

        Args:
            session_id: Session identifier
            audio_stream: Async generator of audio chunks

        Yields:
            Audio response chunks
        """
        # Accumulate audio chunks for processing
        audio_buffer = bytearray()

        async for audio_chunk in audio_stream:
            audio_buffer.extend(audio_chunk)

            # Process when we have enough audio (e.g., 1-2 seconds)
            if (
                len(audio_buffer) >= settings.sample_rate * 2 * 2
            ):  # 2 seconds of 16-bit audio
                try:
                    # Check for speech activity
                    if await self.stt.is_speech_detected(bytes(audio_buffer)):
                        # Process the accumulated audio
                        interaction = await self.process_voice_interaction(
                            session_id, bytes(audio_buffer)
                        )

                        if interaction.audio_output:
                            # Stream the response audio in chunks
                            audio_data = interaction.audio_output.audio_data
                            chunk_size = settings.chunk_size

                            for i in range(0, len(audio_data), chunk_size):
                                chunk = audio_data[i : i + chunk_size]
                                yield chunk

                    # Clear buffer for next interaction
                    audio_buffer.clear()

                except Exception as e:
                    logger.error(f"[{session_id}] Streaming processing error: {str(e)}")
                    # Continue processing subsequent chunks

    def get_performance_metrics(self) -> Dict[str, float]:
        """Return aggregate metrics for SLA reporting."""

        processed = self._latency_stats["count"]
        average_latency = (
            self._latency_stats["total"] / processed if processed else 0.0
        )

        return {
            "average_latency_seconds": average_latency,
            "interactions_processed": processed,
        }

    async def cleanup(self) -> None:
        """Clean up pipeline resources."""
        logger.info("Cleaning up voice pipeline...")

        await asyncio.gather(
            self.stt.cleanup(), self.tts.cleanup(), return_exceptions=True
        )

        if self._openai_client:
            await self._openai_client.close()

        self._conversations.clear()
        self._initialized = False
        logger.info("Voice pipeline cleanup completed")
