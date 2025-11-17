#!/usr/bin/env python3
"""
Migration script para otimizações DynamoDB
Migra dados da estrutura antiga para nova estrutura otimizada
"""

import boto3
import json
import time
from datetime import datetime
from typing import Dict, List

class DynamoDBOptimizationMigrator:
    def __init__(self, project_name: str = "ial-fork"):
        self.project_name = project_name
        self.dynamodb = boto3.resource('dynamodb')
        self.cloudformation = boto3.client('cloudformation')
        
        # Old tables
        self.old_history_table = f'{project_name}-conversation-history'
        self.old_sessions_table = f'{project_name}-user-sessions'
        
        # New tables
        self.new_history_table = f'{project_name}-conversation-history-v2'
        self.new_embeddings_table = f'{project_name}-conversation-embeddings'
    
    def deploy_optimized_tables(self) -> bool:
        """Deploy new optimized table structure"""
        
        print("🚀 Deploying optimized DynamoDB tables...")
        
        try:
            # Deploy CloudFormation template
            with open('/home/ial/phases/00-foundation/07-conversation-memory-optimized.yaml', 'r') as f:
                template_body = f.read()
            
            stack_name = f'{self.project_name}-conversation-memory-optimized'
            
            try:
                self.cloudformation.create_stack(
                    StackName=stack_name,
                    TemplateBody=template_body,
                    Parameters=[
                        {
                            'ParameterKey': 'ProjectName',
                            'ParameterValue': self.project_name
                        }
                    ],
                    Capabilities=['CAPABILITY_IAM']
                )
                
                print(f"✅ Stack {stack_name} creation initiated")
                
                # Wait for stack creation
                waiter = self.cloudformation.get_waiter('stack_create_complete')
                print("⏳ Waiting for stack creation to complete...")
                waiter.wait(StackName=stack_name, WaiterConfig={'Delay': 30, 'MaxAttempts': 20})
                
                print("✅ Optimized tables deployed successfully")
                return True
                
            except self.cloudformation.exceptions.AlreadyExistsException:
                print("ℹ️ Stack already exists, updating...")
                
                self.cloudformation.update_stack(
                    StackName=stack_name,
                    TemplateBody=template_body,
                    Parameters=[
                        {
                            'ParameterKey': 'ProjectName',
                            'ParameterValue': self.project_name
                        }
                    ],
                    Capabilities=['CAPABILITY_IAM']
                )
                
                waiter = self.cloudformation.get_waiter('stack_update_complete')
                waiter.wait(StackName=stack_name, WaiterConfig={'Delay': 30, 'MaxAttempts': 20})
                
                print("✅ Optimized tables updated successfully")
                return True
                
        except Exception as e:
            print(f"❌ Error deploying optimized tables: {e}")
            return False
    
    def migrate_conversation_data(self, batch_size: int = 25) -> Dict:
        """Migrate conversation data to optimized structure"""
        
        print("📦 Migrating conversation data...")
        
        try:
            old_table = self.dynamodb.Table(self.old_history_table)
            new_table = self.dynamodb.Table(self.new_history_table)
        except Exception as e:
            print(f"❌ Error accessing tables: {e}")
            return {'success': False, 'error': str(e)}
        
        migration_stats = {
            'total_items': 0,
            'migrated_items': 0,
            'failed_items': 0,
            'batches_processed': 0
        }
        
        try:
            # Scan old table
            scan_kwargs = {'ProjectionExpression': 'user_id, sort_key, #ts, content, #role, tokens, session_id',
                          'ExpressionAttributeNames': {'#ts': 'timestamp', '#role': 'role'}}
            
            while True:
                response = old_table.scan(**scan_kwargs)
                items = response.get('Items', [])
                
                if not items:
                    break
                
                migration_stats['total_items'] += len(items)
                
                # Process in batches
                for i in range(0, len(items), batch_size):
                    batch = items[i:i + batch_size]
                    
                    with new_table.batch_writer() as batch_writer:
                        for item in batch:
                            try:
                                # Transform to new structure
                                transformed_item = self._transform_conversation_item(item)
                                if transformed_item:
                                    batch_writer.put_item(Item=transformed_item)
                                    migration_stats['migrated_items'] += 1
                                else:
                                    migration_stats['failed_items'] += 1
                            except Exception as e:
                                print(f"⚠️ Error migrating item: {e}")
                                migration_stats['failed_items'] += 1
                    
                    migration_stats['batches_processed'] += 1
                    print(f"📦 Processed batch {migration_stats['batches_processed']}: {migration_stats['migrated_items']}/{migration_stats['total_items']} items")
                
                # Handle pagination
                if 'LastEvaluatedKey' not in response:
                    break
                scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
        
        except Exception as e:
            print(f"❌ Error during migration: {e}")
            migration_stats['error'] = str(e)
        
        print(f"✅ Migration completed: {migration_stats['migrated_items']}/{migration_stats['total_items']} items migrated")
        return migration_stats
    
    def _transform_conversation_item(self, old_item: Dict) -> Dict:
        """Transform old item structure to new optimized structure"""
        
        try:
            user_id = old_item.get('user_id')
            timestamp = int(old_item.get('timestamp', time.time()))
            role = old_item.get('role', 'user')
            content = old_item.get('content', '')
            
            # Extract date from timestamp
            date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
            user_date = f"{user_id}#{date_str}"
            
            # Create new item structure
            new_item = {
                'user_date': user_date,
                'timestamp_type': f"{timestamp}#{role}",
                'user_id': user_id,
                'timestamp': timestamp,
                'role': role,
                'content_summary': content[:200] + "..." if len(content) > 200 else content,
                'content_full': content,
                'tokens': old_item.get('tokens', len(content.split())),
                'session_id': old_item.get('session_id', 'unknown'),
                'ttl': timestamp + (30 * 24 * 3600),  # 30 days TTL
                'migrated': True,
                'migration_timestamp': int(time.time())
            }
            
            return new_item
            
        except Exception as e:
            print(f"⚠️ Error transforming item: {e}")
            return None
    
    def validate_migration(self) -> Dict:
        """Validate migration results"""
        
        print("🔍 Validating migration...")
        
        validation_results = {
            'old_table_count': 0,
            'new_table_count': 0,
            'sample_queries_ok': False,
            'gsi_queries_ok': False
        }
        
        try:
            # Count items in old table
            old_table = self.dynamodb.Table(self.old_history_table)
            old_response = old_table.scan(Select='COUNT')
            validation_results['old_table_count'] = old_response['Count']
            
            # Count items in new table
            new_table = self.dynamodb.Table(self.new_history_table)
            new_response = new_table.scan(Select='COUNT')
            validation_results['new_table_count'] = new_response['Count']
            
            # Test sample queries
            if validation_results['new_table_count'] > 0:
                # Test primary key query
                sample_response = new_table.scan(Limit=1)
                if sample_response.get('Items'):
                    sample_item = sample_response['Items'][0]
                    user_date = sample_item['user_date']
                    
                    query_response = new_table.query(
                        KeyConditionExpression='user_date = :ud',
                        ExpressionAttributeValues={':ud': user_date},
                        Limit=1
                    )
                    validation_results['sample_queries_ok'] = len(query_response.get('Items', [])) > 0
                
                # Test GSI queries
                try:
                    gsi_response = new_table.query(
                        IndexName='UserTimeIndex',
                        KeyConditionExpression='user_id = :uid',
                        ExpressionAttributeValues={':uid': sample_item['user_id']},
                        Limit=1
                    )
                    validation_results['gsi_queries_ok'] = len(gsi_response.get('Items', [])) > 0
                except Exception as e:
                    print(f"⚠️ GSI query test failed: {e}")
            
        except Exception as e:
            print(f"❌ Validation error: {e}")
            validation_results['error'] = str(e)
        
        print(f"📊 Validation results: {validation_results}")
        return validation_results
    
    def run_full_migration(self) -> bool:
        """Run complete migration process"""
        
        print("🚀 Starting DynamoDB optimization migration...")
        
        # Step 1: Deploy optimized tables
        if not self.deploy_optimized_tables():
            print("❌ Failed to deploy optimized tables")
            return False
        
        # Step 2: Migrate data
        migration_result = self.migrate_conversation_data()
        if not migration_result.get('migrated_items', 0) > 0:
            print("❌ No data migrated")
            return False
        
        # Step 3: Validate migration
        validation_result = self.validate_migration()
        if not validation_result.get('sample_queries_ok', False):
            print("❌ Migration validation failed")
            return False
        
        print("✅ DynamoDB optimization migration completed successfully!")
        print(f"📊 Migrated {migration_result['migrated_items']} items")
        print(f"🔍 Validation: {validation_result['new_table_count']} items in new table")
        
        return True

if __name__ == "__main__":
    migrator = DynamoDBOptimizationMigrator()
    success = migrator.run_full_migration()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("💡 Next steps:")
        print("1. Update application to use OptimizedContextEngine")
        print("2. Monitor performance improvements")
        print("3. Consider removing old tables after validation period")
    else:
        print("\n❌ Migration failed. Check logs for details.")
