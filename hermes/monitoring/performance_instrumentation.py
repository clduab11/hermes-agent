"""
Enterprise-grade performance instrumentation for HERMES voice pipeline.

Provides comprehensive latency profiling, percentile tracking, and SLA monitoring
for mission-critical voice interactions with paying law firm customers.
"""

import asyncio
import logging
import time
from collections import deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import AsyncGenerator, Deque, Dict, List, Optional
import statistics

logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    """Voice pipeline processing stages for latency breakdown."""
    STT = "speech_to_text"
    LLM = "llm_processing"
    TTS = "text_to_speech"
    TOTAL = "total_pipeline"
    WEBSOCKET_SEND = "websocket_send"
    AUDIO_ENCODE = "audio_encode"
    AUDIO_DECODE = "audio_decode"


@dataclass
class LatencyMeasurement:
    """Single latency measurement with context."""
    stage: PipelineStage
    duration_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None
    tenant_id: Optional[str] = None
    success: bool = True
    error_type: Optional[str] = None


@dataclass
class LatencyStats:
    """Statistical latency metrics for a pipeline stage."""
    stage: PipelineStage
    count: int = 0
    min_ms: float = float('inf')
    max_ms: float = 0.0
    mean_ms: float = 0.0
    p50_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    recent_samples: Deque[float] = field(default_factory=lambda: deque(maxlen=1000))

    def update(self, duration_ms: float) -> None:
        """Update statistics with new measurement."""
        self.count += 1
        self.min_ms = min(self.min_ms, duration_ms)
        self.max_ms = max(self.max_ms, duration_ms)
        self.recent_samples.append(duration_ms)

        # Recalculate percentiles from recent samples
        if self.recent_samples:
            sorted_samples = sorted(self.recent_samples)
            self.mean_ms = statistics.mean(sorted_samples)
            self.p50_ms = statistics.median(sorted_samples)
            self.p95_ms = sorted_samples[int(len(sorted_samples) * 0.95)] if len(sorted_samples) > 20 else self.mean_ms
            self.p99_ms = sorted_samples[int(len(sorted_samples) * 0.99)] if len(sorted_samples) > 100 else self.mean_ms

    def to_dict(self) -> Dict[str, float]:
        """Export statistics as dictionary."""
        return {
            "stage": self.stage.value,
            "count": self.count,
            "min_ms": self.min_ms if self.min_ms != float('inf') else 0.0,
            "max_ms": self.max_ms,
            "mean_ms": round(self.mean_ms, 2),
            "p50_ms": round(self.p50_ms, 2),
            "p95_ms": round(self.p95_ms, 2),
            "p99_ms": round(self.p99_ms, 2),
        }


