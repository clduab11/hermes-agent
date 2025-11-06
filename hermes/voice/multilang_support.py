"""
HERMES Multi-Language Speech-to-Text and Text-to-Speech Support
Support for international legal practice with multiple languages
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import torch
import whisper
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class SupportedLanguage(Enum):
    """Supported languages for STT/TTS"""

    ENGLISH = ("en", "English", "en-US")
    SPANISH = ("es", "Spanish", "es-ES")
    FRENCH = ("fr", "French", "fr-FR")
    GERMAN = ("de", "German", "de-DE")
    ITALIAN = ("it", "Italian", "it-IT")
    PORTUGUESE = ("pt", "Portuguese", "pt-PT")
    RUSSIAN = ("ru", "Russian", "ru-RU")
    MANDARIN = ("zh", "Chinese (Mandarin)", "zh-CN")
    JAPANESE = ("ja", "Japanese", "ja-JP")
    KOREAN = ("ko", "Korean", "ko-KR")
    ARABIC = ("ar", "Arabic", "ar-SA")
    HINDI = ("hi", "Hindi", "hi-IN")


@dataclass
class LanguageDetectionResult:
    """Language detection result"""

    detected_language: SupportedLanguage
    confidence: float
    alternative_languages: List[Tuple[SupportedLanguage, float]]
    detection_method: str


@dataclass
class TranscriptionResult:
    """STT transcription result with language support"""

    text: str
    language: SupportedLanguage
    confidence: float
    processing_time: float
    segments: List[Dict[str, Any]]
    detected_language_confidence: float


@dataclass
class SynthesisResult:
    """TTS synthesis result with language support"""

    audio_data: bytes
    language: SupportedLanguage
    voice_id: str
    duration: float
    processing_time: float
    metadata: Dict[str, Any]


class MultiLanguageSTT:
    """Multi-language Speech-to-Text processor"""

    def __init__(self, model_size: str = "base", device: str = None):
        self.model_size = model_size
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.whisper_model = None
        self.language_models = {}

        # Language-specific model configuration
        self.language_configs = {
            SupportedLanguage.ENGLISH: {"task": "transcribe", "best_of": 5},
            SupportedLanguage.SPANISH: {"task": "transcribe", "best_of": 3},
            SupportedLanguage.FRENCH: {"task": "transcribe", "best_of": 3},
            SupportedLanguage.GERMAN: {"task": "transcribe", "best_of": 3},
            SupportedLanguage.ITALIAN: {"task": "transcribe", "best_of": 3},
            SupportedLanguage.PORTUGUESE: {"task": "transcribe", "best_of": 3},
            SupportedLanguage.RUSSIAN: {"task": "transcribe", "best_of": 3},
            SupportedLanguage.MANDARIN: {"task": "transcribe", "best_of": 2},
            SupportedLanguage.JAPANESE: {"task": "transcribe", "best_of": 2},
            SupportedLanguage.KOREAN: {"task": "transcribe", "best_of": 2},
            SupportedLanguage.ARABIC: {"task": "transcribe", "best_of": 2},
            SupportedLanguage.HINDI: {"task": "transcribe", "best_of": 2},
        }

        # Legal terminology for each language
        self.legal_vocabulary = {
            SupportedLanguage.ENGLISH: [
                "attorney",
                "lawyer",
                "legal",
                "court",
                "case",
                "lawsuit",
                "contract",
                "plaintiff",
                "defendant",
                "litigation",
                "settlement",
                "damages",
            ],
            SupportedLanguage.SPANISH: [
                "abogado",
                "legal",
                "tribunal",
                "caso",
                "demanda",
                "contrato",
                "demandante",
                "demandado",
                "litigio",
                "acuerdo",
                "daños",
            ],
            SupportedLanguage.FRENCH: [
                "avocat",
                "juridique",
                "tribunal",
                "affaire",
                "procès",
                "contrat",
                "demandeur",
                "défendeur",
                "litige",
                "règlement",
                "dommages",
            ],
            SupportedLanguage.GERMAN: [
                "anwalt",
                "rechtlich",
                "gericht",
                "fall",
                "klage",
                "vertrag",
                "kläger",
                "beklagte",
                "rechtsstreit",
                "vergleich",
                "schäden",
            ],
            SupportedLanguage.ITALIAN: [
                "avvocato",
                "legale",
                "tribunale",
                "caso",
                "causa",
                "contratto",
                "attore",
                "convenuto",
                "contenzioso",
                "accordo",
                "danni",
            ],
            SupportedLanguage.PORTUGUESE: [
                "advogado",
                "legal",
                "tribunal",
                "caso",
                "ação",
                "contrato",
                "requerente",
                "requerido",
                "litígio",
                "acordo",
                "danos",
            ],
            SupportedLanguage.MANDARIN: [
                "律师",
                "法律",
                "法院",
                "案件",
                "诉讼",
                "合同",
                "原告",
                "被告",
                "争议",
                "和解",
                "损害赔偿",
            ],
        }

        self.initialize_models()

    def initialize_models(self):
        """Initialize Whisper models"""
        try:
            logger.info(f"Loading Whisper model '{self.model_size}' on {self.device}")
            self.whisper_model = whisper.load_model(self.model_size, device=self.device)
            logger.info("Multi-language STT models initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize STT models: {e}")
            raise

    async def detect_language(
        self, audio_data: bytes, duration: float = None
    ) -> LanguageDetectionResult:
        """Detect language from audio data"""

        start_time = time.time()

        try:
            # Use Whisper's language detection
            audio_array = whisper.load_audio_from_bytes(audio_data)

            # Detect language using Whisper
            _, language_probs = self.whisper_model.detect_language(audio_array)

            # Convert to our supported languages
            detected_languages = []
            for lang_code, prob in language_probs.items():
                try:
                    # Map Whisper language codes to our enum
                    supported_lang = self._map_whisper_language(lang_code)
                    if supported_lang:
                        detected_languages.append((supported_lang, prob))
                except KeyError:
                    continue

            # Sort by probability
            detected_languages.sort(key=lambda x: x[1], reverse=True)

            if detected_languages:
                primary_lang, confidence = detected_languages[0]
                alternatives = detected_languages[1:6]  # Top 5 alternatives
            else:
                # Fallback to English
                primary_lang = SupportedLanguage.ENGLISH
                confidence = 0.5
                alternatives = []

            processing_time = time.time() - start_time

            logger.debug(
                f"Language detection completed in {processing_time:.2f}s: {primary_lang} (confidence: {confidence:.2f})"
            )

            return LanguageDetectionResult(
                detected_language=primary_lang,
                confidence=confidence,
                alternative_languages=alternatives,
                detection_method="whisper",
            )

        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            # Return English as fallback
            return LanguageDetectionResult(
                detected_language=SupportedLanguage.ENGLISH,
                confidence=0.3,
                alternative_languages=[],
                detection_method="fallback",
            )

    async def transcribe_audio(
        self,
        audio_data: bytes,
        language: SupportedLanguage = None,
        enable_language_detection: bool = True,
    ) -> TranscriptionResult:
        """Transcribe audio with multi-language support"""

        start_time = time.time()

        try:
            audio_array = whisper.load_audio_from_bytes(audio_data)

            # Detect language if not specified
            detected_language = language
            detection_confidence = 1.0

            if language is None and enable_language_detection:
                detection_result = await self.detect_language(audio_data)
                detected_language = detection_result.detected_language
                detection_confidence = detection_result.confidence

            # Get language configuration
            language_code = detected_language.value[0] if detected_language else "en"
            config = self.language_configs.get(
                detected_language, {"task": "transcribe", "best_of": 3}
            )

            # Configure prompt with legal vocabulary
            prompt = ""
            if detected_language in self.legal_vocabulary:
                vocabulary = self.legal_vocabulary[detected_language]
                prompt = " ".join(vocabulary[:10])  # Use first 10 legal terms as prompt

            # Transcribe with language-specific settings
            transcription_options = {
                "language": language_code,
                "task": config["task"],
                "best_of": config["best_of"],
                "beam_size": 5,
                "patience": 1.0,
                "length_penalty": 1.0,
                "suppress_tokens": "-1",
                "initial_prompt": prompt,
                "condition_on_previous_text": True,
                "fp16": torch.cuda.is_available(),
                "compression_ratio_threshold": 2.4,
                "logprob_threshold": -1.0,
                "no_speech_threshold": 0.6,
            }

            result = self.whisper_model.transcribe(audio_array, **transcription_options)

            processing_time = time.time() - start_time

            # Calculate confidence from segments
            confidence = self._calculate_transcription_confidence(result)

            logger.info(
                f"Transcription completed in {processing_time:.2f}s: {detected_language} (confidence: {confidence:.2f})"
            )

            return TranscriptionResult(
                text=result["text"].strip(),
                language=detected_language or SupportedLanguage.ENGLISH,
                confidence=confidence,
                processing_time=processing_time,
                segments=result.get("segments", []),
                detected_language_confidence=detection_confidence,
            )

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise

    def _map_whisper_language(self, whisper_code: str) -> Optional[SupportedLanguage]:
        """Map Whisper language code to our supported language enum"""

        language_mapping = {
            "en": SupportedLanguage.ENGLISH,
            "es": SupportedLanguage.SPANISH,
            "fr": SupportedLanguage.FRENCH,
            "de": SupportedLanguage.GERMAN,
            "it": SupportedLanguage.ITALIAN,
            "pt": SupportedLanguage.PORTUGUESE,
            "ru": SupportedLanguage.RUSSIAN,
            "zh": SupportedLanguage.MANDARIN,
            "ja": SupportedLanguage.JAPANESE,
            "ko": SupportedLanguage.KOREAN,
            "ar": SupportedLanguage.ARABIC,
            "hi": SupportedLanguage.HINDI,
        }

        return language_mapping.get(whisper_code)

    def _calculate_transcription_confidence(
        self, whisper_result: Dict[str, Any]
    ) -> float:
        """Calculate overall confidence from Whisper result segments"""

        if "segments" not in whisper_result or not whisper_result["segments"]:
            return 0.7  # Default confidence

        segments = whisper_result["segments"]
        total_confidence = 0.0
        total_duration = 0.0

        for segment in segments:
            if "avg_logprob" in segment and "end" in segment and "start" in segment:
                # Convert log probability to confidence (approximate)
                log_prob = segment["avg_logprob"]
                confidence = min(1.0, max(0.0, (log_prob + 1.0)))
                duration = segment["end"] - segment["start"]

                total_confidence += confidence * duration
                total_duration += duration

        if total_duration > 0:
            return total_confidence / total_duration

        return 0.7


class MultiLanguageTTS:
    """Multi-language Text-to-Speech processor"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None

        # Voice mappings for different languages
        self.voice_mappings = {
            SupportedLanguage.ENGLISH: {
                "default": "nova",
                "alternatives": ["alloy", "echo", "fable", "onyx", "shimmer"],
                "professional": "nova",
                "friendly": "alloy",
            },
            SupportedLanguage.SPANISH: {
                "default": "nova",
                "alternatives": ["alloy", "echo"],
                "professional": "nova",
                "friendly": "alloy",
            },
            SupportedLanguage.FRENCH: {
                "default": "nova",
                "alternatives": ["alloy", "echo"],
                "professional": "nova",
                "friendly": "alloy",
            },
            SupportedLanguage.GERMAN: {
                "default": "nova",
                "alternatives": ["alloy", "onyx"],
                "professional": "onyx",
                "friendly": "alloy",
            },
            SupportedLanguage.ITALIAN: {
                "default": "nova",
                "alternatives": ["alloy", "echo"],
                "professional": "nova",
                "friendly": "alloy",
            },
            SupportedLanguage.PORTUGUESE: {
                "default": "nova",
                "alternatives": ["alloy", "echo"],
                "professional": "nova",
                "friendly": "alloy",
            },
            SupportedLanguage.MANDARIN: {
                "default": "nova",
                "alternatives": ["alloy"],
                "professional": "nova",
                "friendly": "alloy",
            },
        }

        # Language-specific synthesis parameters
        self.synthesis_configs = {
            SupportedLanguage.ENGLISH: {"speed": 1.0, "model": "tts-1-hd"},
            SupportedLanguage.SPANISH: {"speed": 0.95, "model": "tts-1-hd"},
            SupportedLanguage.FRENCH: {"speed": 0.9, "model": "tts-1-hd"},
            SupportedLanguage.GERMAN: {"speed": 0.85, "model": "tts-1-hd"},
            SupportedLanguage.ITALIAN: {"speed": 0.95, "model": "tts-1-hd"},
            SupportedLanguage.PORTUGUESE: {"speed": 0.9, "model": "tts-1-hd"},
            SupportedLanguage.MANDARIN: {"speed": 0.8, "model": "tts-1-hd"},
        }

    async def get_available_voices(self, language: SupportedLanguage) -> List[str]:
        """Get available voices for a specific language"""

        voice_config = self.voice_mappings.get(language)
        if voice_config:
            voices = [voice_config["default"]] + voice_config["alternatives"]
            return list(set(voices))  # Remove duplicates

        # Fallback to English voices
        return self.voice_mappings[SupportedLanguage.ENGLISH]["alternatives"]

    async def synthesize_text(
        self,
        text: str,
        language: SupportedLanguage = SupportedLanguage.ENGLISH,
        voice_style: str = "professional",
        voice_id: str = None,
        speed: float = None,
    ) -> SynthesisResult:
        """Synthesize text to speech with multi-language support"""

        if not self.client:
            raise ValueError("OpenAI API key not provided for TTS")

        start_time = time.time()

        try:
            # Get voice configuration
            voice_config = self.voice_mappings.get(
                language, self.voice_mappings[SupportedLanguage.ENGLISH]
            )
            synthesis_config = self.synthesis_configs.get(
                language, self.synthesis_configs[SupportedLanguage.ENGLISH]
            )

            # Select voice
            if voice_id and voice_id in voice_config["alternatives"]:
                selected_voice = voice_id
            elif voice_style in voice_config:
                selected_voice = voice_config[voice_style]
            else:
                selected_voice = voice_config["default"]

            # Set synthesis parameters
            synthesis_speed = speed or synthesis_config["speed"]
            model = synthesis_config["model"]

            # Prepare text for specific language
            processed_text = self._prepare_text_for_language(text, language)

            # Generate speech
            response = await self.client.audio.speech.create(
                model=model,
                voice=selected_voice,
                input=processed_text,
                speed=synthesis_speed,
                response_format="mp3",
            )

            audio_data = response.content
            processing_time = time.time() - start_time

            # Estimate duration (rough calculation)
            estimated_duration = (
                len(processed_text.split()) * 0.6 / synthesis_speed
            )  # ~0.6 seconds per word

            logger.info(
                f"TTS synthesis completed in {processing_time:.2f}s: {language} with voice {selected_voice}"
            )

            return SynthesisResult(
                audio_data=audio_data,
                language=language,
                voice_id=selected_voice,
                duration=estimated_duration,
                processing_time=processing_time,
                metadata={
                    "model": model,
                    "speed": synthesis_speed,
                    "text_length": len(processed_text),
                    "word_count": len(processed_text.split()),
                },
            )

        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            raise

    def _prepare_text_for_language(self, text: str, language: SupportedLanguage) -> str:
        """Prepare text for synthesis in specific language"""

        # Language-specific text preprocessing
        if language == SupportedLanguage.MANDARIN:
            # Add pauses for better Chinese pronunciation
            text = text.replace("。", "。 ")
            text = text.replace("，", "， ")
        elif language == SupportedLanguage.GERMAN:
            # Handle German compound words
            text = text.replace(" und ", " und ")
        elif language == SupportedLanguage.FRENCH:
            # Handle French liaisons
            text = text.replace(" et ", " et ")

        # Clean up multiple spaces
        text = " ".join(text.split())

        return text


