#!/usr/bin/env python3
"""
IaL Optimization Engine
Response caching, rate limiting, and performance optimization
"""

import boto3
import json
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class OptimizationEngine:
    def __init__(self, region='us-east-1'):
        self.dynamodb = boto3.client('dynamodb', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        
        # Cache configuration
        self.cache_ttl = {
            'status_queries': 300,      # 5 minutes
            'simple_responses': 3600,   # 1 hour
            'deployment_plans': 1800,   # 30 minutes
            'validation_results': 7200  # 2 hours
        }
        
        # Rate limiting configuration
        self.rate_limits = {
            'per_minute': 30,
            'per_hour': 500,
            'per_day': 2000
        }

    def get_cache_key(self, user_input: str, user_id: str, context: str = '') -> str:
        """Generate cache key for conversation"""
        
        # Normalize input for caching
        normalized_input = user_input.lower().strip()
        
        # Create hash for cache key
        cache_data = f"{normalized_input}:{user_id}:{context}"
        return hashlib.md5(cache_data.encode()).hexdigest()

    def get_cached_response(self, cache_key: str, cache_type: str = 'simple_responses') -> Optional[Dict]:
        """Get cached response if available and not expired"""
        
        try:
            response = self.dynamodb.get_item(
                TableName='ial-conversation-cache',
                Key={'cache_key': {'S': cache_key}}
            )
            
            if 'Item' in response:
                item = response['Item']
                
                # Check TTL
                cached_time = datetime.fromisoformat(item.get('cached_at', {}).get('S', ''))
                ttl_seconds = self.cache_ttl.get(cache_type, 3600)
                
                if datetime.now() - cached_time < timedelta(seconds=ttl_seconds):
                    return {
                        'response': item.get('response', {}).get('S', ''),
                        'metadata': json.loads(item.get('metadata', {}).get('S', '{}')),
                        'cached_at': cached_time.isoformat(),
                        'cache_hit': True
                    }
                else:
                    # Expired cache, delete it
                    self.delete_cached_response(cache_key)
            
            return None
            
        except Exception as e:
            print(f"Error getting cached response: {e}")
            return None

    def cache_response(self, cache_key: str, response: str, metadata: Dict = None, cache_type: str = 'simple_responses'):
        """Cache response for future use"""
        
        try:
            item = {
                'cache_key': {'S': cache_key},
                'response': {'S': response},
                'metadata': {'S': json.dumps(metadata or {})},
                'cache_type': {'S': cache_type},
                'cached_at': {'S': datetime.now().isoformat()},
                'ttl': {'N': str(int(time.time()) + self.cache_ttl.get(cache_type, 3600))}
            }
            
            self.dynamodb.put_item(
                TableName='ial-conversation-cache',
                Item=item
            )
            
        except Exception as e:
            print(f"Error caching response: {e}")

    def delete_cached_response(self, cache_key: str):
        """Delete expired or invalid cached response"""
        
        try:
            self.dynamodb.delete_item(
                TableName='ial-conversation-cache',
                Key={'cache_key': {'S': cache_key}}
            )
        except Exception as e:
            print(f"Error deleting cached response: {e}")

    def check_rate_limit(self, user_id: str) -> Dict:
        """Check if user has exceeded rate limits"""
        
        now = datetime.now()
        
        # Check different time windows
        windows = {
            'minute': (now - timedelta(minutes=1), self.rate_limits['per_minute']),
            'hour': (now - timedelta(hours=1), self.rate_limits['per_hour']),
            'day': (now - timedelta(days=1), self.rate_limits['per_day'])
        }
        
        for window_name, (start_time, limit) in windows.items():
            try:
                # Query recent requests
                response = self.dynamodb.query(
                    TableName='ial-token-usage',
                    KeyConditionExpression='user_id = :user_id AND date_hour >= :start_time',
                    ExpressionAttributeValues={
                        ':user_id': {'S': user_id},
                        ':start_time': {'S': start_time.strftime('%Y-%m-%d-%H')}
                    }
                )
                
                request_count = len(response.get('Items', []))
                
                if request_count >= limit:
                    return {
                        'rate_limited': True,
                        'window': window_name,
                        'limit': limit,
                        'current_count': request_count,
                        'reset_time': self.get_reset_time(window_name)
                    }
                    
            except Exception as e:
                print(f"Error checking rate limit: {e}")
        
        return {'rate_limited': False}

    def get_reset_time(self, window: str) -> str:
        """Get when rate limit resets"""
        
        now = datetime.now()
        
        if window == 'minute':
            reset_time = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
        elif window == 'hour':
            reset_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        else:  # day
            reset_time = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        return reset_time.isoformat()

    def optimize_conversation_context(self, conversation_history: List[Dict], max_tokens: int = 3000) -> List[Dict]:
        """Optimize conversation context to fit within token limits"""
        
        if not conversation_history:
            return []
        
        # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
        total_chars = sum(len(turn.get('user_message', '') + turn.get('assistant_response', '')) 
                         for turn in conversation_history)
        
        if total_chars <= max_tokens * 4:
            return conversation_history
        
        # Keep most recent conversations and summarize older ones
        recent_turns = conversation_history[-5:]  # Keep last 5 turns
        older_turns = conversation_history[:-5]
        
        if older_turns:
            # Create summary of older conversations
            summary = self.summarize_conversation_history(older_turns)
            
            # Add summary as first turn
            optimized_history = [{
                'user_message': '[Previous conversation summary]',
                'assistant_response': summary,
                'timestamp': older_turns[0].get('timestamp', ''),
                'summarized': True
            }]
            
            optimized_history.extend(recent_turns)
            return optimized_history
        
        return recent_turns

    def summarize_conversation_history(self, conversation_turns: List[Dict]) -> str:
        """Create summary of conversation history"""
        
        # Extract key topics and actions
        topics = set()
        actions = set()
        
        for turn in conversation_turns:
            user_msg = turn.get('user_message', '').lower()
            assistant_msg = turn.get('assistant_response', '').lower()
            
            # Extract domains mentioned
            domains = ['security', 'networking', 'compute', 'data', 'application', 'observability', 'ai-ml', 'governance']
            for domain in domains:
                if domain in user_msg or domain in assistant_msg:
                    topics.add(domain)
            
            # Extract actions mentioned
            action_keywords = ['deploy', 'status', 'rollback', 'validate', 'create', 'delete', 'update']
            for action in action_keywords:
                if action in user_msg:
                    actions.add(action)
        
        # Create summary
        summary_parts = []
        
        if topics:
            summary_parts.append(f"Discussed infrastructure domains: {', '.join(sorted(topics))}")
        
        if actions:
            summary_parts.append(f"Performed actions: {', '.join(sorted(actions))}")
        
        summary_parts.append(f"Previous conversation included {len(conversation_turns)} exchanges")
        
        return ". ".join(summary_parts) + "."

    def get_performance_metrics(self, user_id: str = None) -> Dict:
        """Get performance metrics for optimization"""
        
        try:
            # Get cache hit rate
            cache_metrics = self.get_cache_metrics()
            
            # Get response times
            response_metrics = self.get_response_time_metrics()
            
            # Get token usage efficiency
            token_metrics = self.get_token_efficiency_metrics(user_id)
            
            return {
                'cache_performance': cache_metrics,
                'response_performance': response_metrics,
                'token_efficiency': token_metrics,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'error': f"Unable to get performance metrics: {e}"}

    def get_cache_metrics(self) -> Dict:
        """Get cache performance metrics"""
        
        try:
            # Get cache statistics from CloudWatch
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
            
            response = self.cloudwatch.get_metric_statistics(
                Namespace='IaL/Cache',
                MetricName='CacheHitRate',
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average']
            )
            
            datapoints = response.get('Datapoints', [])
            if datapoints:
                avg_hit_rate = sum(dp['Average'] for dp in datapoints) / len(datapoints)
                return {
                    'hit_rate': round(avg_hit_rate, 2),
                    'datapoints': len(datapoints)
                }
            
            return {'hit_rate': 0, 'datapoints': 0}
            
        except Exception as e:
            return {'error': str(e)}

    def get_response_time_metrics(self) -> Dict:
        """Get response time metrics"""
        
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
            
            response = self.cloudwatch.get_metric_statistics(
                Namespace='IaL/Conversations',
                MetricName='ResponseTime',
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average', 'Maximum']
            )
            
            datapoints = response.get('Datapoints', [])
            if datapoints:
                avg_response_time = sum(dp['Average'] for dp in datapoints) / len(datapoints)
                max_response_time = max(dp['Maximum'] for dp in datapoints)
                
                return {
                    'average_response_time': round(avg_response_time, 2),
                    'max_response_time': round(max_response_time, 2),
                    'datapoints': len(datapoints)
                }
            
            return {'average_response_time': 0, 'max_response_time': 0, 'datapoints': 0}
            
        except Exception as e:
            return {'error': str(e)}

    def get_token_efficiency_metrics(self, user_id: str = None) -> Dict:
        """Get token usage efficiency metrics"""
        
        try:
            # Calculate tokens per conversation
            # This would integrate with the cost monitor
            return {
                'avg_tokens_per_conversation': 1500,
                'cost_per_conversation': 0.004,
                'efficiency_score': 85
            }
            
        except Exception as e:
            return {'error': str(e)}

    def publish_performance_metrics(self, metrics: Dict):
        """Publish performance metrics to CloudWatch"""
        
        try:
            metric_data = []
            
            # Cache metrics
            if 'cache_performance' in metrics:
                cache_perf = metrics['cache_performance']
                if 'hit_rate' in cache_perf:
                    metric_data.append({
                        'MetricName': 'CacheHitRate',
                        'Value': cache_perf['hit_rate'],
                        'Unit': 'Percent'
                    })
            
            # Response time metrics
            if 'response_performance' in metrics:
                resp_perf = metrics['response_performance']
                if 'average_response_time' in resp_perf:
                    metric_data.append({
                        'MetricName': 'ResponseTime',
                        'Value': resp_perf['average_response_time'],
                        'Unit': 'Seconds'
                    })
            
            # Token efficiency metrics
            if 'token_efficiency' in metrics:
                token_eff = metrics['token_efficiency']
                if 'efficiency_score' in token_eff:
                    metric_data.append({
                        'MetricName': 'TokenEfficiency',
                        'Value': token_eff['efficiency_score'],
                        'Unit': 'Percent'
                    })
            
            if metric_data:
                self.cloudwatch.put_metric_data(
                    Namespace='IaL/Optimization',
                    MetricData=metric_data
                )
                
        except Exception as e:
            print(f"Error publishing metrics: {e}")

# Example usage
if __name__ == "__main__":
    optimizer = OptimizationEngine()
    
    # Test caching
    cache_key = optimizer.get_cache_key("show me status", "test-user")
    print(f"Cache key: {cache_key}")
    
    # Test rate limiting
    rate_limit = optimizer.check_rate_limit("test-user")
    print(f"Rate limit: {rate_limit}")
    
    # Test performance metrics
    metrics = optimizer.get_performance_metrics()
    print(f"Performance metrics: {json.dumps(metrics, indent=2)}")
