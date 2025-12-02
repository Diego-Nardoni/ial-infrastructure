#!/usr/bin/env python3
"""
Testes para validação de contratos de saída
"""

import pytest
from unittest.mock import Mock, patch
from core.validators.output_contract_validator import OutputContractValidator, ValidationResult

class TestOutputContractValidator:
    
    def setup_method(self):
        self.validator = OutputContractValidator()
    
    def test_validate_required_outputs_success(self):
        """Teste: Todos outputs obrigatórios presentes"""
        outputs = {'VpcId': 'vpc-123', 'SubnetIds': 'subnet-123,subnet-456'}
        contract = {'must_exist': ['VpcId', 'SubnetIds']}
        
        errors = self.validator._validate_required_outputs(outputs, contract)
        assert len(errors) == 0
    
    def test_validate_required_outputs_missing(self):
        """Teste: Output obrigatório ausente"""
        outputs = {'VpcId': 'vpc-123'}
        contract = {'must_exist': ['VpcId', 'SubnetIds']}
        
        errors = self.validator._validate_required_outputs(outputs, contract)
        assert len(errors) == 1
        assert 'SubnetIds' in errors[0]
    
    def test_validate_required_outputs_empty(self):
        """Teste: Output presente mas vazio"""
        outputs = {'VpcId': 'vpc-123', 'SubnetIds': ''}
        contract = {'must_exist': ['VpcId', 'SubnetIds']}
        
        errors = self.validator._validate_required_outputs(outputs, contract)
        assert len(errors) == 1
        assert 'está vazio' in errors[0]
    
    @patch('core.validators.output_contract_validator.boto3.client')
    def test_s3_encryption_validation(self, mock_boto):
        """Teste: Validação de criptografia S3"""
        # Mock S3 client
        mock_s3 = Mock()
        mock_boto.return_value = mock_s3
        mock_s3.get_bucket_encryption.return_value = {
            'ServerSideEncryptionConfiguration': {}
        }
        
        # Criar novo validator com mock
        validator = OutputContractValidator()
        validator.s3_client = mock_s3
        
        result = validator._validate_s3_encryption('test-bucket')
        assert result == True
    
    @patch('core.validators.output_contract_validator.boto3.client')
    def test_s3_no_encryption(self, mock_boto):
        """Teste: S3 sem criptografia"""
        mock_s3 = Mock()
        mock_boto.return_value = mock_s3
        
        # Simular erro de configuração não encontrada
        from botocore.exceptions import ClientError
        mock_s3.get_bucket_encryption.side_effect = ClientError(
            {'Error': {'Code': 'ServerSideEncryptionConfigurationNotFoundError'}},
            'GetBucketEncryption'
        )
        
        # Criar novo validator com mock
        validator = OutputContractValidator()
        validator.s3_client = mock_s3
        
        result = validator._validate_s3_encryption('test-bucket')
        assert result == False

if __name__ == '__main__':
    pytest.main([__file__])
