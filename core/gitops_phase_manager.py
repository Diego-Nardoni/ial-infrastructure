#!/usr/bin/env python3
"""
GitOps Phase Manager - Discovery dinâmico de phases via Git
GitHub como única fonte da verdade
"""

import os
import subprocess
import json
from typing import List, Dict, Optional
from pathlib import Path


class GitOpsPhaseManager:
    """Gerencia phases via GitOps puro - sem hardcoding"""
    
    def __init__(self, repo_path: str = "/home/ial"):
        self.repo_path = repo_path
        self.phases_dir = os.path.join(repo_path, "phases")
        self.deploy_dir = os.path.join(self.phases_dir, ".deploy")
        self.deployed_dir = os.path.join(self.phases_dir, ".deployed")
        
        # Criar diretórios se não existirem
        os.makedirs(self.deploy_dir, exist_ok=True)
        os.makedirs(self.deployed_dir, exist_ok=True)
    
    def discover_phases(self) -> List[Dict[str, str]]:
        """Descobre phases disponíveis dinamicamente via Git"""
        phases = []
        
        try:
            # Listar arquivos YAML em phases/
            for file in Path(self.phases_dir).glob("*.yaml"):
                if file.name.startswith('.'):
                    continue
                
                phases.append({
                    "name": file.stem,
                    "file": file.name,
                    "path": str(file),
                    "size": file.stat().st_size
                })
            
            return sorted(phases, key=lambda x: x['name'])
        
        except Exception as e:
            return [{"error": str(e)}]
    
    def trigger_deployment(self, phase_name: str) -> Dict[str, str]:
        """Cria trigger para deployment via GitOps"""
        
        # 1. Verificar se phase existe
        phases = self.discover_phases()
        phase = next((p for p in phases if phase_name.lower() in p['name'].lower()), None)
        
        if not phase:
            return {
                "status": "error",
                "message": f"Phase '{phase_name}' não encontrada",
                "available_phases": [p['name'] for p in phases]
            }
        
        # 2. Criar trigger file
        trigger_file = os.path.join(self.deploy_dir, f"{phase['name']}.trigger")
        trigger_content = {
            "phase": phase['name'],
            "file": phase['file'],
            "requested_at": subprocess.check_output(['date', '-Iseconds']).decode().strip(),
            "status": "pending"
        }
        
        with open(trigger_file, 'w') as f:
            json.dump(trigger_content, f, indent=2)
        
        # 3. Git commit + push
        try:
            subprocess.run(['git', 'add', self.deploy_dir], cwd=self.repo_path, check=True)
            subprocess.run([
                'git', 'commit', '-m', 
                f'deploy: Trigger deployment of {phase["name"]}'
            ], cwd=self.repo_path, check=True)
            subprocess.run(['git', 'push', 'origin', 'main'], cwd=self.repo_path, check=True)
            
            return {
                "status": "success",
                "message": f"✅ Deployment trigger criado para {phase['name']}",
                "phase": phase['name'],
                "trigger_file": trigger_file,
                "next_steps": [
                    "1. GitHub Actions detectará o trigger em ~30s",
                    "2. Workflow validará CloudFormation",
                    "3. Pull Request será aberto automaticamente",
                    "4. Aprove o PR para executar deployment",
                    "5. Recursos serão criados na AWS"
                ]
            }
        
        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "message": f"Erro no Git: {e}",
                "trigger_created": True,
                "git_failed": True
            }
    
    def list_pending_deployments(self) -> List[Dict]:
        """Lista deployments pendentes"""
        pending = []
        
        for file in Path(self.deploy_dir).glob("*.trigger"):
            with open(file) as f:
                trigger = json.load(f)
                pending.append(trigger)
        
        return pending
    
    def get_deployment_status(self, phase_name: str) -> Optional[Dict]:
        """Verifica status de deployment"""
        status_file = os.path.join(self.deployed_dir, f"{phase_name}.status")
        
        if os.path.exists(status_file):
            with open(status_file) as f:
                return json.load(f)
        
        return None
