import boto3
import json
from typing import Dict, List, Set, Tuple
from core.graph.dependency_graph import DependencyGraph, ResourceState, BlastRadius

class ResourceDiscovery:
    """
    Automatic discovery of resource dependencies from multiple sources
    """
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.cloudformation = boto3.client('cloudformation', region_name=region)
        self.resource_explorer = None
        
        # Try to initialize Resource Explorer
        try:
            self.resource_explorer = boto3.client('resource-explorer-2', region_name=region)
        except Exception:
            print("⚠️ Resource Explorer not available, using alternative discovery methods")
    
    def build_dependency_graph(self) -> DependencyGraph:
        """Build complete dependency graph from all available sources"""
        
        print("🔍 Building dependency graph...")
        graph = DependencyGraph()
        
        # 1. Discover resources from CloudFormation
        cf_resources = self._discover_cloudformation_resources()
        
        # 2. Add nodes to graph
        for resource in cf_resources:
            self._add_resource_to_graph(graph, resource)
        
        # 3. Discover dependencies from multiple sources
        self._discover_cloudformation_dependencies(graph, cf_resources)
        self._discover_heuristic_dependencies(graph)
        self._discover_tag_based_dependencies(graph)
        
        print(f"✅ Dependency graph built: {graph.get_graph_stats()}")
        return graph
    
    def _discover_cloudformation_resources(self) -> List[Dict]:
        """Discover resources from CloudFormation stacks"""
        
        resources = []
        
        try:
            # Get all IAL-related stacks
            stacks_response = self.cloudformation.list_stacks(
                StackStatusFilter=[
                    'CREATE_COMPLETE', 'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_COMPLETE'
                ]
            )
            
            for stack_summary in stacks_response['StackSummaries']:
                stack_name = stack_summary['StackName']
                if stack_name.startswith('ial-'):
                    stack_resources = self._get_stack_resources(stack_name)
                    resources.extend(stack_resources)
        
        except Exception as e:
            print(f"⚠️ Error discovering CloudFormation resources: {e}")
        
        return resources
    
    def _get_stack_resources(self, stack_name: str) -> List[Dict]:
        """Get all resources from a CloudFormation stack"""
        
        resources = []
        
        try:
            response = self.cloudformation.list_stack_resources(StackName=stack_name)
            
            for resource in response['StackResourceSummaries']:
                resource_info = {
                    'id': resource.get('PhysicalResourceId', resource['LogicalResourceId']),
                    'logical_id': resource['LogicalResourceId'],
                    'type': resource['ResourceType'],
                    'stack_name': stack_name,
                    'status': resource['ResourceStatus'],
                    'source': 'cloudformation'
                }
                resources.append(resource_info)
        
        except Exception as e:
            print(f"⚠️ Error getting stack resources for {stack_name}: {e}")
        
        return resources
    
    def _add_resource_to_graph(self, graph: DependencyGraph, resource: Dict):
        """Add a resource to the dependency graph"""
        
        resource_id = resource['id']
        resource_type = resource['type']
        
        # Determine state based on CloudFormation status
        state = ResourceState.HEALTHY
        if resource.get('status') in ['UPDATE_FAILED', 'CREATE_FAILED']:
            state = ResourceState.FAILED
        elif resource.get('status') in ['UPDATE_IN_PROGRESS', 'CREATE_IN_PROGRESS']:
            state = ResourceState.HEALING
        
        # Determine healing priority and blast radius
        priority, blast_radius = self._calculate_resource_criticality(resource_type)
        
        graph.add_node(
            resource_id=resource_id,
            resource_type=resource_type,
            state=state,
            healing_priority=priority,
            blast_radius=blast_radius
        )
        
        # Add metadata
        graph.nodes[resource_id].metadata.update({
            'logical_id': resource.get('logical_id'),
            'stack_name': resource.get('stack_name'),
            'source': resource.get('source')
        })
    
    def _calculate_resource_criticality(self, resource_type: str) -> Tuple[int, BlastRadius]:
        """Calculate healing priority and blast radius for resource type"""
        
        # Priority: 1=critical, 5=low
        # Blast Radius: impact of healing this resource
        
        criticality_map = {
            # Infrastructure Foundation (Critical)
            "AWS::EC2::VPC": (1, BlastRadius.CRITICAL),
            "AWS::EC2::InternetGateway": (1, BlastRadius.HIGH),
            "AWS::EC2::RouteTable": (1, BlastRadius.HIGH),
            
            # Security (High Priority)
            "AWS::EC2::SecurityGroup": (2, BlastRadius.HIGH),
            "AWS::IAM::Role": (2, BlastRadius.MODERATE),
            "AWS::KMS::Key": (2, BlastRadius.MODERATE),
            
            # Data Services (High Priority)
            "AWS::RDS::DBInstance": (2, BlastRadius.HIGH),
            "AWS::DynamoDB::Table": (2, BlastRadius.HIGH),
            "AWS::S3::Bucket": (3, BlastRadius.MODERATE),
            
            # Compute (Medium Priority)
            "AWS::EC2::Instance": (3, BlastRadius.MODERATE),
            "AWS::Lambda::Function": (3, BlastRadius.MINIMAL),
            "AWS::ECS::Service": (3, BlastRadius.MODERATE),
            
            # Networking (Medium Priority)
            "AWS::EC2::Subnet": (3, BlastRadius.HIGH),
            "AWS::ElasticLoadBalancingV2::LoadBalancer": (3, BlastRadius.MODERATE),
            
            # Monitoring/Logging (Low Priority)
            "AWS::Logs::LogGroup": (4, BlastRadius.MINIMAL),
            "AWS::CloudWatch::Alarm": (4, BlastRadius.MINIMAL),
        }
        
        return criticality_map.get(resource_type, (3, BlastRadius.MODERATE))
    
    def _discover_cloudformation_dependencies(self, graph: DependencyGraph, resources: List[Dict]):
        """Discover dependencies from CloudFormation templates"""
        
        # Group resources by stack
        stacks = {}
        for resource in resources:
            stack_name = resource.get('stack_name')
            if stack_name:
                if stack_name not in stacks:
                    stacks[stack_name] = []
                stacks[stack_name].append(resource)
        
        # Analyze each stack's template for dependencies
        for stack_name, stack_resources in stacks.items():
            try:
                template = self._get_stack_template(stack_name)
                if template:
                    self._parse_template_dependencies(graph, template, stack_resources)
            except Exception as e:
                print(f"⚠️ Error analyzing template for {stack_name}: {e}")
    
    def _get_stack_template(self, stack_name: str) -> Dict:
        """Get CloudFormation template for a stack"""
        
        try:
            response = self.cloudformation.get_template(StackName=stack_name)
            return response.get('TemplateBody', {})
        except Exception:
            return {}
    
    def _parse_template_dependencies(self, graph: DependencyGraph, template: Dict, resources: List[Dict]):
        """Parse CloudFormation template to find dependencies"""
        
        template_resources = template.get('Resources', {})
        
        for logical_id, resource_def in template_resources.items():
            # Find the actual resource in our list
            actual_resource = None
            for res in resources:
                if res.get('logical_id') == logical_id:
                    actual_resource = res
                    break
            
            if not actual_resource:
                continue
            
            resource_id = actual_resource['id']
            
            # Check DependsOn
            depends_on = resource_def.get('DependsOn', [])
            if isinstance(depends_on, str):
                depends_on = [depends_on]
            
            for dep_logical_id in depends_on:
                dep_resource = None
                for res in resources:
                    if res.get('logical_id') == dep_logical_id:
                        dep_resource = res
                        break
                
                if dep_resource and resource_id in graph.nodes and dep_resource['id'] in graph.nodes:
                    graph.add_dependency(resource_id, dep_resource['id'])
            
            # Check Ref and GetAtt in Properties
            properties = resource_def.get('Properties', {})
            self._find_property_references(graph, resource_id, properties, resources)
    
    def _find_property_references(self, graph: DependencyGraph, resource_id: str, properties: Dict, resources: List[Dict]):
        """Find resource references in CloudFormation properties"""
        
        def find_refs(obj):
            if isinstance(obj, dict):
                if 'Ref' in obj:
                    ref_logical_id = obj['Ref']
                    # Find referenced resource
                    for res in resources:
                        if res.get('logical_id') == ref_logical_id:
                            if resource_id in graph.nodes and res['id'] in graph.nodes:
                                graph.add_dependency(resource_id, res['id'])
                            break
                
                elif 'Fn::GetAtt' in obj:
                    get_att = obj['Fn::GetAtt']
                    if isinstance(get_att, list) and len(get_att) > 0:
                        ref_logical_id = get_att[0]
                        # Find referenced resource
                        for res in resources:
                            if res.get('logical_id') == ref_logical_id:
                                if resource_id in graph.nodes and res['id'] in graph.nodes:
                                    graph.add_dependency(resource_id, res['id'])
                                break
                
                else:
                    for value in obj.values():
                        find_refs(value)
            
            elif isinstance(obj, list):
                for item in obj:
                    find_refs(item)
        
        find_refs(properties)
    
    def _discover_heuristic_dependencies(self, graph: DependencyGraph):
        """Discover dependencies using heuristic rules"""
        
        for node_id, node in graph.nodes.items():
            resource_type = node.type
            
            # Apply heuristic rules based on resource type
            if resource_type == "AWS::EC2::Instance":
                self._add_ec2_heuristic_deps(graph, node_id)
            elif resource_type == "AWS::RDS::DBInstance":
                self._add_rds_heuristic_deps(graph, node_id)
            elif resource_type == "AWS::ElasticLoadBalancingV2::LoadBalancer":
                self._add_alb_heuristic_deps(graph, node_id)
    
    def _add_ec2_heuristic_deps(self, graph: DependencyGraph, ec2_id: str):
        """Add heuristic dependencies for EC2 instances"""
        
        # EC2 instances typically depend on:
        # - VPC (via subnet)
        # - Security Groups
        # - IAM Instance Profile
        
        for node_id, node in graph.nodes.items():
            if node.type == "AWS::EC2::VPC":
                # EC2 depends on VPC
                graph.add_dependency(ec2_id, node_id)
            elif node.type == "AWS::EC2::SecurityGroup":
                # EC2 typically uses security groups
                graph.add_dependency(ec2_id, node_id)
    
    def _add_rds_heuristic_deps(self, graph: DependencyGraph, rds_id: str):
        """Add heuristic dependencies for RDS instances"""
        
        for node_id, node in graph.nodes.items():
            if node.type == "AWS::EC2::SecurityGroup":
                # RDS depends on security groups
                graph.add_dependency(rds_id, node_id)
            elif node.type == "AWS::RDS::DBSubnetGroup":
                # RDS depends on subnet group
                graph.add_dependency(rds_id, node_id)
    
    def _add_alb_heuristic_deps(self, graph: DependencyGraph, alb_id: str):
        """Add heuristic dependencies for Application Load Balancers"""
        
        for node_id, node in graph.nodes.items():
            if node.type == "AWS::EC2::SecurityGroup":
                # ALB depends on security groups
                graph.add_dependency(alb_id, node_id)
            elif node.type == "AWS::EC2::Subnet":
                # ALB depends on subnets
                graph.add_dependency(alb_id, node_id)
    
    def _discover_tag_based_dependencies(self, graph: DependencyGraph):
        """Discover dependencies from standardized tags"""
        
        # Look for IAL-specific dependency tags
        for node_id, node in graph.nodes.items():
            metadata = node.metadata
            
            # Check for dependency tags (would be populated from actual AWS resources)
            depends_on_tag = metadata.get('ial:depends-on')
            if depends_on_tag:
                dependency_ids = depends_on_tag.split(',')
                for dep_id in dependency_ids:
                    dep_id = dep_id.strip()
                    if dep_id in graph.nodes:
                        graph.add_dependency(node_id, dep_id)
