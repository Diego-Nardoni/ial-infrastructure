#!/usr/bin/env python3
"""
CloudFormation YAML Loader - Loader específico para CloudFormation
"""

import yaml

class CFYAMLLoader:
    """Loader YAML específico para CloudFormation"""
    
    def __init__(self):
        self.loader_type = 'cloudformation'
    
    def load(self, yaml_content: str):
        """Carregar YAML CloudFormation"""
        try:
            return yaml.safe_load(yaml_content)
        except Exception as e:
            print(f"⚠️ CF YAML Loader error: {e}")
            return yaml.safe_load(yaml_content)
    
    def validate_cf_template(self, template: dict) -> bool:
        """Validar template CloudFormation"""
        required_fields = ['AWSTemplateFormatVersion', 'Resources']
        return all(field in template for field in required_fields)
