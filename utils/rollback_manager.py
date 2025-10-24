#!/usr/bin/env python3
"""Professional Rollback Management System for IaL Infrastructure"""

import boto3
import json
import subprocess
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path
from .logger import get_logger

class RollbackManager:
    """Enterprise-grade rollback management with state restoration"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.dynamodb = boto3.client('dynamodb')
        self.table_name = 'ial-rollback-checkpoints'
        self.state_table = 'mcp-provisioning-checklist'
        self._ensure_rollback_table()
    
    def _ensure_rollback_table(self):
        """Ensure rollback checkpoints table exists"""
        try:
            self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {'AttributeName': 'checkpoint_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'checkpoint_id', 'AttributeType': 'S'},
                    {'AttributeName': 'timestamp', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            self.logger.info("Created rollback checkpoints table")
        except self.dynamodb.exceptions.ResourceInUseException:
            pass
        except Exception as e:
            self.logger.error(f"Failed to create rollback table: {e}")
    
    def create_checkpoint(self, description: str = None) -> str:
        """Create rollback checkpoint with current state"""
        checkpoint_id = f"checkpoint-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        timestamp = datetime.now(timezone.utc).isoformat()
        
        try:
            # Capture current git state
            git_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
            git_branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).decode().strip()
            
            # Capture current infrastructure state
            infrastructure_state = self._capture_infrastructure_state()
            
            # Store checkpoint
            checkpoint_data = {
                'checkpoint_id': {'S': checkpoint_id},
                'timestamp': {'S': timestamp},
                'description': {'S': description or f"Auto-checkpoint {timestamp}"},
                'git_commit': {'S': git_commit},
                'git_branch': {'S': git_branch},
                'infrastructure_state': {'S': json.dumps(infrastructure_state)},
                'created_by': {'S': 'ial-system'},
                'status': {'S': 'active'}
            }
            
            self.dynamodb.put_item(
                TableName=self.table_name,
                Item=checkpoint_data
            )
            
            self.logger.info(
                f"Checkpoint created: {checkpoint_id}",
                checkpoint_id=checkpoint_id,
                git_commit=git_commit,
                resources_count=len(infrastructure_state),
                event_type="checkpoint_created"
            )
            
            return checkpoint_id
            
        except Exception as e:
            self.logger.error(f"Failed to create checkpoint: {e}")
            raise
    
    def _capture_infrastructure_state(self) -> List[Dict]:
        """Capture current infrastructure state from DynamoDB"""
        try:
            response = self.dynamodb.scan(
                TableName=self.state_table,
                FilterExpression='#proj = :project',
                ExpressionAttributeNames={'#proj': 'Project'},
                ExpressionAttributeValues={':project': {'S': 'ial'}}
            )
            
            return [
                {
                    'resource_name': item.get('ResourceName', {}).get('S', ''),
                    'resource_type': item.get('ResourceType', {}).get('S', ''),
                    'phase': item.get('Phase', {}).get('S', ''),
                    'status': item.get('Status', {}).get('S', ''),
                    'timestamp': item.get('Timestamp', {}).get('S', '')
                }
                for item in response.get('Items', [])
            ]
        except Exception as e:
            self.logger.error(f"Failed to capture infrastructure state: {e}")
            return []
    
    def list_checkpoints(self, limit: int = 10) -> List[Dict]:
        """List available rollback checkpoints"""
        try:
            response = self.dynamodb.scan(
                TableName=self.table_name,
                FilterExpression='#status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': {'S': 'active'}},
                Limit=limit
            )
            
            checkpoints = []
            for item in response.get('Items', []):
                checkpoints.append({
                    'checkpoint_id': item.get('checkpoint_id', {}).get('S', ''),
                    'timestamp': item.get('timestamp', {}).get('S', ''),
                    'description': item.get('description', {}).get('S', ''),
                    'git_commit': item.get('git_commit', {}).get('S', ''),
                    'git_branch': item.get('git_branch', {}).get('S', '')
                })
            
            # Sort by timestamp (newest first)
            checkpoints.sort(key=lambda x: x['timestamp'], reverse=True)
            return checkpoints
            
        except Exception as e:
            self.logger.error(f"Failed to list checkpoints: {e}")
            return []
    
    def rollback_to_checkpoint(self, checkpoint_id: str, validate: bool = True) -> bool:
        """Rollback to specific checkpoint with validation"""
        try:
            # Get checkpoint data
            response = self.dynamodb.get_item(
                TableName=self.table_name,
                Key={'checkpoint_id': {'S': checkpoint_id}}
            )
            
            if 'Item' not in response:
                self.logger.error(f"Checkpoint not found: {checkpoint_id}")
                return False
            
            checkpoint = response['Item']
            git_commit = checkpoint.get('git_commit', {}).get('S', '')
            infrastructure_state = json.loads(checkpoint.get('infrastructure_state', {}).get('S', '[]'))
            
            self.logger.info(
                f"Starting rollback to checkpoint: {checkpoint_id}",
                checkpoint_id=checkpoint_id,
                git_commit=git_commit,
                event_type="rollback_started"
            )
            
            # 1. Git rollback
            subprocess.run(['git', 'checkout', git_commit], check=True)
            
            # 2. Infrastructure state rollback
            self._restore_infrastructure_state(infrastructure_state)
            
            # 3. Validation (if requested)
            if validate:
                validation_success = self._validate_rollback(infrastructure_state)
                if not validation_success:
                    self.logger.error("Rollback validation failed")
                    return False
            
            self.logger.info(
                f"Rollback completed successfully: {checkpoint_id}",
                checkpoint_id=checkpoint_id,
                event_type="rollback_completed"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}", checkpoint_id=checkpoint_id)
            return False
    
    def _restore_infrastructure_state(self, target_state: List[Dict]):
        """Restore infrastructure state to match checkpoint"""
        try:
            # Clear current state
            current_items = self.dynamodb.scan(
                TableName=self.state_table,
                FilterExpression='#proj = :project',
                ExpressionAttributeNames={'#proj': 'Project'},
                ExpressionAttributeValues={':project': {'S': 'ial'}}
            )
            
            # Delete current items
            for item in current_items.get('Items', []):
                self.dynamodb.delete_item(
                    TableName=self.state_table,
                    Key={
                        'Project': item['Project'],
                        'ResourceName': item['ResourceName']
                    }
                )
            
            # Restore target state
            for resource in target_state:
                self.dynamodb.put_item(
                    TableName=self.state_table,
                    Item={
                        'Project': {'S': 'ial'},
                        'ResourceName': {'S': resource['resource_name']},
                        'ResourceType': {'S': resource['resource_type']},
                        'Phase': {'S': resource['phase']},
                        'Status': {'S': resource['status']},
                        'Timestamp': {'S': resource['timestamp']},
                        'RestoredFrom': {'S': 'rollback'},
                        'RestoreTimestamp': {'S': datetime.now(timezone.utc).isoformat()}
                    }
                )
            
            self.logger.info(f"Infrastructure state restored: {len(target_state)} resources")
            
        except Exception as e:
            self.logger.error(f"Failed to restore infrastructure state: {e}")
            raise
    
    def _validate_rollback(self, expected_state: List[Dict]) -> bool:
        """Validate that rollback restored correct state"""
        try:
            # Get current state after rollback
            current_state = self._capture_infrastructure_state()
            
            # Compare states
            expected_resources = {r['resource_name']: r for r in expected_state}
            current_resources = {r['resource_name']: r for r in current_state}
            
            missing_resources = set(expected_resources.keys()) - set(current_resources.keys())
            extra_resources = set(current_resources.keys()) - set(expected_resources.keys())
            
            if missing_resources or extra_resources:
                self.logger.error(
                    "Rollback validation failed",
                    missing_resources=list(missing_resources),
                    extra_resources=list(extra_resources)
                )
                return False
            
            self.logger.info("Rollback validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Rollback validation error: {e}")
            return False
    
    def auto_rollback_on_failure(self, phase: str, error: str) -> bool:
        """Automatically rollback on deployment failure"""
        try:
            # Find last successful checkpoint
            checkpoints = self.list_checkpoints(limit=5)
            
            if not checkpoints:
                self.logger.error("No checkpoints available for auto-rollback")
                return False
            
            last_checkpoint = checkpoints[0]
            
            self.logger.warning(
                f"Auto-rollback triggered due to failure in {phase}",
                phase=phase,
                error=error,
                target_checkpoint=last_checkpoint['checkpoint_id'],
                event_type="auto_rollback_triggered"
            )
            
            return self.rollback_to_checkpoint(last_checkpoint['checkpoint_id'])
            
        except Exception as e:
            self.logger.error(f"Auto-rollback failed: {e}")
            return False
    
    def cleanup_old_checkpoints(self, keep_count: int = 10):
        """Clean up old checkpoints to save storage"""
        try:
            checkpoints = self.list_checkpoints(limit=100)
            
            if len(checkpoints) <= keep_count:
                return
            
            # Mark old checkpoints as inactive
            old_checkpoints = checkpoints[keep_count:]
            
            for checkpoint in old_checkpoints:
                self.dynamodb.update_item(
                    TableName=self.table_name,
                    Key={'checkpoint_id': {'S': checkpoint['checkpoint_id']}},
                    UpdateExpression='SET #status = :status',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={':status': {'S': 'inactive'}}
                )
            
            self.logger.info(f"Cleaned up {len(old_checkpoints)} old checkpoints")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup checkpoints: {e}")

# Global rollback manager instance
rollback_manager = RollbackManager()