class MultiLanguageProcessor:
    """Combined multi-language STT/TTS processor"""

    def __init__(
        self,
        whisper_model_size: str = "base",
        openai_api_key: str = None,
        default_language: SupportedLanguage = SupportedLanguage.ENGLISH,
    ):
        self.default_language = default_language
        self.stt = MultiLanguageSTT(whisper_model_size)
        self.tts = MultiLanguageTTS(openai_api_key)

        # Language usage statistics
        self.language_stats = {lang: 0 for lang in SupportedLanguage}

    async def process_audio_conversation(
        self,
        audio_data: bytes,
        response_text: str = None,
        preferred_language: SupportedLanguage = None,
        voice_style: str = "professional",
    ) -> Tuple[TranscriptionResult, Optional[SynthesisResult]]:
        """Process full audio conversation (STT + TTS)"""

        # Transcribe input audio
        transcription = await self.stt.transcribe_audio(
            audio_data,
            language=preferred_language,
            enable_language_detection=preferred_language is None,
        )

        # Update language statistics
        self.language_stats[transcription.language] += 1

        synthesis_result = None

        # Generate speech response if text provided
        if response_text:
            synthesis_result = await self.tts.synthesize_text(
                response_text,
                language=transcription.language,  # Use detected language for response
                voice_style=voice_style,
            )

        logger.info(
            f"Processed conversation in {transcription.language} - Transcription confidence: {transcription.confidence:.2f}"
        )

        return transcription, synthesis_result

    async def translate_text(
        self,
        text: str,
        source_language: SupportedLanguage,
        target_language: SupportedLanguage,
        context: str = "legal",
    ) -> str:
        """Translate text between supported languages (placeholder for future implementation)"""

        # This would integrate with a translation service like Google Translate or Azure Translator
        # For now, return the original text
        logger.warning(
            f"Translation not yet implemented: {source_language} -> {target_language}"
        )
        return text

    def get_language_statistics(self) -> Dict[str, int]:
        """Get usage statistics for each language"""
        return {
            lang.value[1]: count
            for lang, count in self.language_stats.items()
            if count > 0
        }

    def get_supported_languages(self) -> List[Dict[str, str]]:
        """Get list of supported languages with metadata"""
        return [
            {
                "code": lang.value[0],
                "name": lang.value[1],
                "locale": lang.value[2],
                "usage_count": self.language_stats[lang],
            }
            for lang in SupportedLanguage
        ]


