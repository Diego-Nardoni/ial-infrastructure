# 🛡️ Estratégia de Chaos Engineering - IaL

## 🎯 **DECISÃO ESTRATÉGICA: FIS DESABILITADO POR PADRÃO**

### **📋 CONTEXTO**
O AWS Fault Injection Simulator (FIS) está **desabilitado por padrão** no projeto IaL para garantir:
- ✅ **Segurança operacional** - Evita instabilidade acidental
- ✅ **Controle de custos** - Zero cobrança até habilitação explícita  
- ✅ **Implementação gradual** - Foco em estabilidade primeiro

---

## 🔧 **CONFIGURAÇÃO ATUAL**

### **Estado Padrão:**
```yaml
Parameters:
  ChaosEnabled:
    Type: String
    Default: 'false'  # ← DESABILITADO POR PADRÃO
    Description: 'Enable chaos engineering experiments (disabled by default for safety)'
```

### **Recursos Criados:**
```bash
ChaosEnabled=false: ❌ Nenhum recurso FIS criado
ChaosEnabled=true:  ✅ Todos os recursos FIS ativos
```

---

## 💰 **IMPACTO FINANCEIRO**

### **Estado Atual (Desabilitado):**
```bash
Custo FIS: $0.00/mês
Custo total projeto: $158.63/mês
Economia: $6.06/mês até habilitação
```

### **Quando Habilitado:**
```bash
Custo FIS: +$6.06/mês
Custo total projeto: $164.69/mês
Experimentos: 4 tipos (network, instance, ECS, database)
```

---

## 📅 **CRONOGRAMA DE ATIVAÇÃO**

### **Fase 1 (Atual): Infraestrutura Estável**
```bash
Status: ChaosEnabled=false
Foco: Observability, backup, logging, estabilidade
Duração: Até sistema estar 100% estável
```

### **Fase 2 (Futura): Chaos Engineering**
```bash
Status: ChaosEnabled=true (quando solicitado)
Pré-requisitos:
- ✅ Sistema rodando estável 2+ semanas
- ✅ Observability 100% funcional
- ✅ Backup/recovery testados
- ✅ Equipe preparada para chaos testing
```

---

## 🎮 **COMO HABILITAR QUANDO NECESSÁRIO**

### **Método 1: CloudFormation Parameter**
```bash
aws cloudformation update-stack \
  --stack-name ial-chaos-engineering \
  --use-previous-template \
  --parameters ParameterKey=ChaosEnabled,ParameterValue=true
```

### **Método 2: Linguagem Natural (Q CLI)**
```bash
"Quero habilitar o chaos engineering agora"
"Ativa os testes de resiliência"
"Liga o FIS para testar o sistema"
```

### **Método 3: GitHub Actions Manual**
```bash
# Workflow dispatch com input ChaosEnabled=true
```

---

## 🛡️ **SAFEGUARDS IMPLEMENTADOS**

### **Proteções Ativas:**
```bash
✅ Default disabled - Evita ativação acidental
✅ Conditional resources - Zero recursos se desabilitado
✅ Cost protection - Zero cobrança até habilitação
✅ Documentation - Processo claro de ativação
```

### **Quando Habilitado:**
```bash
✅ Stop conditions - Para experimentos se sistema instável
✅ Limited blast radius - Afeta apenas recursos tagged
✅ Time bounds - Experimentos têm duração máxima
✅ Emergency rollback - Rollback automático se falha
```

---

## 📊 **MONITORAMENTO DE READINESS**

### **Indicadores para Habilitar FIS:**
```bash
1. System uptime > 99.9% por 2 semanas
2. Zero incidents críticos por 1 mês  
3. Observability dashboards funcionais
4. Backup/recovery testados com sucesso
5. Equipe treinada em procedures de emergência
```

### **Red Flags (NÃO habilitar):**
```bash
❌ Sistema com instabilidade recente
❌ Observability incompleta
❌ Backup não testado
❌ Equipe não preparada
❌ Período de alta demanda
```

---

## 🎯 **PROCESSO DE ATIVAÇÃO**

### **Checklist Pré-Ativação:**
```bash
□ Sistema estável por 2+ semanas
□ Observability 100% funcional
□ Backup/recovery testados
□ Documentação chaos engineering lida
□ Equipe preparada para emergências
□ Período de baixa demanda escolhido
□ Stakeholders notificados
```

### **Processo de Ativação:**
```bash
1. Validar checklist pré-ativação
2. Solicitar ativação via linguagem natural
3. Confirmar recursos FIS criados
4. Executar primeiro teste controlado
5. Monitorar resultados
6. Documentar lições aprendidas
```

---

## 📈 **BENEFÍCIOS DA ESTRATÉGIA**

### **Segurança:**
```bash
✅ Zero risco de chaos acidental
✅ Implementação controlada e gradual
✅ Tempo para preparação adequada
✅ Validação de pré-requisitos
```

### **Financeiro:**
```bash
✅ Zero custos até necessidade real
✅ Budget predictable e controlado
✅ ROI maximizado quando ativado
✅ Sustentabilidade garantida
```

### **Operacional:**
```bash
✅ Foco em estabilidade primeiro
✅ Chaos como evolução natural
✅ Equipe preparada adequadamente
✅ Processo documentado e testado
```

---

## 🚀 **CONCLUSÃO**

A estratégia de **FIS desabilitado por padrão** é a abordagem mais **segura, econômica e responsável** para o projeto IaL:

- **Segurança primeiro:** Sistema estável antes de chaos
- **Custo controlado:** Zero gastos até necessidade
- **Implementação gradual:** Evolução natural e controlada
- **Preparação adequada:** Equipe e processo prontos

**Quando o sistema estiver 100% estável e a equipe preparada, a ativação será simples e segura através de linguagem natural.**

---

*Estratégia definida em: 24 de outubro de 2025*
*Status atual: ChaosEnabled=false (SEGURO)*
*Próxima revisão: Quando solicitada ativação*
