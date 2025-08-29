"""
Core voice pipeline integrating STT, LLM processing, and TTS.
"""
import asyncio
import logging
import time
from typing import Optional, Dict, Any, AsyncGenerator

import openai
from pydantic import BaseModel

from .config import settings
from .speech_to_text import WhisperSTT, TranscriptionResult
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


class VoicePipeline:
    """
    Main voice processing pipeline orchestrating STT -> LLM -> TTS.
    """
    
    def __init__(self):
        self.stt = WhisperSTT()
        self.tts = KokoroTTS()
        self._openai_client: Optional[openai.AsyncOpenAI] = None
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize all pipeline components."""
        logger.info("Initializing HERMES voice pipeline...")
        
        # Initialize OpenAI client
        self._openai_client = openai.AsyncOpenAI(
            api_key=settings.openai_api_key
        )
        
        # Initialize STT and TTS components
        await asyncio.gather(
            self.stt.initialize(),
            self.tts.initialize()
        )
        
        self._initialized = True
        logger.info("Voice pipeline initialized successfully")
    
    async def process_voice_interaction(self, session_id: str, audio_data: bytes) -> VoiceInteraction:
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
        
        interaction = VoiceInteraction(
            session_id=session_id,
            audio_input=audio_data
        )
        
        start_time = time.time()
        
        try:
            # Step 1: Speech-to-Text
            logger.info(f"[{session_id}] Starting STT processing...")
            interaction.transcription = await self.stt.transcribe_audio(audio_data)
            
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
            logger.info(f"[{session_id}] Processing with LLM: '{interaction.transcription.text[:50]}...'")
            interaction.llm_response = await self._process_with_llm(
                interaction.transcription.text,
                session_id
            )
            
            # Step 4: Text-to-Speech
            if interaction.llm_response:
                logger.info(f"[{session_id}] Starting TTS synthesis...")
                interaction.audio_output = await self.tts.synthesize_text(
                    interaction.llm_response
                )
            
            interaction.total_processing_time = time.time() - start_time
            
            logger.info(
                f"[{session_id}] Voice interaction completed in "
                f"{interaction.total_processing_time:.3f}s"
            )
            
            return interaction
            
        except Exception as e:
            interaction.total_processing_time = time.time() - start_time
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
        
        try:
            response = await self._openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                max_tokens=200,  # Keep responses concise for voice
                temperature=0.7,
                timeout=settings.response_timeout * 10  # Allow more time for LLM
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Post-process response
            response_text = self._post_process_response(response_text)
            
            logger.info(f"[{session_id}] LLM response generated: '{response_text[:50]}...'")
            
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
            "off the record"
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
        sentences = response.split('. ')
        if len(sentences) > 3:
            response = '. '.join(sentences[:3]) + '.'
        
        # Add natural speech patterns
        response = response.replace(" and ", " and, ")
        response = response.replace(" but ", " but, ")
        
        return response.strip()
    
    async def stream_process_voice(self, session_id: str, audio_stream: AsyncGenerator[bytes, None]) -> AsyncGenerator[bytes, None]:
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
            if len(audio_buffer) >= settings.sample_rate * 2 * 2:  # 2 seconds of 16-bit audio
                try:
                    # Check for speech activity
                    if await self.stt.is_speech_detected(bytes(audio_buffer)):
                        # Process the accumulated audio
                        interaction = await self.process_voice_interaction(
                            session_id, 
                            bytes(audio_buffer)
                        )
                        
                        if interaction.audio_output:
                            # Stream the response audio in chunks
                            audio_data = interaction.audio_output.audio_data
                            chunk_size = settings.chunk_size
                            
                            for i in range(0, len(audio_data), chunk_size):
                                chunk = audio_data[i:i + chunk_size]
                                yield chunk
                    
                    # Clear buffer for next interaction
                    audio_buffer.clear()
                    
                except Exception as e:
                    logger.error(f"[{session_id}] Streaming processing error: {str(e)}")
                    # Continue processing subsequent chunks
    
    async def cleanup(self) -> None:
        """Clean up pipeline resources."""
        logger.info("Cleaning up voice pipeline...")
        
        await asyncio.gather(
            self.stt.cleanup(),
            self.tts.cleanup(),
            return_exceptions=True
        )
        
        if self._openai_client:
            await self._openai_client.close()
        
        self._initialized = False
        logger.info("Voice pipeline cleanup completed")