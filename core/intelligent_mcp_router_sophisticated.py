#!/usr/bin/env python3
"""
Intelligent MCP Router Sophisticated - Complete Integration
LLM + MCP Mesh + Circuit Breakers + Async/Await
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from core.llm_provider import LLMProvider
from core.mcp_mesh_loader import MCPMeshLoader
from core.service_detector_enhanced import ServiceDetectorEnhanced
from core.domain_mapper_sophisticated import DomainMapperSophisticated
from core.mcp_orchestrator_upgraded import MCPOrchestratorUpgraded
from core.circuit_breaker import CircuitBreaker

class IntelligentMCPRouterSophisticated:
    def __init__(self):
        # Initialize all components
        self.llm_provider = LLMProvider()
        self.mesh_loader = MCPMeshLoader()
        self.service_detector = ServiceDetectorEnhanced(self.mesh_loader)
        self.domain_mapper = DomainMapperSophisticated(self.mesh_loader)
        self.orchestrator = MCPOrchestratorUpgraded(self.mesh_loader)
        
        # Circuit breaker for overall routing
        self.routing_circuit = CircuitBreaker(
            failure_threshold=10,
            timeout=120,
            name="routing"
        )
        
        print(f"✅ LLM Provider: {self.llm_provider.current_provider}")
        print(f"✅ MCP Domains: {len(self.mesh_loader.get_all_domains())}")
        print(f"✅ Circuit Breakers: Ativo")
        
    async def route_request_async(self, request: str) -> Dict[str, Any]:
        """Main async routing method with circuit breaker"""
        start_time = time.time()
        
        if not self.routing_circuit.can_execute():
            return self._fallback_response("Circuit breaker open", start_time)
            
        try:
            # Step 1: LLM Processing (async)
            llm_start = time.time()
            llm_result = await self.llm_provider.process_natural_language_async(request)
            llm_time = time.time() - llm_start
            
            # Step 2: Service Detection (sync, fast)
            detection_start = time.time()
            processed_text = llm_result.get('processed_text', request)
            detection_result = self.service_detector.detect_services(processed_text)
            detection_time = time.time() - detection_start
            
            # Step 3: Domain Mapping (sync, fast)
            mapping_start = time.time()
            domains = self.domain_mapper.map_to_domains(detection_result['detected_services'])
            required_mcps = self.domain_mapper.get_required_mcps(domains)
            
            # Apply pattern optimizations and store pattern
            pattern = detection_result.get('architecture_pattern')
            self._detected_pattern = pattern  # Store for YAML generation
            if pattern:
                required_mcps = self.domain_mapper.apply_optimizations(pattern, required_mcps)
                
            mapping_time = time.time() - mapping_start
            
            # Step 4: MCP Loading (async, parallel)
            loading_start = time.time()
            loaded_mcps = await self.orchestrator.lazy_load_mcps_async(required_mcps)
            loading_time = time.time() - loading_start
            
            # Step 5: Execution (async, parallel)
            execution_start = time.time()
            execution_results = await self._execute_mcps_async(loaded_mcps, request)
            execution_time = time.time() - execution_start
            
            total_time = time.time() - start_time
            
            self.routing_circuit.record_success()
            
            return {
                'status': 'success',
                'request': request,
                'llm_result': {
                    'provider': llm_result['provider'],
                    'confidence': llm_result['confidence'],
                    'entities': llm_result['entities']
                },
                'detection_result': {
                    'domains': detection_result['detected_domains'],
                    'services': detection_result['detected_services'],
                    'pattern': detection_result['architecture_pattern'],
                    'confidence': detection_result['total_confidence']
                },
                'mapping_result': {
                    'required_mcps': len(required_mcps),
                    'loaded_mcps': list(loaded_mcps.keys()),
                    'load_strategy': self.domain_mapper.get_load_strategy(required_mcps)
                },
                'execution_results': execution_results,
                'gitops_info': {
                    'deployment_method': execution_results.get('deployment_method', 'unknown'),
                    'github_status': execution_results.get('github_status'),
                    'pr_url': execution_results.get('pr_url'),
                    'templates_count': execution_results.get('templates_generated', 0)
                },
                'performance_metrics': {
                    'total_time': round(total_time * 1000, 2),  # ms
                    'llm_time': round(llm_time * 1000, 2),
                    'detection_time': round(detection_time * 1000, 2),
                    'mapping_time': round(mapping_time * 1000, 2),
                    'loading_time': round(loading_time * 1000, 2),
                    'execution_time': round(execution_time * 1000, 2)
                },
                'circuit_breaker_metrics': self._get_circuit_breaker_metrics()
            }
            
        except Exception as e:
            self.routing_circuit.record_failure()
            return self._fallback_response(f"Routing failed: {str(e)}", start_time)
            
    async def _execute_mcps_async(self, loaded_mcps: Dict, request: str) -> Dict:
        """Execute MCPs - direct execution for queries, GitOps for infrastructure creation"""
        if not loaded_mcps:
            return {'status': 'no_mcps_loaded'}
            
        try:
            # Detect if this is a query vs infrastructure creation
            is_query = self._is_query_request(request)
            
            if is_query:
                # For queries, execute MCP tools directly
                return await self._execute_query_mcps(loaded_mcps, request)
            else:
                # For infrastructure creation, use GitOps workflow
                return await self._execute_infrastructure_mcps(loaded_mcps, request)
                
        except Exception as e:
            return {'status': 'execution_failed', 'error': str(e)}
    
    def _is_query_request(self, request: str) -> bool:
        """Detect if request is a query vs infrastructure creation"""
        query_keywords = [
            'quantas', 'quantos', 'quanto', 'qual', 'quais', 'como', 'onde', 'quando',
            'mostrar', 'listar', 'ver', 'status', 'info', 'liste', 'mostre',
            'possuo', 'tenho', 'existe', 'existem', 'há', 'show', 'list', 'describe'
        ]
        return any(keyword in request.lower() for keyword in query_keywords)
    
    async def _execute_query_mcps(self, loaded_mcps: Dict, request: str) -> Dict:
        """Execute MCP tools directly for queries - Enhanced with RAG and recommendations"""
        import subprocess
        
        try:
            # Execute basic AWS CLI query first
            request_lower = request.lower()
            aws_command = None
            service_name = "AWS"
            
            # Smart mapping of common AWS services to CLI commands
            if any(term in request_lower for term in ['ec2', 'instanc', 'servidor', 'vm']):
                aws_command = 'aws ec2 describe-instances --query "Reservations[*].Instances[*].[InstanceId,State.Name,InstanceType]" --output table'
                service_name = "EC2"
            elif any(term in request_lower for term in ['s3', 'bucket', 'liste meus s3', 'listar s3', 'meus s3']):
                aws_command = 'aws s3api list-buckets --query "Buckets[*].[Name,CreationDate]" --output table'
                service_name = "S3"
            elif any(term in request_lower for term in ['lambda', 'função', 'funcao', 'function']):
                aws_command = 'aws lambda list-functions --query "Functions[*].[FunctionName,Runtime,LastModified]" --output table'
                service_name = "Lambda"
            elif any(term in request_lower for term in ['vpc', 'rede', 'network']):
                aws_command = 'aws ec2 describe-vpcs --query "Vpcs[*].[VpcId,State,CidrBlock]" --output table'
                service_name = "VPC"
            elif any(term in request_lower for term in ['rds', 'database', 'banco', 'db']):
                aws_command = 'aws rds describe-db-instances --query "DBInstances[*].[DBInstanceIdentifier,DBInstanceStatus,Engine]" --output table'
                service_name = "RDS"
            elif any(term in request_lower for term in ['iam', 'user', 'usuario', 'usuário']):
                aws_command = 'aws iam list-users --query "Users[*].[UserName,CreateDate]" --output table'
                service_name = "IAM"
            elif any(term in request_lower for term in ['stack', 'cloudformation', 'cfn']):
                aws_command = 'aws cloudformation list-stacks --query "StackSummaries[?StackStatus!=`DELETE_COMPLETE`].[StackName,StackStatus,CreationTime]" --output table'
                service_name = "CloudFormation"
            
            if not aws_command:
                return {
                    'status': 'error',
                    'error': 'Service not supported',
                    'response': f"❌ Serviço não suportado ainda. Tente: EC2, S3, Lambda, VPC, RDS, IAM, CloudFormation"
                }
            
            # Execute AWS CLI command
            cmd = aws_command.split()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            
            if result.returncode != 0:
                return {
                    'status': 'error',
                    'error': f"AWS CLI error: {result.stderr}",
                    'response': f"❌ Erro ao consultar recursos {service_name}: {result.stderr}"
                }
            
            # Basic response with data
            response = f"📊 **Seus recursos {service_name}:**\n\n```\n{result.stdout}\n```"
            
            # Add enhanced features using existing components
            try:
                # Add RAG-based insights using real methods
                from lib.knowledge_base_engine import KnowledgeBaseEngine
                rag_engine = KnowledgeBaseEngine()
                insights = rag_engine.get_troubleshooting_guide(service_name.lower())
                if insights and len(str(insights)) > 10:
                    response += f"\n\n💡 **Guia de Troubleshooting:**\n{str(insights)[:200]}..."
            except Exception as e:
                print(f"RAG error: {e}")
            
            try:
                # Add cost validation using real methods
                from core.intent_cost_guardrails import IntentCostGuardrails
                cost_guardrails = IntentCostGuardrails()
                cost_estimate = cost_guardrails.estimate_intent_cost(f"list {service_name.lower()} resources")
                if cost_estimate:
                    cost_value = cost_estimate if isinstance(cost_estimate, (int, float)) else cost_estimate.get('estimated_cost', 'N/A')
                    response += f"\n\n💰 **Estimativa de Custo:** ${cost_value}"
            except Exception as e:
                print(f"Cost error: {e}")
            
            try:
                # Add memory context using real methods
                from core.memory.memory_manager import MemoryManager
                memory_manager = MemoryManager()
                recent_context = memory_manager.get_recent_context(limit=3)
                if recent_context:
                    response += f"\n\n🧠 **Contexto Recente:** {len(recent_context)} conversas relacionadas"
            except Exception as e:
                print(f"Memory error: {e}")
            
            return {
                'status': 'success',
                'type': 'query',
                'results': {'output': result.stdout},
                'response': response
            }
                
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'response': f"❌ Erro ao executar consulta AWS: {str(e)}"
            }
    
    async def _execute_infrastructure_mcps(self, loaded_mcps: Dict, request: str) -> Dict:
        """Execute GitOps workflow for infrastructure creation"""
        # Generate optimized YAML templates from MCPs
        yaml_templates = self._generate_yaml_from_mcps(loaded_mcps, request)
        
        if not yaml_templates:
            return {'status': 'no_templates_generated'}
        
        try:
            # Use GitHub Integration for GitOps workflow
            from core.github_integration import GitHubIntegration
            github_integration = GitHubIntegration()
                
            # Create intent for GitHub integration
            intent = {
                'request': request,
                'mcps_used': list(loaded_mcps.keys()),
                'architecture_pattern': getattr(self, '_detected_pattern', None),
                'timestamp': time.time(),
                'intent': 'create_infrastructure'  # Default intent for now
            }
            
            # Execute GitOps workflow
            github_result = github_integration.execute_infrastructure_deployment(
                yaml_templates, intent
            )
            
            return {
                'status': 'gitops_triggered',
                'github_status': github_result['status'],
                'github_response': github_result['response'],
                'templates_generated': len(yaml_templates),
                'pr_url': github_result.get('github_url'),
                'deployment_method': 'gitops'
            }
            
        except Exception as e:
            return {
                'status': 'gitops_failed',
                'error': str(e),
                'fallback_available': True
            }
            
    def _generate_yaml_from_mcps(self, loaded_mcps: Dict, request: str) -> Dict[str, str]:
        """Generate optimized YAML templates from loaded MCPs"""
        templates = {}
        
        # Generate phase-based templates
        for mcp_name, mcp_instance in loaded_mcps.items():
            if mcp_instance.get('type') == 'core':
                continue  # Skip core MCPs for user workloads
                
            domain = mcp_instance.get('domain', 'unknown')
            capabilities = mcp_instance.get('capabilities', [])
            
            # Generate YAML based on MCP capabilities
            yaml_content = self._generate_yaml_for_mcp(mcp_name, domain, capabilities, request)
            
            if yaml_content:
                # Determine phase directory
                phase_dir = self._get_phase_directory(domain)
                filename = f"{mcp_name.replace('-', '_')}_generated.yaml"
                templates[f"{phase_dir}/{filename}"] = yaml_content
                
        return templates
        
    def _generate_yaml_for_mcp(self, mcp_name: str, domain: str, capabilities: List[str], request: str) -> str:
        """Generate YAML content for specific MCP"""
        # Extract resource name from request
        resource_name = self._extract_resource_name(request, domain)
        
        if 'ecs' in mcp_name.lower():
            return self._generate_ecs_yaml(resource_name, capabilities)
        elif 'rds' in mcp_name.lower():
            return self._generate_rds_yaml(resource_name, capabilities)
        elif 'elb' in mcp_name.lower() or 'alb' in mcp_name.lower():
            return self._generate_elb_yaml(resource_name, capabilities)
        elif 'lambda' in mcp_name.lower():
            return self._generate_lambda_yaml(resource_name, capabilities)
        elif 'dynamodb' in mcp_name.lower():
            return self._generate_dynamodb_yaml(resource_name, capabilities)
        else:
            return self._generate_generic_yaml(mcp_name, resource_name, capabilities)
            
    def _extract_resource_name(self, request: str, domain: str) -> str:
        """Extract resource name from request"""
        # Simple extraction logic
        words = request.lower().split()
        if 'cluster' in words:
            return 'user-cluster'
        elif 'database' in words or 'db' in words:
            return 'user-database'
        elif 'function' in words:
            return 'user-function'
        elif 'table' in words:
            return 'user-table'
        else:
            return f'user-{domain}-resource'
            
    def _get_phase_directory(self, domain: str) -> str:
        """Get phase directory for domain"""
        phase_mapping = {
            'compute': 'phases/01-compute',
            'data': 'phases/02-data',
            'networking': 'phases/03-networking',
            'security': 'phases/04-security',
            'serverless': 'phases/05-serverless',
            'observability': 'phases/06-observability'
        }
        return phase_mapping.get(domain, 'phases/99-misc')
        
    def _generate_ecs_yaml(self, resource_name: str, capabilities: List[str]) -> str:
        """Generate ECS cluster YAML"""
        return f"""AWSTemplateFormatVersion: '2010-09-09'
