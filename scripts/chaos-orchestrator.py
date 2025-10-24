#!/usr/bin/env python3
"""
IaL Chaos Engineering Orchestrator
Advanced chaos experiment orchestration and analysis
"""

import boto3
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import concurrent.futures
import statistics

class ChaosOrchestrator:
    def __init__(self, project_name: str = 'ial', environment: str = 'dev'):
        self.project_name = project_name
        self.environment = environment
        
        # AWS clients
        self.fis_client = boto3.client('fis')
        self.cloudwatch = boto3.client('cloudwatch')
        self.elbv2 = boto3.client('elbv2')
        self.ecs = boto3.client('ecs')
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def analyze_system_health(self) -> Dict:
        """Comprehensive system health analysis"""
        health_metrics = {
            'timestamp': datetime.now().isoformat(),
            'overall_health': 'unknown',
            'components': {},
            'recommendations': []
        }
        
        try:
            # Check ALB health
            alb_health = self._check_alb_health()
            health_metrics['components']['alb'] = alb_health
            
            # Check ECS health
            ecs_health = self._check_ecs_health()
            health_metrics['components']['ecs'] = ecs_health
            
            # Check CloudWatch metrics
            metrics_health = self._check_metrics_health()
            health_metrics['components']['metrics'] = metrics_health
            
            # Calculate overall health
            component_scores = [comp.get('score', 0) for comp in health_metrics['components'].values()]
            overall_score = statistics.mean(component_scores) if component_scores else 0
            
            if overall_score >= 0.9:
                health_metrics['overall_health'] = 'excellent'
            elif overall_score >= 0.7:
                health_metrics['overall_health'] = 'good'
            elif overall_score >= 0.5:
                health_metrics['overall_health'] = 'fair'
            else:
                health_metrics['overall_health'] = 'poor'
            
            # Generate recommendations
            health_metrics['recommendations'] = self._generate_health_recommendations(health_metrics)
            
        except Exception as e:
            self.logger.error(f"Health analysis failed: {e}")
            health_metrics['overall_health'] = 'error'
            health_metrics['error'] = str(e)
        
        return health_metrics

    def _check_alb_health(self) -> Dict:
        """Check Application Load Balancer health"""
        try:
            # Get target groups
            response = self.elbv2.describe_target_groups()
            target_groups = response.get('TargetGroups', [])
            
            if not target_groups:
                return {'status': 'no_targets', 'score': 0.0}
            
            healthy_targets = 0
            total_targets = 0
            
            for tg in target_groups:
                if self.project_name in tg.get('TargetGroupName', ''):
                    health_response = self.elbv2.describe_target_health(
                        TargetGroupArn=tg['TargetGroupArn']
                    )
                    
                    for target in health_response.get('TargetHealthDescriptions', []):
                        total_targets += 1
                        if target.get('TargetHealth', {}).get('State') == 'healthy':
                            healthy_targets += 1
            
            if total_targets == 0:
                return {'status': 'no_targets', 'score': 0.0}
            
            health_ratio = healthy_targets / total_targets
            
            return {
                'status': 'healthy' if health_ratio >= 0.8 else 'degraded',
                'healthy_targets': healthy_targets,
                'total_targets': total_targets,
                'health_ratio': health_ratio,
                'score': health_ratio
            }
            
        except Exception as e:
            self.logger.error(f"ALB health check failed: {e}")
            return {'status': 'error', 'error': str(e), 'score': 0.0}

    def _check_ecs_health(self) -> Dict:
        """Check ECS service health"""
        try:
            # List ECS clusters
            clusters_response = self.ecs.list_clusters()
            clusters = [c for c in clusters_response.get('clusterArns', []) 
                       if self.project_name in c]
            
            if not clusters:
                return {'status': 'no_clusters', 'score': 0.0}
            
            total_services = 0
            healthy_services = 0
            
            for cluster_arn in clusters:
                services_response = self.ecs.list_services(cluster=cluster_arn)
                service_arns = services_response.get('serviceArns', [])
                
                if service_arns:
                    services_detail = self.ecs.describe_services(
                        cluster=cluster_arn,
                        services=service_arns
                    )
                    
                    for service in services_detail.get('services', []):
                        total_services += 1
                        running_count = service.get('runningCount', 0)
                        desired_count = service.get('desiredCount', 0)
                        
                        if running_count >= desired_count and desired_count > 0:
                            healthy_services += 1
            
            if total_services == 0:
                return {'status': 'no_services', 'score': 0.0}
            
            health_ratio = healthy_services / total_services
            
            return {
                'status': 'healthy' if health_ratio >= 0.8 else 'degraded',
                'healthy_services': healthy_services,
                'total_services': total_services,
                'health_ratio': health_ratio,
                'score': health_ratio
            }
            
        except Exception as e:
            self.logger.error(f"ECS health check failed: {e}")
            return {'status': 'error', 'error': str(e), 'score': 0.0}

    def _check_metrics_health(self) -> Dict:
        """Check CloudWatch metrics health"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=10)
            
            # Check for recent metric data
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/ApplicationELB',
                MetricName='RequestCount',
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Sum']
            )
            
            datapoints = response.get('Datapoints', [])
            
            if not datapoints:
                return {'status': 'no_data', 'score': 0.5}
            
            # Check if metrics are recent
            latest_datapoint = max(datapoints, key=lambda x: x['Timestamp'])
            time_diff = (end_time - latest_datapoint['Timestamp'].replace(tzinfo=None)).total_seconds()
            
            if time_diff > 600:  # More than 10 minutes old
                return {'status': 'stale_data', 'score': 0.3}
            
            return {
                'status': 'healthy',
                'latest_timestamp': latest_datapoint['Timestamp'].isoformat(),
                'datapoints_count': len(datapoints),
                'score': 1.0
            }
            
        except Exception as e:
            self.logger.error(f"Metrics health check failed: {e}")
            return {'status': 'error', 'error': str(e), 'score': 0.0}

    def _generate_health_recommendations(self, health_metrics: Dict) -> List[str]:
        """Generate health improvement recommendations"""
        recommendations = []
        
        # ALB recommendations
        alb_health = health_metrics['components'].get('alb', {})
        if alb_health.get('score', 0) < 0.8:
            recommendations.append("Consider scaling up ALB targets or investigating unhealthy instances")
        
        # ECS recommendations
        ecs_health = health_metrics['components'].get('ecs', {})
        if ecs_health.get('score', 0) < 0.8:
            recommendations.append("Review ECS service configurations and task health")
        
        # Metrics recommendations
        metrics_health = health_metrics['components'].get('metrics', {})
        if metrics_health.get('score', 0) < 0.8:
            recommendations.append("Check CloudWatch metrics collection and data freshness")
        
        # Overall recommendations
        overall_score = statistics.mean([comp.get('score', 0) for comp in health_metrics['components'].values()])
        if overall_score < 0.7:
            recommendations.append("System health is below optimal - consider postponing chaos experiments")
        
        return recommendations

    def intelligent_chaos_scheduling(self) -> Dict:
        """Intelligently schedule chaos experiments based on system health"""
        schedule = {
            'timestamp': datetime.now().isoformat(),
            'recommended_experiments': [],
            'postponed_experiments': [],
            'system_readiness': 'unknown'
        }
        
        # Analyze current system health
        health_analysis = self.analyze_system_health()
        overall_health = health_analysis.get('overall_health', 'unknown')
        
        # Define experiment risk levels
        experiments = [
            {'name': 'network-latency', 'risk': 'low', 'duration': 5},
            {'name': 'ecs-task-termination', 'risk': 'medium', 'duration': 3},
            {'name': 'instance-termination', 'risk': 'high', 'duration': 10}
        ]
        
        # Schedule based on health
        if overall_health in ['excellent', 'good']:
            schedule['system_readiness'] = 'ready'
            schedule['recommended_experiments'] = experiments
        elif overall_health == 'fair':
            schedule['system_readiness'] = 'limited'
            schedule['recommended_experiments'] = [exp for exp in experiments if exp['risk'] in ['low', 'medium']]
            schedule['postponed_experiments'] = [exp for exp in experiments if exp['risk'] == 'high']
        else:
            schedule['system_readiness'] = 'not_ready'
            schedule['postponed_experiments'] = experiments
        
        schedule['health_analysis'] = health_analysis
        return schedule

    def execute_intelligent_chaos_suite(self) -> Dict:
        """Execute chaos suite with intelligent scheduling"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'scheduling_analysis': {},
            'executed_experiments': [],
            'postponed_experiments': [],
            'summary': {'total': 0, 'executed': 0, 'postponed': 0, 'successful': 0, 'failed': 0}
        }
        
        # Get intelligent scheduling
        scheduling = self.intelligent_chaos_scheduling()
        results['scheduling_analysis'] = scheduling
        
        if scheduling['system_readiness'] == 'not_ready':
            self.logger.warning("System not ready for chaos experiments - postponing all tests")
            results['postponed_experiments'] = scheduling['postponed_experiments']
            results['summary']['postponed'] = len(scheduling['postponed_experiments'])
            return results
        
        # Execute recommended experiments
        for experiment in scheduling['recommended_experiments']:
            self.logger.info(f"Executing {experiment['name']} experiment")
            
            # Execute experiment (simplified for this implementation)
            experiment_result = {
                'name': experiment['name'],
                'risk_level': experiment['risk'],
                'duration': experiment['duration'],
                'status': 'simulated_success',  # In real implementation, call actual FIS
                'execution_time': datetime.now().isoformat()
            }
            
            results['executed_experiments'].append(experiment_result)
            results['summary']['executed'] += 1
            results['summary']['successful'] += 1
            
            # Wait between experiments
            time.sleep(30)
        
        # Add postponed experiments
        results['postponed_experiments'] = scheduling.get('postponed_experiments', [])
        results['summary']['postponed'] = len(results['postponed_experiments'])
        results['summary']['total'] = results['summary']['executed'] + results['summary']['postponed']
        
        return results

    def generate_resilience_report(self) -> Dict:
        """Generate comprehensive resilience report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'system_health': {},
            'chaos_readiness': {},
            'resilience_score': 0.0,
            'recommendations': [],
            'next_actions': []
        }
        
        # System health analysis
        report['system_health'] = self.analyze_system_health()
        
        # Chaos readiness analysis
        report['chaos_readiness'] = self.intelligent_chaos_scheduling()
        
        # Calculate resilience score
        health_score = statistics.mean([
            comp.get('score', 0) for comp in report['system_health']['components'].values()
        ])
        
        readiness_score = 1.0 if report['chaos_readiness']['system_readiness'] == 'ready' else 0.5
        
        report['resilience_score'] = (health_score + readiness_score) / 2
        
        # Generate recommendations
        if report['resilience_score'] >= 0.9:
            report['recommendations'].append("System shows excellent resilience - ready for advanced chaos testing")
        elif report['resilience_score'] >= 0.7:
            report['recommendations'].append("System resilience is good - continue regular chaos testing")
        else:
            report['recommendations'].append("System resilience needs improvement - focus on stability first")
        
        # Next actions
        if report['chaos_readiness']['system_readiness'] == 'ready':
            report['next_actions'].append("Execute full chaos engineering suite")
        elif report['chaos_readiness']['system_readiness'] == 'limited':
            report['next_actions'].append("Execute low-risk chaos experiments only")
        else:
            report['next_actions'].append("Improve system health before chaos testing")
        
        return report

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='IaL Chaos Engineering Orchestrator')
    parser.add_argument('--action', choices=['health', 'schedule', 'execute', 'report'], 
                       required=True, help='Action to perform')
    parser.add_argument('--project', default='ial', help='Project name')
    parser.add_argument('--environment', default='dev', help='Environment')
    
    args = parser.parse_args()
    
    orchestrator = ChaosOrchestrator(args.project, args.environment)
    
    if args.action == 'health':
        result = orchestrator.analyze_system_health()
        print(json.dumps(result, indent=2, default=str))
    
    elif args.action == 'schedule':
        result = orchestrator.intelligent_chaos_scheduling()
        print(json.dumps(result, indent=2, default=str))
    
    elif args.action == 'execute':
        result = orchestrator.execute_intelligent_chaos_suite()
        print(json.dumps(result, indent=2, default=str))
    
    elif args.action == 'report':
        result = orchestrator.generate_resilience_report()
        print(json.dumps(result, indent=2, default=str))
