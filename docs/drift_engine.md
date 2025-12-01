# 🔄 Drift Engine Documentation

**Version:** 6.30.0  
**Last Updated:** 2025-12-01  
**Status:** Production Ready

---

## 📋 **Overview**

The Drift Engine provides continuous monitoring and automatic healing of infrastructure drift between Git (desired state) and AWS (current state).

## 🏗️ **Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Git Repository  │    │ AWS Resources   │    │ Drift Engine    │
│ (Desired State) │◄──►│ (Current State) │◄──►│ (Comparison)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Auto Healer     │◄───│ Risk Classifier │◄───│ Drift Detector  │
│ (Correction)    │    │ (Severity)      │    │ (Detection)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
                                          ┌─────────────────┐
                                          │ Reverse Sync    │
                                          │ (AWS → Git)     │
                                          └─────────────────┘
```

## 🔍 **Drift Detection Process**

### **1. State Comparison**
```python
# Compare desired vs current state
desired_spec = phase_builder.build_desired_spec(phases)
current_state = audit_validator.get_current_aws_state()
drift_items = drift_detector.compare_states(desired_spec, current_state)
```

### **2. Drift Types Detected**

| Drift Type | Description | Severity |
|------------|-------------|----------|
| `missing_resource` | Resource in Git but not in AWS | HIGH |
| `extra_resource` | Resource in AWS but not in Git | MEDIUM |
| `configuration_drift` | Resource exists but config differs | VARIABLE |
| `tag_drift` | Resource tags don't match | LOW |

### **3. Risk Classification**
```python
class RiskLevel(Enum):
    LOW = "low"           # Tags, descriptions
    MEDIUM = "medium"     # Non-critical config
    HIGH = "high"         # Security, networking
    CRITICAL = "critical" # Data loss risk
```

## 🛠️ **Core Components**

### **DriftDetector**
- **Location:** `core/drift/drift_detector.py`
- **Purpose:** Compare Git vs AWS state
- **Methods:**
  - `detect_drift()` - Main detection logic
  - `compare_states()` - State comparison
  - `classify_drift()` - Risk assessment

### **AutoHealer**
- **Location:** `core/drift/auto_healer.py`
- **Purpose:** Automatic drift correction
- **Methods:**
  - `heal_drift()` - Execute healing
  - `can_auto_heal()` - Safety checks
  - `create_healing_plan()` - Plan generation

### **ReverseSync**
- **Location:** `core/drift/reverse_sync.py`
- **Purpose:** Sync AWS changes back to Git
- **Methods:**
  - `sync_from_aws()` - Main sync logic
  - `generate_phase_updates()` - Update phases
  - `create_sync_pr()` - Create PR with changes

## 🔄 **Drift Detection Flow**

### **Continuous Monitoring**
```bash
# Scheduled via CloudWatch Events
0 */6 * * * /usr/local/bin/ialctl drift check
```

### **Manual Detection**
```bash
# Via CLI
python3 ialctl_integrated.py "mostrar drift"
python3 ialctl_debug.py --debug drift

# Via Agent Core
User: "verificar drift atual"
Agent: check_drift tool → Analysis → Report
```

### **Detection Algorithm**
```python
def detect_drift():
    # 1. Get desired state from Git
    phases = ["00-foundation", "10-security", "20-network", "30-compute"]
    desired_spec = build_desired_spec(phases)
    
    # 2. Get current state from AWS
    current_state = get_current_aws_state()
    
    # 3. Compare states
    drift_items = []
    for resource_id, desired_config in desired_spec.items():
        current_config = current_state.get(resource_id)
        
        if not current_config:
            drift_items.append({
                'type': 'missing_resource',
                'resource_id': resource_id,
                'severity': 'high'
            })
        elif desired_config != current_config:
            drift_items.append({
                'type': 'configuration_drift',
                'resource_id': resource_id,
                'severity': classify_severity(desired_config, current_config)
            })
    
    return drift_items
```

## 🔧 **Auto-Healing Process**

### **Healing Decision Matrix**

| Drift Type | Auto-Heal | Condition |
|------------|-----------|-----------|
| Missing tags | ✅ Yes | Always safe |
| Config drift | ⚠️ Conditional | Non-destructive only |
| Missing resource | ❌ No | Requires approval |
| Extra resource | ❌ No | Requires approval |

### **Healing Workflow**
```python
def auto_heal_drift(drift_items):
    healing_plan = []
    
    for drift in drift_items:
        if can_auto_heal(drift):
            healing_plan.append(create_healing_action(drift))
        else:
            # Create PR for manual review
            create_manual_review_pr(drift)
    
    # Execute safe healings
    execute_healing_plan(healing_plan)
```

### **Safety Checks**
```python
def can_auto_heal(drift_item):
    # Never auto-heal destructive changes
    if drift_item['type'] in ['missing_resource', 'extra_resource']:
        return False
    
    # Only heal low-risk configuration changes
    if drift_item['severity'] in ['low', 'medium']:
        return True
    
    return False