Description: 'ECS Cluster generated by IAL MCP Router'

Parameters:
  ProjectName:
    Type: String
    Default: ial-user
    Description: Project name for resource naming

Resources:
  ECSCluster:
    Type: AWS::ECS::Cluster
    Properties:
      ClusterName: !Sub '${{ProjectName}}-{resource_name}'
      CapacityProviders:
        - FARGATE
        - FARGATE_SPOT
      DefaultCapacityProviderStrategy:
        - CapacityProvider: FARGATE
          Weight: 1
      ClusterSettings:
        - Name: containerInsights
          Value: enabled
      Tags:
        - Key: Name
          Value: !Sub '${{ProjectName}}-{resource_name}'
        - Key: ManagedBy
          Value: IAL-MCP-Router
        - Key: Domain
          Value: compute

Outputs:
  ClusterArn:
    Description: ECS Cluster ARN
    Value: !Ref ECSCluster
    Export:
      Name: !Sub '${{ProjectName}}-{resource_name}-arn'
"""

    def _generate_rds_yaml(self, resource_name: str, capabilities: List[str]) -> str:
        """Generate RDS database YAML"""
        return f"""AWSTemplateFormatVersion: '2010-09-09'
Description: 'RDS Database generated by IAL MCP Router'

Parameters:
  ProjectName:
    Type: String
    Default: ial-user
    Description: Project name for resource naming

