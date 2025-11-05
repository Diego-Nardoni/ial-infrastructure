#!/usr/bin/env python3
"""
Observability Engine - Sistema de Monitoramento Completo
CloudWatch integration, custom metrics, dashboards e alertas
"""

import boto3
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import time

class ObservabilityEngine:
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        
        # AWS clients
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.logs = boto3.client('logs', region_name=region)
        
        # Namespace para métricas customizadas
        self.namespace = 'IAL/StateManagement'
        
        # Log group para auditoria
        self.log_group = '/ial/state-management'
        
        # Inicializar log group
        self._ensure_log_group_exists()
    
    def _ensure_log_group_exists(self):
        """Garante que o log group existe"""
        try:
            self.logs.describe_log_groups(logGroupNamePrefix=self.log_group)
        except Exception:
            try:
                self.logs.create_log_group(
                    logGroupName=self.log_group,
                    tags={
                        'Project': 'IAL',
                        'Component': 'StateManagement',
                        'Environment': 'Production'
                    }
                )
                print(f"✅ Log group criado: {self.log_group}")
            except Exception as e:
                print(f"⚠️ Erro ao criar log group: {e}")
    
    def publish_metric(self, metric_name: str, value: float, unit: str = 'Count', 
                      dimensions: Optional[Dict[str, str]] = None) -> bool:
        """Publica métrica customizada no CloudWatch"""
        try:
            metric_data = {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit,
                'Timestamp': datetime.utcnow()
            }
            
            if dimensions:
                metric_data['Dimensions'] = [
                    {'Name': k, 'Value': v} for k, v in dimensions.items()
                ]
            
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=[metric_data]
            )
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao publicar métrica {metric_name}: {e}")
            return False
    
    def log_audit_event(self, event_type: str, details: Dict, level: str = 'INFO') -> bool:
        """Registra evento de auditoria"""
        try:
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'level': level,
                'event_type': event_type,
                'details': details,
                'source': 'ial_state_management'
            }
            
            # Criar log stream se necessário
            log_stream = f"state-events-{datetime.utcnow().strftime('%Y-%m-%d')}"
            
            try:
                self.logs.create_log_stream(
                    logGroupName=self.log_group,
                    logStreamName=log_stream
                )
            except self.logs.exceptions.ResourceAlreadyExistsException:
                pass  # Log stream já existe
            
            # Enviar log
            self.logs.put_log_events(
                logGroupName=self.log_group,
                logStreamName=log_stream,
                logEvents=[{
                    'timestamp': int(time.time() * 1000),
                    'message': json.dumps(log_entry, ensure_ascii=False)
                }]
            )
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao registrar evento de auditoria: {e}")
            return False
    
    def track_desired_state_generation(self, spec_metadata: Dict) -> bool:
        """Rastreia geração de desired state"""
        try:
            # Métricas
            self.publish_metric('DesiredStateGenerated', 1)
            self.publish_metric('TotalResources', spec_metadata.get('total_resources', 0))
            self.publish_metric('TotalDomains', spec_metadata.get('total_domains', 0))
            
            # Auditoria
            self.log_audit_event('desired_state_generated', {
                'spec_version': spec_metadata.get('version'),
                'spec_hash': spec_metadata.get('spec_hash'),
                'total_resources': spec_metadata.get('total_resources'),
                'total_domains': spec_metadata.get('total_domains')
            })
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao rastrear geração de desired state: {e}")
            return False
    
    def track_resource_catalog_operation(self, operation: str, resource_count: int, 
                                       success: bool, duration_ms: float) -> bool:
        """Rastreia operações do catálogo de recursos"""
        try:
            # Métricas de performance
            self.publish_metric(f'CatalogOperation_{operation}', 1, 
                              dimensions={'Success': str(success)})
            self.publish_metric(f'CatalogOperation_{operation}_Duration', duration_ms, 'Milliseconds')
            self.publish_metric(f'CatalogOperation_{operation}_ResourceCount', resource_count)
            
            # Auditoria
            self.log_audit_event('catalog_operation', {
                'operation': operation,
                'resource_count': resource_count,
                'success': success,
                'duration_ms': duration_ms
            }, level='INFO' if success else 'ERROR')
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao rastrear operação do catálogo: {e}")
            return False
    
    def track_drift_detection(self, drift_results: List[Dict]) -> bool:
        """Rastreia detecção de drift"""
        try:
            total_drifts = len(drift_results)
            critical_drifts = len([d for d in drift_results if d.get('severity') == 'critical'])
            warning_drifts = len([d for d in drift_results if d.get('severity') == 'warning'])
            
            # Métricas
            self.publish_metric('DriftDetectionRun', 1)
            self.publish_metric('TotalDrifts', total_drifts)
            self.publish_metric('CriticalDrifts', critical_drifts)
            self.publish_metric('WarningDrifts', warning_drifts)
            
            # Métricas por tipo de drift
            drift_types = {}
            for drift in drift_results:
                drift_type = drift.get('drift_type', 'unknown')
                drift_types[drift_type] = drift_types.get(drift_type, 0) + 1
            
            for drift_type, count in drift_types.items():
                self.publish_metric(f'DriftType_{drift_type}', count)
            
            # Auditoria
            self.log_audit_event('drift_detection', {
                'total_drifts': total_drifts,
                'critical_drifts': critical_drifts,
                'warning_drifts': warning_drifts,
                'drift_types': drift_types
            }, level='WARN' if critical_drifts > 0 else 'INFO')
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao rastrear detecção de drift: {e}")
            return False
    
    def track_reconciliation(self, remediation_plan: Dict, execution_result: Optional[Dict] = None) -> bool:
        """Rastreia reconciliação"""
        try:
            immediate_actions = len(remediation_plan['phases']['immediate'])
            scheduled_actions = len(remediation_plan['phases']['scheduled'])
            manual_actions = len(remediation_plan['phases']['manual'])
            
            # Métricas do plano
            self.publish_metric('ReconciliationPlanGenerated', 1)
            self.publish_metric('ImmediateActions', immediate_actions)
            self.publish_metric('ScheduledActions', scheduled_actions)
            self.publish_metric('ManualActions', manual_actions)
            
            # Métricas de execução se disponível
            if execution_result:
                success_rate = execution_result.get('success_rate', 0)
                total_actions = execution_result.get('total_actions', 0)
                
                self.publish_metric('ReconciliationExecuted', 1)
                self.publish_metric('ReconciliationSuccessRate', success_rate, 'Percent')
                self.publish_metric('ReconciliationActionsExecuted', total_actions)
            
            # Auditoria
            audit_details = {
                'immediate_actions': immediate_actions,
                'scheduled_actions': scheduled_actions,
                'manual_actions': manual_actions,
                'risk_assessment': remediation_plan.get('risk_assessment')
            }
            
            if execution_result:
                audit_details.update({
                    'execution_success_rate': execution_result.get('success_rate'),
                    'execution_dry_run': execution_result.get('dry_run'),
                    'execution_errors': len(execution_result.get('errors', []))
                })
            
            self.log_audit_event('reconciliation', audit_details)
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao rastrear reconciliação: {e}")
            return False
    
    def track_validation(self, validation_result: Dict) -> bool:
        """Rastreia validação"""
        try:
            validation_passed = validation_result.get('validation_passed', False)
            total_errors = validation_result.get('statistics', {}).get('total_errors', 0)
            total_warnings = validation_result.get('statistics', {}).get('total_warnings', 0)
            validation_score = validation_result.get('statistics', {}).get('validation_score', 0)
            
            # Métricas
            self.publish_metric('ValidationRun', 1)
            self.publish_metric('ValidationPassed', 1 if validation_passed else 0)
            self.publish_metric('ValidationErrors', total_errors)
            self.publish_metric('ValidationWarnings', total_warnings)
            self.publish_metric('ValidationScore', validation_score, 'Percent')
            
            # Auditoria
            self.log_audit_event('validation', {
                'validation_passed': validation_passed,
                'total_errors': total_errors,
                'total_warnings': total_warnings,
                'validation_score': validation_score,
                'total_resources': validation_result.get('total_resources', 0)
            }, level='ERROR' if not validation_passed else 'INFO')
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao rastrear validação: {e}")
            return False
    
    def create_dashboard(self, dashboard_name: str = 'IAL-StateManagement') -> bool:
        """Cria dashboard do CloudWatch"""
        try:
            dashboard_body = {
                "widgets": [
                    {
                        "type": "metric",
                        "x": 0, "y": 0, "width": 12, "height": 6,
                        "properties": {
                            "metrics": [
                                [self.namespace, "DesiredStateGenerated"],
                                [self.namespace, "DriftDetectionRun"],
                                [self.namespace, "ValidationRun"],
                                [self.namespace, "ReconciliationPlanGenerated"]
                            ],
                            "period": 300,
                            "stat": "Sum",
                            "region": self.region,
                            "title": "IAL Operations Overview"
                        }
                    },
                    {
                        "type": "metric",
                        "x": 12, "y": 0, "width": 12, "height": 6,
                        "properties": {
                            "metrics": [
                                [self.namespace, "TotalDrifts"],
                                [self.namespace, "CriticalDrifts"],
                                [self.namespace, "WarningDrifts"]
                            ],
                            "period": 300,
                            "stat": "Average",
                            "region": self.region,
                            "title": "Drift Detection Metrics"
                        }
                    },
                    {
                        "type": "metric",
                        "x": 0, "y": 6, "width": 12, "height": 6,
                        "properties": {
                            "metrics": [
                                [self.namespace, "ValidationScore"],
                                [self.namespace, "ReconciliationSuccessRate"]
                            ],
                            "period": 300,
                            "stat": "Average",
                            "region": self.region,
                            "title": "Quality Metrics",
                            "yAxis": {"left": {"min": 0, "max": 100}}
                        }
                    },
                    {
                        "type": "log",
                        "x": 12, "y": 6, "width": 12, "height": 6,
                        "properties": {
                            "query": f"SOURCE '{self.log_group}'\n| fields @timestamp, event_type, level\n| filter level = \"ERROR\"\n| sort @timestamp desc\n| limit 20",
                            "region": self.region,
                            "title": "Recent Errors",
                            "view": "table"
                        }
                    }
                ]
            }
            
            self.cloudwatch.put_dashboard(
                DashboardName=dashboard_name,
                DashboardBody=json.dumps(dashboard_body)
            )
            
            print(f"✅ Dashboard criado: {dashboard_name}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao criar dashboard: {e}")
            return False
    
    def create_alarms(self) -> List[str]:
        """Cria alarmes do CloudWatch"""
        alarms_created = []
        
        alarm_configs = [
            {
                'AlarmName': 'IAL-CriticalDrifts-High',
                'MetricName': 'CriticalDrifts',
                'Threshold': 5,
                'ComparisonOperator': 'GreaterThanThreshold',
                'AlarmDescription': 'Muitos drifts críticos detectados'
            },
            {
                'AlarmName': 'IAL-ValidationScore-Low',
                'MetricName': 'ValidationScore',
                'Threshold': 80,
                'ComparisonOperator': 'LessThanThreshold',
                'AlarmDescription': 'Score de validação baixo'
            },
            {
                'AlarmName': 'IAL-ReconciliationFailure',
                'MetricName': 'ReconciliationSuccessRate',
                'Threshold': 90,
                'ComparisonOperator': 'LessThanThreshold',
                'AlarmDescription': 'Taxa de sucesso de reconciliação baixa'
            }
        ]
        
        for config in alarm_configs:
            try:
                self.cloudwatch.put_metric_alarm(
                    AlarmName=config['AlarmName'],
                    ComparisonOperator=config['ComparisonOperator'],
                    EvaluationPeriods=2,
                    MetricName=config['MetricName'],
                    Namespace=self.namespace,
                    Period=300,
                    Statistic='Average',
                    Threshold=config['Threshold'],
                    ActionsEnabled=True,
                    AlarmDescription=config['AlarmDescription'],
                    Unit='Count' if 'Score' not in config['MetricName'] else 'Percent'
                )
                
                alarms_created.append(config['AlarmName'])
                print(f"✅ Alarme criado: {config['AlarmName']}")
                
            except Exception as e:
                print(f"❌ Erro ao criar alarme {config['AlarmName']}: {e}")
        
        return alarms_created
    
    def get_metrics_summary(self, hours: int = 24) -> Dict:
        """Recupera resumo de métricas das últimas horas"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            metrics_to_query = [
                'DesiredStateGenerated', 'DriftDetectionRun', 'ValidationRun',
                'TotalDrifts', 'CriticalDrifts', 'ValidationScore'
            ]
            
            summary = {
                'period': f'Last {hours} hours',
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'metrics': {}
            }
            
            for metric_name in metrics_to_query:
                try:
                    response = self.cloudwatch.get_metric_statistics(
                        Namespace=self.namespace,
                        MetricName=metric_name,
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=3600,  # 1 hora
                        Statistics=['Sum', 'Average', 'Maximum']
                    )
                    
                    datapoints = response.get('Datapoints', [])
                    if datapoints:
                        latest = max(datapoints, key=lambda x: x['Timestamp'])
                        summary['metrics'][metric_name] = {
                            'latest_value': latest.get('Sum', latest.get('Average', 0)),
                            'timestamp': latest['Timestamp'].isoformat(),
                            'datapoints_count': len(datapoints)
                        }
                    else:
                        summary['metrics'][metric_name] = {
                            'latest_value': 0,
                            'timestamp': None,
                            'datapoints_count': 0
                        }
                        
                except Exception as e:
                    print(f"⚠️ Erro ao recuperar métrica {metric_name}: {e}")
                    summary['metrics'][metric_name] = {'error': str(e)}
            
            return summary
            
        except Exception as e:
            print(f"❌ Erro ao recuperar resumo de métricas: {e}")
            return {'error': str(e)}
    
    def get_recent_audit_logs(self, hours: int = 24, limit: int = 100) -> List[Dict]:
        """Recupera logs de auditoria recentes"""
        try:
            end_time = int(time.time() * 1000)
            start_time = int((time.time() - (hours * 3600)) * 1000)
            
            query = f"""
            fields @timestamp, event_type, level, details
            | filter @timestamp >= {start_time} and @timestamp <= {end_time}
            | sort @timestamp desc
            | limit {limit}
            """
            
            # Iniciar query
            response = self.logs.start_query(
                logGroupName=self.log_group,
                startTime=start_time,
                endTime=end_time,
                queryString=query
            )
            
            query_id = response['queryId']
            
            # Aguardar conclusão da query
            max_attempts = 30
            for _ in range(max_attempts):
                result = self.logs.get_query_results(queryId=query_id)
                
                if result['status'] == 'Complete':
                    # Processar resultados
                    logs = []
                    for result_row in result.get('results', []):
                        log_entry = {}
                        for field in result_row:
                            log_entry[field['field']] = field['value']
                        logs.append(log_entry)
                    
                    return logs
                
                elif result['status'] == 'Failed':
                    print(f"❌ Query de logs falhou: {result.get('statistics', {})}")
                    return []
                
                time.sleep(1)
            
            print("⚠️ Timeout na query de logs")
            return []
            
        except Exception as e:
            print(f"❌ Erro ao recuperar logs de auditoria: {e}")
            return []
    
    def generate_observability_report(self) -> Dict:
        """Gera relatório completo de observabilidade"""
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'report_version': '3.1',
            'metrics_summary': self.get_metrics_summary(24),
            'recent_audit_logs': self.get_recent_audit_logs(24, 50),
            'system_health': 'unknown'
        }
        
        try:
            # Avaliar saúde do sistema baseado nas métricas
            metrics = report['metrics_summary'].get('metrics', {})
            
            critical_drifts = metrics.get('CriticalDrifts', {}).get('latest_value', 0)
            validation_score = metrics.get('ValidationScore', {}).get('latest_value', 100)
            
            if critical_drifts > 5:
                report['system_health'] = 'critical'
            elif critical_drifts > 0 or validation_score < 80:
                report['system_health'] = 'warning'
            else:
                report['system_health'] = 'healthy'
            
            # Adicionar recomendações
            report['recommendations'] = []
            
            if critical_drifts > 0:
                report['recommendations'].append(f"🚨 {critical_drifts} drift(s) crítico(s) detectado(s). Ação imediata necessária.")
            
            if validation_score < 90:
                report['recommendations'].append(f"📊 Score de validação baixo ({validation_score}%). Revisar configurações.")
            
            if not report['recommendations']:
                report['recommendations'].append("✅ Sistema operando normalmente.")
            
        except Exception as e:
            report['error'] = f"Erro ao avaliar saúde do sistema: {e}"
        
        return report

def main():
    """Função principal para testes"""
    print("📊 IAL Observability Engine v3.1")
    print("=" * 50)
    
    obs = ObservabilityEngine()
    
    # Teste de métricas
    print("📈 Testando publicação de métricas...")
    obs.publish_metric('TestMetric', 42, 'Count', {'TestDimension': 'TestValue'})
    
    # Teste de auditoria
    print("📝 Testando log de auditoria...")
    obs.log_audit_event('test_event', {'test_key': 'test_value'})
    
    # Criar dashboard
    print("📊 Criando dashboard...")
    obs.create_dashboard('IAL-Test-Dashboard')
    
    # Criar alarmes
    print("🚨 Criando alarmes...")
    alarms = obs.create_alarms()
    print(f"✅ {len(alarms)} alarmes criados")
    
    # Gerar relatório
    print("📄 Gerando relatório de observabilidade...")
    report = obs.generate_observability_report()
    print(f"📊 Saúde do sistema: {report['system_health']}")
    
    return 0

if __name__ == "__main__":
    exit(main())
