# 🏗️ IAL Architecture Documentation

**Version:** 6.30.0 + Bedrock Agent Core  
**Last Updated:** 2025-12-01  
**Status:** Production Ready

---

## 📋 **Overview**

The Infrastructure Assistant Layer (IAL) is a conversational AI system for AWS infrastructure management that combines Bedrock Agent Core with robust NLP fallback capabilities.

## 🏛️ **High-Level Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                           │
├─────────────────────────────────────────────────────────────────┤
│ ialctl_debug.py │ ialctl_agent_enhanced.py │ ialctl_integrated.py │
├─────────────────────────────────────────────────────────────────┤
│                    COGNITIVE LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│ Enhanced Fallback System                                        │
│ ┌─────────────────┬─────────────────┬─────────────────┐        │
│ │ Bedrock Agent   │ NLP Fallback    │ Sandbox Mode    │        │
│ │ Core (Primary)  │ (Automatic)     │ (Safe Testing)  │        │
│ └─────────────────┴─────────────────┴─────────────────┘        │
├─────────────────────────────────────────────────────────────────┤
│                    ORCHESTRATION LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│ MCP Orchestrator │ Cognitive Engine │ Master Engine Final      │
├─────────────────────────────────────────────────────────────────┤
│                    INFRASTRUCTURE LAYER                        │
├─────────────────────────────────────────────────────────────────┤
│ Step Functions │ Lambdas │ CloudFormation │ DynamoDB │ S3       │
└─────────────────────────────────────────────────────────────────┘
```

## 🧠 **Cognitive Processing Flow**

### **Primary Path: Bedrock Agent Core**
```
User Input → Enhanced Fallback System → Bedrock Agent Core
    ↓
Agent Tools:
├── get_aws_docs (MCP AWS Official)
├── estimate_cost (Cost Guardrails)
├── risk_validation (Validation System)
├── generate_phases (Phase Builder)
├── apply_phase (Step Functions)
├── check_drift (Drift Engine)
└── reverse_sync (Reverse Sync)
    ↓
AWS Infrastructure Operations
```

### **Fallback Path: NLP Local**
```
User Input → Enhanced Fallback System → Cognitive Engine
    ↓
IAS → Cost Guardrails → Phase Builder → GitHub PR → CI/CD
    ↓
AWS Infrastructure Operations
```

### **Sandbox Path: Safe Testing**
```
User Input → Enhanced Fallback System → Sandbox Mode
    ↓
Phase Builder → Local Preview Generation
    ↓
