#!/usr/bin/env python3
"""
Contract Enforcer - Integra validação de contratos no pipeline de deploy
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List
from .output_contract_validator import OutputContractValidator, ValidationResult

class ContractEnforcer:
    def __init__(self, region: str = 'us-east-1'):
        self.validator = OutputContractValidator(region)
        
    def enforce_phase_contract(self, phase_file: str, stack_name: str) -> ValidationResult:
        """Valida contrato de uma phase após deploy"""
        
        # 1. Carregar contrato da phase
        contract = self._load_phase_contract(phase_file)
        if not contract:
            return ValidationResult(
                success=False,
                errors=[f"Contrato não encontrado em {phase_file}"],
                warnings=[]
            )
        
        # 2. Validar contrato
        result = self.validator.validate_stack_contract(stack_name, contract)
        
        # 3. Log resultado
        self._log_validation_result(phase_file, stack_name, result)
        
        return result
    
    def _load_phase_contract(self, phase_file: str) -> Dict[str, Any]:
        """Carrega contrato de saída do arquivo phase.yaml"""
        try:
            with open(phase_file, 'r') as f:
                phase_data = yaml.safe_load(f)
                
            return phase_data.get('outputs_contract', {})
            
        except Exception as e:
            print(f"❌ Erro ao carregar phase {phase_file}: {e}")
            return {}
    
    def _log_validation_result(self, phase_file: str, stack_name: str, result: ValidationResult):
        """Log resultado da validação"""
        phase_name = Path(phase_file).stem
        
        if result.success:
            print(f"✅ Contrato validado: {phase_name} → {stack_name}")
        else:
            print(f"❌ Contrato violado: {phase_name} → {stack_name}")
            for error in result.errors:
                print(f"   • {error}")
                
        if result.warnings:
            for warning in result.warnings:
                print(f"⚠️  {warning}")
    
    def validate_pipeline_contracts(self, phases_dir: str, stack_prefix: str) -> Dict[str, ValidationResult]:
        """Valida contratos de todas as phases de um pipeline"""
        results = {}
        
        phases_path = Path(phases_dir)
        for phase_file in phases_path.glob("*.yaml"):
            phase_name = phase_file.stem
            stack_name = f"{stack_prefix}-{phase_name}"
            
            result = self.enforce_phase_contract(str(phase_file), stack_name)
            results[phase_name] = result
            
        return results
    
    def block_on_contract_violation(self, result: ValidationResult, phase_name: str) -> bool:
        """Decide se deve bloquear pipeline baseado na violação"""
        if result.success:
            return False
            
        # Critérios para bloqueio
        critical_violations = [
            'não encontrado',
            'não está criptografado', 
            'não é SecureString'
        ]
        
        for error in result.errors:
            if any(critical in error for critical in critical_violations):
                print(f"🚨 BLOQUEANDO PIPELINE: Violação crítica em {phase_name}")
                print(f"   Erro: {error}")
                return True
                
        return False

# Função para integração com Step Functions
def validate_phase_outputs(phase_file: str, stack_name: str, region: str = 'us-east-1') -> Dict[str, Any]:
    """Função para uso em Step Functions"""
    enforcer = ContractEnforcer(region)
    result = enforcer.enforce_phase_contract(phase_file, stack_name)
    
    return {
        'success': result.success,
        'errors': result.errors,
        'warnings': result.warnings,
        'should_block': enforcer.block_on_contract_violation(result, Path(phase_file).stem)
    }
