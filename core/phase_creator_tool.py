#!/usr/bin/env python3
"""
Phase Creator Tool - Cria phases YAML para infraestrutura AWS
"""

import os
import yaml
from datetime import datetime
from typing import Dict, Any


def create_infrastructure_phase(
    phase_number: int,
    resource_type: str,
    resource_name: str,
    properties: Dict[str, Any]
) -> Dict[str, str]:
    """
    Cria uma phase YAML para infraestrutura AWS
    
    Args:
        phase_number: Número da phase (ex: 20)
        resource_type: Tipo do recurso AWS (ex: VPC, S3, EKS)
        resource_name: Nome do recurso
        properties: Propriedades específicas do recurso
    
    Returns:
        Dict com path do arquivo e conteúdo YAML
    """
    
    # Inferir resource_type se não especificado ou genérico
    if not resource_type or resource_type.lower() in ['network', 'networking', 'rede']:
        resource_type = "VPC"
        resource_name = resource_name or "network"
    
    # Templates básicos por tipo de recurso
    templates = {
        "VPC": _generate_vpc_yaml,
        "S3": _generate_s3_yaml,
        "EKS": _generate_eks_yaml,
        "RDS": _generate_rds_yaml,
        "Lambda": _generate_lambda_yaml,
    }
    
    generator = templates.get(resource_type.upper(), _generate_generic_yaml)
    yaml_content = generator(resource_name, properties)
    
    # Salvar arquivo
    filename = f"{phase_number:02d}-{resource_type.lower()}-{resource_name}.yaml"
    filepath = os.path.join("/home/ial/phases", filename)
    
    # Criar diretório se não existir
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w') as f:
        f.write(yaml_content)
    
    # Mostrar preview do YAML
    preview = "\n".join(yaml_content.split("\n")[:20]) + "\n..."
    
    return {
        "status": "success",
        "message": f"✅ Phase {filename} criada com sucesso!",
        "filepath": filepath,
        "filename": filename,
        "yaml_preview": preview,
        "next_steps": [
            "1. Revise o YAML gerado em: " + filepath,
            "2. Faça commit: git add phases/ && git commit -m 'Add network phase'",
            "3. Push: git push origin main",
            "4. GitHub Actions criará Pull Request automaticamente",
            "5. Aprove o PR para provisionar na AWS"
        ]
    }


def _generate_vpc_yaml(name: str, props: Dict) -> str:
    """Gera YAML para VPC"""
    return f"""AWSTemplateFormatVersion: '2010-09-09'
Description: 'Network infrastructure - {name}'

Resources:
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: {props.get('cidr', '10.0.0.0/16')}
      EnableDnsHostnames: true
      EnableDnsSupport: true
      Tags:
        - Key: Name
          Value: {name}
        - Key: ManagedBy
          Value: IAL
        - Key: CreatedAt
          Value: {datetime.now().isoformat()}

  PublicSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: {props.get('public_subnet_1', '10.0.1.0/24')}
      AvailabilityZone: !Select [0, !GetAZs '']
      MapPublicIpOnLaunch: true
      Tags:
        - Key: Name
          Value: {name}-public-1

  PublicSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: {props.get('public_subnet_2', '10.0.2.0/24')}
      AvailabilityZone: !Select [1, !GetAZs '']
      MapPublicIpOnLaunch: true
      Tags:
        - Key: Name
          Value: {name}-public-2

  InternetGateway:
    Type: AWS::EC2::InternetGateway
    Properties:
      Tags:
        - Key: Name
          Value: {name}-igw

  AttachGateway:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      VpcId: !Ref VPC
      InternetGatewayId: !Ref InternetGateway

  PublicRouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC
      Tags:
        - Key: Name
          Value: {name}-public-rt

  PublicRoute:
    Type: AWS::EC2::Route
    DependsOn: AttachGateway
    Properties:
      RouteTableId: !Ref PublicRouteTable
      DestinationCidrBlock: 0.0.0.0/0
      GatewayId: !Ref InternetGateway

Outputs:
  VPCId:
    Value: !Ref VPC
    Export:
      Name: !Sub '${{AWS::StackName}}-VPCId'
  
  PublicSubnet1Id:
    Value: !Ref PublicSubnet1
    Export:
      Name: !Sub '${{AWS::StackName}}-PublicSubnet1'
  
  PublicSubnet2Id:
    Value: !Ref PublicSubnet2
    Export:
      Name: !Sub '${{AWS::StackName}}-PublicSubnet2'
"""


def _generate_s3_yaml(name: str, props: Dict) -> str:
    """Gera YAML para S3 Bucket"""
    return f"""AWSTemplateFormatVersion: '2010-09-09'
Description: 'S3 Bucket - {name}'

Resources:
  Bucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: {name}
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
      VersioningConfiguration:
        Status: Enabled
      Tags:
        - Key: ManagedBy
          Value: IAL
        - Key: CreatedAt
          Value: {datetime.now().isoformat()}

Outputs:
  BucketName:
    Value: !Ref Bucket
  BucketArn:
    Value: !GetAtt Bucket.Arn
"""


def _generate_generic_yaml(name: str, props: Dict) -> str:
    """Gera YAML genérico"""
    return f"""AWSTemplateFormatVersion: '2010-09-09'
Description: 'Generic resource - {name}'

# TODO: Customize this template for your specific resource type

Resources:
  Resource:
    Type: AWS::CloudFormation::WaitConditionHandle
    Properties: {{}}

Outputs:
  ResourceId:
    Value: !Ref Resource
"""


# Outros generators...
_generate_eks_yaml = _generate_generic_yaml
_generate_rds_yaml = _generate_generic_yaml
_generate_lambda_yaml = _generate_generic_yaml
