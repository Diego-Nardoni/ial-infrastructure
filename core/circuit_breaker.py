#!/usr/bin/env python3
"""
Circuit Breaker Pattern Implementation
"""

import time
import threading
from enum import Enum
from typing import Dict, Optional

class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60, name: str = "circuit"):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.name = name
        
        # State management
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self.lock = threading.Lock()
        
        # Metrics
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        
    def can_execute(self) -> bool:
        """Check if circuit allows execution"""
        with self.lock:
            if self.state == CircuitState.CLOSED:
                return True
            elif self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    return True
                return False
            elif self.state == CircuitState.HALF_OPEN:
                return True
                
    def record_success(self):
        """Record successful execution"""
        with self.lock:
            self.total_requests += 1
            self.successful_requests += 1
            
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                
    def record_failure(self):
        """Record failed execution"""
        with self.lock:
            self.total_requests += 1
            self.failed_requests += 1
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        return (time.time() - self.last_failure_time) >= self.timeout
        
    def get_metrics(self) -> Dict:
        """Get circuit breaker metrics"""
        with self.lock:
            success_rate = (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0
            return {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self.failure_count,
                "total_requests": self.total_requests,
                "success_rate": round(success_rate, 2),
                "last_failure_time": self.last_failure_time
            }
