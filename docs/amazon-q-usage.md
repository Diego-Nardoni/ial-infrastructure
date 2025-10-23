# Amazon Q + MCP Tools - Guia de Uso

**IaL v2.0 - Interface de Linguagem Natural**

---

## 🎯 Visão Geral

Com IaL v2.0, você pode gerenciar infraestrutura AWS usando linguagem natural através do Amazon Q.

**Fluxo:**
```
Você → Amazon Q → MCP Tools → Git Push → GitHub Actions → AWS
```

---

## 🚀 Comandos Disponíveis

### **1. Adicionar Porta no Security Group**

```bash
q chat "Adicione porta 8443 no security group do ALB"
```

**O que acontece:**
1. Amazon Q entende: "adicionar ingress rule"
2. MCP tool atualiza: `phases/03-networking.yaml`
3. Git commit: "Add port 8443 to ALB SG"
4. Git push para GitHub
5. GitHub Actions aplica mudança na AWS

**Resultado:**
```
✅ Porta 8443 adicionada ao Security Group ALB (sg-abc123)
Tempo: 2-3 minutos
```

---

### **2. Remover Porta do Security Group**

```bash
q chat "Remova a porta 22 do security group do ALB"
```

**Resultado:**
```
✅ Porta 22 removida do Security Group ALB
```

---

### **3. Escalar ECS Service**

```bash
q chat "Aumente o número mínimo de tasks ECS para 5"
```

**O que acontece:**
1. Atualiza `phases/08-ecs-task-service.yaml`
2. Modifica `desired_count: 5`
3. GitHub Actions aplica mudança

**Resultado:**
```
✅ ECS Service escalado para 5 tasks mínimas
```

---

### **4. Modificar Health Check do ALB**

```bash
q chat "Mude o health check do ALB para /health em vez de /actuator/health/readiness"
```

**Resultado:**
```
✅ Health check path atualizado para /health
```

---

### **5. Adicionar Tag em Recursos**

```bash
q chat "Adicione a tag Environment=Production em todos os recursos"
```

**Resultado:**
```
✅ Tag Environment=Production adicionada em 61 recursos
```

---

### **6. Rollback**

```bash
q chat "Desfaça a última mudança"
```

**O que acontece:**
1. Amazon Q identifica último commit
2. Git revert automático
3. GitHub Actions aplica rollback

**Resultado:**
```
✅ Rollback completo - porta 8443 removida
Tempo: 2 minutos
```

---

## 💡 Dicas de Uso

### **Seja Específico**

❌ Ruim: "Adicione uma porta"  
✅ Bom: "Adicione porta 8443 no security group do ALB"

### **Use Nomes de Recursos**

❌ Ruim: "Escale a aplicação"  
✅ Bom: "Aumente o número mínimo de tasks ECS para 5"

### **Contexto Ajuda**

✅ "Adicione porta 8443 no SG do ALB para tráfego HTTPS alternativo"

Amazon Q entende o contexto e pode sugerir configurações adicionais.

---

## 🔍 Verificar Mudanças

### **Antes de Aplicar**

Amazon Q sempre mostra o que será modificado:

```
📝 Mudanças propostas:
- Arquivo: phases/03-networking.yaml
- Campo: security_group_alb.ingress
- Ação: Adicionar porta 8443
- Impacto: Permite tráfego HTTPS na porta 8443

Confirmar? (y/n)
```

### **Após Aplicar**

```bash
# Ver status do deploy
q chat "Qual o status do último deploy?"

# Ver recursos criados
q chat "Liste todos os recursos criados"

# Ver custos
q chat "Quanto está custando a infraestrutura?"
```

---

## ⚠️ Validações Automáticas

Amazon Q valida automaticamente:

### **Segurança**

```bash
q chat "Abra a porta 22 para 0.0.0.0/0"
```

