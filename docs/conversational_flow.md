# 💬 Conversational Flow Documentation

**Version:** 6.30.0  
**Last Updated:** 2025-12-01  
**Status:** Production Ready

---

## 📋 **Overview**

The IAL conversational flow provides natural language interaction for AWS infrastructure management through multiple processing modes.

## 🔄 **Complete Flow Diagram**

```
User Input
    ↓
Enhanced Fallback System
    ↓
┌─────────────────────────────────────────────────────────┐
│                Processing Mode Selection                 │
├─────────────────┬─────────────────┬─────────────────────┤
│ Bedrock Agent   │ NLP Fallback    │ Sandbox Mode        │
│ Core (Primary)  │ (Automatic)     │ (Safe Testing)      │
└─────────────────┴─────────────────┴─────────────────────┘
    ↓                    ↓                    ↓
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ 7 Agent Tools   │ │ Cognitive       │ │ Phase Builder   │
│ • get_aws_docs  │ │ Engine Pipeline │ │ Preview Only    │
│ • estimate_cost │ │ • IAS           │ │                 │
│ • risk_validate │ │ • Cost Guards   │ │ Output:         │
│ • generate_ph   │ │ • Phase Builder │ │ /sandbox_out/   │
│ • apply_phase   │ │ • GitHub PR     │ │ preview.yaml    │
│ • check_drift   │ │ • Step Funcs    │ │                 │
│ • reverse_sync  │ │ • Auto-Heal     │ │                 │
└─────────────────┘ └─────────────────┘ └─────────────────┘
    ↓                    ↓                    ↓
AWS Infrastructure   AWS Infrastructure   No AWS Operations
```

## 🎯 **Conversation Types**

### **1. Infrastructure Creation**
```
User: "Quero criar um ECS privado com Redis"

Agent Core Flow:
1. get_aws_docs → Busca documentação ECS/Redis
2. risk_validation → Valida arquitetura proposta
3. estimate_cost → Calcula custos estimados
4. generate_phases → Gera DAG de fases
5. [User Confirmation] → Aguarda confirmação
6. apply_phase → Executa via Step Functions
7. check_drift → Valida deployment
```

### **2. Drift Management**
```
User: "Mostrar drift atual"

Agent Core Flow:
1. check_drift → Analisa Git vs AWS
2. [Show Results] → Apresenta diferenças
3. [User Decision] → Corrigir ou manter?
4. reverse_sync → Sincroniza se necessário
```

### **3. Cost Analysis**
```
User: "Quanto custa minha infraestrutura?"

Agent Core Flow:
1. get_aws_docs → Busca informações de pricing
2. estimate_cost → Calcula custos atuais
3. [Show Analysis] → Apresenta breakdown
4. [Optimization] → Sugere otimizações
```

## 🧠 **Memory Integration**

### **Conversational Context**
```python
# Memory Manager maintains context across sessions
memory_manager.store_conversation(
    user_id="user123",
    session_id="session456",
    context={
        "previous_requests": ["criar ECS", "mostrar drift"],
        "infrastructure_state": {...},
        "user_preferences": {...}
    }
)
```

### **Context Retrieval**
```python
# Context Engine retrieves relevant history
context = context_engine.build_context_for_query(
    query="adicionar Redis ao ECS",
    user_id="user123"
)
# Returns: Previous ECS configuration, user preferences, etc.
```

## 🔀 **Mode Selection Logic**

### **Enhanced Fallback Decision Tree**
```python
def determine_mode(user_input, flags):
    if flags.get('sandbox') or os.getenv('IAL_MODE') == 'sandbox':
        return ProcessingMode.SANDBOX
    
    if flags.get('offline'):
        return ProcessingMode.FALLBACK_NLP
    
    if agent_core_available():
        return ProcessingMode.AGENT_CORE
    else:
        return ProcessingMode.FALLBACK_NLP
```

## 📊 **Conversation Examples**

### **Example 1: Complete Infrastructure Setup**

**User:** "Preciso de uma aplicação web com banco de dados"

**Agent Response:**
```
🧠 Analisando sua solicitação...

📋 Arquitetura Proposta:
• ECS Fargate para aplicação web
• RDS PostgreSQL para banco de dados
• ALB para load balancing
• VPC com subnets privadas

💰 Estimativa de Custo: ~$180/mês

⚠️ Validação de Riscos: ✅ Aprovada
• Encryption at rest: ✅
• Network isolation: ✅
• Backup strategy: ✅

🔧 Fases de Deployment:
1. Foundation (VPC, Security)
2. Database (RDS)
3. Compute (ECS)
4. Load Balancer (ALB)

Confirma a criação? (sim/não)
```

### **Example 2: Drift Detection**

**User:** "verificar drift"

**Agent Response:**
```
🔍 Analisando drift Git ↔ AWS...

📊 Resultados:
✅ 45 recursos em sync
⚠️ 3 recursos com drift:
• ecs-cluster-prod: CPU modificado manualmente
• rds-main: Backup window alterado
• alb-web: Security group modificado

🔧 Ações Recomendadas:
1. Reverse sync para atualizar Git
2. Ou reverter mudanças manuais

Deseja executar reverse sync? (sim/não)
```

### **Example 3: Sandbox Mode**

**User:** "criar lambda com DynamoDB" (modo sandbox)

**Agent Response:**
```
🏖️ MODO SANDBOX - Nenhuma operação AWS será executada

📋 Preview Gerado:
• Lambda function com Python runtime
• DynamoDB table com GSI
• IAM roles e policies
• CloudWatch logs

📁 Arquivo gerado: /sandbox_outputs/20251201_140500/phases_preview.yaml

💡 Para aplicar na AWS:
python3 ialctl_integrated.py "criar lambda com DynamoDB"
```

## 🔧 **CLI Integration**

### **Interactive Mode**
```bash
python3 ialctl_integrated.py
# Enters conversational mode with Agent Core
```

### **Single Command**
```bash
python3 ialctl_integrated.py "criar ECS com Redis"
# Processes single command
```

### **Debug Mode**
```bash
python3 ialctl_debug.py --debug "criar infraestrutura"
# Shows detailed processing information
```

## 📈 **Performance Optimization**

### **Response Time Targets**
- Simple queries: <2 seconds
- Complex infrastructure: <10 seconds
- Drift analysis: <5 seconds
- Cost estimation: <3 seconds

### **Caching Strategy**
- AWS documentation cached for 1 hour
- Cost estimates cached for 30 minutes
- Drift results cached for 5 minutes

## 🔍 **Debug Information**

### **Debug Mode Output**
```bash
python3 ialctl_debug.py --debug "criar ECS"

🔍 DEBUG INFO:
Request ID: abc123-def456
Processing Mode: AGENT_CORE
Agent Tools Called:
  1. get_aws_docs (850ms)
  2. risk_validation (1200ms)
  3. estimate_cost (650ms)
  4. generate_phases (2100ms)
Total Processing Time: 4.8s
Memory Used: 45MB
Tokens Estimated: 2,450
```

## 🎯 **Best Practices**

### **For Users**
1. Be specific in requests ("ECS Fargate" vs "container")
2. Mention constraints upfront ("low cost", "high availability")
3. Use sandbox mode for exploration
4. Review generated phases before applying

### **For Developers**
1. Monitor telemetry logs for performance
2. Use debug mode for troubleshooting
3. Test fallback scenarios regularly
4. Keep documentation updated

---

**Flow Status:** ✅ Production Ready  
**Agent Integration:** ✅ Complete  
**Fallback Support:** ✅ Robust  
**Documentation:** ✅ Comprehensive
