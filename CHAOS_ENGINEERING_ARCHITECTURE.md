# Chaos Engineering Architecture

## Overview
IAL implements a **hybrid chaos engineering architecture** that combines the power of AWS FIS with intelligent dependency-aware orchestration.

## Architecture Components

### 1. Chaos Controller (Application-Level)
- **Location:** `/home/ial/core/chaos/chaos_controller.py`
- **Responsibility:** Application-level chaos + intelligent orchestration
- **Failure Types:**
  - `configuration_drift` - Triggers existing auto-healing systems
  - `service_degradation` - Controlled performance impact testing

### 2. AWS FIS (Infrastructure-Level)  
- **Location:** `/home/ial/phases/00-foundation/05-chaos-engineering.yaml`
- **Responsibility:** Infrastructure-level chaos experiments
- **Failure Types:**
  - `instance_termination` - EC2 instance failure simulation
  - `network_partition` - Network latency injection
  - `resource_exhaustion` - ECS task termination

### 3. Unified Interface
- **Location:** `/home/ial/graph_chaos_cli.py`
- **Purpose:** Single entry point for all chaos experiments
- **Features:** Intelligent routing based on failure type

## Key Differentiators

### Dependency-Aware Chaos
- Integrates with dependency graph for intelligent targeting
- Prevents cascade failures through graph analysis
- Optimizes healing order based on resource relationships

### Safety-First Design
- Both components disabled by default
- Multiple safety layers and approval workflows
- Automatic rollback mechanisms

## Usage Examples

### Validate Configuration
```bash
python graph_chaos_cli.py validate-config
```

### Application Chaos (via Chaos Controller)
```bash
python graph_chaos_cli.py start --type configuration_drift --target my-service
```

### Infrastructure Chaos (via AWS FIS)
```bash
python graph_chaos_cli.py start --type instance_termination --target i-1234567890abcdef0
```

## Safety Controls

### Default State: DISABLED
- Chaos Controller: `enabled: false`
- AWS FIS: `ChaosEnabled: 'false'`

### Enable Requirements
1. **Chaos Controller:**
   - Set `enabled: true` in config
   - Set `CHAOS_ENGINEERING_ENABLED=true` env var
   - Set `require_explicit_enable: false`

2. **AWS FIS:**
   - Deploy with `ChaosEnabled: 'true'` parameter

### Environment Controls
- **Allowed:** development, staging, sandbox
- **Blocked:** production, prod, live

## Integration Benefits

1. **No Redundancy:** Clear separation of responsibilities
2. **Unified Interface:** Single CLI for all chaos types  
3. **Intelligent Routing:** Automatic selection of appropriate backend
4. **Graph Integration:** Dependency-aware experiment planning
5. **Safety Layers:** Multiple fail-safes and approval workflows

## Architecture Decision

This hybrid approach provides:
- **AWS FIS:** Battle-tested infrastructure chaos capabilities
- **Chaos Controller:** Unique dependency-aware orchestration
- **Combined:** Market-leading intelligent chaos engineering platform
