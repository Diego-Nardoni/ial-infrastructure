#!/usr/bin/env python3
"""
Thread-Safe Resource Catalog - DynamoDB State Management
Fixed version with proper thread safety and memory management
"""

import boto3
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from botocore.config import Config
from botocore.exceptions import ClientError, BotoCoreError
import hashlib
from pathlib import Path
from collections import OrderedDict

class ThreadSafeResourceCatalog:
    def __init__(self, table_name: str = "ial-state", region: str = "us-east-1"):
        self.table_name = table_name
        self.region = region
        
        # Thread-safe configuration
        config = Config(
            retries={'max_attempts': 3, 'mode': 'adaptive'},
            max_pool_connections=50,
            region_name=region
        )
        
        self.dynamodb = boto3.client('dynamodb', config=config)
        self.dynamodb_resource = boto3.resource('dynamodb', config=config)
        
        # Thread-safe cache with TTL and size limits
        self._cache = OrderedDict()
        self._cache_ttl = 300  # 5 minutes
        self._cache_max_size = 1000  # Prevent memory leaks
        self._cache_lock = threading.RLock()  # Reentrant lock
        
        # Rate limiting for DynamoDB
        self._rate_limiter = threading.Semaphore(10)  # Max 10 concurrent operations
        self._last_request_time = {}
        self._min_request_interval = 0.1  # 100ms between requests
        
        # Initialize table
        self._ensure_table_exists()
    
    def _get_cache_key(self, resource_id: str, operation: str = "get") -> str:
        """Generate cache key"""
        return f"{operation}:{resource_id}"
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Check if cache entry is still valid"""
        return time.time() - cache_entry["timestamp"] < self._cache_ttl
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Thread-safe cache retrieval"""
        with self._cache_lock:
            if cache_key in self._cache:
                entry = self._cache[cache_key]
                if self._is_cache_valid(entry):
                    # Move to end (LRU)
                    self._cache.move_to_end(cache_key)
                    return entry["data"]
                else:
                    # Remove expired entry
                    del self._cache[cache_key]
            return None
    
    def _set_cache(self, cache_key: str, data: Any) -> None:
        """Thread-safe cache storage with size management"""
        with self._cache_lock:
            # Remove oldest entries if cache is full
            while len(self._cache) >= self._cache_max_size:
                self._cache.popitem(last=False)
            
            self._cache[cache_key] = {
                "data": data,
                "timestamp": time.time()
            }
    
    def _rate_limit(self, operation: str) -> None:
        """Rate limiting for DynamoDB operations"""
        with self._rate_limiter:
            current_time = time.time()
            last_time = self._last_request_time.get(operation, 0)
            
            if current_time - last_time < self._min_request_interval:
                time.sleep(self._min_request_interval - (current_time - last_time))
            
            self._last_request_time[operation] = time.time()
    
    def _ensure_table_exists(self):
        """Ensure DynamoDB table exists with proper error handling"""
        try:
            self.dynamodb.describe_table(TableName=self.table_name)
            print(f"✅ Table {self.table_name} found")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print(f"⚠️ Table {self.table_name} not found, creating...")
                self._create_table()
            else:
                raise
    
    def _create_table(self):
        """Create optimized DynamoDB table"""
        try:
            table = self.dynamodb_resource.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {'AttributeName': 'resource_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'resource_id', 'AttributeType': 'S'},
                    {'AttributeName': 'timestamp', 'AttributeType': 'S'},
                    {'AttributeName': 'resource_type', 'AttributeType': 'S'},
                    {'AttributeName': 'status', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'type-timestamp-index',
                        'KeySchema': [
                            {'AttributeName': 'resource_type', 'KeyType': 'HASH'},
                            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            
            # Wait for table to be active
            table.wait_until_exists()
            print(f"✅ Table {self.table_name} created successfully")
            
        except Exception as e:
            print(f"❌ Failed to create table: {e}")
            raise
    
    def register_resource(self, resource_id: str, resource_data: Dict) -> bool:
        """Thread-safe resource registration"""
        try:
            self._rate_limit("write")
            
            timestamp = datetime.utcnow().isoformat()
            
            item = {
                'resource_id': {'S': resource_id},
                'timestamp': {'S': timestamp},
                'resource_type': {'S': resource_data.get('type', 'unknown')},
                'status': {'S': resource_data.get('status', 'active')},
                'metadata': {'S': json.dumps(resource_data)},
                'last_updated': {'S': timestamp}
            }
            
            self.dynamodb.put_item(
                TableName=self.table_name,
                Item=item
            )
            
            # Update cache
            cache_key = self._get_cache_key(resource_id)
            self._set_cache(cache_key, resource_data)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to register resource {resource_id}: {e}")
            return False
    
    def get_resource(self, resource_id: str) -> Optional[Dict]:
        """Thread-safe resource retrieval with caching"""
        cache_key = self._get_cache_key(resource_id)
        
        # Check cache first
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data
        
        try:
            self._rate_limit("read")
            
            response = self.dynamodb.query(
                TableName=self.table_name,
                KeyConditionExpression='resource_id = :rid',
                ExpressionAttributeValues={
                    ':rid': {'S': resource_id}
                },
                ScanIndexForward=False,  # Latest first
                Limit=1
            )
            
            if response['Items']:
                item = response['Items'][0]
                metadata = json.loads(item['metadata']['S'])
                
                # Cache the result
                self._set_cache(cache_key, metadata)
                
                return metadata
            
            return None
            
        except Exception as e:
            print(f"❌ Failed to get resource {resource_id}: {e}")
            return None
    
    def get_all_resources(self) -> Dict[str, Dict]:
        """Thread-safe retrieval of all resources with caching"""
        cache_key = "all_resources"
        
        # Check cache first
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data
        
        try:
            self._rate_limit("scan")
            
            resources = {}
            
            # Use paginated scan for large datasets
            paginator = self.dynamodb.get_paginator('scan')
            
            for page in paginator.paginate(TableName=self.table_name):
                for item in page['Items']:
                    resource_id = item['resource_id']['S']
                    metadata = json.loads(item['metadata']['S'])
                    
                    # Keep only the latest version of each resource
                    if resource_id not in resources:
                        resources[resource_id] = metadata
                    else:
                        # Compare timestamps
                        current_ts = item['timestamp']['S']
                        existing_ts = resources[resource_id].get('timestamp', '')
                        if current_ts > existing_ts:
                            resources[resource_id] = metadata
            
            # Cache the result
            self._set_cache(cache_key, resources)
            
            return resources
            
        except Exception as e:
            print(f"❌ Failed to get all resources: {e}")
            return {}
    
    def cleanup_cache(self) -> None:
        """Manual cache cleanup for memory management"""
        with self._cache_lock:
            current_time = time.time()
            expired_keys = []
            
            for key, entry in self._cache.items():
                if current_time - entry["timestamp"] > self._cache_ttl:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
            
            print(f"🧹 Cleaned up {len(expired_keys)} expired cache entries")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics for monitoring"""
        with self._cache_lock:
            return {
                "cache_size": len(self._cache),
                "max_size": self._cache_max_size,
                "ttl_seconds": self._cache_ttl,
                "hit_ratio": getattr(self, '_cache_hits', 0) / max(getattr(self, '_cache_requests', 1), 1)
            }

# Backward compatibility alias
ResourceCatalog = ThreadSafeResourceCatalog
