#!/usr/bin/env python3

class IaLNaturalProcessor:
    def __init__(self):
        pass
    
    def _enrich_context_if_needed(self, user_input):
        # Keywords para LISTAGEM (não deve gerar YAML)
        list_indicators = [
            "liste as fases", "listar fases", "mostrar fases", "fases disponiveis",
            "quais fases", "ver fases", "fases do ial", "phases ial"
        ]
        
        # Keywords para CRIACAO (só gera YAML se fase não existir)
        create_indicators = [
            "criar fase", "nova fase", "adicionar fase", "gerar fase", 
            "implementar fase", "criar uma fase", "fazer uma fase"
        ]
        
        # LISTAGEM - apenas informacao, sem geracao de YAML
        if any(indicator in user_input.lower() for indicator in list_indicators):
            return f"""
CONTEXTO: O usuario quer VER/LISTAR as fases do sistema IAL do repositorio GitHub.

ACAO: Consultar GitHub para listar fases existentes, NAO gerar templates YAML.

INSTRUCOES PARA O LLM:
1. Use o MCP GitHub para acessar o repositorio
2. Liste os diretorios em /phases/
3. Mostre apenas as fases que existem no GitHub
4. NAO use informacoes hardcoded
5. NAO gere nenhum arquivo YAML

PERGUNTA DO USUARIO: {user_input}

IMPORTANTE: Consulte o GitHub como fonte unica da verdade para listar fases existentes.
"""
        
        # CRIACAO - consultar GitHub para verificar fases existentes
        elif any(indicator in user_input.lower() for indicator in create_indicators):
            return f"""
CONTEXTO: O usuario quer trabalhar com fases do sistema IAL.

INSTRUCOES PARA O LLM:
1. PRIMEIRO: Use MCP GitHub para consultar diretorio /phases/
2. Verifique quais fases ja existem no repositorio
3. Se fase solicitada JA EXISTE: apenas informar e mostrar conteudo
4. Se fase solicitada e NOVA: criar estrutura completa com YAML

REGRAS IMPORTANTES:
- GitHub e a unica fonte da verdade
- NAO use listas hardcoded de fases
- Consulte sempre o repositorio atual
- Padrao de nomenclatura: XX-nome-da-fase

PERGUNTA DO USUARIO: {user_input}

IMPORTANTE: 
- Consulte GitHub primeiro para verificar fases existentes
- So crie YAML se a fase realmente nao existir no repositorio
"""
        
        # Retorna input original se nao precisar de contexto
        return user_input

    def process_command(self, user_input, user_id, session_id):
        # Implementacao basica
        enriched_input = self._enrich_context_if_needed(user_input)
        return f"Processando: {enriched_input[:100]}..."
