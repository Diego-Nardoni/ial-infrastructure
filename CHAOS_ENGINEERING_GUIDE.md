# 🧪 IaL Chaos Engineering Guide

## 🎯 **OVERVIEW**

O IaL implementa **Chaos Engineering** usando **AWS Fault Injection Simulator (FIS)** para validar a resiliência do sistema através de falhas controladas. Este é o **primeiro projeto open source** com chaos engineering completo e custo otimizado.

---

## 🏗️ **ARCHITECTURE**

### **🔧 Core Components:**

```bash
📁 phases/00e-chaos-engineering.yaml    # Infrastructure
📁 scripts/chaos-runner.py              # Automation
📁 .github/workflows/chaos-pipeline.yml # CI/CD Integration
📁 chaos/                               # Experiment Definitions
```

### **🎛️ AWS Services Used:**
- **AWS FIS:** Fault injection experiments
- **CloudWatch:** Monitoring and stop conditions
- **SNS:** Notifications and alerting
- **IAM:** Secure experiment execution
- **CloudWatch Logs:** Experiment logging

---

## 🧪 **EXPERIMENT TYPES**

### **1. Network Chaos (Weekly)**
```yaml
Experiment: Network Latency Injection
Duration: 5 minutes
Target: 50% of subnets
Impact: +100ms latency, ±50ms jitter
Cost: $0.70/test × 4 = $2.80/month
```

**Purpose:** Validate application resilience to network degradation

### **2. Infrastructure Chaos (Weekly)**
```yaml
Experiment: Random Instance Termination
Duration: 10 minutes (auto-restart)
Target: 1 random instance
Impact: Instance stop/start cycle
Cost: $0.10/test × 4 = $0.40/month
```

**Purpose:** Test auto-scaling and service recovery

### **3. Application Chaos (Bi-weekly)**
```yaml
Experiment: ECS Task Termination
Duration: 3 minutes
Target: 25% of ECS tasks
Impact: Task restart via ECS service
Cost: $0.20/test × 2 = $0.40/month
```

**Purpose:** Validate ECS service resilience and task recovery

### **4. Database Chaos (Monthly)**
```yaml
Experiment: Database Connection Failures
Duration: 5 minutes
Target: Connection pool stress
Impact: Simulated connection failures
Cost: $0.40/test × 1 = $0.40/month
```

**Purpose:** Test circuit breakers and connection handling

---

## 🚀 **GETTING STARTED**

### **📋 Prerequisites:**
```bash
✅ AWS FIS permissions configured
✅ CloudWatch alarms set up
✅ SNS topic for notifications
✅ Target resources tagged properly
✅ Stop conditions configured
```

### **🔧 Quick Setup:**
```bash
# 1. Deploy chaos infrastructure
aws cloudformation deploy \
  --template-file phases/00e-chaos-engineering.yaml \
  --stack-name ial-chaos-engineering \
  --parameter-overrides ChaosEnabled=true \
  --capabilities CAPABILITY_NAMED_IAM

# 2. Configure notifications
aws sns subscribe \
  --topic-arn arn:aws:sns:region:account:ial-chaos-notifications \
  --protocol email \
  --notification-endpoint your-email@domain.com

# 3. Test chaos runner
cd scripts
python3 chaos-runner.py --action list --project ial
```

---

## 🎮 **USAGE**

### **🤖 Automated Execution (Recommended):**
```bash
# Weekly chaos suite (GitHub Actions)
# Runs every Monday at 2 AM UTC automatically
# Includes all experiment types in sequence
```

### **🔧 Manual Execution:**
```bash
# List available experiments
python3 chaos-runner.py --action list

# Run specific experiment
python3 chaos-runner.py --action start --template-id ial-network-latency

# Monitor experiment
python3 chaos-runner.py --action monitor --experiment-id exp-123456

# Run weekly suite manually
python3 chaos-runner.py --action weekly
```

### **🎯 Targeted Testing:**
```bash
# Network resilience only
python3 chaos-runner.py --action start --template-id ial-network-latency

# Infrastructure resilience only
python3 chaos-runner.py --action start --template-id ial-instance-termination

# Application resilience only
python3 chaos-runner.py --action start --template-id ial-ecs-task-termination
```

