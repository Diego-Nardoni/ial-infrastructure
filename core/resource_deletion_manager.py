#!/usr/bin/env python3
"""
Resource Deletion Manager - Exclusão de recursos individuais com cleanup completo
"""

import boto3
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class ResourceInfo:
    resource_id: str
    resource_type: str
    aws_service: str
    arn: Optional[str] = None
    metadata: Dict = None

class ResourceDeletionManager:
    """Gerencia exclusão de recursos individuais AWS com cleanup completo"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.session = boto3.Session(region_name=region)
        
        # AWS Clients
        self.s3 = self.session.client('s3')
        self.lambda_client = self.session.client('lambda')
        self.dynamodb = self.session.client('dynamodb')
        self.rds = self.session.client('rds')
        self.ec2 = self.session.client('ec2')
        self.elbv2 = self.session.client('elbv2')
        self.cf = self.session.client('cloudformation')
        
        # Resource catalog for dependency tracking
        try:
            from graph.dependency_graph import DependencyGraph
            from resource_catalog import ResourceCatalog
            self.dependency_graph = DependencyGraph(region=region)
            self.resource_catalog = ResourceCatalog()
            self.tracking_enabled = True
        except ImportError:
            self.tracking_enabled = False
    
    def delete_resource(self, resource_identifier: str, force: bool = False) -> Dict[str, Any]:
        """Delete individual AWS resource with complete cleanup"""
        
        print(f"🗑️ Iniciando exclusão do recurso: {resource_identifier}")
        
        # 1. Identify resource type and get info
        resource_info = self._identify_resource(resource_identifier)
        if not resource_info:
            return {'success': False, 'error': f'Resource {resource_identifier} not found or not supported'}
        
        print(f"📋 Recurso identificado: {resource_info.resource_type} ({resource_info.aws_service})")
        
        # 2. Check dependencies
        if not force:
            dependency_check = self._check_resource_dependencies(resource_info)
            if not dependency_check['safe']:
                return {
                    'success': False,
                    'error': 'Resource has dependencies',
                    'dependencies': dependency_check['blocking_dependencies'],
                    'suggestion': 'Use force=True to override or delete dependent resources first'
                }
        
        # 3. Execute deletion
        deletion_result = self._execute_resource_deletion(resource_info)
        if not deletion_result['success']:
            return deletion_result
        
        # 4. Cleanup dependencies and tracking
        cleanup_result = self._cleanup_resource_dependencies(resource_info)
        
        print(f"✅ Recurso {resource_identifier} deletado com sucesso")
        
        return {
            'success': True,
            'resource': resource_info.resource_id,
            'type': resource_info.resource_type,
            'cleanup_performed': cleanup_result['cleanup_count'],
            'dependencies_removed': cleanup_result['dependencies_removed']
        }
    
    def _identify_resource(self, identifier: str) -> Optional[ResourceInfo]:
        """Identify AWS resource type and get information"""
        
        # S3 Bucket
        if self._is_s3_bucket(identifier):
            try:
                self.s3.head_bucket(Bucket=identifier)
                return ResourceInfo(
                    resource_id=identifier,
                    resource_type='S3::Bucket',
                    aws_service='s3',
                    arn=f'arn:aws:s3:::{identifier}'
                )
            except:
                pass
        
        # Lambda Function
        if self._is_lambda_function(identifier):
            try:
                response = self.lambda_client.get_function(FunctionName=identifier)
                return ResourceInfo(
                    resource_id=identifier,
                    resource_type='Lambda::Function',
                    aws_service='lambda',
                    arn=response['Configuration']['FunctionArn']
                )
            except:
                pass
        
        # DynamoDB Table
        if self._is_dynamodb_table(identifier):
            try:
                response = self.dynamodb.describe_table(TableName=identifier)
                return ResourceInfo(
                    resource_id=identifier,
                    resource_type='DynamoDB::Table',
                    aws_service='dynamodb',
                    arn=response['Table']['TableArn']
                )
            except:
                pass
        
        # RDS Instance
        if self._is_rds_instance(identifier):
            try:
                response = self.rds.describe_db_instances(DBInstanceIdentifier=identifier)
                db = response['DBInstances'][0]
                return ResourceInfo(
                    resource_id=identifier,
                    resource_type='RDS::DBInstance',
                    aws_service='rds',
                    arn=db['DBInstanceArn']
                )
            except:
                pass
        
        return None
    
    def _execute_resource_deletion(self, resource_info: ResourceInfo) -> Dict[str, Any]:
        """Execute actual AWS resource deletion"""
        
        try:
            if resource_info.resource_type == 'S3::Bucket':
                return self._delete_s3_bucket(resource_info)
            elif resource_info.resource_type == 'Lambda::Function':
                return self._delete_lambda_function(resource_info)
            elif resource_info.resource_type == 'DynamoDB::Table':
                return self._delete_dynamodb_table(resource_info)
            elif resource_info.resource_type == 'RDS::DBInstance':
                return self._delete_rds_instance(resource_info)
            else:
                return {'success': False, 'error': f'Deletion not implemented for {resource_info.resource_type}'}
                
        except Exception as e:
            return {'success': False, 'error': f'Deletion failed: {str(e)}'}
    
    def _delete_s3_bucket(self, resource_info: ResourceInfo) -> Dict[str, Any]:
        """Delete S3 bucket with all objects"""
        bucket_name = resource_info.resource_id
        
        # Empty bucket first
        try:
            paginator = self.s3.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=bucket_name):
                if 'Contents' in page:
                    objects = [{'Key': obj['Key']} for obj in page['Contents']]
                    self.s3.delete_objects(Bucket=bucket_name, Delete={'Objects': objects})
        except Exception as e:
            print(f"⚠️ Error emptying bucket: {e}")
        
        # Delete bucket
        self.s3.delete_bucket(Bucket=bucket_name)
        return {'success': True, 'action': 'bucket_deleted'}
    
    def _delete_lambda_function(self, resource_info: ResourceInfo) -> Dict[str, Any]:
        """Delete Lambda function"""
        self.lambda_client.delete_function(FunctionName=resource_info.resource_id)
        return {'success': True, 'action': 'function_deleted'}
    
    def _delete_dynamodb_table(self, resource_info: ResourceInfo) -> Dict[str, Any]:
        """Delete DynamoDB table"""
        self.dynamodb.delete_table(TableName=resource_info.resource_id)
        
        # Wait for deletion
        waiter = self.dynamodb.get_waiter('table_not_exists')
        waiter.wait(TableName=resource_info.resource_id)
        
        return {'success': True, 'action': 'table_deleted'}
    
    def _delete_rds_instance(self, resource_info: ResourceInfo) -> Dict[str, Any]:
        """Delete RDS instance"""
        self.rds.delete_db_instance(
            DBInstanceIdentifier=resource_info.resource_id,
            SkipFinalSnapshot=True,
            DeleteAutomatedBackups=True
        )
        return {'success': True, 'action': 'db_instance_deleted'}
    
    def _check_resource_dependencies(self, resource_info: ResourceInfo) -> Dict[str, Any]:
        """Check if resource has dependencies"""
        if not self.tracking_enabled:
            return {'safe': True, 'blocking_dependencies': []}
        
        blocking_deps = []
        
        if resource_info.resource_id in self.dependency_graph.nodes:
            dependents = self.dependency_graph.nodes[resource_info.resource_id].dependents
            blocking_deps.extend(dependents)
        
        return {
            'safe': len(blocking_deps) == 0,
            'blocking_dependencies': blocking_deps
        }
    
    def _cleanup_resource_dependencies(self, resource_info: ResourceInfo) -> Dict[str, Any]:
        """Cleanup all dependencies and tracking for deleted resource"""
        cleanup_count = 0
        dependencies_removed = []
        
        if not self.tracking_enabled:
            return {'cleanup_count': 0, 'dependencies_removed': []}
        
        try:
            # Remove from dependency graph
            if resource_info.resource_id in self.dependency_graph.nodes:
                result = self.dependency_graph.remove_resource(resource_info.resource_id)
                if result['success']:
                    dependencies_removed = result['impacted_resources']
                    cleanup_count += 1
            
            # Remove from resource catalog
            try:
                self.resource_catalog.remove_resource(resource_info.resource_id)
                cleanup_count += 1
            except Exception as e:
                print(f"⚠️ Error removing from catalog: {e}")
            
            # Remove DynamoDB tracking entries
            cleanup_count += self._cleanup_dynamodb_tracking(resource_info)
            
        except Exception as e:
            print(f"⚠️ Error during cleanup: {e}")
        
        return {
            'cleanup_count': cleanup_count,
            'dependencies_removed': dependencies_removed
        }
    
    def _cleanup_dynamodb_tracking(self, resource_info: ResourceInfo) -> int:
        """Remove all DynamoDB tracking entries for resource"""
        cleanup_count = 0
        
        try:
            # Remove from ial-resource-catalog table
            table_name = 'ial-resource-catalog'
            
            # Remove main resource entry
            try:
                self.dynamodb.delete_item(
                    TableName=table_name,
                    Key={
                        'PK': {'S': f'RESOURCE#{resource_info.resource_id}'},
                        'SK': {'S': 'META'}
                    }
                )
                cleanup_count += 1
            except:
                pass
            
            # Remove dependency entries
            try:
                # Query all dependencies
                response = self.dynamodb.query(
                    TableName=table_name,
                    KeyConditionExpression='PK = :pk',
                    ExpressionAttributeValues={
                        ':pk': {'S': f'RESOURCE#{resource_info.resource_id}'}
                    }
                )
                
                for item in response.get('Items', []):
                    if item['SK']['S'].startswith('DEPENDS_ON#'):
                        self.dynamodb.delete_item(
                            TableName=table_name,
                            Key={
                                'PK': item['PK'],
                                'SK': item['SK']
                            }
                        )
                        cleanup_count += 1
            except Exception as e:
                print(f"⚠️ Error cleaning dependencies: {e}")
                
        except Exception as e:
            print(f"⚠️ Error accessing DynamoDB: {e}")
        
        return cleanup_count
    
    # Resource type detection helpers
    def _is_s3_bucket(self, identifier: str) -> bool:
        return bool(re.match(r'^[a-z0-9][a-z0-9\-]*[a-z0-9]$', identifier) and len(identifier) >= 3)
    
    def _is_lambda_function(self, identifier: str) -> bool:
        return bool(re.match(r'^[a-zA-Z0-9\-_]+$', identifier))
    
    def _is_dynamodb_table(self, identifier: str) -> bool:
        return bool(re.match(r'^[a-zA-Z0-9\-_.]+$', identifier))
    
    def _is_rds_instance(self, identifier: str) -> bool:
        return bool(re.match(r'^[a-zA-Z][a-zA-Z0-9\-]*$', identifier))