Resources:
  DBSubnetGroup:
    Type: AWS::RDS::DBSubnetGroup
    Properties:
      DBSubnetGroupDescription: Subnet group for RDS database
      SubnetIds:
        - !ImportValue VPC-PrivateSubnet1
        - !ImportValue VPC-PrivateSubnet2
      Tags:
        - Key: Name
          Value: !Sub '${{ProjectName}}-{resource_name}-subnet-group'

  DatabaseInstance:
    Type: AWS::RDS::DBInstance
    Properties:
      DBInstanceIdentifier: !Sub '${{ProjectName}}-{resource_name}'
      DBInstanceClass: db.t3.micro
      Engine: mysql
      EngineVersion: '8.0'
      MasterUsername: admin
      ManageMasterUserPassword: true
      AllocatedStorage: 20
      StorageType: gp2
      DBSubnetGroupName: !Ref DBSubnetGroup
      VPCSecurityGroups:
        - !ImportValue VPC-DatabaseSecurityGroup
      BackupRetentionPeriod: 7
      MultiAZ: false
      StorageEncrypted: true
      Tags:
        - Key: Name
          Value: !Sub '${{ProjectName}}-{resource_name}'
        - Key: ManagedBy
          Value: IAL-MCP-Router
        - Key: Domain
          Value: data