# Helper function to load audio from bytes (for Whisper compatibility)
def load_audio_from_bytes(audio_bytes: bytes):
    """
    Load audio from bytes for Whisper processing.
    
    Uses secure temporary file handling to prevent orphaned files and
    potential security issues with file permissions.
    
    Args:
        audio_bytes: Raw audio data as bytes
        
    Returns:
        numpy.ndarray: Audio data loaded at 16kHz sample rate
    """
    import tempfile
    import librosa

    # Use context manager for automatic cleanup and better security
    # tempfile.NamedTemporaryFile creates files with mode 0600 (owner read/write only)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as temp_file:
        temp_file.write(audio_bytes)
        temp_file.flush()
        
        # Load with librosa for Whisper compatibility
        # Read while file is still open and secured
        audio, _ = librosa.load(temp_file.name, sr=16000, mono=True)
        
        # File is automatically deleted when context exits
        return audio


# Monkey patch for Whisper
whisper.load_audio_from_bytes = load_audio_from_bytes

# Global processor instance
multilang_processor: Optional[MultiLanguageProcessor] = None


def get_multilang_processor() -> MultiLanguageProcessor:
    """Get global multi-language processor instance"""
    global multilang_processor
    if multilang_processor is None:
        multilang_processor = MultiLanguageProcessor()
    return multilang_processor
