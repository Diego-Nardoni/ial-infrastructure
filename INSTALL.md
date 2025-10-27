# 🚀 IaL - Instalação Rápida

## Instalação em 2 passos:

### 1. Execute o instalador:
```bash
cd /home/ial
python3 setup.py
```

### 2. Quando aparecer a pergunta, digite:
```
instalar tudo
```

## ✅ Após a instalação:

O sistema criará automaticamente:
- ✅ Alias `ial` no seu shell
- ✅ Script de ativação `activate_alias.sh`
- ✅ Infraestrutura AWS necessária

## 🎯 Como usar:

### Opção 1: Alias (mais fácil)
```bash
source ~/.bashrc
ial
```

### Opção 2: Script de ativação
```bash
./activate_alias.sh
```

### Opção 3: Comando direto
```bash
cd /home/ial && python3 natural_language_processor.py interactive
```

## 💬 Comandos especiais:
- `clear` ou `Ctrl+L` - Limpa a tela
- `quit` ou `exit` - Sair do sistema
- `status` - Status do sistema

## 💬 Exemplos de uso:
```
👤 Você: "Qual o status da minha infraestrutura?"
👤 Você: "Crie um bucket S3 seguro"
👤 Você: "Deploy segurança para produção"
👤 Você: clear  # Limpa a tela
```

## 🔧 Troubleshooting:

**Problema**: Alias não funciona
**Solução**: `source ~/.bashrc && ial`

**Problema**: AWS não configurado
**Solução**: `aws configure` primeiro

**Problema**: Bedrock não disponível
**Solução**: Habilite Claude 3.5 no AWS Console → Bedrock → Model access

**Problema**: Ctrl+L não limpa a tela
**Solução**: Use o comando `clear` como alternativa
