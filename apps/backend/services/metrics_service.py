"""
Redis-backed Metrics Service for Compliance Monitoring
Provides persistent, atomic metrics tracking across restarts.
"""
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

# Try to import redis, fall back to in-memory if not available
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory metrics (will not persist)")


class ComplianceMetricsService:
    """
    Metrics service with Redis persistence.
    Falls back to in-memory storage if Redis is unavailable.
    """
    
    # Redis key prefixes
    KEY_PREFIX = "compliance:"
    TOTAL_KEY = "compliance:total"
    APPROVED_KEY = "compliance:approved"
    BLOCKED_KEY = "compliance:blocked"
    MANUAL_REVIEW_KEY = "compliance:manual_review"
    CONFIDENCES_KEY = "compliance:confidences"
    LAST_RESET_KEY = "compliance:last_reset"
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize metrics service.
        
        Args:
            redis_url: Redis connection URL. Defaults to REDIS_URL env var or localhost.
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_client = None
        self._in_memory_metrics = {
            "total": 0,
            "approved": 0,
            "blocked": 0,
            "manual_review": 0,
            "confidences": [],
            "last_reset": datetime.utcnow().isoformat()
        }
        
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5
                )
                # Test connection
                self.redis_client.ping()
                logger.info(f"Connected to Redis at {self.redis_url}")
                self._initialize_keys()
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}, using in-memory")
                self.redis_client = None
    
    def _initialize_keys(self) -> None:
        """Initialize Redis keys if they don't exist."""
        if not self.redis_client:
            return
        
        pipe = self.redis_client.pipeline()
        if not self.redis_client.exists(self.TOTAL_KEY):
            pipe.set(self.TOTAL_KEY, 0)
        if not self.redis_client.exists(self.APPROVED_KEY):
            pipe.set(self.APPROVED_KEY, 0)
        if not self.redis_client.exists(self.BLOCKED_KEY):
            pipe.set(self.BLOCKED_KEY, 0)
        if not self.redis_client.exists(self.MANUAL_REVIEW_KEY):
            pipe.set(self.MANUAL_REVIEW_KEY, 0)
        if not self.redis_client.exists(self.LAST_RESET_KEY):
            pipe.set(self.LAST_RESET_KEY, datetime.utcnow().isoformat())
        pipe.execute()
    
    def increment_transaction(self, action: str, confidence: float) -> None:
        """
        Record a transaction decision.
        
        Args:
            action: Decision action ('approved', 'blocked', 'manual_review')
            confidence: Confidence score (0-100)
        """
        if self.redis_client:
            try:
                pipe = self.redis_client.pipeline()
                pipe.incr(self.TOTAL_KEY)
                
                # Map action to key
                action_key_map = {
                    "approve": self.APPROVED_KEY,
                    "approved": self.APPROVED_KEY,
                    "block": self.BLOCKED_KEY,
                    "blocked": self.BLOCKED_KEY,
                    "manual_review": self.MANUAL_REVIEW_KEY,
                }
                action_key = action_key_map.get(action.lower())
                if action_key:
                    pipe.incr(action_key)
                
                # Store confidence with timestamp as score for time-based queries
                timestamp = datetime.utcnow().timestamp()
                pipe.zadd(self.CONFIDENCES_KEY, {f"{timestamp}:{confidence}": timestamp})
                
                # Keep only last 10000 confidence scores
                pipe.zremrangebyrank(self.CONFIDENCES_KEY, 0, -10001)
                
                pipe.execute()
                return
            except Exception as e:
                logger.error(f"Redis error in increment_transaction: {e}")
        
        # Fallback to in-memory
        self._in_memory_metrics["total"] += 1
        action_map = {
            "approve": "approved",
            "approved": "approved",
            "block": "blocked",
            "blocked": "blocked",
            "manual_review": "manual_review",
        }
        action_normalized = action_map.get(action.lower(), action.lower())
        if action_normalized in self._in_memory_metrics:
            self._in_memory_metrics[action_normalized] += 1
        self._in_memory_metrics["confidences"].append(confidence)
        # Keep only last 10000
        if len(self._in_memory_metrics["confidences"]) > 10000:
            self._in_memory_metrics["confidences"] = self._in_memory_metrics["confidences"][-10000:]
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics with calculated rates.
        
        Returns:
            Dict with all metrics and calculated rates.
        """
        if self.redis_client:
            try:
                pipe = self.redis_client.pipeline()
                pipe.get(self.TOTAL_KEY)
                pipe.get(self.APPROVED_KEY)
                pipe.get(self.BLOCKED_KEY)
                pipe.get(self.MANUAL_REVIEW_KEY)
                pipe.zrange(self.CONFIDENCES_KEY, 0, -1)
                pipe.get(self.LAST_RESET_KEY)
                
                results = pipe.execute()
                
                total = int(results[0] or 0)
                approved = int(results[1] or 0)
                blocked = int(results[2] or 0)
                manual_review = int(results[3] or 0)
                confidence_entries = results[4] or []
                last_reset = results[5] or datetime.utcnow().isoformat()
                
                # Parse confidence values
                confidences = []
                for entry in confidence_entries:
                    try:
                        _, conf = entry.split(":")
                        confidences.append(float(conf))
                    except (ValueError, AttributeError):
                        pass
                
                return self._calculate_metrics(
                    total, approved, blocked, manual_review, confidences, last_reset
                )
            except Exception as e:
                logger.error(f"Redis error in get_metrics: {e}")
        
        # Fallback to in-memory
        return self._calculate_metrics(
            self._in_memory_metrics["total"],
            self._in_memory_metrics["approved"],
            self._in_memory_metrics["blocked"],
            self._in_memory_metrics["manual_review"],
            self._in_memory_metrics["confidences"],
            self._in_memory_metrics["last_reset"]
        )
    
    def _calculate_metrics(
        self,
        total: int,
        approved: int,
        blocked: int,
        manual_review: int,
        confidences: list,
        last_reset: str
    ) -> Dict[str, Any]:
        """Calculate rates and statistics from raw counts."""
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # Calculate percentiles if we have enough data
        percentiles = {}
        if len(confidences) >= 10:
            sorted_conf = sorted(confidences)
            percentiles = {
                "p50": sorted_conf[len(sorted_conf) // 2],
                "p90": sorted_conf[int(len(sorted_conf) * 0.9)],
                "p99": sorted_conf[int(len(sorted_conf) * 0.99)] if len(sorted_conf) >= 100 else None
            }
        
        return {
            "total_transactions": total,
            "approved": approved,
            "blocked": blocked,
            "manual_review": manual_review,
            "approval_rate": round((approved / total * 100) if total > 0 else 0, 2),
            "block_rate": round((blocked / total * 100) if total > 0 else 0, 2),
            "manual_review_rate": round((manual_review / total * 100) if total > 0 else 0, 2),
            "avg_confidence": round(avg_confidence, 2),
            "confidence_percentiles": percentiles,
            "sample_count": len(confidences),
            "last_reset": last_reset,
            "storage": "redis" if self.redis_client else "in_memory"
        }
    
    def reset_metrics(self) -> Dict[str, Any]:
        """
        Reset all metrics counters.
        
        Returns:
            Dict with reset confirmation and timestamp.
        """
        reset_time = datetime.utcnow().isoformat()
        
        if self.redis_client:
            try:
                pipe = self.redis_client.pipeline()
                pipe.set(self.TOTAL_KEY, 0)
                pipe.set(self.APPROVED_KEY, 0)
                pipe.set(self.BLOCKED_KEY, 0)
                pipe.set(self.MANUAL_REVIEW_KEY, 0)
                pipe.delete(self.CONFIDENCES_KEY)
                pipe.set(self.LAST_RESET_KEY, reset_time)
                pipe.execute()
                
                return {"status": "reset", "timestamp": reset_time, "storage": "redis"}
            except Exception as e:
                logger.error(f"Redis error in reset_metrics: {e}")
        
        # Fallback to in-memory
        self._in_memory_metrics = {
            "total": 0,
            "approved": 0,
            "blocked": 0,
            "manual_review": 0,
            "confidences": [],
            "last_reset": reset_time
        }
        return {"status": "reset", "timestamp": reset_time, "storage": "in_memory"}
    
    def health_check(self) -> Dict[str, Any]:
        """Check service health and Redis connectivity."""
        if self.redis_client:
            try:
                self.redis_client.ping()
                return {
                    "status": "healthy",
                    "redis_connected": True,
                    "redis_url": self.redis_url.split("@")[-1] if "@" in self.redis_url else self.redis_url
                }
            except Exception as e:
                return {
                    "status": "degraded",
                    "redis_connected": False,
                    "error": str(e),
                    "fallback": "in_memory"
                }
        
        return {
            "status": "healthy",
            "redis_connected": False,
            "fallback": "in_memory"
        }


# Singleton instance
_metrics_service_instance = None


def get_metrics_service() -> ComplianceMetricsService:
    """Get or create singleton metrics service instance."""
    global _metrics_service_instance
    if _metrics_service_instance is None:
        _metrics_service_instance = ComplianceMetricsService()
    return _metrics_service_instance
