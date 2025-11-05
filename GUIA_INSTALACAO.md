# Guia de Instalação - IAL (Infrastructure as Language)

## Instalação via Pacote .deb (Recomendado)

Você pode instalar o IAL para linha de comando no Ubuntu usando o pacote .deb.

Para instalar o IAL para linha de comando no Ubuntu, siga o procedimento abaixo.

### 1. Baixe o IAL para linha de comando no Ubuntu
```bash
wget https://github.com/SEU_USUARIO/ial/releases/latest/download/ialctl_amd64.deb
```

### 2. Instale o pacote
```bash
sudo dpkg -i ialctl_amd64.deb
sudo apt-get install -f
```

### 3. Verificar Instalação
```bash
ialctl --version
ialctl
```

## Método 2: Build e Instalação Manual

### 1. Clonar o Repositório
```bash
git clone <URL_DO_REPOSITORIO> /opt/ial
cd /opt/ial
```

### 2. Instalar Dependências de Build
```bash
sudo apt update
sudo apt install -y python3-pip python3-venv git build-essential ruby ruby-dev
sudo gem install fpm
pip3 install pyinstaller boto3 pyyaml openai
```

### 3. Executar Build
```bash
./build/build_linux.sh
```

### 4. Instalar o Pacote Gerado
```bash
sudo dpkg -i dist/packages/ialctl_*_amd64.deb
```

## Método 3: Instalação Direta do Binário

### 1. Copiar Binário
```bash
# Após o build ou download
sudo cp dist/linux/ialctl /usr/local/bin/
sudo chmod +x /usr/local/bin/ialctl
```

### 2. Verificar Instalação
```bash
ialctl --version
```

## Configuração Inicial

### 1. Configurar AWS (Opcional - para funcionalidade completa)
```bash
# Instalar AWS CLI se necessário
sudo apt install awscli

# Configurar credenciais
aws configure
```

### 2. Configurar Variáveis de Ambiente
```bash
# Criar arquivo de configuração
sudo mkdir -p /etc/ial
sudo cp parameters.env.example /etc/ial/parameters.env

# Editar configurações
sudo nano /etc/ial/parameters.env
```

### 3. Testar Funcionalidade Básica
```bash
# Teste básico (modo fallback)
ialctl

# Teste com entrada
echo "Hello, I need help with my infrastructure" | ialctl
```

## Verificação da Instalação

### 1. Verificar Versão
```bash
ialctl --version
```

### 2. Teste de Funcionalidade
```bash
# Modo interativo
ialctl

# Comando direto
ialctl "show me the system status"
```

### 3. Verificar Logs (se necessário)
```bash
# Logs do sistema
journalctl -u ialctl

# Logs locais
tail -f /var/log/ial/ial.log
```

## Solução de Problemas

### Erro: "No module named 'ial_master_engine'"
- **Normal**: Sistema funcionando em modo fallback
- **Solução**: Configure AWS Bedrock para funcionalidade completa

### Erro: "Permission denied"
```bash
sudo chmod +x /usr/local/bin/ialctl
```

### Erro: Dependências faltando
```bash
sudo apt-get install -f
```

### Erro: Python não encontrado
```bash
sudo apt install python3 python3-pip
```

## Desinstalação

### Via apt (se instalado via .deb)
```bash
sudo apt remove ialctl
```

### Manual
```bash
sudo rm /usr/local/bin/ialctl
sudo rm -rf /etc/ial
```

## Funcionalidades Disponíveis

### Modo Fallback (Sem AWS)
- ✅ Processamento básico de linguagem natural
- ✅ Comandos de infraestrutura básicos
- ✅ Análise de configurações

### Modo Completo (Com AWS Bedrock)
- ✅ IA conversacional avançada
- ✅ Integração completa com AWS
- ✅ Análise de custos e compliance
- ✅ Automação de infraestrutura

## Suporte

Para problemas ou dúvidas:
1. Verificar logs: `journalctl -u ialctl`
2. Testar modo básico: `ialctl --help`
3. Verificar configuração: `cat /etc/ial/parameters.env`

---

**Versão do Guia**: 1.0  
**Última Atualização**: 2025-11-04  
**Compatibilidade**: Ubuntu 20.04+, Debian 11+
