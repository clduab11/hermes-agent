"""
Test voice pipeline components without requiring actual audio processing.
"""
import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock, patch

# Set test environment variables
os.environ["OPENAI_API_KEY"] = "test-key-123"
os.environ["DEBUG"] = "true"

from hermes.config import settings
from hermes.voice_pipeline import VoicePipeline
from hermes.speech_to_text import WhisperSTT, TranscriptionResult
from hermes.text_to_speech import KokoroTTS, SynthesisResult


class TestVoicePipelineComponents:
    """Test individual voice pipeline components."""
    
    @pytest.mark.asyncio
    async def test_voice_pipeline_initialization(self):
        """Test voice pipeline can be initialized."""
        pipeline = VoicePipeline()
        
        # Mock the component initialization
        with patch.object(pipeline.stt, 'initialize', new_callable=AsyncMock) as mock_stt_init, \
             patch.object(pipeline.tts, 'initialize', new_callable=AsyncMock) as mock_tts_init:
            
            await pipeline.initialize()
            
            assert pipeline._initialized is True
            mock_stt_init.assert_called_once()
            mock_tts_init.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_llm_processing(self):
        """Test LLM processing without actual API calls."""
        pipeline = VoicePipeline()
        
        # Mock OpenAI client
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "I'd be happy to help you schedule an appointment."
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response
        
        pipeline._openai_client = mock_client
        
        result = await pipeline._process_with_llm("I need to schedule an appointment", "test-session")
        
        assert "appointment" in result.lower()
        mock_client.chat.completions.create.assert_called_once()
    
    def test_prohibited_content_detection(self):
        """Test prohibited content detection."""
        pipeline = VoicePipeline()
        
        # Test prohibited patterns
        prohibited_texts = [
            "what should i do in court",
            "should i plead guilty",
            "what are my chances of winning"
        ]
        
        for text in prohibited_texts:
            assert pipeline._contains_prohibited_content(text) is True
        
        # Test allowed content
        allowed_texts = [
            "I need to schedule an appointment",
            "What are your office hours",
            "Can you help me with estate planning"
        ]
        
        for text in allowed_texts:
            assert pipeline._contains_prohibited_content(text) is False
    
    def test_response_post_processing(self):
        """Test response post-processing."""
        pipeline = VoicePipeline()
        
        # Test markdown removal
        input_text = "**Hello** this is a _test_ with `code` formatting."
        expected = "Hello this is a test with code formatting."
        result = pipeline._post_process_response(input_text)
        assert result == expected
        
        # Test length limiting
        long_text = "Sentence one. Sentence two. Sentence three. Sentence four."
        result = pipeline._post_process_response(long_text)
        sentences = result.split('. ')
        assert len(sentences) <= 4  # Should limit to 3 sentences + final period


class TestSTTComponent:
    """Test Speech-to-Text component."""
    
    def test_stt_initialization(self):
        """Test STT component can be created."""
        stt = WhisperSTT()
        assert stt._model is None
        assert stt._device == settings.whisper_device
        assert stt._model_name == settings.whisper_model
    
    def test_audio_preparation(self):
        """Test audio data preparation."""
        stt = WhisperSTT()
        
        # Create dummy 16-bit PCM audio data
        import numpy as np
        dummy_audio = np.random.randint(-32768, 32767, 1000, dtype=np.int16)
        audio_bytes = dummy_audio.tobytes()
        
        prepared_audio = stt._prepare_audio(audio_bytes)
        
        assert isinstance(prepared_audio, np.ndarray)
        assert prepared_audio.dtype == np.float32
        assert len(prepared_audio) == 1000
        assert np.all(prepared_audio >= -1.0) and np.all(prepared_audio <= 1.0)
    
    @pytest.mark.asyncio
    async def test_voice_activity_detection(self):
        """Test basic voice activity detection."""
        stt = WhisperSTT()
        
        # Test with silence (zeros)
        silence = b'\x00' * 1024
        is_speech = await stt.is_speech_detected(silence)
        assert is_speech is False
        
        # Test with noise (random data)
        import numpy as np
        noise = np.random.randint(-1000, 1000, 512, dtype=np.int16).tobytes()
        is_speech = await stt.is_speech_detected(noise)
        assert isinstance(is_speech, bool)


class TestTTSComponent:
    """Test Text-to-Speech component."""
    
    def test_tts_initialization(self):
        """Test TTS component can be created."""
        tts = KokoroTTS()
        assert tts._client is None
        assert tts._api_url == settings.kokoro_api_url
        assert tts._voice == settings.kokoro_voice
    
    def test_text_preprocessing(self):
        """Test text preprocessing for TTS."""
        tts = KokoroTTS()
        
        # Test symbol replacement
        input_text = "Contact us @ 555-1234 & we'll help you 100%"
        result = asyncio.run(tts.preprocess_text(input_text))
        expected = "Contact us at 555-1234 and we'll help you 100 percent."
        assert result == expected
        
        # Test abbreviation expansion
        input_text = "Dr. Smith at 123 Main St."
        result = asyncio.run(tts.preprocess_text(input_text))
        assert "Doctor Smith" in result
        assert "Street" in result
    
    def test_legal_disclaimer_injection(self):
        """Test legal disclaimer injection."""
        tts = KokoroTTS()
        
        # Test with legal content
        legal_text = "I advise you to contact the court immediately"
        result = tts._add_legal_disclaimer(legal_text)
        assert "does not constitute legal advice" in result
        
        # Test with non-legal content
        normal_text = "Our office hours are 9 AM to 5 PM"
        result = tts._add_legal_disclaimer(normal_text)
        assert result == normal_text  # No disclaimer added
    
    @pytest.mark.asyncio 
    async def test_duration_estimation(self):
        """Test audio duration estimation."""
        tts = KokoroTTS()
        
        short_text = "Hello"
        duration = await tts.estimate_duration(short_text)
        assert 0.5 <= duration <= 2.0  # Should be short
        
        long_text = "This is a much longer text that should take significantly more time to synthesize and speak aloud."
        duration = await tts.estimate_duration(long_text)
        assert duration > 3.0  # Should be longer


class TestConfiguration:
    """Test configuration management."""
    
    def test_settings_loading(self):
        """Test settings are loaded correctly."""
        assert settings.openai_api_key == "test-key-123"
        assert settings.debug is True
        assert settings.whisper_model == "base"
        assert settings.confidence_threshold == 0.85
    
    def test_audio_configuration(self):
        """Test audio-related configuration."""
        assert settings.sample_rate == 16000
        assert settings.chunk_size == 1024
        assert settings.max_audio_length == 30
        assert settings.response_timeout == 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])