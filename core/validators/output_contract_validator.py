#!/usr/bin/env python3
"""
Output Contract Validator - Valida contratos de saída em runtime
"""

import boto3
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class ValidationResult:
    success: bool
    errors: List[str]
    warnings: List[str]

class OutputContractValidator:
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.cf_client = boto3.client('cloudformation', region_name=region)
        self.s3_client = boto3.client('s3', region_name=region)
        self.rds_client = boto3.client('rds', region_name=region)
        self.ssm_client = boto3.client('ssm', region_name=region)
        
    def validate_stack_contract(self, stack_name: str, contract: Dict[str, Any]) -> ValidationResult:
        """Valida contrato de saída completo para um stack"""
        errors = []
        warnings = []
        
        try:
            # 1. Obter outputs do stack
            stack_outputs = self._get_stack_outputs(stack_name)
            
            # 2. Validar outputs obrigatórios
            missing_outputs = self._validate_required_outputs(stack_outputs, contract)
            errors.extend(missing_outputs)
            
            # 3. Validar criptografia
            encryption_errors = self._validate_encryption(stack_outputs, contract)
            errors.extend(encryption_errors)
            
            # 4. Validar tags
            tag_errors = self._validate_tags(stack_name, contract)
            errors.extend(tag_errors)
            
            return ValidationResult(
                success=len(errors) == 0,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            return ValidationResult(
                success=False,
                errors=[f"Erro na validação: {str(e)}"],
                warnings=[]
            )
    
    def _get_stack_outputs(self, stack_name: str) -> Dict[str, str]:
        """Obtém outputs do CloudFormation stack"""
        try:
            response = self.cf_client.describe_stacks(StackName=stack_name)
            stack = response['Stacks'][0]
            
            outputs = {}
            for output in stack.get('Outputs', []):
                outputs[output['OutputKey']] = output['OutputValue']
                
            return outputs
            
        except Exception as e:
            raise Exception(f"Erro ao obter outputs do stack {stack_name}: {str(e)}")
    
    def _validate_required_outputs(self, outputs: Dict[str, str], contract: Dict[str, Any]) -> List[str]:
        """Valida se todos os outputs obrigatórios existem"""
        errors = []
        required = contract.get('must_exist', [])
        
        for output_key in required:
            if output_key not in outputs:
                errors.append(f"Output obrigatório '{output_key}' não encontrado")
            elif not outputs[output_key]:
                errors.append(f"Output obrigatório '{output_key}' está vazio")
                
        return errors
    
    def _validate_encryption(self, outputs: Dict[str, str], contract: Dict[str, Any]) -> List[str]:
        """Valida se outputs sensíveis estão criptografados"""
        errors = []
        encrypted_required = contract.get('must_be_encrypted', [])
        
        for output_key in encrypted_required:
            if output_key not in outputs:
                continue  # Já validado em required_outputs
                
            output_value = outputs[output_key]
            
            # Detectar tipo de recurso e validar criptografia
            if output_key.lower().endswith('bucketname') or 'bucket' in output_key.lower():
                if not self._validate_s3_encryption(output_value):
                    errors.append(f"S3 bucket '{output_value}' não está criptografado")
                    
            elif output_key.lower().endswith('dbendpoint') or 'database' in output_key.lower():
                if not self._validate_rds_encryption(output_value):
                    errors.append(f"RDS instance '{output_value}' não está criptografado")
                    
            elif output_key.lower().endswith('parameter') or 'param' in output_key.lower():
                if not self._validate_ssm_encryption(output_value):
                    errors.append(f"SSM Parameter '{output_value}' não é SecureString")
                    
        return errors
    
    def _validate_s3_encryption(self, bucket_name: str) -> bool:
        """Verifica se bucket S3 tem criptografia habilitada"""
        try:
            response = self.s3_client.get_bucket_encryption(Bucket=bucket_name)
            return 'ServerSideEncryptionConfiguration' in response
        except Exception as e:
            # Check if it's the specific "not found" error
            if hasattr(e, 'response') and e.response.get('Error', {}).get('Code') == 'ServerSideEncryptionConfigurationNotFoundError':
                return False
            # For any other error, assume not encrypted
            return False
    
    def _validate_rds_encryption(self, db_endpoint: str) -> bool:
        """Verifica se RDS instance tem encryption at rest"""
        try:
            # Extrair DB identifier do endpoint
            db_identifier = db_endpoint.split('.')[0]
            
            response = self.rds_client.describe_db_instances(DBInstanceIdentifier=db_identifier)
            db_instance = response['DBInstances'][0]
            
            return db_instance.get('StorageEncrypted', False)
            
        except Exception:
            return False  # Assume não criptografado se não conseguir verificar
    
    def _validate_ssm_encryption(self, parameter_name: str) -> bool:
        """Verifica se SSM Parameter é SecureString"""
        try:
            response = self.ssm_client.get_parameter(Name=parameter_name)
            return response['Parameter']['Type'] == 'SecureString'
        except Exception:
            return False
    
    def _validate_tags(self, stack_name: str, contract: Dict[str, Any]) -> List[str]:
        """Valida se stack tem tags obrigatórias"""
        errors = []
        required_tags = contract.get('tags_must_include', [])
        
        if not required_tags:
            return errors
            
        try:
            response = self.cf_client.describe_stacks(StackName=stack_name)
            stack_tags = {tag['Key']: tag['Value'] for tag in response['Stacks'][0].get('Tags', [])}
            
            for required_tag in required_tags:
                if required_tag not in stack_tags:
                    errors.append(f"Tag obrigatória '{required_tag}' não encontrada no stack")
                    
        except Exception as e:
            errors.append(f"Erro ao validar tags: {str(e)}")
            
        return errors
    
    def validate_cross_phase_dependencies(self, 
                                        source_stack: str, 
                                        target_inputs: Dict[str, str]) -> ValidationResult:
        """Valida se outputs de um stack atendem inputs de outro"""
        errors = []
        warnings = []
        
        try:
            source_outputs = self._get_stack_outputs(source_stack)
            
            for input_key, expected_output in target_inputs.items():
                if expected_output not in source_outputs:
                    errors.append(f"Input '{input_key}' espera output '{expected_output}' que não existe")
                elif not source_outputs[expected_output]:
                    errors.append(f"Output '{expected_output}' existe mas está vazio")
                    
        except Exception as e:
            errors.append(f"Erro na validação cross-phase: {str(e)}")
            
        return ValidationResult(
            success=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

# Função utilitária para uso direto
def validate_stack_outputs(stack_name: str, contract: Dict[str, Any], region: str = 'us-east-1') -> ValidationResult:
    """Função utilitária para validação rápida"""
    validator = OutputContractValidator(region)
    return validator.validate_stack_contract(stack_name, contract)
