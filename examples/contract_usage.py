#!/usr/bin/env python3
"""
Exemplos de uso da validação de contratos
"""

from core.validators import validate_stack_outputs, ContractEnforcer

def example_basic_validation():
    """Exemplo básico de validação"""
    
    # Contrato esperado
    contract = {
        'must_exist': ['VpcId', 'SubnetIds', 'SecurityGroupId'],
        'must_be_encrypted': ['DatabaseEndpoint'],
        'tags_must_include': ['ial:managed', 'env:prod']
    }
    
    # Validar stack
    result = validate_stack_outputs('my-vpc-stack', contract)
    
    if result.success:
        print("✅ Contrato validado com sucesso!")
    else:
        print("❌ Violações encontradas:")
        for error in result.errors:
            print(f"   • {error}")

def example_pipeline_validation():
    """Exemplo de validação de pipeline completo"""
    
    enforcer = ContractEnforcer()
    
    # Validar todas as phases
    results = enforcer.validate_pipeline_contracts(
        phases_dir='/home/ial/phases/workloads/web-app',
        stack_prefix='webapp-prod'
    )
    
    # Verificar se alguma phase falhou
    failed_phases = [name for name, result in results.items() if not result.success]
    
    if failed_phases:
        print(f"❌ Phases com violações: {failed_phases}")
        return False
    else:
        print("✅ Todas as phases passaram na validação!")
        return True

def example_cross_phase_validation():
    """Exemplo de validação entre phases"""
    
    enforcer = ContractEnforcer()
    
    # Validar se outputs da phase networking atendem inputs da phase compute
    target_inputs = {
        'VpcId': 'VpcId',           # Input VpcId espera output VpcId
        'SubnetIds': 'PrivateSubnetIds',  # Input SubnetIds espera output PrivateSubnetIds
        'SecurityGroup': 'WebSecurityGroupId'
    }
    
    result = enforcer.validator.validate_cross_phase_dependencies(
        source_stack='webapp-prod-01-networking',
        target_inputs=target_inputs
    )
    
    if result.success:
        print("✅ Dependências cross-phase validadas!")
    else:
        print("❌ Problemas nas dependências:")
        for error in result.errors:
            print(f"   • {error}")

if __name__ == '__main__':
    print("🔧 Exemplos de Validação de Contratos\n")
    
    print("1. Validação Básica:")
    example_basic_validation()
    
    print("\n2. Validação de Pipeline:")
    example_pipeline_validation()
    
    print("\n3. Validação Cross-Phase:")
    example_cross_phase_validation()
