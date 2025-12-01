#!/usr/bin/env python3
"""
Fast Tests - Core Imports and Basic Functionality
Should run in < 5 seconds
"""

import unittest
import sys
import os

# Add IAL to path for testing
sys.path.insert(0, '/home/ial')

class TestCoreImports(unittest.TestCase):
    """Test that core modules can be imported"""
    
    def test_foundation_deployer_import(self):
        """Test Foundation Deployer import"""
        try:
            from core.foundation_deployer import FoundationDeployer
            deployer = FoundationDeployer()
            self.assertTrue(hasattr(deployer, 'deploy_foundation_core'))
        except ImportError as e:
            self.fail(f"Failed to import FoundationDeployer: {e}")
    
    def test_cognitive_engine_import(self):
        """Test Cognitive Engine import"""
        try:
            from core.cognitive_engine import CognitiveEngine
            engine = CognitiveEngine()
            self.assertTrue(hasattr(engine, 'process_intent'))
        except ImportError as e:
            self.fail(f"Failed to import CognitiveEngine: {e}")
    
    def test_mcp_orchestrator_import(self):
        """Test MCP Orchestrator import"""
        try:
            from mcp_orchestrator import MCPOrchestrator
            orchestrator = MCPOrchestrator()
            self.assertTrue(hasattr(orchestrator, 'execute_mcp_group'))
        except ImportError as e:
            self.fail(f"Failed to import MCPOrchestrator: {e}")
    
    def test_bedrock_agent_core_import(self):
        """Test Bedrock Agent Core import"""
        try:
            from core.bedrock_agent_core import BedrockAgentCore
            agent = BedrockAgentCore()
            self.assertTrue(hasattr(agent, 'is_available'))
        except ImportError as e:
            self.fail(f"Failed to import BedrockAgentCore: {e}")

class TestPhaseStructure(unittest.TestCase):
    """Test phase directory structure"""
    
    def test_phases_directory_exists(self):
        """Test that phases directory exists"""
        phases_dir = "/home/ial/phases"
        self.assertTrue(os.path.exists(phases_dir), "Phases directory should exist")
    
    def test_foundation_phase_exists(self):
        """Test that foundation phase exists"""
        foundation_dir = "/home/ial/phases/00-foundation"
        self.assertTrue(os.path.exists(foundation_dir), "Foundation phase should exist")
    
    def test_bedrock_templates_exist(self):
        """Test that Bedrock Agent templates exist"""
        templates = [
            "/home/ial/phases/00-foundation/44-bedrock-agent-core.yaml",
            "/home/ial/phases/00-foundation/43-bedrock-agent-lambda.yaml"
        ]
        for template in templates:
            self.assertTrue(os.path.exists(template), f"Template should exist: {template}")

if __name__ == '__main__':
    unittest.main()