---

## 📊 **MONITORING & OBSERVABILITY**

### **🎛️ Key Metrics:**
```bash
Namespace: AWS/FIS
- ExperimentState: running/completed/failed
- ExperimentDuration: actual vs expected
- TargetResourceCount: resources affected

Namespace: IaL/Chaos
- SystemRecoveryTime: time to full recovery
- ServiceAvailability: uptime during chaos
- ErrorRate: application errors during test
```

### **🚨 Stop Conditions:**
```bash
1. HealthyHostCount < 1 (ALB)
2. ErrorRate > 10% (Application)
3. ResponseTime > 5000ms (Performance)
4. Manual intervention trigger
```

### **📈 Success Criteria:**
```bash
✅ System maintains >99% availability
✅ Recovery time < 5 minutes
✅ No data loss or corruption
✅ Graceful degradation observed
✅ Auto-scaling responds correctly
```

---

## 🛡️ **SAFETY MEASURES**

### **🔒 Built-in Safeguards:**
```bash
1. Stop Conditions: Automatic experiment termination
2. Resource Targeting: Limited blast radius
3. Time Limits: Maximum experiment duration
4. Rollback Integration: Automatic recovery
5. Notification System: Real-time alerts
```

### **🚨 Emergency Procedures:**
```bash
# Stop all running experiments
aws fis list-experiments --query 'experiments[?state.status==`running`].id' --output text | \
xargs -I {} aws fis stop-experiment --id {}

# Trigger emergency rollback
cd utils
python3 rollback_manager.py --action emergency-rollback --reason chaos-failure

# Check system health
aws elbv2 describe-target-health --target-group-arn <target-group-arn>
```

---

## 💰 **COST OPTIMIZATION**

### **📊 Monthly Cost Breakdown:**
```bash
Network Latency Tests:    $2.80/month (weekly)
Instance Termination:    $0.40/month (weekly)
ECS Task Termination:    $0.40/month (bi-weekly)
Database Connection:     $0.40/month (monthly)
CloudWatch Metrics:      $1.50/month (custom metrics)
SNS Notifications:       $0.04/month (alerts)
CloudWatch Logs:         $0.52/month (experiment logs)

TOTAL: $6.06/month (realistic usage)
```

### **💡 Cost Optimization Tips:**
```bash
1. Adjust experiment frequency based on needs
2. Use resource tags to limit blast radius
3. Optimize experiment duration
4. Leverage free tier where possible
5. Monitor actual vs estimated costs
```

---

## 🔧 **CONFIGURATION**

### **🎯 Resource Targeting:**
```yaml
# Tag resources for chaos testing
Tags:
  Environment: dev|staging|prod
  ChaosEnabled: true|false
  ChaosLevel: low|medium|high
  CriticalService: true|false
```

### **⚙️ Experiment Customization:**
```yaml
# Network Latency
Parameters:
  duration: PT5M          # 5 minutes
  latencyMs: '100'        # 100ms delay
  jitterMs: '50'          # ±50ms variation
  
# Instance Termination
Parameters:
  startInstancesAfterDuration: PT10M  # Auto-restart after 10min
  
# ECS Task Termination
Parameters:
  reason: 'Chaos engineering test'
```

---

## 📈 **RESULTS & REPORTING**

### **📊 Automated Reports:**
```bash
Location: reports/chaos/chaos-report-YYYYMMDD-HHMMSS.md
Content:
- Experiment summary
- System resilience metrics
- Recovery time analysis
- Improvement recommendations
```

### **🎯 Key Performance Indicators:**
```bash
1. Mean Time To Recovery (MTTR): <5 minutes
2. System Availability: >99.9%
3. Experiment Success Rate: >95%
4. False Positive Rate: <5%
5. Cost Efficiency: <$10/month
```

---

## 🚀 **ADVANCED FEATURES**

### **🔄 Integration with Rollback System:**
```python
# Automatic rollback on chaos failure
if chaos_experiment_failed():
    rollback_manager.emergency_rollback(
        reason="chaos-experiment-failure",
        target_checkpoint="last-stable"
    )
```