Outputs:
  DatabaseEndpoint:
    Description: RDS Database Endpoint
    Value: !GetAtt DatabaseInstance.Endpoint.Address
    Export:
      Name: !Sub '${{ProjectName}}-{resource_name}-endpoint'
"""

    def _generate_elb_yaml(self, resource_name: str, capabilities: List[str]) -> str:
        """Generate Application Load Balancer YAML"""
        return f"""AWSTemplateFormatVersion: '2010-09-09'
Description: 'Application Load Balancer generated by IAL MCP Router'

Parameters:
  ProjectName:
    Type: String
    Default: ial-user
    Description: Project name for resource naming

Resources:
  ApplicationLoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Name: !Sub '${{ProjectName}}-{resource_name}'
      Type: application
      Scheme: internet-facing
      Subnets:
        - !ImportValue VPC-PublicSubnet1
        - !ImportValue VPC-PublicSubnet2
      SecurityGroups:
        - !ImportValue VPC-LoadBalancerSecurityGroup
      Tags:
        - Key: Name
          Value: !Sub '${{ProjectName}}-{resource_name}'
        - Key: ManagedBy
          Value: IAL-MCP-Router
        - Key: Domain
          Value: networking

  TargetGroup:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    Properties:
      Name: !Sub '${{ProjectName}}-{resource_name}-tg'
      Port: 80
      Protocol: HTTP
      VpcId: !ImportValue VPC-Id
      HealthCheckPath: /health
      HealthCheckProtocol: HTTP
      TargetType: ip

  Listener:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      DefaultActions:
        - Type: forward
          TargetGroupArn: !Ref TargetGroup
      LoadBalancerArn: !Ref ApplicationLoadBalancer
      Port: 80
      Protocol: HTTP

