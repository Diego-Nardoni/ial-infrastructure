#!/usr/bin/env python3
"""
IaL Knowledge Base Engine
RAG system for infrastructure documentation and best practices
"""

import boto3
import json
import os
from typing import Dict, List, Optional
from datetime import datetime

class KnowledgeBaseEngine:
    def __init__(self, region='us-east-1'):
        self.bedrock = boto3.client('bedrock-runtime', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.dynamodb = boto3.client('dynamodb', region_name=region)
        
        # Knowledge base configuration
        self.knowledge_base = {
            'aws_best_practices': {
                'security': [
                    "Enable encryption at rest and in transit for all data",
                    "Use IAM roles instead of access keys where possible",
                    "Implement least privilege access principles",
                    "Enable AWS CloudTrail for audit logging",
                    "Use AWS KMS for key management",
                    "Enable MFA for privileged accounts"
                ],
                'networking': [
                    "Use VPC for network isolation",
                    "Implement security groups as virtual firewalls",
                    "Use private subnets for backend resources",
                    "Enable VPC Flow Logs for monitoring",
                    "Use NAT Gateway for outbound internet access",
                    "Implement network ACLs for additional security"
                ],
                'compute': [
                    "Use Auto Scaling for high availability",
                    "Implement health checks for load balancers",
                    "Use container orchestration for microservices",
                    "Enable detailed monitoring",
                    "Implement blue-green deployments",
                    "Use spot instances for cost optimization"
                ],
                'data': [
                    "Enable automated backups",
                    "Use read replicas for read scaling",
                    "Implement data encryption",
                    "Use DynamoDB for NoSQL workloads",
                    "Enable point-in-time recovery",
                    "Implement data lifecycle policies"
                ]
            },
            'troubleshooting': {
                'deployment_failures': [
                    "Check CloudFormation events for error details",
                    "Verify IAM permissions for resources",
                    "Check resource limits and quotas",
                    "Validate template syntax",
                    "Review dependency order",
                    "Check for naming conflicts"
                ],
                'performance_issues': [
                    "Monitor CloudWatch metrics",
                    "Check resource utilization",
                    "Review application logs",
                    "Analyze network latency",
                    "Check database performance",
                    "Review auto-scaling policies"
                ]
            },
            'cost_optimization': [
                "Use Reserved Instances for predictable workloads",
                "Implement auto-scaling to match demand",
                "Use S3 lifecycle policies for data archiving",
                "Monitor and optimize data transfer costs",
                "Use CloudWatch to identify unused resources",
                "Implement cost allocation tags"
            ]
        }

    def search_knowledge_base(self, query: str, category: str = None) -> List[Dict]:
        """Search knowledge base for relevant information"""
        
        query_lower = query.lower()
        results = []
        
        # Search in best practices
        if not category or category == 'best_practices':
            for domain, practices in self.knowledge_base['aws_best_practices'].items():
                for practice in practices:
                    if any(word in practice.lower() for word in query_lower.split()):
                        results.append({
                            'type': 'best_practice',
                            'domain': domain,
                            'content': practice,
                            'relevance_score': self.calculate_relevance(query_lower, practice.lower())
                        })
        
        # Search in troubleshooting
        if not category or category == 'troubleshooting':
            for issue_type, solutions in self.knowledge_base['troubleshooting'].items():
                for solution in solutions:
                    if any(word in solution.lower() for word in query_lower.split()):
                        results.append({
                            'type': 'troubleshooting',
                            'issue_type': issue_type,
                            'content': solution,
                            'relevance_score': self.calculate_relevance(query_lower, solution.lower())
                        })
        
        # Search in cost optimization
        if not category or category == 'cost_optimization':
            for tip in self.knowledge_base['cost_optimization']:
                if any(word in tip.lower() for word in query_lower.split()):
                    results.append({
                        'type': 'cost_optimization',
                        'content': tip,
                        'relevance_score': self.calculate_relevance(query_lower, tip.lower())
                    })
        
        # Sort by relevance score
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return results[:5]  # Return top 5 results

    def calculate_relevance(self, query: str, content: str) -> float:
        """Calculate relevance score between query and content"""
        
        query_words = set(query.split())
        content_words = set(content.split())
        
        # Calculate Jaccard similarity
        intersection = query_words.intersection(content_words)
        union = query_words.union(content_words)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)

    def generate_rag_response(self, user_query: str, conversation_context: str = '') -> Dict:
        """Generate response using RAG (Retrieval Augmented Generation)"""
        
        # Search knowledge base
        relevant_docs = self.search_knowledge_base(user_query)
        
        if not relevant_docs:
            return {
                'response': "I don't have specific documentation for that query, but I can help with general infrastructure questions.",
                'sources': [],
                'rag_used': False
            }
        
        # Prepare context for Bedrock
        context_parts = []
        sources = []
        
        for doc in relevant_docs:
            context_parts.append(f"- {doc['content']}")
            sources.append({
                'type': doc['type'],
                'content': doc['content'][:100] + '...' if len(doc['content']) > 100 else doc['content'],
                'relevance': doc['relevance_score']
            })
        
        knowledge_context = "\n".join(context_parts)
        
        # Create prompt for Bedrock
        system_prompt = f"""You are an AWS infrastructure expert. Use the following knowledge base information to answer the user's question accurately and helpfully.

Knowledge Base Information:
{knowledge_context}

Instructions:
- Use the provided knowledge base information to answer the question
- If the knowledge base doesn't contain relevant information, say so
- Provide practical, actionable advice
- Reference AWS best practices when applicable
- Be concise but comprehensive
"""
        
        messages = [
            {"role": "user", "content": f"Context: {conversation_context}\n\nQuestion: {user_query}"}
        ]
        
        try:
            # Use Bedrock for response generation
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "system": system_prompt,
                "messages": messages,
                "temperature": 0.3
            }
            
            response = self.bedrock.invoke_model(
                modelId='anthropic.claude-3-haiku-20240307-v1:0',  # Use Haiku for cost efficiency
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            generated_response = response_body['content'][0]['text']
            
            return {
                'response': generated_response,
                'sources': sources,
                'rag_used': True,
                'knowledge_base_hits': len(relevant_docs)
            }
            
        except Exception as e:
            return {
                'response': f"I found relevant information but had trouble generating a response: {str(e)}",
                'sources': sources,
                'rag_used': False,
                'error': str(e)
            }

    def add_to_knowledge_base(self, content: str, category: str, subcategory: str = None):
        """Add new content to knowledge base"""
        
        try:
            # Store in DynamoDB for persistence
            item = {
                'knowledge_id': {'S': f"{category}#{subcategory}#{datetime.now().isoformat()}"},
                'category': {'S': category},
                'subcategory': {'S': subcategory or 'general'},
                'content': {'S': content},
                'created_at': {'S': datetime.now().isoformat()},
                'ttl': {'N': str(int(datetime.now().timestamp()) + 86400 * 365)}  # 1 year TTL
            }
            
            self.dynamodb.put_item(
                TableName='ial-knowledge-base',
                Item=item
            )
            
            return {'success': True, 'message': 'Content added to knowledge base'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_documentation_summary(self, domain: str) -> Dict:
        """Get documentation summary for a domain"""
        
        domain_docs = {
            'security': {
                'overview': 'Security domain implements encryption, access control, and compliance',
                'key_components': ['KMS encryption', 'IAM roles', 'Secrets Manager', 'WAF protection'],
                'best_practices': self.knowledge_base['aws_best_practices']['security'][:3],
                'common_issues': ['Permission denied errors', 'Key rotation failures', 'WAF rule conflicts']
            },
            'networking': {
                'overview': 'Networking domain provides VPC, subnets, and connectivity',
                'key_components': ['VPC', 'Subnets', 'Security Groups', 'Flow Logs'],
                'best_practices': self.knowledge_base['aws_best_practices']['networking'][:3],
                'common_issues': ['Connectivity issues', 'Security group misconfigurations', 'Routing problems']
            },
            'compute': {
                'overview': 'Compute domain manages containers, scaling, and load balancing',
                'key_components': ['ECS clusters', 'Auto Scaling', 'Application Load Balancer', 'ECR'],
                'best_practices': self.knowledge_base['aws_best_practices']['compute'][:3],
                'common_issues': ['Service startup failures', 'Scaling issues', 'Health check failures']
            },
            'data': {
                'overview': 'Data domain handles databases, storage, and data management',
                'key_components': ['RDS Aurora', 'DynamoDB', 'Redis', 'S3 storage'],
                'best_practices': self.knowledge_base['aws_best_practices']['data'][:3],
                'common_issues': ['Connection timeouts', 'Backup failures', 'Performance degradation']
            }
        }
        
        return domain_docs.get(domain, {
            'overview': f'{domain} domain documentation not available',
            'key_components': [],
            'best_practices': [],
            'common_issues': []
        })

    def get_troubleshooting_guide(self, issue_description: str) -> Dict:
        """Get troubleshooting guide for specific issues"""
        
        issue_lower = issue_description.lower()
        
        # Categorize the issue
        if any(word in issue_lower for word in ['deploy', 'create', 'stack', 'template']):
            category = 'deployment_failures'
        elif any(word in issue_lower for word in ['slow', 'performance', 'latency', 'timeout']):
            category = 'performance_issues'
        else:
            category = 'general'
        
        if category in self.knowledge_base['troubleshooting']:
            solutions = self.knowledge_base['troubleshooting'][category]
            
            return {
                'issue_category': category,
                'solutions': solutions,
                'additional_resources': [
                    'Check AWS CloudTrail logs for API calls',
                    'Review CloudWatch metrics and alarms',
                    'Consult AWS documentation for specific services'
                ]
            }
        
        return {
            'issue_category': 'unknown',
            'solutions': [
                'Check AWS service health dashboard',
                'Review CloudFormation events',
                'Check IAM permissions',
                'Consult AWS support if issue persists'
            ],
            'additional_resources': []
        }

# Example usage
if __name__ == "__main__":
    kb = KnowledgeBaseEngine()
    
    # Test knowledge base search
    results = kb.search_knowledge_base("security encryption")
    print("Search results:", json.dumps(results, indent=2))
    
    # Test RAG response
    rag_response = kb.generate_rag_response("How do I secure my database?")
    print("RAG response:", json.dumps(rag_response, indent=2))
    
    # Test documentation summary
    docs = kb.get_documentation_summary("security")
    print("Documentation:", json.dumps(docs, indent=2))
