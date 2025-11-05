# GitHub MCP Server Integration

## Visão Geral

O GitHub MCP Server foi integrado ao sistema IAL para fornecer capacidades completas de integração com GitHub, incluindo gerenciamento de repositórios, issues, pull requests e workflows.

## Configuração

### 1. Variáveis de Ambiente

```bash
export GITHUB_TOKEN="your_github_personal_access_token"
```

### 2. Instalação

O GitHub MCP Server é instalado automaticamente via npm:

```bash
npx -y @modelcontextprotocol/server-github
```

### 3. Configuração no IAL

O servidor está configurado em:
- `/home/ial/config/mcp-mesh.yaml` - Domínio DevOps
- `/home/ial/mcp-server-config.json` - Configuração do servidor
- `/home/ial/config/github_mcp.yaml` - Configuração específica

## Capacidades

### Repositórios
- `create_repository` - Criar novos repositórios
- `search_repositories` - Buscar repositórios
- `fork_repository` - Fazer fork de repositórios
- `get_repository_info` - Obter informações do repositório

### Issues
- `create_issue` - Criar issues
- `list_issues` - Listar issues
- `update_issue` - Atualizar issues
- `close_issue` - Fechar issues

### Pull Requests
- `create_pull_request` - Criar PRs
- `list_pull_requests` - Listar PRs
- `merge_pull_request` - Fazer merge de PRs
- `review_pull_request` - Revisar PRs

### Arquivos
- `get_file` - Obter conteúdo de arquivos
- `create_or_update_file` - Criar/atualizar arquivos
- `push_files` - Push de múltiplos arquivos
- `delete_file` - Deletar arquivos

### Busca
- `search_code` - Buscar código
- `search_issues` - Buscar issues
- `search_repositories` - Buscar repositórios
- `search_users` - Buscar usuários

### Workflows
- `list_workflows` - Listar workflows
- `trigger_workflow` - Disparar workflows
- `get_workflow_runs` - Obter execuções de workflows

## Integração Automática com IAL

### Triggers Automáticos

1. **Mudanças de Infraestrutura**
   - Evento: `infrastructure_change`
   - Ação: Criar PR automaticamente
   - Template: `infrastructure_update`

2. **Detecção de Drift**
   - Evento: `drift_detected`
   - Ação: Criar issue automaticamente
   - Template: `drift_alert`

3. **Deploy Completo**
   - Evento: `deployment_complete`
   - Ação: Atualizar issue existente
   - Template: `deployment_status`

### Palavras-chave de Ativação

O GitHub MCP é ativado automaticamente quando detectadas as seguintes palavras-chave:

- `github`, `git`, `repository`, `repo`
- `pull request`, `pr`, `commit`, `branch`, `merge`
- `issue`, `workflow`, `action`
- `ci/cd`, `pipeline`, `deployment`, `release`

## Exemplos de Uso

### Criar Repositório
```python
result = await github_mcp.create_repository(
    name="my-new-repo",
    description="Repository created by IAL",
    private=False
)
```

### Criar Issue para Drift
```python
result = await github_mcp.create_issue(
    owner="myorg",
    repo="infrastructure",
    title="Infrastructure Drift Detected - S3 Bucket",
    body="Drift detected in S3 bucket configuration..."
)
```

### Criar PR para Mudanças
```python
result = await github_mcp.create_pull_request(
    owner="myorg",
    repo="infrastructure",
    title="Infrastructure Update - 2025-11-05",
    body="Automated infrastructure changes...",
    head="feature/auto-update",
    base="main"
)
```

## Monitoramento

### Métricas Coletadas
- `api_calls_total` - Total de chamadas à API
- `api_errors_total` - Total de erros
- `response_time` - Tempo de resposta
- `rate_limit_remaining` - Rate limit restante

### Alertas Configurados
- Rate limit baixo (< 100 requests)
- Muitos erros (> 10 erros)

## Segurança

### Configurações de Segurança
- Validação de token obrigatória
- Rate limiting habilitado
- Operações permitidas: read, write, admin (repositórios específicos)

### Boas Práticas
1. Use Personal Access Tokens com escopo mínimo necessário
2. Configure webhooks para eventos importantes
3. Monitore uso de rate limits
4. Revise permissões regularmente

## Troubleshooting

### Problemas Comuns

1. **Token inválido**
   - Verifique se `GITHUB_TOKEN` está configurado
   - Confirme se o token tem as permissões necessárias

2. **Rate limit excedido**
   - Aguarde reset do rate limit
   - Configure throttling automático

3. **Timeout de conexão**
   - Verifique conectividade de rede
   - Aumente timeout se necessário

### Logs
```bash
# Visualizar logs do GitHub MCP
tail -f /home/ial/logs/github_mcp.log

# Filtrar erros
grep "ERROR" /home/ial/logs/github_mcp.log
```

## Próximos Passos

1. Configurar webhooks para eventos GitHub
2. Implementar sincronização bidirecional
3. Adicionar suporte para GitHub Actions
4. Integrar com sistema de notificações IAL