/sandbox_outputs/<timestamp>/phases_preview.yaml
```

## 🔄 **Fallback Decision Matrix**

| Condition | Processing Mode | Reason |
|-----------|----------------|---------|
| Agent Core available + No flags | Bedrock Agent Core | Primary path |
| Agent Core timeout/error | NLP Fallback | Automatic fallback |
| `--offline` flag | NLP Fallback | User preference |
| `--sandbox` flag | Sandbox Mode | Safe testing |
| `IAL_MODE=sandbox` | Sandbox Mode | Environment setting |

## 📊 **Component Responsibilities**

### **Enhanced Fallback System**
- **Purpose:** Intelligent routing between processing modes
- **Location:** `core/enhanced_fallback_system.py`
- **Responsibilities:**
  - Mode detection and routing
  - Structured telemetry logging
  - Error handling and recovery
  - Request ID generation

### **Bedrock Agent Core**
- **Purpose:** Primary cognitive processing via managed AI
- **Location:** `core/bedrock_agent_core.py`
- **Responsibilities:**
  - Agent session management
  - Tool invocation coordination
  - Memory and context handling
  - Response generation

### **Agent Tools Lambda**
- **Purpose:** Execute IAL operations as Bedrock Agent tools
- **Location:** `core/agent_tools_lambda.py`
- **Responsibilities:**
  - Tool request parsing
  - IAL component integration
  - Response formatting
  - Error handling

### **MCP Orchestrator**
- **Purpose:** Coordinate multiple MCP servers
- **Location:** `mcp_orchestrator.py`
- **Responsibilities:**
  - MCP server management
  - Parallel execution coordination
  - Health checking
  - Result aggregation

### **Cognitive Engine**
- **Purpose:** NLP-based processing (fallback)
- **Location:** `core/cognitive_engine.py`
- **Responsibilities:**
  - Intent analysis
  - Pipeline orchestration (IAS → Cost → Phase → GitOps)
  - Memory integration
  - MCP coordination

### **Drift Engine**
- **Purpose:** Infrastructure drift detection and correction
- **Location:** `core/drift/`
- **Responsibilities:**
  - Git vs AWS state comparison
  - Drift classification
  - Auto-healing coordination
  - Reverse synchronization

### **Memory System**
- **Purpose:** Infinite conversational memory
- **Location:** `core/memory/`
- **Responsibilities:**
  - Conversation persistence
  - Context retrieval
  - Bedrock embeddings
  - Cross-session continuity

## 🔧 **Processing Modes**

### **1. Agent Core Mode (Primary)**
- **Trigger:** Default behavior when Agent Core available
- **Processing:** Bedrock Agent "IALCoreBrain" with 7 tools
- **Benefits:** Managed AI, advanced reasoning, tool coordination
- **Fallback:** Automatic to NLP if unavailable

### **2. NLP Fallback Mode**
- **Trigger:** Agent Core unavailable or `--offline` flag
- **Processing:** Local CognitiveEngine + MasterEngine
- **Benefits:** Always available, no external dependencies
- **Performance:** Equivalent to original IAL functionality

### **3. Sandbox Mode**
- **Trigger:** `--sandbox` flag or `IAL_MODE=sandbox`
- **Processing:** Preview generation only, no AWS operations
- **Benefits:** Safe testing, cost-free exploration
- **Output:** Local YAML files in `/sandbox_outputs/`

### **4. Debug Mode**
- **Trigger:** `--debug` flag
- **Processing:** Any mode with enhanced logging
- **Benefits:** Detailed execution visibility
- **Output:** Structured logs, request tracing, performance metrics

## 📁 **Directory Structure**

```
/home/ial/
├── core/                           # Core components
│   ├── bedrock_agent_core.py      # Bedrock Agent integration
│   ├── agent_tools_lambda.py      # Agent tools implementation
│   ├── enhanced_fallback_system.py # Intelligent fallback
│   ├── cognitive_engine.py        # NLP processing engine
│   ├── master_engine_final.py     # Master routing engine
│   ├── drift/                     # Drift detection system
│   ├── memory/                    # Memory management
│   └── validation/                # Risk and cost validation
├── phases/                        # CloudFormation templates
│   ├── 00-foundation/             # Foundation infrastructure
│   ├── 10-security/               # Security components
│   ├── 20-network/                # Network infrastructure
│   └── ...                       # Other phases
├── docs/                          # Technical documentation
├── tests/                         # Automated tests
├── logs/                          # Telemetry and debug logs
├── sandbox_outputs/               # Sandbox preview outputs
├── ialctl_debug.py               # Debug CLI
├── ialctl_agent_enhanced.py      # Enhanced CLI
└── ialctl_integrated.py          # Original CLI (updated)
```

## 🔍 **Data Flow**

### **Request Processing**
1. **Input Reception:** CLI receives user input
2. **Mode Detection:** Enhanced Fallback System determines processing mode
3. **Request ID Generation:** Unique identifier for telemetry tracking
4. **Processing:** Route to appropriate cognitive system
5. **Tool Execution:** Execute infrastructure operations
6. **Response Generation:** Format and return results
7. **Telemetry Logging:** Record execution metrics

### **Telemetry Flow**
```
User Action → Request ID → Processing Events → Structured Logs
    ↓
