import json
import boto3
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)
cloudwatch = boto3.client('cloudwatch')

def lambda_handler(event, context):
    """CloudWatch Metrics Publisher"""
    try:
        metrics = event.get("metrics", [])
        namespace = event.get("namespace", "IAL/Custom")
        
        logger.info(f"Publishing {len(metrics)} metrics to {namespace}")
        
        metric_data = []
        for metric in metrics:
            metric_data.append({
                'MetricName': metric['name'],
                'Value': metric['value'],
                'Unit': metric.get('unit', 'Count'),
                'Timestamp': datetime.utcnow(),
                'Dimensions': metric.get('dimensions', [])
            })
        
        # Publish metrics in batches of 20 (CloudWatch limit)
        for i in range(0, len(metric_data), 20):
            batch = metric_data[i:i+20]
            cloudwatch.put_metric_data(
                Namespace=namespace,
                MetricData=batch
            )
        
        logger.info(f"Published {len(metric_data)} metrics successfully")
        return {
            "status": "OK",
            "metrics_published": len(metric_data),
            "namespace": namespace
        }
        
    except Exception as e:
        logger.error(f"Metrics publishing failed: {str(e)}")
        raise Exception(f"Metrics publishing failed: {str(e)}")
