# CHANGELOG v3.14.1-HOTFIX - 2025-12-01

## 🔧 HOTFIX: Query vs Create Intent Detection

### ✅ Problema Corrigido
- **Issue:** "liste meus buckets do s3" estava fazendo deploy da foundation
- **Causa:** Intelligent MCP Router não diferenciava query vs create
- **Solução:** Adicionada detecção de intenção via LLM patterns

### 🧠 Correção Implementada
```python
# Detectar intenção (query vs create)
is_query = any(word in user_input for word in [
    'liste', 'list', 'show', 'mostrar', 'ver', 'consultar'
])

# Query → Resource Query Path (boto3 direto)
# Create → AWS Real Executor (deploy)
```

### 🎯 Resultado
```
IAL> liste meus buckets do s3
📋 RESOURCE QUERY REQUEST - Consulta direta via boto3

📋 **S3 Resources**
🪣 ial-artifacts-221082174220 (criado: 2025-11-13)
🪣 ial-fork-state-221082174220 (criado: 2025-11-10)
✅ Total: 10 recursos
```

### 📦 Novo Instalador
- **Binário:** `ialctl` (47.8MB)
- **Pacote:** `ialctl-3.14.1-HOTFIX-20251201.deb`
- **Correção:** Intent detection funcional
- **Performance:** Consultas sub-segundo

---
**Status:** ✅ HOTFIX DEPLOYED  
**Versão:** 3.14.1-HOTFIX-20251201  
**Compilado:** 2025-12-01 20:27 UTC
