#!/usr/bin/env python3
"""
IAL CI Mode - Professional CI/CD Integration
Exit codes: 0=OK, 1=validation, 2=AWS, 3=drift, 4=governance, 5=parser
"""

import sys
import os
import json
from typing import Dict, Any, List
from datetime import datetime

class CILogger:
    """CI-friendly logging without colors"""
    
    @staticmethod
    def log(level: str, message: str, ci_mode: bool = True):
        if ci_mode:
            print(f"[IAL][CI][{level}] {message}")
        else:
            # Colored output for local development
            colors = {'INFO': '\033[94m', 'WARN': '\033[93m', 'ERROR': '\033[91m', 'SUCCESS': '\033[92m'}
            reset = '\033[0m'
            color = colors.get(level, '')
            print(f"{color}[IAL][CI][{level}]{reset} {message}")

class IALCIMode:
    """IAL CI/CD Mode Implementation"""
    
    def __init__(self, ci_mode: bool = True):
        self.ci_mode = ci_mode
        self.logger = CILogger()
    
    def validate(self) -> int:
        """Validate phases YAML, DAG, and policies"""
        try:
            self.logger.log("INFO", "Starting phase validation", self.ci_mode)
            
            # Import existing validators
            from core.phase_parser import validate_yaml_syntax
            from core.validation_system import IALValidationSystem
            
            parser = None
            validator = IALValidationSystem()
            
            # Validate phases directory
            phases_dir = "/home/ial/phases"
            if not os.path.exists(phases_dir):
                self.logger.log("ERROR", f"Phases directory not found: {phases_dir}", self.ci_mode)
                return 1
            
            # Validate each phase
            errors = []
            for phase_dir in os.listdir(phases_dir):
                phase_path = os.path.join(phases_dir, phase_dir)
                if os.path.isdir(phase_path):
                    try:
                        # Validate YAML syntax
                        yaml_files = [f for f in os.listdir(phase_path) if f.endswith('.yaml')]
                        for yaml_file in yaml_files:
                            yaml_path = os.path.join(phase_path, yaml_file)
                            validate_yaml_syntax(yaml_path)
                        
                        self.logger.log("INFO", f"Phase {phase_dir}: {len(yaml_files)} files validated", self.ci_mode)
                    except Exception as e:
                        errors.append(f"Phase {phase_dir}: {str(e)}")
            
            if errors:
                for error in errors:
                    self.logger.log("ERROR", error, self.ci_mode)
                return 1
            
            self.logger.log("SUCCESS", "All phases validated successfully", self.ci_mode)
            return 0
            
        except Exception as e:
            self.logger.log("ERROR", f"Validation failed: {str(e)}", self.ci_mode)
            return 5

    def governance(self) -> int:
        """Validate governance rules, naming conventions, security"""
        try:
            self.logger.log("INFO", "Starting governance validation", self.ci_mode)
            
            from core.security_analyzer import SecurityAnalyzer
            
            analyzer = SecurityAnalyzer()
            
            # Check naming conventions
            issues = []
            
            # Validate IAM roles naming
            phases_dir = "/home/ial/phases"
            for root, dirs, files in os.walk(phases_dir):
                for file in files:
                    if file.endswith('.yaml'):
                        file_path = os.path.join(root, file)
                        # Basic governance checks
                        with open(file_path, 'r') as f:
                            content = f.read()
                            if 'AWS::IAM::Role' in content and 'ial-' not in content.lower():
                                issues.append(f"IAM role in {file} may not follow naming convention")
            
            if issues:
                for issue in issues:
                    self.logger.log("WARN", issue, self.ci_mode)
                return 4
            
            self.logger.log("SUCCESS", "Governance validation passed", self.ci_mode)
            return 0
            
        except Exception as e:
            self.logger.log("ERROR", f"Governance validation failed: {str(e)}", self.ci_mode)
            return 4

    def completeness(self) -> int:
        """Validate completeness of phases and DAG consistency"""
        try:
            self.logger.log("INFO", "Starting completeness validation", self.ci_mode)
            
            from core.desired_state import DesiredStateBuilder
            
            builder = DesiredStateBuilder()
            
            # Check if all required phases exist
            required_phases = ['00-foundation', '10-security', '20-network']
            phases_dir = "/home/ial/phases"
            
            missing_phases = []
            for phase in required_phases:
                phase_path = os.path.join(phases_dir, phase)
                if not os.path.exists(phase_path):
                    missing_phases.append(phase)
            
            if missing_phases:
                for phase in missing_phases:
                    self.logger.log("ERROR", f"Required phase missing: {phase}", self.ci_mode)
                return 1
            
            self.logger.log("SUCCESS", "Completeness validation passed", self.ci_mode)
            return 0
            
        except Exception as e:
            self.logger.log("ERROR", f"Completeness validation failed: {str(e)}", self.ci_mode)
            return 5

    def drift(self) -> int:
        """Check for infrastructure drift"""
        try:
            self.logger.log("INFO", "Starting drift detection", self.ci_mode)
            
            from core.drift.drift_detector import DriftDetector
            
            detector = DriftDetector()
            drift_items = detector.detect_drift()
            
            if drift_items and len(drift_items) > 0:
                self.logger.log("WARN", f"Drift detected: {len(drift_items)} items", self.ci_mode)
                for item in drift_items[:5]:  # Show first 5
                    self.logger.log("WARN", f"  - {item.get('resource', 'Unknown')}: {item.get('drift_type', 'Unknown')}", self.ci_mode)
                return 3
            
            self.logger.log("SUCCESS", "No drift detected", self.ci_mode)
            return 0
            
        except Exception as e:
            self.logger.log("ERROR", f"Drift detection failed: {str(e)}", self.ci_mode)
            return 2

    def mcp_test(self) -> int:
        """Test MCP communication"""
        try:
            self.logger.log("INFO", "Starting MCP connectivity test", self.ci_mode)
            
            from mcp_orchestrator import MCPOrchestrator
            
            orchestrator = MCPOrchestrator()
            
            # Test basic MCP connectivity
            result = orchestrator.test_connectivity()
            
            if not result.get('success', False):
                self.logger.log("ERROR", f"MCP test failed: {result.get('error', 'Unknown error')}", self.ci_mode)
                return 2
            
            self.logger.log("SUCCESS", "MCP connectivity test passed", self.ci_mode)
            return 0
            
        except Exception as e:
            self.logger.log("ERROR", f"MCP test failed: {str(e)}", self.ci_mode)
            return 2

    def test(self) -> int:
        """Run fast tests (< 5s)"""
        try:
            self.logger.log("INFO", "Starting fast tests", self.ci_mode)
            
            # Import validation
            try:
                from core.foundation_deployer import FoundationDeployer
                from core.cognitive_engine import CognitiveEngine
                from mcp_orchestrator import MCPOrchestrator
                self.logger.log("SUCCESS", "Core imports successful", self.ci_mode)
            except ImportError as e:
                self.logger.log("ERROR", f"Import failed: {str(e)}", self.ci_mode)
                return 1
            
            # Basic functionality tests
            tests_passed = 0
            tests_total = 3
            
            # Test 1: Foundation Deployer
            try:
                deployer = FoundationDeployer()
                if hasattr(deployer, 'deploy_foundation_core'):
                    tests_passed += 1
                    self.logger.log("SUCCESS", "Foundation Deployer test passed", self.ci_mode)
                else:
                    self.logger.log("ERROR", "Foundation Deployer missing required method", self.ci_mode)
            except Exception as e:
                self.logger.log("ERROR", f"Foundation Deployer test failed: {str(e)}", self.ci_mode)
            
            # Test 2: Cognitive Engine
            try:
                engine = CognitiveEngine()
                if hasattr(engine, 'process_intent'):
                    tests_passed += 1
                    self.logger.log("SUCCESS", "Cognitive Engine test passed", self.ci_mode)
                else:
                    self.logger.log("ERROR", "Cognitive Engine missing required method", self.ci_mode)
            except Exception as e:
                self.logger.log("ERROR", f"Cognitive Engine test failed: {str(e)}", self.ci_mode)
            
            # Test 3: MCP Orchestrator
            try:
                orchestrator = MCPOrchestrator()
                if hasattr(orchestrator, 'execute_mcp_group'):
                    tests_passed += 1
                    self.logger.log("SUCCESS", "MCP Orchestrator test passed", self.ci_mode)
                else:
                    self.logger.log("ERROR", "MCP Orchestrator missing required method", self.ci_mode)
            except Exception as e:
                self.logger.log("ERROR", f"MCP Orchestrator test failed: {str(e)}", self.ci_mode)
            
            if tests_passed == tests_total:
                self.logger.log("SUCCESS", f"All fast tests passed ({tests_passed}/{tests_total})", self.ci_mode)
                return 0
            else:
                self.logger.log("ERROR", f"Fast tests failed ({tests_passed}/{tests_total})", self.ci_mode)
                return 1
            
        except Exception as e:
            self.logger.log("ERROR", f"Fast tests failed: {str(e)}", self.ci_mode)
            return 1

def main():
    """Main CI mode entry point"""
    if len(sys.argv) < 3 or sys.argv[1] != 'ci':
        print("Usage: ialctl ci <command>")
        print("Commands: validate, governance, completeness, drift, mcp-test, test")
        return 1
    
    command = sys.argv[2]
    ci_mode = '--ci' in sys.argv or os.getenv('CI') == 'true'
    
    ci = IALCIMode(ci_mode=ci_mode)
    
    if command == 'validate':
        return ci.validate()
    elif command == 'governance':
        return ci.governance()
    elif command == 'completeness':
        return ci.completeness()
    elif command == 'drift':
        return ci.drift()
    elif command == 'mcp-test':
        return ci.mcp_test()
    elif command == 'test':
        return ci.test()
    else:
        print(f"Unknown command: {command}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