```

## 🔄 **Reverse Sync Process**

### **When to Use Reverse Sync**
- Manual changes made in AWS Console
- Emergency fixes applied directly
- Configuration drift detected
- Compliance requirements

### **Reverse Sync Workflow**
```python
def reverse_sync():
    # 1. Detect current AWS state
    current_state = get_current_aws_state()
    
    # 2. Generate updated phases
    updated_phases = generate_phase_updates(current_state)
    
    # 3. Create Git branch
    branch_name = f"reverse-sync-{timestamp}"
    create_git_branch(branch_name)
    
    # 4. Update phase files
    update_phase_files(updated_phases)
    
    # 5. Create PR
    create_pr({
        'title': 'Reverse Sync: AWS → Git',
        'description': 'Sync manual AWS changes back to Git',
        'branch': branch_name
    })
```

## 📊 **Drift Reporting**

### **CLI Output Example**
```bash
$ python3 ialctl_integrated.py "mostrar drift"

🔍 DRIFT ANALYSIS REPORT
========================

📊 Summary:
✅ 45 resources in sync
⚠️ 8 resources with drift
❌ 2 critical issues

🔍 Drift Details:

HIGH SEVERITY:
• ecs-cluster-prod
  Type: configuration_drift
  Issue: CPU reservation changed from 512 to 1024
  Location: phases/30-compute/02-ecs-cluster.yaml
  
• rds-main-db
  Type: configuration_drift  
  Issue: Backup window changed from 03:00-04:00 to 05:00-06:00
  Location: phases/40-data/02-aurora-postgresql.yaml

MEDIUM SEVERITY:
• alb-web-prod
  Type: tag_drift
  Issue: Missing tag 'Environment=production'
  Location: phases/30-compute/05-alb.yaml

🔧 Recommended Actions:
1. Review high severity changes
2. Run reverse sync to update Git
3. Or revert manual changes in AWS

Commands:
• Reverse sync: ialctl reverse-sync
• Auto-heal safe items: ialctl drift heal
• Show detailed diff: ialctl drift diff
```

### **Agent Core Integration**
```
User: "verificar drift"

Agent Response:
🔍 Executando análise de drift...

📊 Resultados encontrados:
• 3 recursos com drift detectado
• 2 mudanças de alta severidade
• 1 mudança de baixa severidade

🔧 Posso executar reverse sync para sincronizar as mudanças do AWS para o Git?
Ou prefere que eu reverta as mudanças manuais no AWS?
```

## 🚨 **Alerting & Notifications**

### **CloudWatch Alarms**
```yaml
DriftDetectionAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: IAL-DriftDetected
    MetricName: DriftCount
    Threshold: 0
    ComparisonOperator: GreaterThanThreshold
    AlarmActions:
      - !Ref SNSTopic
```

### **SNS Notifications**
```json
{
  "AlarmName": "IAL-DriftDetected",
  "NewStateValue": "ALARM",
  "NewStateReason": "3 resources detected with configuration drift",
  "Timestamp": "2025-12-01T14:00:00.000Z"
}
```

## 🧪 **Testing Drift Detection**

### **Simulate Drift**
```bash
# Create intentional drift for testing
aws ec2 modify-instance-attribute \
  --instance-id i-1234567890abcdef0 \
  --instance-type t3.large

# Run drift detection
python3 ialctl_debug.py --debug "verificar drift"
```

### **Test Auto-Healing**
```bash
# Test safe auto-healing (tags)
aws ec2 create-tags \
  --resources i-1234567890abcdef0 \
  --tags Key=TestTag,Value=TestValue

# Run auto-heal
python3 ialctl_integrated.py "corrigir drift automaticamente"
```

## 📈 **Performance Metrics**

### **Detection Performance**
- Small environments (<50 resources): <30 seconds
- Medium environments (50-200 resources): <2 minutes
- Large environments (200+ resources): <5 minutes

### **Healing Performance**
- Tag corrections: <10 seconds
- Configuration updates: 1-5 minutes
- Resource recreation: 5-30 minutes

## 🔧 **Configuration**

### **Environment Variables**
```bash
IAL_DRIFT_CHECK_INTERVAL=6h    # How often to check for drift
IAL_AUTO_HEAL_ENABLED=true     # Enable auto-healing
IAL_REVERSE_SYNC_AUTO=false    # Auto reverse sync (not recommended)
```

### **Drift Sensitivity**
```yaml
# config/drift_config.yaml
sensitivity:
  tags: medium          # Tag drift sensitivity
  configuration: high   # Config drift sensitivity
  resources: critical   # Resource drift sensitivity

auto_heal:
  enabled: true
  max_resources: 10     # Max resources to heal per run
  severity_limit: medium # Max severity to auto-heal
```

---

**Engine Status:** ✅ Production Ready  
**Auto-Healing:** ✅ Safe & Tested  
**Reverse Sync:** ✅ Functional  
**Monitoring:** ✅ Comprehensive
