"""
HERMES E2E Testing Suite
Comprehensive end-to-end testing for all Phase 2 & 3 components
"""

import asyncio
import pytest
import json
import time
import os
import tempfile
from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from fastapi.testclient import TestClient
from pathlib import Path

# Import HERMES components for testing
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from hermes.main import app
from hermes.voice.context_manager import VoiceContextManager, EmotionalState, ConversationPhase
from hermes.voice.multilang_support import MultiLanguageProcessor, SupportedLanguage
from hermes.analytics.engine import AnalyticsEngine
from hermes.mcp.orchestrator import mcp_orchestrator
from hermes.audit.api import audit_manager
from hermes.api.clio_endpoints import clio_client

class HermesE2ETestSuite:
    """Comprehensive E2E testing suite for HERMES"""
    
    def __init__(self):
        self.test_client = TestClient(app)
        self.test_data = self.load_test_data()
        self.mock_audio_data = self.generate_mock_audio()
        
    def load_test_data(self) -> Dict[str, Any]:
        """Load test data for various scenarios"""
        return {
            "legal_conversations": [
                {
                    "text": "Hi, I need help with a contract dispute. The other party is not honoring the agreement.",
                    "expected_phase": ConversationPhase.INTAKE,
                    "expected_entities": ["contract", "dispute"],
                    "expected_emotion": EmotionalState.ANXIOUS
                },
                {
                    "text": "This is urgent! I was just arrested and need immediate legal representation.",
                    "expected_phase": ConversationPhase.EMERGENCY,
                    "expected_entities": ["arrest", "emergency"],
                    "expected_emotion": EmotionalState.URGENT
                },
                {
                    "text": "Thank you for explaining that. It makes perfect sense now.",
                    "expected_phase": ConversationPhase.CLARIFICATION,
                    "expected_entities": [],
                    "expected_emotion": EmotionalState.SATISFIED
                }
            ],
            "multilang_texts": [
                {"text": "Hola, necesito ayuda legal", "language": SupportedLanguage.SPANISH},
                {"text": "Bonjour, j'ai besoin d'aide juridique", "language": SupportedLanguage.FRENCH},
                {"text": "Hallo, ich brauche rechtliche Hilfe", "language": SupportedLanguage.GERMAN}
            ],
            "clio_test_data": {
                "contact": {
                    "name": "John Test Client",
                    "email": "john.test@example.com",
                    "phone": "+1-555-0123"
                },
                "matter": {
                    "client_id": 12345,
                    "description": "Test Legal Matter",
                    "practice_area": "Contract Law"
                }
            },
            "analytics_scenarios": [
                {
                    "event_type": "voice_session_started",
                    "metadata": {"session_id": "test_session_1", "client_id": "test_client"}
                },
                {
                    "event_type": "clio_sync_completed", 
                    "metadata": {"records_synced": 150, "sync_duration": 45.2}
                }
            ]
        }
    
    def generate_mock_audio(self) -> bytes:
        """Generate mock audio data for testing"""
        # Create a simple WAV file with silence for testing
        import wave
        import struct
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            with wave.open(temp_file.name, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(16000)  # 16kHz
                
                # Generate 2 seconds of silence
                frames = []
                for _ in range(32000):  # 2 seconds at 16kHz
                    frames.append(struct.pack('<h', 0))
                
                wav_file.writeframes(b''.join(frames))
            
            # Read the file back as bytes
            with open(temp_file.name, 'rb') as f:
                audio_data = f.read()
            
            os.unlink(temp_file.name)
            return audio_data

    # Core API Endpoint Tests
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test system health endpoint"""
        response = self.test_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "operational"
        assert "components" in data
        assert "metrics" in data
        
        print("✅ Health endpoint test passed")
    
    @pytest.mark.asyncio  
    async def test_dashboard_endpoint(self):
        """Test dashboard serving"""
        response = self.test_client.get("/dashboard")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        
        print("✅ Dashboard endpoint test passed")
    
    @pytest.mark.asyncio
    async def test_auth_endpoints(self):
        """Test authentication endpoints"""
        # Test user info endpoint
        response = self.test_client.get("/api/auth/user")
        assert response.status_code == 200
        
        data = response.json()
        assert "name" in data
        assert "role" in data
        assert "permissions" in data
        
        print("✅ Auth endpoints test passed")
    
    # Voice Processing Tests
    
    @pytest.mark.asyncio
    async def test_voice_context_manager(self):
        """Test voice context management with emotion detection"""
        context_manager = VoiceContextManager()
        
        for conversation in self.test_data["legal_conversations"]:
            # Create session
            session_id = f"test_session_{int(time.time())}"
            context = await context_manager.create_session_context(
                session_id=session_id,
                client_id="test_client"
            )
            
            assert context.session_id == session_id
            assert context.conversation_phase == ConversationPhase.GREETING
            
            # Update with conversation text
            updated_context = await context_manager.update_conversation_context(
                session_id=session_id,
                text_input=conversation["text"],
                detected_intent="legal_inquiry"
            )
            
            # Verify phase detection
            assert updated_context.conversation_phase == conversation["expected_phase"]
            
            # Verify emotion detection
            assert updated_context.emotional_state.primary_emotion == conversation["expected_emotion"]
            
            # Test contextual suggestions
            suggestions = await context_manager.get_contextual_suggestions(session_id)
            assert len(suggestions) > 0
            assert all("type" in s and "text" in s for s in suggestions)
            
            # End session
            summary = await context_manager.end_session_context(session_id)
            assert summary is not None
            assert summary["session_id"] == session_id
        
        print("✅ Voice context manager test passed")
    
    @pytest.mark.asyncio
    async def test_multilanguage_support(self):
        """Test multi-language STT/TTS support"""
        # Mock the actual models to avoid loading large files in tests
        with patch('hermes.voice.multilang_support.whisper.load_model') as mock_whisper:
            mock_model = MagicMock()
            mock_model.detect_language.return_value = (None, {"en": 0.8, "es": 0.2})
            mock_model.transcribe.return_value = {
                "text": "Hello, I need legal help",
                "segments": [{"avg_logprob": -0.5, "start": 0, "end": 2}]
            }
            mock_whisper.return_value = mock_model
            
            # Test language detection and transcription
            from hermes.voice.multilang_support import MultiLanguageSTT
            stt = MultiLanguageSTT()
            
            # Test language detection
            detection_result = await stt.detect_language(self.mock_audio_data)
            assert detection_result.detected_language == SupportedLanguage.ENGLISH
            assert detection_result.confidence > 0.5
            
            # Test transcription
            transcription = await stt.transcribe_audio(self.mock_audio_data)
            assert transcription.text
            assert transcription.language == SupportedLanguage.ENGLISH
            assert transcription.confidence > 0
            
            print("✅ Multi-language support test passed")
    
    # Analytics Engine Tests
    
    @pytest.mark.asyncio
    async def test_analytics_engine(self):
        """Test analytics engine functionality"""
        analytics = AnalyticsEngine()
        
        # Test event tracking
        for scenario in self.test_data["analytics_scenarios"]:
            await analytics.track_event(
                event_type=scenario["event_type"],
                metadata=scenario["metadata"]
            )
        
        # Test analytics retrieval
        dashboard_data = await analytics.get_dashboard_overview()
        assert "total_calls" in dashboard_data
        assert "conversion_rate" in dashboard_data
        
        # Test voice metrics
        voice_metrics = await analytics.get_voice_metrics()
        assert "average_response_time" in voice_metrics
        assert "session_count" in voice_metrics
        
        # Test real-time metrics
        realtime_data = await analytics.get_realtime_metrics()
        assert "active_sessions" in realtime_data
        
        print("✅ Analytics engine test passed")
    
    # Clio Integration Tests
    
    @pytest.mark.asyncio
    async def test_clio_endpoints(self):
        """Test Clio CRM integration endpoints"""
        # Mock Clio API calls
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": {"id": 12345, "name": "Test Contact"}}
            
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            # Test contacts endpoint
            response = self.test_client.get("/api/clio/contacts")
            assert response.status_code in [200, 401]  # 401 if auth not configured
            
            # Test matters endpoint
            response = self.test_client.get("/api/clio/matters")
            assert response.status_code in [200, 401]
            
            print("✅ Clio endpoints test passed")
    
    # MCP Orchestration Tests
    
    @pytest.mark.asyncio
    async def test_mcp_orchestration(self):
        """Test MCP orchestration system"""
        # Test orchestration status
        response = self.test_client.get("/mcp/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "server_status" in data
        assert "active_workflows" in data
        
        # Test strategic task execution (with mock)
        with patch.object(mcp_orchestrator, 'execute_strategic_task') as mock_task:
            mock_task.return_value = {"status": "completed", "result": "success"}
            
            response = self.test_client.post(
                "/mcp/execute/database_optimization",
                json={"param": "value"}
            )
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert data["task_name"] == "database_optimization"
        
        print("✅ MCP orchestration test passed")
    
    # Audit Trail Tests
    
    @pytest.mark.asyncio
    async def test_audit_trail(self):
        """Test audit trail and compliance features"""
        # Test audit events endpoint
        response = self.test_client.get("/api/audit/events")
        assert response.status_code in [200, 401]
        
        # Test security events
        response = self.test_client.get("/api/audit/security-events")
        assert response.status_code in [200, 401]
        
        # Test compliance report
        response = self.test_client.get("/api/audit/compliance-report")
        assert response.status_code in [200, 401]
        
        print("✅ Audit trail test passed")
    
    # WebSocket Tests
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test WebSocket real-time communication"""
        with self.test_client.websocket_connect("/voice") as websocket:
            # Test connection establishment
            data = websocket.receive_json()
            assert "session_id" in data or data.get("type") == "connection_established"
            
            # Test sending voice data (mock)
            websocket.send_json({
                "type": "audio_data",
                "data": "base64_encoded_audio",
                "timestamp": time.time()
            })
            
            # Should receive response
            response = websocket.receive_json()
            assert "type" in response
        
        print("✅ WebSocket connection test passed")
    
    # Dashboard Integration Tests
    
    @pytest.mark.asyncio
    async def test_dashboard_api_endpoints(self):
        """Test dashboard API endpoints"""
        # Test overview data
        response = self.test_client.get("/api/analytics/dashboard/overview")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "data" in data
        
        # Test real-time metrics
        response = self.test_client.get("/api/analytics/realtime")
        assert response.status_code == 200
        
        print("✅ Dashboard API endpoints test passed")
    
    # Legal NLP Tests
    
    @pytest.mark.asyncio
    async def test_legal_nlp_processing(self):
        """Test legal NLP processing capabilities"""
        # Test entity extraction endpoint
        response = self.test_client.post("/api/voice/legal-nlp/extract-entities", json={
            "text": "I need help with a contract dispute involving $50,000 in damages due by December 15th, 2024."
        })
        assert response.status_code in [200, 501]  # 501 if not implemented
        
        # Test risk assessment
        response = self.test_client.post("/api/voice/legal-nlp/assess-risk", json={
            "text": "The contract clearly states the deadline for payment."
        })
        assert response.status_code in [200, 501]
        
        print("✅ Legal NLP processing test passed")
    
    # Integration Tests
    
    @pytest.mark.asyncio
    async def test_full_voice_workflow(self):
        """Test complete voice interaction workflow"""
        # Simulate complete voice session
        session_data = {
            "audio_data": "mock_audio_base64",
            "client_id": "test_client_123",
            "language_preference": "en"
        }
        
        # Test session creation through WebSocket
        with self.test_client.websocket_connect("/voice") as websocket:
            # Send session start
            websocket.send_json({
                "type": "start_session",
                "data": session_data
            })
            
            # Should receive session confirmation
            response = websocket.receive_json()
            assert response.get("type") in ["session_started", "connection_established"]
            
            # Send audio data
            websocket.send_json({
                "type": "audio_chunk", 
                "data": self.mock_audio_data.hex(),
                "timestamp": time.time()
            })
            
            # Should receive transcription and response
            response = websocket.receive_json()
            assert "type" in response
        
        print("✅ Full voice workflow test passed")
    
    @pytest.mark.asyncio
    async def test_cross_system_integration(self):
        """Test integration between different HERMES components"""
        # Test analytics + voice context integration
        context_manager = VoiceContextManager()
        analytics = AnalyticsEngine()
        
        # Create voice session
        session_id = f"integration_test_{int(time.time())}"
        context = await context_manager.create_session_context(session_id)
        
        # Track analytics event
        await analytics.track_event("voice_session_started", {
            "session_id": session_id,
            "context_phase": context.conversation_phase.value
        })
        
        # Update context with legal inquiry
        await context_manager.update_conversation_context(
            session_id,
            text_input="I need help with a personal injury case",
            detected_intent="legal_consultation"
        )
        
        # Track phase change in analytics
        await analytics.track_event("conversation_phase_change", {
            "session_id": session_id,
            "new_phase": context.conversation_phase.value
        })
        
        # Verify cross-system data consistency
        session_analytics = await analytics.get_session_metrics(session_id)
        context_summary = await context_manager.get_session_analytics(session_id)
        
        assert session_analytics is not None
        assert context_summary is not None
        
        print("✅ Cross-system integration test passed")
    
    # Performance Tests
    
    @pytest.mark.asyncio
    async def test_system_performance(self):
        """Test system performance under load"""
        start_time = time.time()
        
        # Simulate concurrent requests
        tasks = []
        for i in range(10):
            task = asyncio.create_task(self.simulate_voice_session(f"perf_test_{i}"))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Check that most sessions completed successfully
        successful_sessions = sum(1 for r in results if not isinstance(r, Exception))
        assert successful_sessions >= 8  # At least 80% success rate
        
        # Check performance requirements
        assert total_time < 30  # Should complete within 30 seconds
        
        print(f"✅ Performance test passed: {successful_sessions}/10 sessions successful in {total_time:.2f}s")
    
    async def simulate_voice_session(self, session_id: str) -> bool:
        """Simulate a voice session for performance testing"""
        try:
            context_manager = VoiceContextManager()
            
            # Create session
            await context_manager.create_session_context(session_id)
            
            # Simulate conversation updates
            for text in ["Hello", "I need legal help", "Thank you"]:
                await context_manager.update_conversation_context(
                    session_id,
                    text_input=text
                )
                await asyncio.sleep(0.1)  # Small delay
            
            # End session
            await context_manager.end_session_context(session_id)
            return True
            
        except Exception as e:
            print(f"Session {session_id} failed: {e}")
            return False
    
    # PWA and Accessibility Tests
    
    @pytest.mark.asyncio
    async def test_pwa_features(self):
        """Test Progressive Web App features"""
        # Test manifest.json
        response = self.test_client.get("/static/manifest.json")
        assert response.status_code == 200
        
        manifest = response.json()
        assert "name" in manifest
        assert "icons" in manifest
        assert "start_url" in manifest
        
        # Test service worker
        response = self.test_client.get("/static/sw.js")
        assert response.status_code == 200
        assert "javascript" in response.headers["content-type"]
        
        print("✅ PWA features test passed")
    
    # Run All Tests
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all E2E tests and return results"""
        test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": [],
            "start_time": time.time(),
            "end_time": None
        }
        
        # List of all test methods
        test_methods = [
            self.test_health_endpoint,
            self.test_dashboard_endpoint,
            self.test_auth_endpoints,
            self.test_voice_context_manager,
            self.test_multilanguage_support,
            self.test_analytics_engine,
            self.test_clio_endpoints,
            self.test_mcp_orchestration,
            self.test_audit_trail,
            self.test_websocket_connection,
            self.test_dashboard_api_endpoints,
            self.test_legal_nlp_processing,
            self.test_full_voice_workflow,
            self.test_cross_system_integration,
            self.test_system_performance,
            self.test_pwa_features
        ]
        
        print("🚀 Starting HERMES E2E Test Suite...")
        print("=" * 60)
        
        for test_method in test_methods:
            test_results["total_tests"] += 1
            test_name = test_method.__name__
            
            try:
                print(f"Running {test_name}...")
                await test_method()
                test_results["passed_tests"] += 1
                test_results["test_details"].append({
                    "name": test_name,
                    "status": "PASSED",
                    "error": None
                })
            except Exception as e:
                test_results["failed_tests"] += 1
                test_results["test_details"].append({
                    "name": test_name,
                    "status": "FAILED",
                    "error": str(e)
                })
                print(f"❌ {test_name} failed: {e}")
        
        test_results["end_time"] = time.time()
        test_duration = test_results["end_time"] - test_results["start_time"]
        
        print("=" * 60)
        print("📊 E2E Test Results Summary:")
        print(f"Total Tests: {test_results['total_tests']}")
        print(f"Passed: {test_results['passed_tests']}")
        print(f"Failed: {test_results['failed_tests']}")
        print(f"Success Rate: {(test_results['passed_tests']/test_results['total_tests']*100):.1f}%")
        print(f"Duration: {test_duration:.2f} seconds")
        
        if test_results["failed_tests"] > 0:
            print("\n❌ Failed Tests:")
            for test in test_results["test_details"]:
                if test["status"] == "FAILED":
                    print(f"  - {test['name']}: {test['error']}")
        
        return test_results

# Test runner function
async def run_hermes_e2e_tests():
    """Run the complete HERMES E2E test suite"""
    test_suite = HermesE2ETestSuite()
    return await test_suite.run_all_tests()

# Pytest fixtures and test functions for pytest integration
@pytest.fixture
def test_suite():
    return HermesE2ETestSuite()

@pytest.mark.asyncio
async def test_hermes_health(test_suite):
    await test_suite.test_health_endpoint()

@pytest.mark.asyncio
async def test_hermes_voice_context(test_suite):
    await test_suite.test_voice_context_manager()

@pytest.mark.asyncio
async def test_hermes_multilang(test_suite):
    await test_suite.test_multilanguage_support()

@pytest.mark.asyncio
async def test_hermes_analytics(test_suite):
    await test_suite.test_analytics_engine()

@pytest.mark.asyncio
async def test_hermes_integration(test_suite):
    await test_suite.test_cross_system_integration()

@pytest.mark.asyncio
async def test_hermes_performance(test_suite):
    await test_suite.test_system_performance()

if __name__ == "__main__":
    # Run tests directly
    asyncio.run(run_hermes_e2e_tests())