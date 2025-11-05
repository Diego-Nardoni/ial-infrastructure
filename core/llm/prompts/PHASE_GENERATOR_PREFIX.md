# IaL — Phase Generator (STRICT MODE)

Gere um **phase.yaml** seguindo EXATAMENTE o schema `ial/v1` e o template canônico.
NUNCA omita seções. NUNCA mude nomes de campos. Inclua `wa_pillars` (≥3).
Inclua `outputs_contract.must_exist` com pelo menos 1 item e `tags_must_include` contendo `ial:managed`.

Use como referência o arquivo `templates/prompt_phase_template.yaml`.

## CAMPOS OBRIGATÓRIOS:

### metadata:
- name: Formato "NN-nome-descritivo" (ex: "01-networking-vpc")
- domain: Domínio técnico (networking, security, compute, etc.)
- priority: Número 1-1000
- wa_pillars: Mínimo 3 pilares Well-Architected

### spec:
- description: Descrição clara (mínimo 10 caracteres)
- parameters: Use variáveis de ambiente (${ENVIRONMENT}, ${AWS_DEFAULT_REGION})
- artifacts.cloudformation.template: Caminho do template CloudFormation

### outputs_contract:
- must_exist: Lista com pelo menos 1 output obrigatório
- tags_must_include: Deve conter "ial:managed"

### tests:
- lint: Lista de ferramentas de lint
- acceptance.natural_validation: Prompts para validação LLM

### gitops:
- repo: Use "${GITHUB_REPOSITORY}"
- base_branch: Use "${GITHUB_BASE_REF}"
- require_reviews: true
- required_checks: Mínimo 4 checks

## PADRÕES AWS REFERENCE:
- Use variáveis de ambiente: ${ENVIRONMENT}, ${AWS_DEFAULT_REGION}
- Use cookiecutter placeholders: {{cookiecutter.variable}}
- Evite valores hardcoded
- Use SSM Parameter Store para configurações

## EXEMPLO DE USO:
```yaml
apiVersion: ial/v1
kind: Phase
metadata:
  name: "02-security-kms"
  domain: "security"
  priority: 200
  wa_pillars: [security, cost-optimization, operational-excellence]
spec:
  parameters:
    env: "${ENVIRONMENT}"
    region: "${AWS_DEFAULT_REGION}"
gitops:
  repo: "${GITHUB_REPOSITORY}"
  base_branch: "${GITHUB_BASE_REF}"
```

SEMPRE valide contra o schema antes de retornar o YAML.
