"""
Monitoring and Metrics
=====================

Production monitoring, metrics collection, and health checks.
"""

import asyncio
import sys
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Deque, Dict, Optional

# Add src to path for imports
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from core.logging_config import get_logger  # noqa: E402

logger = get_logger(__name__)


@dataclass
class RequestMetric:
    """Request metric data."""

    method: str
    path: str
    status_code: int
    duration_ms: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ServiceHealth:
    """Service health status."""

    status: str  # healthy, degraded, unhealthy
    uptime_seconds: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time_ms: float
    error_rate: float
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    services: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class MetricsCollector:
    """Collects and aggregates application metrics."""

    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics
        self.start_time = datetime.now()
        self.metrics: Deque[RequestMetric] = deque(maxlen=max_metrics)
        self.error_log: Deque[Dict[str, Any]] = deque(maxlen=100)
        self.request_counts = defaultdict(int)
        self.status_counts = defaultdict(int)
        self._lock = asyncio.Lock()

    async def record_request(self, method: str, path: str, status_code: int, duration_ms: float):
        """Record a request metric."""
        async with self._lock:
            metric = RequestMetric(
                method=method,
                path=path,
                status_code=status_code,
                duration_ms=duration_ms,
                timestamp=datetime.now(),
            )
            self.metrics.append(metric)
            self.request_counts[f"{method} {path}"] += 1
            self.status_counts[status_code] += 1

            if status_code >= 400:
                self.error_log.append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "method": method,
                        "path": path,
                        "status_code": status_code,
                        "duration_ms": duration_ms,
                    }
                )

    async def get_health(self) -> ServiceHealth:
        """Get current service health."""
        async with self._lock:
            if not self.metrics:
                return ServiceHealth(
                    status="healthy",
                    uptime_seconds=(datetime.now() - self.start_time).total_seconds(),
                    total_requests=0,
                    successful_requests=0,
                    failed_requests=0,
                    average_response_time_ms=0.0,
                    error_rate=0.0,
                )

            # Calculate metrics
            total = len(self.metrics)
            successful = sum(1 for m in self.metrics if 200 <= m.status_code < 400)
            failed = sum(1 for m in self.metrics if m.status_code >= 400)
            avg_duration = sum(m.duration_ms for m in self.metrics) / total
            error_rate = (failed / total) * 100 if total > 0 else 0.0

            # Determine status
            if error_rate > 10:
                status = "unhealthy"
            elif error_rate > 5:
                status = "degraded"
            else:
                status = "healthy"

            # Get last error
            last_error = None
            last_error_time = None
            if self.error_log:
                last_error_data = self.error_log[-1]
                last_err = last_error_data
                last_error = f"{last_err['method']} {last_err['path']} - {last_err['status_code']}"
                last_error_time = datetime.fromisoformat(last_error_data["timestamp"])

            return ServiceHealth(
                status=status,
                uptime_seconds=(datetime.now() - self.start_time).total_seconds(),
                total_requests=total,
                successful_requests=successful,
                failed_requests=failed,
                average_response_time_ms=round(avg_duration, 2),
                error_rate=round(error_rate, 2),
                last_error=last_error,
                last_error_time=last_error_time,
            )

    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        async with self._lock:
            if not self.metrics:
                return {
                    "total_requests": 0,
                    "requests_per_minute": 0,
                    "average_response_time_ms": 0,
                    "error_rate_percent": 0,
                    "top_endpoints": [],
                    "status_code_distribution": {},
                }

            # Calculate time window
            now = datetime.now()
            one_minute_ago = now - timedelta(minutes=1)
            recent_metrics = [m for m in self.metrics if m.timestamp >= one_minute_ago]

            total = len(self.metrics)
            recent_count = len(recent_metrics)
            avg_duration = sum(m.duration_ms for m in self.metrics) / total
            failed = sum(1 for m in self.metrics if m.status_code >= 400)
            error_rate = (failed / total) * 100 if total > 0 else 0.0

            # Top endpoints
            endpoint_counts = defaultdict(int)
            for m in self.metrics:
                endpoint_counts[f"{m.method} {m.path}"] += 1
            top_endpoints = sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:10]

            return {
                "total_requests": total,
                "requests_per_minute": recent_count,
                "average_response_time_ms": round(avg_duration, 2),
                "error_rate_percent": round(error_rate, 2),
                "top_endpoints": [{"endpoint": k, "count": v} for k, v in top_endpoints],
                "status_code_distribution": dict(self.status_counts),
            }


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector
