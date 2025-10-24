#!/usr/bin/env python3
"""Professional Logging System for IaL Infrastructure"""

import logging
import json
import boto3
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

class IaLLogger:
    """Enterprise-grade logging for Infrastructure as Language"""
    
    def __init__(self, name: str, log_group: str = "ial-infrastructure"):
        self.logger = logging.getLogger(name)
        self.log_group = log_group
        self.session_id = self._generate_session_id()
        self.setup_logging()
    
    def setup_logging(self):
        """Configure structured logging with CloudWatch integration"""
        
        # Clear existing handlers
        self.logger.handlers.clear()
        self.logger.setLevel(logging.INFO)
        
        # Console handler with structured format
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler for local debugging
        log_dir = Path("/tmp/ial-logs")
        log_dir.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_dir / f"ial-{datetime.now().strftime('%Y%m%d')}.log")
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(session_id)s | %(message)s',
            defaults={'session_id': self.session_id}
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # CloudWatch handler (if available)
        try:
            self.cloudwatch = boto3.client('logs')
            self._ensure_log_group()
        except Exception:
            self.cloudwatch = None
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID for tracking"""
        return f"ial-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{os.getpid()}"
    
    def _ensure_log_group(self):
        """Ensure CloudWatch log group exists"""
        try:
            self.cloudwatch.create_log_group(logGroupName=self.log_group)
        except self.cloudwatch.exceptions.ResourceAlreadyExistsException:
            pass
        except Exception as e:
            self.logger.warning(f"Could not create CloudWatch log group: {e}")
    
    def _log_to_cloudwatch(self, level: str, message: str, extra: Dict[str, Any]):
        """Send structured log to CloudWatch"""
        if not self.cloudwatch:
            return
        
        try:
            log_event = {
                'timestamp': int(datetime.now(timezone.utc).timestamp() * 1000),
                'message': json.dumps({
                    'level': level,
                    'message': message,
                    'session_id': self.session_id,
                    'logger': self.logger.name,
                    **extra
                })
            }
            
            # Create log stream if needed
            stream_name = f"ial-{datetime.now().strftime('%Y/%m/%d')}"
            try:
                self.cloudwatch.create_log_stream(
                    logGroupName=self.log_group,
                    logStreamName=stream_name
                )
            except self.cloudwatch.exceptions.ResourceAlreadyExistsException:
                pass
            
            # Send log event
            self.cloudwatch.put_log_events(
                logGroupName=self.log_group,
                logStreamName=stream_name,
                logEvents=[log_event]
            )
        except Exception as e:
            # Don't fail the main operation if logging fails
            self.logger.warning(f"CloudWatch logging failed: {e}")
    
    def info(self, message: str, **kwargs):
        """Log info message with structured data"""
        self.logger.info(message, extra=kwargs)
        self._log_to_cloudwatch('INFO', message, kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with structured data"""
        self.logger.warning(message, extra=kwargs)
        self._log_to_cloudwatch('WARNING', message, kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with structured data"""
        self.logger.error(message, extra=kwargs)
        self._log_to_cloudwatch('ERROR', message, kwargs)
    
    def deployment_started(self, phase: str, resources_expected: int, **kwargs):
        """Log deployment start with context"""
        self.info(
            f"Deployment started: {phase}",
            phase=phase,
            resources_expected=resources_expected,
            event_type="deployment_started",
            **kwargs
        )
    
    def deployment_completed(self, phase: str, resources_created: int, duration: float, **kwargs):
        """Log deployment completion with metrics"""
        self.info(
            f"Deployment completed: {phase}",
            phase=phase,
            resources_created=resources_created,
            duration_seconds=duration,
            event_type="deployment_completed",
            **kwargs
        )
    
    def deployment_failed(self, phase: str, error: str, **kwargs):
        """Log deployment failure with error context"""
        self.error(
            f"Deployment failed: {phase}",
            phase=phase,
            error=error,
            event_type="deployment_failed",
            **kwargs
        )
    
    def resource_created(self, resource_name: str, resource_type: str, phase: str, **kwargs):
        """Log resource creation"""
        self.info(
            f"Resource created: {resource_name}",
            resource_name=resource_name,
            resource_type=resource_type,
            phase=phase,
            event_type="resource_created",
            **kwargs
        )
    
    def validation_result(self, status: str, completion_rate: float, expected: int, created: int, **kwargs):
        """Log validation results"""
        self.info(
            f"Validation completed: {status}",
            status=status,
            completion_rate=completion_rate,
            expected_resources=expected,
            created_resources=created,
            event_type="validation_completed",
            **kwargs
        )

# Global logger instance
def get_logger(name: str) -> IaLLogger:
    """Get or create logger instance"""
    return IaLLogger(name)
