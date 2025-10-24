#!/usr/bin/env python3
"""Bedrock Cost Analysis and Optimization for IaL"""

import json
import os
from datetime import datetime, timedelta
from collections import defaultdict

def main():
    """Analyze Bedrock usage and costs"""
    
    print("💰 Analyzing Bedrock usage and costs...")
    
    usage_data = load_usage_data()
    
    if not usage_data:
        print("⚠️ No usage data found")
        return
    
    # Analyze costs
    cost_analysis = analyze_costs(usage_data)
    
    # Generate recommendations
    recommendations = generate_recommendations(usage_data, cost_analysis)
    
    # Create report
    generate_cost_report(cost_analysis, recommendations)
    
    print(f"✅ Cost analysis complete - see reports/bedrock_cost_analysis.json")

def load_usage_data():
    """Load Bedrock usage data from logs"""
    
    usage_file = '/home/ial/logs/bedrock_usage.jsonl'
    
    if not os.path.exists(usage_file):
        return []
    
    usage_data = []
    
    with open(usage_file, 'r') as f:
        for line in f:
            if line.strip():
                try:
                    usage = json.loads(line)
                    usage_data.append(usage)
                except json.JSONDecodeError:
                    continue
    
    return usage_data

def analyze_costs(usage_data):
    """Analyze costs by various dimensions"""
    
    analysis = {
        'total_cost': 0,
        'total_calls': len(usage_data),
        'by_model': defaultdict(lambda: {'calls': 0, 'cost': 0, 'input_tokens': 0, 'output_tokens': 0}),
        'by_operation': defaultdict(lambda: {'calls': 0, 'cost': 0}),
        'by_date': defaultdict(lambda: {'calls': 0, 'cost': 0}),
        'daily_average': 0,
        'monthly_projection': 0
    }
    
    # Pricing (per 1M tokens)
    pricing = {
        'anthropic.claude-3-5-sonnet-20240620-v1:0': {'input': 3.00, 'output': 15.00},
        'anthropic.claude-3-haiku-20240307-v1:0': {'input': 0.25, 'output': 1.25}
    }
    
    for usage in usage_data:
        model_id = usage['model_id']
        operation = usage['operation']
        date = usage['timestamp'][:10]  # YYYY-MM-DD
        
        input_tokens = usage['input_tokens']
        output_tokens = usage['output_tokens']
        
        # Calculate cost
        if model_id in pricing:
            input_cost = input_tokens * pricing[model_id]['input'] / 1000000
            output_cost = output_tokens * pricing[model_id]['output'] / 1000000
            total_cost = input_cost + output_cost
        else:
            total_cost = 0
        
        # Update totals
        analysis['total_cost'] += total_cost
        
        # Update by model
        analysis['by_model'][model_id]['calls'] += 1
        analysis['by_model'][model_id]['cost'] += total_cost
        analysis['by_model'][model_id]['input_tokens'] += input_tokens
        analysis['by_model'][model_id]['output_tokens'] += output_tokens
        
        # Update by operation
        analysis['by_operation'][operation]['calls'] += 1
        analysis['by_operation'][operation]['cost'] += total_cost
        
        # Update by date
        analysis['by_date'][date]['calls'] += 1
        analysis['by_date'][date]['cost'] += total_cost
    
    # Calculate averages and projections
    if analysis['by_date']:
        days_with_data = len(analysis['by_date'])
        analysis['daily_average'] = analysis['total_cost'] / days_with_data
        analysis['monthly_projection'] = analysis['daily_average'] * 30
    
    return analysis

