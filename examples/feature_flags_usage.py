#!/usr/bin/env python3
"""
Exemplos de uso do sistema de feature flags
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.feature_flags_manager import FeatureFlagsManager, is_feature_enabled
from core.integrations.drift_integration import get_drift_integration
from core.drift.drift_detector_enhanced import detect_drift_with_flags

def example_basic_usage():
    """Exemplo básico de uso"""
    print("🚩 Exemplo 1: Uso Básico de Feature Flags")
    
    # Check if feature is enabled
    if is_feature_enabled("drift_detection"):
        print("✅ Drift detection is enabled")
    else:
        print("❌ Drift detection is disabled")
    
    # Check experimental features
    if is_feature_enabled("experimental_features"):
        print("🧪 Experimental features enabled")
    else:
        print("🔒 Experimental features disabled")

def example_drift_integration():
    """Exemplo de integração com drift detection"""
    print("\n🔍 Exemplo 2: Integração com Drift Detection")
    
    drift_integration = get_drift_integration()
    scope = "webapp-prod"
    
    # Check drift configuration
    config = drift_integration.get_drift_config(scope)
    print(f"📋 Drift config for {scope}:")
    print(f"   Detect enabled: {config['detect_enabled']}")
    print(f"   Auto-heal enabled: {config['auto_heal_enabled']}")
    print(f"   State: {config['drift_state']}")

def example_enhanced_drift_detection():
    """Exemplo de drift detection com feature flags"""
    print("\n🔧 Exemplo 3: Enhanced Drift Detection")
    
    scope = "webapp-prod"
    resources = ["vpc-123", "subnet-456", "sg-789"]
    
    # Detect drift with feature flag integration
    result = detect_drift_with_flags(scope, resources)
    
    print(f"🎯 Drift detection result for {scope}:")
    print(f"   Status: {result['status']}")
    print(f"   Drift found: {result['drift_found']}")
    
    if "config" in result:
        print(f"   Detection enabled: {result['config']['detect_enabled']}")
        print(f"   Auto-heal enabled: {result['config']['auto_heal_enabled']}")

def example_feature_management():
    """Exemplo de gerenciamento de features"""
    print("\n⚙️ Exemplo 4: Gerenciamento de Features")
    
    try:
        manager = FeatureFlagsManager()
        
        # This would work if DynamoDB table exists
        print("📝 Setting feature flags (requires DynamoDB table):")
        print("   manager.set_flag('experimental_features', True, 'dev', 'Testing new features')")
        print("   manager.set_flag('advanced_monitoring', False, 'prod', 'Not ready for production')")
        
    except Exception as e:
        print(f"⚠️ Feature management requires DynamoDB table: {e}")

def example_cli_usage():
    """Exemplo de uso via CLI"""
    print("\n💻 Exemplo 5: Uso via CLI")
    print("Comandos disponíveis:")
    print("   python3 cli/feature_flags_cli.py check drift_detection")
    print("   python3 cli/feature_flags_cli.py enable experimental_features --scope dev")
    print("   python3 cli/feature_flags_cli.py drift pause webapp-prod --duration 2 --reason 'Maintenance window'")
    print("   python3 cli/feature_flags_cli.py drift resume webapp-prod")

if __name__ == '__main__':
    print("🚩 Feature Flags - Exemplos de Uso\n")
    
    example_basic_usage()
    example_drift_integration()
    example_enhanced_drift_detection()
    example_feature_management()
    example_cli_usage()
    
    print("\n✅ Todos os exemplos executados com sucesso!")
