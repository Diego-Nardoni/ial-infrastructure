#!/usr/bin/env python3
"""
IAL Validation System - Comprehensive validation of deployed resources
"""

import boto3
import json
import time
from typing import Dict, List, Any

class IALValidationSystem:
    def __init__(self, project_name: str = "ial-fork"):
        self.project_name = project_name
        self.session = boto3.Session()
        
    def validate_complete_deployment(self) -> Dict[str, Any]:
        """Validate complete IAL deployment"""
        print("🔍 Iniciando validação completa da infraestrutura IAL...")
        
        results = {
            'validation_timestamp': time.time(),
            'project_name': self.project_name,
            'overall_status': 'unknown',
            'validations': {},
            'summary': {}
        }
        
        # Validate CloudFormation stacks
        cf_validation = self.validate_cloudformation_stacks()
        results['validations']['cloudformation'] = cf_validation
        
        # Validate DynamoDB tables
        dynamo_validation = self.validate_dynamodb_tables()
        results['validations']['dynamodb'] = dynamo_validation
        
        # Validate S3 buckets
        s3_validation = self.validate_s3_buckets()
        results['validations']['s3'] = s3_validation
        
        # Validate Lambda functions
        lambda_validation = self.validate_lambda_functions()
        results['validations']['lambda'] = lambda_validation
        
        # Validate Step Functions
        sfn_validation = self.validate_step_functions()
        results['validations']['stepfunctions'] = sfn_validation
        
        # Calculate overall status
        results['overall_status'] = self.calculate_overall_status(results['validations'])
        results['summary'] = self.generate_summary(results['validations'])
        
        return results
    
    def validate_cloudformation_stacks(self) -> Dict[str, Any]:
        """Validate CloudFormation stacks"""
        try:
            cf = self.session.client('cloudformation')
            
            # List stacks with project name
            stacks = cf.list_stacks(
                StackStatusFilter=['CREATE_COMPLETE', 'UPDATE_COMPLETE']
            )
            
            project_stacks = [
                stack for stack in stacks['StackSummaries']
                if self.project_name in stack['StackName']
            ]
            
            stack_details = []
            for stack in project_stacks:
                try:
                    detail = cf.describe_stacks(StackName=stack['StackName'])
                    stack_info = detail['Stacks'][0]
                    
                    stack_details.append({
                        'name': stack_info['StackName'],
                        'status': stack_info['StackStatus'],
                        'creation_time': stack_info['CreationTime'].isoformat(),
                        'outputs': len(stack_info.get('Outputs', [])),
                        'resources': self.count_stack_resources(stack['StackName'])
                    })
                except Exception as e:
                    stack_details.append({
                        'name': stack['StackName'],
                        'status': 'ERROR',
                        'error': str(e)
                    })
            
            return {
                'status': 'success',
                'total_stacks': len(project_stacks),
                'stacks': stack_details
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def validate_dynamodb_tables(self) -> Dict[str, Any]:
        """Validate DynamoDB tables"""
        try:
            dynamodb = self.session.client('dynamodb')
            
            # List all tables
            tables = dynamodb.list_tables()
            
            # Filter project tables
            project_tables = [
                table for table in tables['TableNames']
                if self.project_name in table
            ]
            
            table_details = []
            for table_name in project_tables:
                try:
                    table_info = dynamodb.describe_table(TableName=table_name)
                    table = table_info['Table']
                    
                    table_details.append({
                        'name': table['TableName'],
                        'status': table['TableStatus'],
                        'item_count': table.get('ItemCount', 0),
                        'size_bytes': table.get('TableSizeBytes', 0),
                        'billing_mode': table.get('BillingModeSummary', {}).get('BillingMode', 'UNKNOWN')
                    })
                except Exception as e:
                    table_details.append({
                        'name': table_name,
                        'status': 'ERROR',
                        'error': str(e)
                    })
            
            return {
                'status': 'success',
                'total_tables': len(project_tables),
                'tables': table_details
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def validate_s3_buckets(self) -> Dict[str, Any]:
        """Validate S3 buckets"""
        try:
            s3 = self.session.client('s3')
            
            # List all buckets
            buckets = s3.list_buckets()
            
            # Filter project buckets
            project_buckets = [
                bucket for bucket in buckets['Buckets']
                if self.project_name in bucket['Name']
            ]
            
            bucket_details = []
            for bucket in project_buckets:
                try:
                    # Get bucket location
                    location = s3.get_bucket_location(Bucket=bucket['Name'])
                    
                    # Get bucket encryption
                    try:
                        encryption = s3.get_bucket_encryption(Bucket=bucket['Name'])
                        encrypted = True
                    except:
                        encrypted = False
                    
                    bucket_details.append({
                        'name': bucket['Name'],
                        'creation_date': bucket['CreationDate'].isoformat(),
                        'region': location.get('LocationConstraint', 'us-east-1'),
                        'encrypted': encrypted
                    })
                except Exception as e:
                    bucket_details.append({
                        'name': bucket['Name'],
                        'status': 'ERROR',
                        'error': str(e)
                    })
            
            return {
                'status': 'success',
                'total_buckets': len(project_buckets),
                'buckets': bucket_details
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def validate_lambda_functions(self) -> Dict[str, Any]:
        """Validate Lambda functions"""
        try:
            lambda_client = self.session.client('lambda')
            
            # List all functions
            functions = lambda_client.list_functions()
            
            # Filter project functions
            project_functions = [
                func for func in functions['Functions']
                if self.project_name in func['FunctionName']
            ]
            
            function_details = []
            for func in project_functions:
                try:
                    function_details.append({
                        'name': func['FunctionName'],
                        'runtime': func['Runtime'],
                        'state': func['State'],
                        'last_modified': func['LastModified'],
                        'memory_size': func['MemorySize'],
                        'timeout': func['Timeout']
                    })
                except Exception as e:
                    function_details.append({
                        'name': func['FunctionName'],
                        'status': 'ERROR',
                        'error': str(e)
                    })
            
            return {
                'status': 'success',
                'total_functions': len(project_functions),
                'functions': function_details
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def validate_step_functions(self) -> Dict[str, Any]:
        """Validate Step Functions"""
        try:
            sfn = self.session.client('stepfunctions')
            
            # List state machines
            state_machines = sfn.list_state_machines()
            
            # Filter project state machines
            project_sfn = [
                sm for sm in state_machines['stateMachines']
                if self.project_name in sm['name']
            ]
            
            sfn_details = []
            for sm in project_sfn:
                try:
                    sfn_details.append({
                        'name': sm['name'],
                        'status': sm['status'],
                        'type': sm['type'],
                        'creation_date': sm['creationDate'].isoformat()
                    })
                except Exception as e:
                    sfn_details.append({
                        'name': sm['name'],
                        'status': 'ERROR',
                        'error': str(e)
                    })
            
            return {
                'status': 'success',
                'total_state_machines': len(project_sfn),
                'state_machines': sfn_details
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def count_stack_resources(self, stack_name: str) -> int:
        """Count resources in a CloudFormation stack"""
        try:
            cf = self.session.client('cloudformation')
            resources = cf.list_stack_resources(StackName=stack_name)
            return len(resources['StackResourceSummaries'])
        except:
            return 0
    
    def calculate_overall_status(self, validations: Dict) -> str:
        """Calculate overall validation status"""
        error_count = sum(1 for v in validations.values() if v.get('status') == 'error')
        
        if error_count == 0:
            return 'healthy'
        elif error_count < len(validations) / 2:
            return 'warning'
        else:
            return 'critical'
    
    def generate_summary(self, validations: Dict) -> Dict[str, Any]:
        """Generate validation summary"""
        summary = {
            'total_resources': 0,
            'healthy_services': 0,
            'error_services': 0,
            'resource_breakdown': {}
        }
        
        for service, validation in validations.items():
            if validation.get('status') == 'success':
                summary['healthy_services'] += 1
            else:
                summary['error_services'] += 1
            
            # Count resources by type
            if service == 'cloudformation':
                count = validation.get('total_stacks', 0)
            elif service == 'dynamodb':
                count = validation.get('total_tables', 0)
            elif service == 's3':
                count = validation.get('total_buckets', 0)
            elif service == 'lambda':
                count = validation.get('total_functions', 0)
            elif service == 'stepfunctions':
                count = validation.get('total_state_machines', 0)
            else:
                count = 0
            
            summary['resource_breakdown'][service] = count
            summary['total_resources'] += count
        
        return summary
    
    def print_validation_report(self, results: Dict[str, Any]):
        """Print formatted validation report"""
        print("\n" + "="*60)
        print("🔍 IAL INFRASTRUCTURE VALIDATION REPORT")
        print("="*60)
        
        print(f"📋 Project: {results['project_name']}")
        print(f"⏰ Validation Time: {time.ctime(results['validation_timestamp'])}")
        print(f"🎯 Overall Status: {results['overall_status'].upper()}")
        
        print(f"\n📊 SUMMARY:")
        summary = results['summary']
        print(f"   Total Resources: {summary['total_resources']}")
        print(f"   Healthy Services: {summary['healthy_services']}")
        print(f"   Error Services: {summary['error_services']}")
        
        print(f"\n📈 RESOURCE BREAKDOWN:")
        for service, count in summary['resource_breakdown'].items():
            status = "✅" if results['validations'][service].get('status') == 'success' else "❌"
            print(f"   {status} {service.title()}: {count}")
        
        # Show detailed errors if any
        for service, validation in results['validations'].items():
            if validation.get('status') == 'error':
                print(f"\n❌ {service.upper()} ERROR:")
                print(f"   {validation.get('error', 'Unknown error')}")
        
        print("\n" + "="*60)