### **🎛️ Custom Experiment Creation:**
```yaml
# Create custom FIS experiment template
CustomExperiment:
  Type: AWS::FIS::ExperimentTemplate
  Properties:
    Description: 'Custom chaos experiment'
    Actions:
      CustomAction:
        ActionId: aws:ec2:reboot-instances
        Parameters:
          duration: PT2M
```

---

## 🏆 **BEST PRACTICES**

### **✅ Do's:**
```bash
✅ Start with low-impact experiments
✅ Monitor system health continuously
✅ Document all experiments and results
✅ Integrate with existing monitoring
✅ Test during low-traffic periods
✅ Have rollback procedures ready
✅ Communicate with stakeholders
```

### **❌ Don'ts:**
```bash
❌ Run chaos in production without testing
❌ Skip stop condition configuration
❌ Ignore experiment results
❌ Run multiple experiments simultaneously
❌ Exceed blast radius limits
❌ Disable safety mechanisms
❌ Run without proper monitoring
```

---

## 🔍 **TROUBLESHOOTING**

### **🚨 Common Issues:**

#### **Experiment Won't Start:**
```bash
Cause: Missing IAM permissions
Solution: Check FIS execution role permissions

Cause: Invalid target selection
Solution: Verify resource tags and selection criteria
```

#### **Experiment Stops Immediately:**
```bash
Cause: Stop condition triggered
Solution: Check CloudWatch alarms and system health

Cause: Resource not available
Solution: Verify target resources exist and are healthy
```

#### **High Costs:**
```bash
Cause: Too frequent execution
Solution: Adjust experiment schedule

Cause: Large blast radius
Solution: Reduce target selection percentage
```

---

## 📚 **LEARNING RESOURCES**

### **📖 Documentation:**
```bash
- AWS FIS User Guide
- Chaos Engineering Principles
- Site Reliability Engineering (SRE)
- Well-Architected Framework - Reliability Pillar
```

### **🎓 Training:**
```bash
- AWS FIS Workshop
- Chaos Engineering Fundamentals
- SRE Best Practices
- Incident Response Training
```

---

## 🤝 **CONTRIBUTING**

### **🔧 Adding New Experiments:**
```bash
1. Create experiment template in phases/00e-chaos-engineering.yaml
2. Add automation logic to scripts/chaos-runner.py
3. Update GitHub Actions workflow
4. Test thoroughly in dev environment
5. Document experiment in this guide
6. Submit pull request
```

### **📊 Improving Monitoring:**
```bash
1. Identify new metrics to track
2. Add CloudWatch custom metrics
3. Update dashboards and alarms
4. Test alerting mechanisms
5. Document new monitoring capabilities
```

---

## 🎯 **ROADMAP**

### **🚀 Phase 1 (Current):**
- [x] Basic FIS experiments
- [x] Automated execution
- [x] Safety mechanisms
- [x] Cost optimization

### **🔮 Phase 2 (Future):**
- [ ] Multi-region chaos testing
- [ ] Advanced failure scenarios
- [ ] ML-based experiment optimization
- [ ] Integration with external tools

---

## 📞 **SUPPORT**

### **🆘 Getting Help:**
```bash
1. Check troubleshooting section
2. Review experiment logs in CloudWatch
3. Check GitHub Issues
4. Contact maintainers
```

### **🐛 Reporting Issues:**
```bash
1. Describe the problem clearly
2. Include experiment logs
3. Provide system configuration
4. Steps to reproduce
```

---

## 🏆 **CONCLUSION**

O **IaL Chaos Engineering** representa um marco na engenharia de confiabilidade open source:

- **Primeiro projeto** com chaos engineering completo
- **Custo otimizado** para sustentabilidade
- **Automação completa** com GitHub Actions
- **Integração nativa** com observability
- **Segurança robusta** com múltiplas salvaguardas

**RESULTADO:** Sistema enterprise-ready com resiliência comprovada por apenas **$6/mês** adicional.

---

**🚀 Ready to embrace chaos? Start your resilience journey today!** 💪⚡