Outputs:
  LoadBalancerDNS:
    Description: Load Balancer DNS Name
    Value: !GetAtt ApplicationLoadBalancer.DNSName
    Export:
      Name: !Sub '${{ProjectName}}-{resource_name}-dns'
"""

    def _generate_lambda_yaml(self, resource_name: str, capabilities: List[str]) -> str:
        """Generate Lambda function YAML"""
        return f"""AWSTemplateFormatVersion: '2010-09-09'
Description: 'Lambda Function generated by IAL MCP Router'

Parameters:
  ProjectName:
    Type: String
    Default: ial-user
    Description: Project name for resource naming

Resources:
  LambdaExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub '${{ProjectName}}-{resource_name}-role'
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

  LambdaFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: !Sub '${{ProjectName}}-{resource_name}'
      Runtime: python3.11
      Handler: index.lambda_handler
      Role: !GetAtt LambdaExecutionRole.Arn
      Code:
        ZipFile: |
          def lambda_handler(event, context):
              return {{
                  'statusCode': 200,
                  'body': 'Hello from IAL MCP Router generated Lambda!'
              }}
      Timeout: 30
      MemorySize: 128
      Tags:
        - Key: Name
          Value: !Sub '${{ProjectName}}-{resource_name}'
        - Key: ManagedBy
          Value: IAL-MCP-Router
        - Key: Domain
          Value: serverless

Outputs:
  FunctionArn:
    Description: Lambda Function ARN
    Value: !GetAtt LambdaFunction.Arn
    Export:
      Name: !Sub '${{ProjectName}}-{resource_name}-arn'
"""

    def _generate_dynamodb_yaml(self, resource_name: str, capabilities: List[str]) -> str:
        """Generate DynamoDB table YAML"""
        return f"""AWSTemplateFormatVersion: '2010-09-09'
Description: 'DynamoDB Table generated by IAL MCP Router'

Parameters:
  ProjectName:
    Type: String
    Default: ial-user
    Description: Project name for resource naming

Resources:
  DynamoDBTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub '${{ProjectName}}-{resource_name}'
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: id
          AttributeType: S
      KeySchema:
        - AttributeName: id
          KeyType: HASH
      PointInTimeRecoverySpecification:
        PointInTimeRecoveryEnabled: true
      SSESpecification:
        SSEEnabled: true
      Tags:
        - Key: Name
          Value: !Sub '${{ProjectName}}-{resource_name}'
        - Key: ManagedBy
          Value: IAL-MCP-Router
        - Key: Domain
          Value: data

