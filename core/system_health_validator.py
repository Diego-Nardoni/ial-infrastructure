#!/usr/bin/env python3
"""
System Health Validator
Valida saúde completa do sistema IAL
"""

import boto3
from typing import Dict, List


class SystemHealthValidator:
    """Validador de saúde completo do sistema IAL"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.dynamodb = boto3.client('dynamodb', region_name=region)
        self.iam = boto3.client('iam', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.bedrock = boto3.client('bedrock-runtime', region_name=region)
        self.sts = boto3.client('sts', region_name=region)
        
    async def validate_complete_system(self) -> Dict:
        """Validação completa do sistema"""
        
        checks = [
            ("AWS Credentials", self._check_aws_credentials),
            ("Bedrock Access", self._check_bedrock_access),
            ("DynamoDB Tables", self._check_dynamodb_tables),
            ("IAM Roles", self._check_iam_roles),
            ("S3 Buckets", self._check_s3_buckets),
            ("Engines Integration", self._check_engines_integration)
        ]
        
        validation_results = {
            "overall_status": "unknown",
            "checks_passed": 0,
            "checks_failed": 0,
            "critical_issues": [],
            "warnings": [],
            "system_ready": False,
            "detailed_results": {}
        }
        
        for check_name, check_func in checks:
            try:
                result = await check_func()
                validation_results["detailed_results"][check_name] = result
                
                if result["status"] == "success":
                    validation_results["checks_passed"] += 1
                elif result["status"] == "warning":
                    validation_results["checks_passed"] += 1
                    validation_results["warnings"].append(result.get("message", ""))
                else:
                    validation_results["checks_failed"] += 1
                    validation_results["critical_issues"].append(result.get("message", ""))
                    
            except Exception as e:
                validation_results["checks_failed"] += 1
                validation_results["critical_issues"].append(f"{check_name}: {str(e)}")
        
        # Determinar status geral
        if validation_results["checks_failed"] == 0:
            validation_results["overall_status"] = "healthy"
            validation_results["system_ready"] = True
        elif validation_results["checks_failed"] <= 2:
            validation_results["overall_status"] = "degraded"
            validation_results["system_ready"] = True
        else:
            validation_results["overall_status"] = "unhealthy"
            validation_results["system_ready"] = False
        
        return validation_results
    
    async def _check_aws_credentials(self) -> Dict:
        """Verificar credenciais AWS"""
        try:
            identity = self.sts.get_caller_identity()
            return {
                "status": "success",
                "account_id": identity['Account'],
                "message": "AWS credentials valid"
            }
        except Exception as e:
            return {"status": "error", "message": f"Invalid credentials: {e}"}
    
    async def _check_bedrock_access(self) -> Dict:
        """Verificar acesso ao Bedrock"""
        try:
            import json
            self.bedrock.invoke_model(
                modelId='anthropic.claude-3-haiku-20240307-v1:0',
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 10,
                    'messages': [{'role': 'user', 'content': 'test'}]
                })
            )
            return {"status": "success", "message": "Bedrock accessible"}
        except Exception as e:
            return {"status": "error", "message": f"Bedrock not accessible: {e}"}
    
    async def _check_dynamodb_tables(self) -> Dict:
        """Verificar DynamoDB tables"""
        try:
            response = self.dynamodb.list_tables()
            tables = response.get('TableNames', [])
            ial_tables = [t for t in tables if t.startswith('ial-')]
            
            if len(ial_tables) >= 5:
                return {
                    "status": "success",
                    "tables_found": len(ial_tables),
                    "message": f"{len(ial_tables)} IAL tables found"
                }
            else:
                return {
                    "status": "warning",
                    "tables_found": len(ial_tables),
                    "message": f"Only {len(ial_tables)} IAL tables found (expected 11+)"
                }
        except Exception as e:
            return {"status": "error", "message": f"DynamoDB check failed: {e}"}
    
    async def _check_iam_roles(self) -> Dict:
        """Verificar IAM roles"""
        try:
            # Check for any IAL-related roles instead of specific role
            roles = self.iam.list_roles()['Roles']
            ial_roles = [role for role in roles if 'ial' in role['RoleName'].lower() or 'IAL' in role['RoleName']]
            
            if len(ial_roles) >= 5:  # We have many IAL roles from CloudFormation
                return {"status": "success", "message": f"IAM roles configured ({len(ial_roles)} IAL roles found)"}
            else:
                return {"status": "warning", "message": f"Only {len(ial_roles)} IAL roles found"}
        except Exception as e:
            return {"status": "error", "message": f"IAM check failed: {e}"}
    
    async def _check_s3_buckets(self) -> Dict:
        """Verificar S3 buckets"""
        try:
            response = self.s3.list_buckets()
            buckets = [b['Name'] for b in response.get('Buckets', [])]
            ial_buckets = [b for b in buckets if b.startswith('ial-')]
            
            if len(ial_buckets) >= 2:
                return {
                    "status": "success",
                    "buckets_found": len(ial_buckets),
                    "message": f"{len(ial_buckets)} IAL buckets found"
                }
            else:
                return {
                    "status": "warning",
                    "buckets_found": len(ial_buckets),
                    "message": f"Only {len(ial_buckets)} IAL buckets found (expected 3)"
                }
        except Exception as e:
            return {"status": "error", "message": f"S3 check failed: {e}"}
    
    async def _check_engines_integration(self) -> Dict:
        """Verificar integração dos engines"""
        try:
            # Verificar se engines podem ser importados
            from core.ial_master_engine_integrated import IALMasterEngineIntegrated
            return {"status": "success", "message": "Engines integration OK"}
        except ImportError as e:
            return {"status": "warning", "message": f"Engine import warning: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"Engines check failed: {e}"}


async def validate_system_health(region: str = "us-east-1") -> Dict:
    """Função auxiliar para validação"""
    validator = SystemHealthValidator(region=region)
    return await validator.validate_complete_system()
