#!/usr/bin/env python3
"""Professional Backup Manager for IaL Infrastructure"""

import boto3
import json
import os
import sys
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

# Import professional logging
sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import get_logger
from utils.observability import put_custom_metric

logger = get_logger(__name__)

class IaLBackupManager:
    """Professional backup management for IaL infrastructure"""
    
    def __init__(self):
        self.dynamodb = boto3.client('dynamodb')
        self.s3 = boto3.client('s3')
        self.lambda_client = boto3.client('lambda')
        self.cloudformation = boto3.client('cloudformation')
        
        # Get resource names from CloudFormation
        self.table_name = 'mcp-provisioning-checklist'
        self.backup_bucket = self._get_backup_bucket_name()
        self.backup_lambda = self._get_backup_lambda_arn()
    
    def _get_backup_bucket_name(self) -> Optional[str]:
        """Get backup bucket name from CloudFormation"""
        try:
            response = self.cloudformation.describe_stacks(
                StackName='ial-00d-backup-strategy'
            )
            
            for output in response['Stacks'][0]['Outputs']:
                if output['OutputKey'] == 'BackupBucketName':
                    return output['OutputValue']
            
            return None
        except Exception as e:
            logger.warning(f"Could not get backup bucket name: {e}")
            return None
    
    def _get_backup_lambda_arn(self) -> Optional[str]:
        """Get backup test Lambda ARN from CloudFormation"""
        try:
            response = self.cloudformation.describe_stacks(
                StackName='ial-00d-backup-strategy'
            )
            
            for output in response['Stacks'][0]['Outputs']:
                if output['OutputKey'] == 'BackupTestLambdaArn':
                    return output['OutputValue']
            
            return None
        except Exception as e:
            logger.warning(f"Could not get backup Lambda ARN: {e}")
            return None
    
    def check_pitr_status(self) -> Dict[str, Any]:
        """Check Point-in-Time Recovery status"""
        try:
            response = self.dynamodb.describe_continuous_backups(
                TableName=self.table_name
            )
            
            pitr_desc = response['ContinuousBackupsDescription']['PointInTimeRecoveryDescription']
            
            result = {
                'table_name': self.table_name,
                'pitr_enabled': pitr_desc['PointInTimeRecoveryStatus'] == 'ENABLED',
                'earliest_restorable_time': pitr_desc.get('EarliestRestorableDateTime'),
                'latest_restorable_time': pitr_desc.get('LatestRestorableDateTime'),
                'status': pitr_desc['PointInTimeRecoveryStatus']
            }
            
            logger.info(f"PITR status checked for {self.table_name}", 
                       pitr_enabled=result['pitr_enabled'],
                       status=result['status'])
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to check PITR status: {e}")
            return {'error': str(e)}
    
    def create_on_demand_backup(self, backup_name: str = None) -> Dict[str, Any]:
        """Create on-demand backup of DynamoDB table"""
        try:
            if not backup_name:
                backup_name = f"ial-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            response = self.dynamodb.create_backup(
                TableName=self.table_name,
                BackupName=backup_name
            )
            
            result = {
                'backup_arn': response['BackupDetails']['BackupArn'],
                'backup_name': response['BackupDetails']['BackupName'],
                'backup_status': response['BackupDetails']['BackupStatus'],
                'creation_time': response['BackupDetails']['BackupCreationDateTime'].isoformat(),
                'table_name': self.table_name
            }
            
            logger.info(f"On-demand backup created: {backup_name}",
                       backup_arn=result['backup_arn'],
                       backup_status=result['backup_status'])
            
            # Send metric
            put_custom_metric("BackupCreated", 1, "Count", 
                             namespace="IaL/Backup",
                             dimensions={"Project": "ial", "BackupType": "OnDemand"})
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to create on-demand backup: {e}")
            put_custom_metric("BackupFailed", 1, "Count",
                             namespace="IaL/Backup",
                             dimensions={"Project": "ial", "BackupType": "OnDemand"})
            return {'error': str(e)}
    
    def list_backups(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List available backups"""
        try:
            response = self.dynamodb.list_backups(
                TableName=self.table_name,
                Limit=limit
            )
            
            backups = []
            for backup in response['BackupSummaries']:
                backups.append({
                    'backup_arn': backup['BackupArn'],
                    'backup_name': backup['BackupName'],
                    'backup_status': backup['BackupStatus'],
                    'backup_type': backup['BackupType'],
                    'creation_time': backup['BackupCreationDateTime'].isoformat(),
                    'size_bytes': backup.get('BackupSizeBytes', 0)
                })
            
            logger.info(f"Listed {len(backups)} backups for {self.table_name}")
            return backups
            
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            return []
    
    def backup_configuration_files(self) -> Dict[str, Any]:
        """Backup configuration files to S3"""
        if not self.backup_bucket:
            return {'error': 'Backup bucket not configured'}
        
        try:
            backup_timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            backup_prefix = f"config-backup-{backup_timestamp}"
            
            # Files to backup
            config_files = [
                'phases/*.yaml',
                'scripts/*.py',
                'utils/*.py',
                'orchestration/*.yaml',
                '.github/workflows/*.yml'
            ]
            
            uploaded_files = []
            
            # Get project root
            project_root = Path(__file__).parent.parent
            
            for pattern in config_files:
                files = list(project_root.glob(pattern))
                
                for file_path in files:
                    if file_path.is_file():
                        # Create S3 key
                        relative_path = file_path.relative_to(project_root)
                        s3_key = f"{backup_prefix}/{relative_path}"
                        
                        # Upload file
                        with open(file_path, 'rb') as f:
                            self.s3.put_object(
                                Bucket=self.backup_bucket,
                                Key=s3_key,
                                Body=f.read(),
                                ContentType='text/plain',
                                Metadata={
                                    'backup_timestamp': backup_timestamp,
                                    'original_path': str(relative_path),
                                    'project': 'ial'
                                }
                            )
                        
                        uploaded_files.append({
                            'local_path': str(file_path),
                            's3_key': s3_key,
                            'size': file_path.stat().st_size
                        })
            
            result = {
                'backup_timestamp': backup_timestamp,
                'backup_prefix': backup_prefix,
                'bucket': self.backup_bucket,
                'files_uploaded': len(uploaded_files),
                'total_size': sum(f['size'] for f in uploaded_files),
                'files': uploaded_files
            }
            
            logger.info(f"Configuration backup completed: {len(uploaded_files)} files",
                       backup_prefix=backup_prefix,
                       total_size=result['total_size'])
            
            # Send metric
            put_custom_metric("ConfigurationBackupCompleted", 1, "Count",
                             namespace="IaL/Backup",
                             dimensions={"Project": "ial", "BackupType": "Configuration"})
            
            put_custom_metric("ConfigurationFilesBackedUp", len(uploaded_files), "Count",
                             namespace="IaL/Backup",
                             dimensions={"Project": "ial"})
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to backup configuration files: {e}")
            put_custom_metric("ConfigurationBackupFailed", 1, "Count",
                             namespace="IaL/Backup",
                             dimensions={"Project": "ial"})
            return {'error': str(e)}
    
    def test_recovery_capability(self) -> Dict[str, Any]:
        """Test recovery capabilities"""
        try:
            # Test 1: Check PITR status
            pitr_status = self.check_pitr_status()
            
            # Test 2: Verify backup bucket access
            bucket_test = self._test_backup_bucket_access()
            
            # Test 3: Simulate recovery time estimation
            recovery_estimate = self._estimate_recovery_time()
            
            result = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'tests': {
                    'pitr_status': pitr_status,
                    'backup_bucket_access': bucket_test,
                    'recovery_time_estimate': recovery_estimate
                },
                'overall_status': 'PASSED' if all([
                    pitr_status.get('pitr_enabled', False),
                    bucket_test.get('accessible', False),
                    recovery_estimate.get('estimated_time_minutes', 999) < 30
                ]) else 'FAILED'
            }
            
            logger.info(f"Recovery capability test completed",
                       overall_status=result['overall_status'])
            
            # Send metrics
            status_value = 1 if result['overall_status'] == 'PASSED' else 0
            put_custom_metric("RecoveryTestPassed", status_value, "Count",
                             namespace="IaL/Backup",
                             dimensions={"Project": "ial"})
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to test recovery capability: {e}")
            return {'error': str(e)}
    
    def _test_backup_bucket_access(self) -> Dict[str, Any]:
        """Test backup bucket accessibility"""
        if not self.backup_bucket:
            return {'accessible': False, 'error': 'Backup bucket not configured'}
        
        try:
            # Test write access
            test_key = f"access-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
            test_content = "IaL backup access test"
            
            self.s3.put_object(
                Bucket=self.backup_bucket,
                Key=test_key,
                Body=test_content
            )
            
            # Test read access
            response = self.s3.get_object(
                Bucket=self.backup_bucket,
                Key=test_key
            )
            
            # Cleanup
            self.s3.delete_object(
                Bucket=self.backup_bucket,
                Key=test_key
            )
            
            return {
                'accessible': True,
                'bucket': self.backup_bucket,
                'test_key': test_key,
                'test_successful': True
            }
            
        except Exception as e:
            return {
                'accessible': False,
                'bucket': self.backup_bucket,
                'error': str(e)
            }
    
    def _estimate_recovery_time(self) -> Dict[str, Any]:
        """Estimate recovery time based on data size"""
        try:
            # Get table size
            response = self.dynamodb.describe_table(TableName=self.table_name)
            table_size_bytes = response['Table']['TableSizeBytes']
            item_count = response['Table']['ItemCount']
            
            # Estimate recovery time (rough calculation)
            # PITR recovery typically takes 5-10 minutes for small tables
            base_time = 5  # minutes
            size_factor = max(1, table_size_bytes / (1024 * 1024 * 100))  # 100MB chunks
            estimated_time = base_time + (size_factor * 2)
            
            return {
                'table_size_bytes': table_size_bytes,
                'item_count': item_count,
                'estimated_time_minutes': min(estimated_time, 30),  # Cap at 30 minutes
                'recovery_method': 'Point-in-Time Recovery'
            }
            
        except Exception as e:
            return {
                'estimated_time_minutes': 15,  # Default estimate
                'error': str(e)
            }
    
    def run_backup_test(self) -> Dict[str, Any]:
        """Run comprehensive backup test"""
        if not self.backup_lambda:
            logger.warning("Backup test Lambda not configured, running local tests")
            return self.test_recovery_capability()
        
        try:
            # Invoke backup test Lambda
            response = self.lambda_client.invoke(
                FunctionName=self.backup_lambda,
                InvocationType='RequestResponse',
                Payload=json.dumps({
                    'source': 'manual',
                    'test_type': 'comprehensive'
                })
            )
            
            # Parse response
            payload = json.loads(response['Payload'].read())
            
            if response['StatusCode'] == 200:
                result = json.loads(payload['body'])
                logger.info("Backup test completed successfully via Lambda")
                return result
            else:
                logger.error(f"Backup test Lambda failed: {payload}")
                return {'error': 'Lambda execution failed', 'details': payload}
                
        except Exception as e:
            logger.error(f"Failed to run backup test via Lambda: {e}")
            # Fallback to local test
            return self.test_recovery_capability()

def main():
    """Main backup manager CLI"""
    
    parser = argparse.ArgumentParser(description='IaL Backup Manager')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Check backup status')
    
    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Create backups')
    backup_parser.add_argument('--type', choices=['dynamodb', 'config', 'all'], 
                              default='all', help='Backup type')
    backup_parser.add_argument('--name', help='Backup name (for DynamoDB)')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List backups')
    list_parser.add_argument('--limit', type=int, default=10, help='Number of backups to list')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test backup and recovery')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    backup_manager = IaLBackupManager()
    
    try:
        if args.command == 'status':
            print("📊 Backup Status:")
            pitr_status = backup_manager.check_pitr_status()
            
            if 'error' in pitr_status:
                print(f"❌ Error checking PITR: {pitr_status['error']}")
            else:
                status_icon = "✅" if pitr_status['pitr_enabled'] else "❌"
                print(f"{status_icon} Point-in-Time Recovery: {pitr_status['status']}")
                if pitr_status['pitr_enabled']:
                    print(f"   Earliest restore: {pitr_status['earliest_restorable_time']}")
                    print(f"   Latest restore: {pitr_status['latest_restorable_time']}")
        
        elif args.command == 'backup':
            if args.type in ['dynamodb', 'all']:
                print("💾 Creating DynamoDB backup...")
                result = backup_manager.create_on_demand_backup(args.name)
                if 'error' in result:
                    print(f"❌ DynamoDB backup failed: {result['error']}")
                else:
                    print(f"✅ DynamoDB backup created: {result['backup_name']}")
            
            if args.type in ['config', 'all']:
                print("📁 Backing up configuration files...")
                result = backup_manager.backup_configuration_files()
                if 'error' in result:
                    print(f"❌ Configuration backup failed: {result['error']}")
                else:
                    print(f"✅ Configuration backup completed: {result['files_uploaded']} files")
        
        elif args.command == 'list':
            print("📋 Available Backups:")
            backups = backup_manager.list_backups(args.limit)
            
            if not backups:
                print("No backups found")
            else:
                for backup in backups:
                    print(f"  • {backup['backup_name']} ({backup['backup_type']})")
                    print(f"    Status: {backup['backup_status']}")
                    print(f"    Created: {backup['creation_time']}")
                    print(f"    Size: {backup['size_bytes']} bytes")
                    print()
        
        elif args.command == 'test':
            print("🧪 Testing backup and recovery capabilities...")
            result = backup_manager.run_backup_test()
            
            if 'error' in result:
                print(f"❌ Test failed: {result['error']}")
            else:
                status_icon = "✅" if result.get('overall_status') == 'PASSED' else "❌"
                print(f"{status_icon} Overall Status: {result.get('overall_status', 'UNKNOWN')}")
                
                if 'tests' in result:
                    for test_name, test_result in result['tests'].items():
                        print(f"  • {test_name}: {test_result}")
    
    except Exception as e:
        logger.error(f"Backup manager operation failed: {e}")
        print(f"❌ Operation failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