**Resposta:**
```
⚠️ ATENÇÃO: Abrir SSH (22) para internet (0.0.0.0/0) é um risco de segurança.

Alternativas recomendadas:
1. Restringir a um IP específico
2. Usar AWS Systems Manager Session Manager
3. Usar bastion host

Você tem certeza? (y/n)
```

### **Custos**

```bash
q chat "Aumente o número máximo de tasks ECS para 50"
```

**Resposta:**
```
⚠️ ATENÇÃO: Isso pode aumentar o custo mensal em ~$900/mês

Custo atual: $470/mês
Custo estimado: $1,370/mês (+191%)

Confirmar? (y/n)
```

---

## 🎓 Exemplos Avançados

### **Mudanças Complexas**

```bash
q chat "Escale a aplicação para Black Friday:
- Mínimo 10 tasks
- Máximo 50 tasks
- Redis 10GB
- ALB timeout 120 segundos"
```

**Resultado:**
```
✅ Infraestrutura escalada para Black Friday

Mudanças aplicadas:
- ECS: 10-50 tasks (antes: 3-10)
- Redis: 10GB (antes: 5GB)
- ALB timeout: 120s (antes: 60s)

Custo estimado: $850/mês (+81%)
Tempo: 5 minutos
```

### **Troubleshooting**

```bash
q chat "Por que o health check está falhando?"
```

**Resposta:**
```
🔍 Análise do health check:

Problema identificado:
- Path configurado: /actuator/health/readiness
- Aplicação respondendo em: /health
- Status: 404 Not Found

Solução:
1. Mudar path do ALB para /health, ou
2. Mudar path da aplicação para /actuator/health/readiness

Quer que eu corrija? (y/n)
```

---

## 📊 Monitoramento

### **Ver Status**

```bash
q chat "Mostre o status da infraestrutura"
```

**Resposta:**
```
📊 Status da Infraestrutura

✅ Recursos: 61/61 criados
✅ Health checks: Todos passando
⚠️ Drift detectado: 1 recurso
💰 Custo mensal: $475

Último deploy: 2025-10-23 14:30 (há 2 horas)
Por: engineer-a
Status: SUCCESS
```

### **Ver Drift**

```bash
q chat "Há algum drift na infraestrutura?"
```

**Resposta:**
```
⚠️ 1 drift detectado:

Security Group sg-abc123:
- Porta 22 foi adicionada manualmente
- Severidade: CRITICAL
- Detectado: há 15 minutos

Quer corrigir automaticamente? (y/n)
```

---

## 🔧 Configuração

### **Primeira Vez**

```bash
# 1. Instalar dependências
pip install pyyaml

# 2. Configurar MCP tools
# (Amazon Q já vem com MCP configurado)

# 3. Testar
q chat "Olá, você pode me ajudar com infraestrutura AWS?"
```

### **Verificar Configuração**

```bash
q chat "Liste os MCP tools disponíveis"
```

**Resposta:**
```
🔧 MCP Tools Disponíveis:

1. update_yaml_file - Atualiza arquivos YAML
2. git_commit - Faz commit das mudanças
3. git_push - Faz push para GitHub

Status: ✅ Todos funcionando
```

---

## ✅ Boas Práticas

1. **Sempre revise mudanças** antes de confirmar
2. **Use comandos específicos** para melhores resultados
3. **Teste em dev** antes de aplicar em produção
4. **Monitore custos** após mudanças de escala
5. **Verifique drift** regularmente

---

## 🆘 Ajuda

```bash
# Ajuda geral
q chat "Como usar Amazon Q para gerenciar infraestrutura?"

# Ajuda específica
q chat "Como adicionar uma porta no security group?"

# Exemplos
q chat "Me dê exemplos de comandos que posso usar"
```

---

**Documentação completa:** `/home/ial/docs/`  
**MCP Tools:** `/home/ial/mcp-tools/`  
**Suporte:** Amazon Q está sempre disponível para ajudar! 🚀
