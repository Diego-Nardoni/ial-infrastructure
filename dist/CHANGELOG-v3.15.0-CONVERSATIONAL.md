# IAL v3.15.0-CONVERSATIONAL - Sistema de Diálogo Inteligente

## 🎯 NOVA FUNCIONALIDADE PRINCIPAL

### Sistema Conversacional LLM+MCP
- **LLM Clarification Engine**: Análise inteligente de requisitos ambíguos
- **MCP Fallback Analysis**: Detecção técnica de gaps quando LLM falha
- **Perguntas Contextuais**: Por tipo de serviço (ECS, RDS, Lambda, etc.)
- **Interface Conversacional**: Clara, estruturada e profissional

## 🔧 EXEMPLO DE USO

```bash
$ ialctl
🔵 IAL> crie uma ecs

🤔 **Preciso de mais detalhes sobre: 'crie uma ecs'**

**1. Qual aplicação você quer containerizar?**
   1) Aplicação web (nginx/apache)
   2) API backend (node/python)
   3) Worker/batch job
   4) Microserviço customizado
   💡 *Preciso saber a imagem Docker, CPU, memória e portas*

**2. Como será o acesso de rede?**
   1) Público com ALB
   2) Privado (VPC)
   3) Sem acesso externo
   💡 *Define se usa VPC pública, privada ou load balancer*

**3. Quantas instâncias você precisa?**
   1) 1 instância (desenvolvimento)
   2) 2-5 instâncias (produção)
   3) Auto scaling baseado em CPU
   💡 *Define configurações de auto scaling*

📝 **Responda com detalhes ou números das opções para prosseguir.**
```

## ✅ CORREÇÕES IMPLEMENTADAS

### Error Handling Enterprise-Grade
- **Timeout Robusto**: 15s no LLM com fallback automático
- **Template JSON**: Corrigido escape de chaves
- **Status Preservation**: Mantém `needs_clarification` até o usuário
- **Fallback Chain**: LLM → MCP → Emergency (nunca falha)

### Arquitetura Robusta
- **MCP Orchestrator**: Método `analyze_requirements` implementado
- **Service Detection**: ECS, RDS, Lambda, S3, API Gateway, VPC, EC2
- **Gap Analysis**: Por serviço específico (task_definition, networking, etc.)
- **Confidence Scoring**: Baseado na especificidade do input

## 🎯 SERVIÇOS SUPORTADOS

### ECS (Elastic Container Service)
- **Gaps Detectados**: task_definition, networking, scaling
- **Perguntas**: Aplicação, acesso de rede, instâncias

### RDS (Relational Database Service)
- **Gaps Detectados**: database_engine, instance_size, availability
- **Perguntas**: Engine, tamanho, Multi-AZ

### Lambda
- **Gaps Detectados**: runtime, performance_config
- **Perguntas**: Linguagem, performance

## 🔧 INSTALAÇÃO

```bash
# Download
wget https://github.com/Diego-Nardoni/ial-infrastructure/releases/download/v3.15.0/ialctl-3.15.0-CONVERSATIONAL-20251202.deb

# Instalar
sudo dpkg -i ialctl-3.15.0-CONVERSATIONAL-20251202.deb

# Usar
ialctl  # Interface conversacional
ialctl start  # Deploy foundation
```

## 📋 COMPATIBILIDADE

- **AWS Bedrock**: LLM provider principal
- **MCP Servers**: 17 MCPs (9 core + 8 domain-specific)
- **Fallback Robusto**: Funciona mesmo com falhas de LLM
- **Memory System**: Integração completa com DynamoDB

## 🎉 RESULTADO

**ANTES**: "crie uma ecs" → Gera templates automaticamente
**AGORA**: "crie uma ecs" → Faz perguntas inteligentes → Gera templates refinados

Sistema conversacional enterprise-grade que transforma requisitos ambíguos em especificações técnicas precisas através de diálogo inteligente.
