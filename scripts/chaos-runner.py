#!/usr/bin/env python3
"""
IaL Chaos Engineering Runner
Automated chaos experiments execution and monitoring
"""

import boto3
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

class ChaosRunner:
    def __init__(self, project_name: str = 'ial', environment: str = 'dev'):
        self.project_name = project_name
        self.environment = environment
        self.fis_client = boto3.client('fis')
        self.cloudwatch = boto3.client('cloudwatch')
        self.sns = boto3.client('sns')
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def list_experiment_templates(self) -> List[Dict]:
        """List all FIS experiment templates for the project"""
        try:
            response = self.fis_client.list_experiment_templates()
            templates = []
            
            for template in response.get('experimentTemplates', []):
                if self.project_name in template.get('id', ''):
                    templates.append(template)
            
            return templates
        except Exception as e:
            self.logger.error(f"Error listing experiment templates: {e}")
            return []

    def start_experiment(self, template_id: str, tags: Dict = None) -> Optional[str]:
        """Start a chaos experiment"""
        try:
            experiment_tags = {
                'Project': self.project_name,
                'Environment': self.environment,
                'StartedBy': 'chaos-runner',
                'StartTime': datetime.now().isoformat()
            }
            
            if tags:
                experiment_tags.update(tags)
            
            response = self.fis_client.start_experiment(
                experimentTemplateId=template_id,
                tags=experiment_tags
            )
            
            experiment_id = response['experiment']['id']
            self.logger.info(f"Started experiment {experiment_id} from template {template_id}")
            
            # Send notification
            self._send_notification(
                f"Chaos Experiment Started",
                f"Experiment ID: {experiment_id}\nTemplate: {template_id}\nTime: {datetime.now()}"
            )
            
            return experiment_id
            
        except Exception as e:
            self.logger.error(f"Error starting experiment: {e}")
            return None

    def get_experiment_status(self, experiment_id: str) -> Dict:
        """Get the status of a running experiment"""
        try:
            response = self.fis_client.get_experiment(id=experiment_id)
            return response['experiment']
        except Exception as e:
            self.logger.error(f"Error getting experiment status: {e}")
            return {}

    def stop_experiment(self, experiment_id: str) -> bool:
        """Stop a running experiment"""
        try:
            self.fis_client.stop_experiment(id=experiment_id)
            self.logger.info(f"Stopped experiment {experiment_id}")
            
            self._send_notification(
                f"Chaos Experiment Stopped",
                f"Experiment ID: {experiment_id}\nStopped at: {datetime.now()}"
            )
            
            return True
        except Exception as e:
            self.logger.error(f"Error stopping experiment: {e}")
            return False

    def monitor_experiment(self, experiment_id: str, timeout_minutes: int = 30) -> Dict:
        """Monitor experiment until completion"""
        start_time = datetime.now()
        timeout = timedelta(minutes=timeout_minutes)
        
        while datetime.now() - start_time < timeout:
            status = self.get_experiment_status(experiment_id)
            state = status.get('state', {}).get('status', 'unknown')
            
            self.logger.info(f"Experiment {experiment_id} status: {state}")
            
            if state in ['completed', 'stopped', 'failed']:
                return status
            
            time.sleep(30)  # Check every 30 seconds
        
        # Timeout reached
        self.logger.warning(f"Experiment {experiment_id} monitoring timeout")
        self.stop_experiment(experiment_id)
        return self.get_experiment_status(experiment_id)

    def run_weekly_chaos_suite(self) -> Dict:
        """Run the weekly chaos engineering suite"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'experiments': [],
            'summary': {'total': 0, 'successful': 0, 'failed': 0}
        }
        
        # Define weekly experiment schedule
        experiments = [
            {'name': 'network-latency', 'duration': 5},
            {'name': 'instance-termination', 'duration': 10},
            {'name': 'ecs-task-termination', 'duration': 3}
        ]
        
        for exp in experiments:
            template_id = f"{self.project_name}-{exp['name']}"
            
            self.logger.info(f"Starting {exp['name']} experiment")
            experiment_id = self.start_experiment(template_id)
            
            if experiment_id:
                # Monitor experiment
                final_status = self.monitor_experiment(experiment_id, exp['duration'] + 5)
                
                experiment_result = {
                    'name': exp['name'],
                    'experiment_id': experiment_id,
                    'template_id': template_id,
                    'status': final_status.get('state', {}).get('status', 'unknown'),
                    'duration': exp['duration']
                }
                
                results['experiments'].append(experiment_result)
                results['summary']['total'] += 1
                
                if final_status.get('state', {}).get('status') == 'completed':
                    results['summary']['successful'] += 1
                else:
                    results['summary']['failed'] += 1
            
            # Wait between experiments
            time.sleep(60)
        
        # Send summary notification
        self._send_summary_notification(results)
        
        return results

    def _send_notification(self, subject: str, message: str):
        """Send SNS notification"""
        try:
            topic_arn = f"arn:aws:sns:{boto3.Session().region_name}:{boto3.client('sts').get_caller_identity()['Account']}:{self.project_name}-chaos-notifications"
            
            self.sns.publish(
                TopicArn=topic_arn,
                Subject=subject,
                Message=message
            )
        except Exception as e:
            self.logger.error(f"Error sending notification: {e}")

    def _send_summary_notification(self, results: Dict):
        """Send experiment suite summary"""
        summary = results['summary']
        message = f"""
Chaos Engineering Weekly Suite Complete

Summary:
- Total Experiments: {summary['total']}
- Successful: {summary['successful']}
- Failed: {summary['failed']}
- Success Rate: {(summary['successful']/summary['total']*100):.1f}%

Timestamp: {results['timestamp']}
        """
        
        self._send_notification("Weekly Chaos Suite Complete", message)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='IaL Chaos Engineering Runner')
    parser.add_argument('--action', choices=['list', 'start', 'stop', 'monitor', 'weekly'], 
                       required=True, help='Action to perform')
    parser.add_argument('--template-id', help='Experiment template ID')
    parser.add_argument('--experiment-id', help='Experiment ID')
    parser.add_argument('--project', default='ial', help='Project name')
    parser.add_argument('--environment', default='dev', help='Environment')
    
    args = parser.parse_args()
    
    runner = ChaosRunner(args.project, args.environment)
    
    if args.action == 'list':
        templates = runner.list_experiment_templates()
        print(json.dumps(templates, indent=2, default=str))
    
    elif args.action == 'start':
        if not args.template_id:
            print("--template-id required for start action")
            exit(1)
        experiment_id = runner.start_experiment(args.template_id)
        print(f"Started experiment: {experiment_id}")
    
    elif args.action == 'stop':
        if not args.experiment_id:
            print("--experiment-id required for stop action")
            exit(1)
        success = runner.stop_experiment(args.experiment_id)
        print(f"Stop experiment: {'success' if success else 'failed'}")
    
    elif args.action == 'monitor':
        if not args.experiment_id:
            print("--experiment-id required for monitor action")
            exit(1)
        status = runner.monitor_experiment(args.experiment_id)
        print(json.dumps(status, indent=2, default=str))
    
    elif args.action == 'weekly':
        results = runner.run_weekly_chaos_suite()
        print(json.dumps(results, indent=2, default=str))