/home/ial/logs/ial_telemetry.log (JSON format)
    ↓
Optional: CloudWatch Logs / OpenTelemetry
```

## 🛡️ **Security Architecture**

### **Agent Core Security**
- Bedrock Agent runtime isolation
- IAM-based tool permissions
- Lambda execution boundaries
- Request/response validation

### **Fallback Security**
- Local processing (no external calls)
- Existing IAL security model
- Step Functions isolation
- CloudFormation stack boundaries

### **Sandbox Security**
- No AWS API calls
- Local file system only
- Preview generation only
- Safe for testing/exploration

## 📈 **Performance Characteristics**

### **Agent Core Mode**
- **Latency:** 2-5 seconds (network dependent)
- **Throughput:** Limited by Bedrock quotas
- **Memory:** ~200MB (optimized MCP mesh)
- **Scalability:** Managed by AWS Bedrock

### **NLP Fallback Mode**
- **Latency:** <1 second (local processing)
- **Throughput:** CPU bound
- **Memory:** ~200MB (84% reduction achieved)
- **Scalability:** Single instance

### **Sandbox Mode**
- **Latency:** <500ms (no AWS calls)
- **Throughput:** I/O bound (local files)
- **Memory:** ~100MB (minimal components)
- **Scalability:** Local file system

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Processing Mode
IAL_MODE=sandbox                    # Force sandbox mode

# Agent Core
IAL_AGENT_ID=<agent-id>            # Bedrock Agent ID
IAL_PROJECT_NAME=ial               # Project identifier
IAL_REGION=us-east-1               # AWS region

# Telemetry
IAL_TELEMETRY_ENABLED=true         # Enable telemetry
IAL_LOG_LEVEL=INFO                 # Logging level
```

### **CLI Flags**
```bash
--debug      # Enable debug mode
--offline    # Force NLP fallback
--sandbox    # Enable sandbox mode
--telemetry  # Show telemetry logs
```

## 🔄 **Operational Modes**

### **Development Mode**
```bash
python3 ialctl_debug.py --debug --sandbox
```
- Full debug visibility
- Safe sandbox testing
- No AWS resource creation
- Detailed telemetry

### **Testing Mode**
```bash
python3 ialctl_agent_enhanced.py --offline
```
- NLP fallback testing
- Full functionality
- Local processing
- Production-equivalent

### **Production Mode**
```bash
python3 ialctl_agent_enhanced.py
```
- Bedrock Agent Core primary
- Automatic fallback
- Full AWS operations
- Optimized performance

## 📊 **Monitoring and Observability**

### **Telemetry Events**
- `intent_received`: User input captured
- `attempting_agent_core`: Agent Core processing started
- `agent_core_success`: Agent Core completed successfully
- `agent_core_failed`: Agent Core failed, falling back
- `using_fallback_nlp`: NLP fallback activated
- `sandbox_mode_processing`: Sandbox mode activated
- `tool_invocation`: Agent tool called
- `operation_completed`: Infrastructure operation finished

### **Metrics Available**
- Request processing time
- Success/failure rates by mode
- Tool invocation frequency
- Fallback activation rate
- Error patterns and causes

### **Log Locations**
- **Telemetry:** `/home/ial/logs/ial_telemetry.log`
- **Debug:** Console output when `--debug` enabled
- **Sandbox:** `/home/ial/sandbox_outputs/<timestamp>/`

---

## 🎯 **Design Principles**

1. **Resilience First:** Always have a working fallback
2. **Zero Downtime:** Never break existing functionality
3. **Observability:** Full visibility into system behavior
4. **Safety:** Sandbox mode for risk-free exploration
5. **Performance:** Optimized for sub-second responses
6. **Compatibility:** 100% backward compatibility maintained

This architecture ensures IAL remains robust, scalable, and maintainable while providing advanced AI capabilities through Bedrock Agent Core.