Outputs:
  TableName:
    Description: DynamoDB Table Name
    Value: !Ref DynamoDBTable
    Export:
      Name: !Sub '${{ProjectName}}-{resource_name}-name'
"""

    def _generate_generic_yaml(self, mcp_name: str, resource_name: str, capabilities: List[str]) -> str:
        """Generate generic YAML for unknown MCP types"""
        return f"""AWSTemplateFormatVersion: '2010-09-09'
Description: 'Generic resource generated by IAL MCP Router for {mcp_name}'

Parameters:
  ProjectName:
    Type: String
    Default: ial-user
    Description: Project name for resource naming

Resources:
  # Generic resource placeholder
  # MCP: {mcp_name}
  # Capabilities: {', '.join(capabilities)}
  # This template needs manual implementation
  
  PlaceholderResource:
    Type: AWS::CloudFormation::WaitConditionHandle
    Properties: {{}}

Outputs:
  PlaceholderOutput:
    Description: Placeholder output for {mcp_name}
    Value: !Ref PlaceholderResource
"""
        
    async def _execute_single_mcp_async(self, mcp_name: str, mcp_instance: Any, request: str) -> Dict:
        """Execute single MCP async"""
        try:
            # Simulate MCP execution
            await asyncio.sleep(0.1)  # Simulate execution time
            
            return {
                'mcp_name': mcp_name,
                'request_processed': request,
                'capabilities_used': mcp_instance.get('capabilities', []),
                'execution_time': 0.1,
                'resources_created': f"simulated_{mcp_name}_resources"
            }
            
        except Exception as e:
            raise Exception(f"MCP {mcp_name} execution failed: {e}")
            
    def _fallback_response(self, error_message: str, start_time: float) -> Dict[str, Any]:
        """Generate fallback response"""
        return {
            'status': 'fallback',
            'error': error_message,
            'fallback_used': True,
            'performance_metrics': {
                'total_time': round((time.time() - start_time) * 1000, 2)
            },
            'circuit_breaker_metrics': self._get_circuit_breaker_metrics()
        }
        
    def _get_circuit_breaker_metrics(self) -> Dict:
        """Get performance metrics from all circuit breakers"""
        metrics = {
            'routing_circuit': self.routing_circuit.get_metrics(),
            'llm_circuits': {},
            'mcp_circuits': {}
        }
        
        # LLM circuit breaker metrics
        for provider, circuit in self.llm_provider.circuit_breakers.items():
            metrics['llm_circuits'][provider] = circuit.get_metrics()
            
        # MCP circuit breaker metrics
        for mcp_name, circuit in self.orchestrator.circuit_breakers.items():
            metrics['mcp_circuits'][mcp_name] = circuit.get_metrics()
            
        return metrics
        
    def route_request(self, request: str) -> Dict[str, Any]:
        """Sync wrapper with proper event loop handling"""
        try:
            # Check if we're already in an event loop
            try:
                loop = asyncio.get_running_loop()
                # We're in a running loop, use thread executor
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._run_in_new_loop, request)
                    return future.result(timeout=15)
            except RuntimeError:
                # No running loop, we can use the current thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self.route_request_async(request))
                finally:
                    loop.close()
                    
        except Exception as e:
            return self._fallback_response(f"Router error: {str(e)}", time.time())
    
    def _run_in_new_loop(self, request: str) -> Dict[str, Any]:
        """Run async method in new event loop in separate thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.route_request_async(request))
        finally:
            loop.close()
            
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        health_status = {
            'overall_status': 'healthy',
            'components': {},
            'timestamp': time.time()
        }
        
        # Check LLM provider
        try:
            llm_metrics = self.llm_provider.get_metrics()
            health_status['components']['llm_provider'] = {
                'status': 'healthy',
                'metrics': llm_metrics
            }
        except Exception as e:
            health_status['components']['llm_provider'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['overall_status'] = 'degraded'
            
        # Check MCP orchestrator
        try:
            await self.orchestrator.health_check_mcps_async()
            orchestrator_metrics = self.orchestrator.get_metrics()
            health_status['components']['mcp_orchestrator'] = {
                'status': 'healthy',
                'metrics': orchestrator_metrics
            }
        except Exception as e:
            health_status['components']['mcp_orchestrator'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['overall_status'] = 'degraded'
            
        return health_status
        
    async def cleanup(self):
        """Cleanup all resources"""
        await self.orchestrator.cleanup()
        #print("✅ Router cleanup completed")
