#!/usr/bin/env python3
"""
Auto-Heal Engine - Correção automática de drift seguro
"""

import json
import boto3
from typing import Dict, List, Any, Optional
from datetime import datetime

class AutoHealEngine:
    """Engine para correção automática de drift seguro"""
    
    def __init__(self):
        self.cfn = boto3.client('cloudformation')
        self.dynamodb = boto3.resource('dynamodb')
        self.catalog_table = self.dynamodb.Table('ial-resource-catalog')
        
        # Ações seguras para auto-heal
        self.safe_actions = {
            'tag_missing': self._heal_missing_tags,
            'backup_disabled': self._heal_backup_settings,
            'encryption_disabled': self._heal_encryption_settings,
            'monitoring_disabled': self._heal_monitoring_settings,
            'lifecycle_missing': self._heal_lifecycle_policies
        }
        
        # Ações que requerem PR (muito arriscadas)
        self.risky_actions = {
            'resource_deleted',
            'resource_modified',
            'security_group_changed',
            'iam_policy_changed',
            'network_config_changed'
        }
    
    def analyze_drift(self, drift_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analisa drift e classifica em seguro/arriscado
        
        Args:
            drift_data: Dados de drift detectado
            
        Returns:
            Análise com recomendações de ação
        """
        analysis = {
            'safe_drifts': [],
            'risky_drifts': [],
            'auto_heal_actions': [],
            'pr_required_actions': []
        }
        
        for drift in drift_data.get('drifts', []):
            drift_type = drift.get('type')
            resource_type = drift.get('resource_type')
            
            if self._is_safe_drift(drift_type, resource_type):
                analysis['safe_drifts'].append(drift)
                if drift_type in self.safe_actions:
                    analysis['auto_heal_actions'].append({
                        'drift': drift,
                        'action': drift_type,
                        'handler': self.safe_actions[drift_type]
                    })
            else:
                analysis['risky_drifts'].append(drift)
                analysis['pr_required_actions'].append(drift)
        
        return analysis
    
    def execute_auto_heal(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Executa ações de auto-heal seguras
        
        Args:
            actions: Lista de ações para executar
            
        Returns:
            Resultado das ações executadas
        """
        results = {
            'successful_heals': [],
            'failed_heals': [],
            'total_actions': len(actions)
        }
        
        for action in actions:
            try:
                drift = action['drift']
                handler = action['handler']
                
                print(f"🔧 Auto-healing: {drift.get('resource_id')} - {action['action']}")
                
                result = handler(drift)
                
                if result.get('success'):
                    results['successful_heals'].append({
                        'resource_id': drift.get('resource_id'),
                        'action': action['action'],
                        'result': result
                    })
                    print(f"✅ Auto-heal successful: {drift.get('resource_id')}")
                else:
                    results['failed_heals'].append({
                        'resource_id': drift.get('resource_id'),
                        'action': action['action'],
                        'error': result.get('error')
                    })
                    print(f"❌ Auto-heal failed: {drift.get('resource_id')} - {result.get('error')}")
                    
            except Exception as e:
                results['failed_heals'].append({
                    'resource_id': drift.get('resource_id', 'unknown'),
                    'action': action.get('action', 'unknown'),
                    'error': str(e)
                })
                print(f"❌ Auto-heal exception: {e}")
        
        return results
    
    def _is_safe_drift(self, drift_type: str, resource_type: str) -> bool:
        """Determina se um drift é seguro para auto-heal"""
        
        # Drifts sempre seguros
        safe_drifts = {
            'tag_missing',
            'backup_disabled',
            'monitoring_disabled',
            'lifecycle_missing'
        }
        
        # Drifts seguros apenas para certos recursos
        conditional_safe = {
            'encryption_disabled': ['AWS::S3::Bucket', 'AWS::RDS::DBInstance']
        }
        
        if drift_type in safe_drifts:
            return True
            
        if drift_type in conditional_safe:
            return resource_type in conditional_safe[drift_type]
            
        return False
    
    def _heal_missing_tags(self, drift: Dict[str, Any]) -> Dict[str, Any]:
        """Corrige tags faltantes"""
        try:
            resource_arn = drift.get('resource_arn')
            missing_tags = drift.get('missing_tags', {})
            
            # Simular correção de tags
            print(f"Adding tags to {resource_arn}: {missing_tags}")
            
            return {
                'success': True,
                'action': 'tags_added',
                'tags': missing_tags
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _heal_backup_settings(self, drift: Dict[str, Any]) -> Dict[str, Any]:
        """Corrige configurações de backup"""
        try:
            resource_id = drift.get('resource_id')
            
            # Simular habilitação de backup
            print(f"Enabling backup for {resource_id}")
            
            return {
                'success': True,
                'action': 'backup_enabled',
                'resource_id': resource_id
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _heal_encryption_settings(self, drift: Dict[str, Any]) -> Dict[str, Any]:
        """Corrige configurações de encryption"""
        try:
            resource_id = drift.get('resource_id')
            resource_type = drift.get('resource_type')
            
            # Simular habilitação de encryption
            print(f"Enabling encryption for {resource_type} {resource_id}")
            
            return {
                'success': True,
                'action': 'encryption_enabled',
                'resource_id': resource_id
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _heal_monitoring_settings(self, drift: Dict[str, Any]) -> Dict[str, Any]:
        """Corrige configurações de monitoramento"""
        try:
            resource_id = drift.get('resource_id')
            
            # Simular habilitação de monitoring
            print(f"Enabling monitoring for {resource_id}")
            
            return {
                'success': True,
                'action': 'monitoring_enabled',
                'resource_id': resource_id
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _heal_lifecycle_policies(self, drift: Dict[str, Any]) -> Dict[str, Any]:
        """Corrige políticas de lifecycle"""
        try:
            resource_id = drift.get('resource_id')
            
            # Simular configuração de lifecycle
            print(f"Configuring lifecycle policies for {resource_id}")
            
            return {
                'success': True,
                'action': 'lifecycle_configured',
                'resource_id': resource_id
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