def generate_recommendations(usage_data, cost_analysis):
    """Generate cost optimization recommendations"""
    
    recommendations = []
    
    # Model usage optimization
    sonnet_usage = cost_analysis['by_model'].get('anthropic.claude-3-5-sonnet-20240620-v1:0', {})
    haiku_usage = cost_analysis['by_model'].get('anthropic.claude-3-haiku-20240307-v1:0', {})
    
    if sonnet_usage.get('cost', 0) > haiku_usage.get('cost', 0) * 2:
        recommendations.append({
            'type': 'model_optimization',
            'priority': 'medium',
            'description': 'Consider using Claude 3 Haiku for simpler operations',
            'potential_savings': sonnet_usage.get('cost', 0) * 0.8,  # Estimate 80% savings
            'implementation': 'Add complexity assessment to select appropriate model'
        })
    
    # Token optimization
    avg_input_tokens = sum(u['input_tokens'] for u in usage_data) / len(usage_data) if usage_data else 0
    avg_output_tokens = sum(u['output_tokens'] for u in usage_data) / len(usage_data) if usage_data else 0
    
    if avg_input_tokens > 3000:
        recommendations.append({
            'type': 'prompt_optimization',
            'priority': 'high',
            'description': 'Input prompts are large - consider optimization',
            'potential_savings': cost_analysis['total_cost'] * 0.3,
            'implementation': 'Reduce prompt size, use more focused queries'
        })
    
    if avg_output_tokens > 2000:
        recommendations.append({
            'type': 'output_optimization',
            'priority': 'medium',
            'description': 'Output tokens are high - consider limiting response length',
            'potential_savings': cost_analysis['total_cost'] * 0.2,
            'implementation': 'Add max_tokens limits, request more concise responses'
        })
    
    # Caching opportunities
    test_gen_calls = cost_analysis['by_operation'].get('test_generation', {}).get('calls', 0)
    if test_gen_calls > 10:
        recommendations.append({
            'type': 'caching',
            'priority': 'high',
            'description': 'Implement test caching for similar deployments',
            'potential_savings': cost_analysis['by_operation'].get('test_generation', {}).get('cost', 0) * 0.6,
            'implementation': 'Cache generated tests based on resource fingerprint'
        })
    
    # Monthly cost projection
    monthly_proj = cost_analysis['monthly_projection']
    if monthly_proj > 5:  # $5/month threshold
        recommendations.append({
            'type': 'cost_monitoring',
            'priority': 'low',
            'description': f'Monthly projection is ${monthly_proj:.2f} - consider budget alerts',
            'potential_savings': 0,
            'implementation': 'Set up CloudWatch billing alarms'
        })
    
    return recommendations

def generate_cost_report(cost_analysis, recommendations):
    """Generate comprehensive cost report"""
    
    os.makedirs('/home/ial/reports', exist_ok=True)
    
    report = {
        'timestamp': datetime.utcnow().isoformat(),
        'summary': {
            'total_cost': round(cost_analysis['total_cost'], 4),
            'total_calls': cost_analysis['total_calls'],
            'daily_average': round(cost_analysis['daily_average'], 4),
            'monthly_projection': round(cost_analysis['monthly_projection'], 2)
        },
        'breakdown': {
            'by_model': dict(cost_analysis['by_model']),
            'by_operation': dict(cost_analysis['by_operation']),
            'by_date': dict(cost_analysis['by_date'])
        },
        'recommendations': recommendations,
        'optimization_potential': sum(r.get('potential_savings', 0) for r in recommendations)
    }
    
    # Save detailed report
    with open('/home/ial/reports/bedrock_cost_analysis.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print(f"\n💰 BEDROCK COST ANALYSIS")
    print(f"Total Cost: ${report['summary']['total_cost']}")
    print(f"Total API Calls: {report['summary']['total_calls']}")
    print(f"Daily Average: ${report['summary']['daily_average']}")
    print(f"Monthly Projection: ${report['summary']['monthly_projection']}")
    
    if recommendations:
        print(f"\n💡 OPTIMIZATION RECOMMENDATIONS ({len(recommendations)}):")
        for rec in recommendations:
            savings = rec.get('potential_savings', 0)
            print(f"  - {rec['description']} (Save: ${savings:.2f})")
    
    total_savings = sum(r.get('potential_savings', 0) for r in recommendations)
    if total_savings > 0:
        print(f"\n🎯 Total Optimization Potential: ${total_savings:.2f}/month")

if __name__ == "__main__":
    main()
