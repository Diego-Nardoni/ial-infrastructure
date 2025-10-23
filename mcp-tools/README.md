# MCP Tools for IaL v2.0

MCP (Model Context Protocol) tools para integração com Amazon Q.

## Tools Disponíveis

### 1. update_yaml_file
Atualiza arquivos YAML de infraestrutura.

**Uso com Amazon Q:**
```bash
q chat "Adicione porta 8443 no security group do ALB"
```

**Uso direto:**
```bash
python update_yaml_file.py \
  "phases/03-networking.yaml" \
  "security_group_alb.ingress" \
  "append" \
  '{"port": 8443, "cidr": "0.0.0.0/0"}'
```

### 2. git_commit
Faz commit das mudanças.

**Uso com Amazon Q:**
```bash
# Automático após update_yaml_file
```

**Uso direto:**
```bash
python git_commit.py \
  "phases/03-networking.yaml" \
  "Add port 8443 to ALB SG"
```

### 3. git_push
Faz push para repositório remoto.

**Uso com Amazon Q:**
```bash
# Automático após git_commit
```

**Uso direto:**
```bash
python git_push.py origin main
```

## Configuração

Para usar com Amazon Q, adicione ao `mcp-server-config.json`:

```json
{
  "mcpServers": {
    "ial-tools": {
      "command": "python",
      "args": ["-m", "mcp_tools.server"],
      "tools": [
        "update_yaml_file",
        "git_commit",
        "git_push"
      ]
    }
  }
}
```

## Fluxo Completo

```
1. Você: q chat "Adicione porta 8443 no SG do ALB"
   ↓
2. Amazon Q chama: update_yaml_file()
   ↓
3. Amazon Q chama: git_commit()
   ↓
4. Amazon Q chama: git_push()
   ↓
5. GitHub Actions detecta push e aplica mudanças
```

## Dependências

```bash
pip install pyyaml
```

## Testes

```bash
# Test update_yaml_file
python update_yaml_file.py \
  "phases/03-networking.yaml" \
  "test.field" \
  "replace" \
  "test_value"

# Test git_commit
python git_commit.py \
  "phases/03-networking.yaml" \
  "Test commit"

# Test git_push
python git_push.py origin main
```