class PerformanceInstrument:
    """
    Enterprise-grade performance instrumentation for voice pipeline.

    Tracks:
    - Per-stage latency (STT, LLM, TTS)
    - Percentile distributions (p50, p95, p99)
    - Per-tenant performance metrics
    - SLA compliance (target: <500ms p95)
    - Error rates by stage
    """

    # SLA targets for law firm customers
    SLA_TARGET_P95_MS = 500.0  # 500ms p95 latency target
    SLA_TARGET_P99_MS = 1000.0  # 1s p99 latency target
    ERROR_RATE_THRESHOLD = 0.01  # 1% error rate threshold

    def __init__(self):
        self._stage_stats: Dict[PipelineStage, LatencyStats] = {
            stage: LatencyStats(stage=stage) for stage in PipelineStage
        }
        self._tenant_stats: Dict[str, Dict[PipelineStage, LatencyStats]] = {}
        self._measurements: Deque[LatencyMeasurement] = deque(maxlen=10000)
        self._errors_by_stage: Dict[PipelineStage, int] = {stage: 0 for stage in PipelineStage}
        self._lock = asyncio.Lock()

        # Alert thresholds
        self._last_alert_time: Dict[str, datetime] = {}
        self._alert_cooldown = timedelta(minutes=5)

    @asynccontextmanager
    async def measure(
        self,
        stage: PipelineStage,
        session_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> AsyncGenerator[None, None]:
        """
        Context manager for measuring pipeline stage latency.

        Usage:
            async with instrument.measure(PipelineStage.STT, session_id="abc123"):
                result = await stt.transcribe(audio)

        Args:
            stage: Pipeline stage being measured
            session_id: Optional session identifier
            tenant_id: Optional tenant identifier
        """
        start_time = time.perf_counter()
        error_occurred = False
        error_type = None

        try:
            yield
        except Exception as e:
            error_occurred = True
            error_type = type(e).__name__
            raise
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Record measurement
            measurement = LatencyMeasurement(
                stage=stage,
                duration_ms=duration_ms,
                session_id=session_id,
                tenant_id=tenant_id,
                success=not error_occurred,
                error_type=error_type
            )

            await self._record_measurement(measurement)

    async def _record_measurement(self, measurement: LatencyMeasurement) -> None:
        """Record and analyze latency measurement."""
        async with self._lock:
            # Store measurement
            self._measurements.append(measurement)

            # Update global stage stats
            self._stage_stats[measurement.stage].update(measurement.duration_ms)

            # Update tenant-specific stats if tenant_id provided
            if measurement.tenant_id:
                if measurement.tenant_id not in self._tenant_stats:
                    self._tenant_stats[measurement.tenant_id] = {
                        stage: LatencyStats(stage=stage) for stage in PipelineStage
                    }
                self._tenant_stats[measurement.tenant_id][measurement.stage].update(
                    measurement.duration_ms
                )

            # Track errors
            if not measurement.success:
                self._errors_by_stage[measurement.stage] += 1

            # Check SLA compliance and alert if breached
            await self._check_sla_compliance(measurement)

    async def _check_sla_compliance(self, measurement: LatencyMeasurement) -> None:
        """Check if measurement breaches SLA and alert if necessary."""
        stats = self._stage_stats[measurement.stage]

        # Check p95 SLA breach
        if stats.p95_ms > self.SLA_TARGET_P95_MS:
            await self._alert_sla_breach(
                f"{measurement.stage.value} p95 latency ({stats.p95_ms:.0f}ms) exceeds target ({self.SLA_TARGET_P95_MS:.0f}ms)",
                severity="WARNING"
            )

        # Check p99 SLA breach
        if stats.p99_ms > self.SLA_TARGET_P99_MS:
            await self._alert_sla_breach(
                f"{measurement.stage.value} p99 latency ({stats.p99_ms:.0f}ms) exceeds target ({self.SLA_TARGET_P99_MS:.0f}ms)",
                severity="CRITICAL"
            )

        # Check error rate
        error_rate = self._errors_by_stage[measurement.stage] / max(stats.count, 1)
        if error_rate > self.ERROR_RATE_THRESHOLD:
            await self._alert_sla_breach(
                f"{measurement.stage.value} error rate ({error_rate:.1%}) exceeds threshold ({self.ERROR_RATE_THRESHOLD:.1%})",
                severity="CRITICAL"
            )

    async def _alert_sla_breach(self, message: str, severity: str = "WARNING") -> None:
        """Send alert for SLA breach with cooldown."""
        alert_key = f"{severity}:{message}"
        now = datetime.utcnow()

        # Check cooldown
        if alert_key in self._last_alert_time:
            if now - self._last_alert_time[alert_key] < self._alert_cooldown:
                return  # Skip duplicate alert during cooldown

        # Log alert
        if severity == "CRITICAL":
            logger.error(f"🚨 SLA BREACH [CRITICAL]: {message}")
        else:
            logger.warning(f"⚠️  SLA BREACH [WARNING]: {message}")

        # Update alert time
        self._last_alert_time[alert_key] = now

        # TODO: Send to external alerting system (PagerDuty, etc.)
        # In production, integrate with alerting service:
        # await alert_service.send_alert(message, severity)

    def get_global_stats(self) -> Dict[str, Dict]:
        """Get global latency statistics across all stages."""
        return {
            stage.value: stats.to_dict()
            for stage, stats in self._stage_stats.items()
        }

    def get_tenant_stats(self, tenant_id: str) -> Optional[Dict[str, Dict]]:
        """Get latency statistics for specific tenant."""
        if tenant_id not in self._tenant_stats:
            return None

        return {
            stage.value: stats.to_dict()
            for stage, stats in self._tenant_stats[tenant_id].items()
        }

    def get_sla_compliance_report(self) -> Dict[str, any]:
        """
        Generate SLA compliance report for customer dashboard.

        Returns:
            dict with SLA metrics and compliance status
        """
        total_stats = self._stage_stats[PipelineStage.TOTAL]
        stt_stats = self._stage_stats[PipelineStage.STT]
        llm_stats = self._stage_stats[PipelineStage.LLM]
        tts_stats = self._stage_stats[PipelineStage.TTS]

        # Calculate error rates
        total_requests = max(total_stats.count, 1)
        total_errors = sum(self._errors_by_stage.values())
        error_rate = total_errors / total_requests

        # Determine compliance status
        p95_compliant = total_stats.p95_ms <= self.SLA_TARGET_P95_MS
        p99_compliant = total_stats.p99_ms <= self.SLA_TARGET_P99_MS
        error_rate_compliant = error_rate <= self.ERROR_RATE_THRESHOLD

        overall_compliant = p95_compliant and p99_compliant and error_rate_compliant

        return {
            "sla_status": "COMPLIANT" if overall_compliant else "BREACH",
            "summary": {
                "total_requests": total_requests,
                "total_errors": total_errors,
                "error_rate": round(error_rate, 4),
                "uptime_percentage": round((1 - error_rate) * 100, 2),
            },
            "latency_targets": {
                "p95_target_ms": self.SLA_TARGET_P95_MS,
                "p95_actual_ms": round(total_stats.p95_ms, 2),
                "p95_compliant": p95_compliant,
                "p99_target_ms": self.SLA_TARGET_P99_MS,
                "p99_actual_ms": round(total_stats.p99_ms, 2),
                "p99_compliant": p99_compliant,
            },
            "stage_breakdown": {
                "stt": {
                    "mean_ms": round(stt_stats.mean_ms, 2),
                    "p95_ms": round(stt_stats.p95_ms, 2),
                },
                "llm": {
                    "mean_ms": round(llm_stats.mean_ms, 2),
                    "p95_ms": round(llm_stats.p95_ms, 2),
                },
                "tts": {
                    "mean_ms": round(tts_stats.mean_ms, 2),
                    "p95_ms": round(tts_stats.p95_ms, 2),
                },
                "total": {
                    "mean_ms": round(total_stats.mean_ms, 2),
                    "p50_ms": round(total_stats.p50_ms, 2),
                    "p95_ms": round(total_stats.p95_ms, 2),
                    "p99_ms": round(total_stats.p99_ms, 2),
                },
            },
            "error_breakdown": {
                stage.value: count
                for stage, count in self._errors_by_stage.items()
                if count > 0
            },
        }

    def get_recent_measurements(
        self,
        limit: int = 100,
        stage: Optional[PipelineStage] = None,
        tenant_id: Optional[str] = None
    ) -> List[Dict]:
        """Get recent measurements with optional filtering."""
        measurements = list(self._measurements)

        # Filter by stage if specified
        if stage:
            measurements = [m for m in measurements if m.stage == stage]

        # Filter by tenant if specified
        if tenant_id:
            measurements = [m for m in measurements if m.tenant_id == tenant_id]

        # Return most recent N measurements
        recent = measurements[-limit:]

        return [
            {
                "stage": m.stage.value,
                "duration_ms": round(m.duration_ms, 2),
                "timestamp": m.timestamp.isoformat(),
                "session_id": m.session_id,
                "tenant_id": m.tenant_id,
                "success": m.success,
                "error_type": m.error_type,
            }
            for m in recent
        ]

    async def reset_stats(self, tenant_id: Optional[str] = None) -> None:
        """Reset statistics (for testing or billing period rollover)."""
        async with self._lock:
            if tenant_id:
                # Reset tenant-specific stats
                if tenant_id in self._tenant_stats:
                    del self._tenant_stats[tenant_id]
                logger.info(f"Reset performance stats for tenant: {tenant_id}")
            else:
                # Reset global stats
                self._stage_stats = {
                    stage: LatencyStats(stage=stage) for stage in PipelineStage
                }
                self._tenant_stats.clear()
                self._measurements.clear()
                self._errors_by_stage = {stage: 0 for stage in PipelineStage}
                logger.info("Reset all performance stats")


# Global performance instrument instance
performance_instrument = PerformanceInstrument()


async def get_performance_dashboard() -> Dict[str, any]:
    """
    Get comprehensive performance dashboard data for monitoring.

    Returns:
        Complete performance metrics suitable for Grafana/dashboard display
    """
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "global_stats": performance_instrument.get_global_stats(),
        "sla_compliance": performance_instrument.get_sla_compliance_report(),
        "recent_measurements": performance_instrument.get_recent_measurements(limit=50),
        "active_tenants": len(performance_instrument._tenant_stats),
    }
