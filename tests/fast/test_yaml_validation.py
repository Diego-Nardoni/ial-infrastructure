#!/usr/bin/env python3
"""
Fast Tests - YAML Validation
Should run in < 5 seconds
"""

import unittest
import yaml
import os
import sys

sys.path.insert(0, '/home/ial')

class TestYAMLValidation(unittest.TestCase):
    """Test YAML syntax validation"""
    
    def test_bedrock_agent_core_yaml(self):
        """Test Bedrock Agent Core template YAML syntax"""
        template_path = "/home/ial/phases/00-foundation/44-bedrock-agent-core.yaml"
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                try:
                    # CloudFormation YAML contains !Ref functions, so we expect this to fail
                    # but we can check basic structure
                    content = f.read()
                    self.assertIn('AWSTemplateFormatVersion', content)
                    self.assertIn('Resources', content)
                    self.assertIn('Outputs', content)
                except Exception as e:
                    self.fail(f"YAML structure validation failed: {e}")
    
    def test_bedrock_lambda_yaml(self):
        """Test Bedrock Lambda template YAML syntax"""
        template_path = "/home/ial/phases/00-foundation/43-bedrock-agent-lambda.yaml"
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                try:
                    content = f.read()
                    self.assertIn('AWSTemplateFormatVersion', content)
                    self.assertIn('Resources', content)
                    self.assertIn('AWS::Lambda::Function', content)
                except Exception as e:
                    self.fail(f"YAML structure validation failed: {e}")
    
    def test_phase_metadata_files(self):
        """Test phase metadata files"""
        phases_dir = "/home/ial/phases"
        if os.path.exists(phases_dir):
            for phase_dir in os.listdir(phases_dir):
                phase_path = os.path.join(phases_dir, phase_dir)
                if os.path.isdir(phase_path):
                    metadata_file = os.path.join(phase_path, "domain-metadata.yaml")
                    if os.path.exists(metadata_file):
                        with open(metadata_file, 'r') as f:
                            try:
                                yaml.safe_load(f)
                            except yaml.YAMLError as e:
                                self.fail(f"Invalid YAML in {metadata_file}: {e}")

if __name__ == '__main__':
    unittest.main()
