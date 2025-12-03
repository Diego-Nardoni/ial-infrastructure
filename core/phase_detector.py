#!/usr/bin/env python3
"""
Phase Detector - Detecta phases existentes e sugere ações apropriadas
"""

import os
import re
from typing import Dict, List, Optional, Tuple

class PhaseDetector:
    """Detecta phases existentes e sugere comportamento apropriado"""
    
    def __init__(self, phases_dir: str = "/home/ial/phases"):
        self.phases_dir = phases_dir
        self.existing_phases = self._scan_existing_phases()
    
    def _scan_existing_phases(self) -> Dict[str, Dict]:
        """Escaneia phases existentes no diretório"""
        phases = {}
        
        try:
            if not os.path.exists(self.phases_dir):
                return phases
            
            for item in os.listdir(self.phases_dir):
                item_path = os.path.join(self.phases_dir, item)
                
                # Skip workloads directory and non-phase directories
                if item == 'workloads' or not os.path.isdir(item_path):
                    continue
                
                # Check if it's a phase directory (starts with number)
                if re.match(r'^\d{2}-', item):
                    phase_info = self._analyze_phase(item, item_path)
                    phases[item] = phase_info
            
            return phases
            
        except Exception as e:
            print(f"⚠️ Erro escaneando phases: {e}")
            return {}
    
    def _analyze_phase(self, phase_name: str, phase_path: str) -> Dict:
        """Analisa uma phase específica"""
        
        try:
            files = []
            total_size = 0
            
            for file in os.listdir(phase_path):
                if file.endswith(('.yaml', '.yml')):
                    file_path = os.path.join(phase_path, file)
                    file_size = os.path.getsize(file_path)
                    files.append({
                        'name': file,
                        'size': file_size
                    })
                    total_size += file_size
            
            return {
                'name': phase_name,
                'path': phase_path,
                'files': files,
                'file_count': len(files),
                'total_size': total_size,
                'exists': True
            }
            
        except Exception as e:
            return {
                'name': phase_name,
                'path': phase_path,
                'exists': False,
                'error': str(e)
            }
    
    def detect_phase_intent(self, user_request: str) -> Optional[Dict]:
        """Detecta se o usuário está tentando criar/modificar uma phase existente"""
        
        request_lower = user_request.lower()
        
        # Padrões para detectar intenção de phase
        phase_patterns = [
            r'criar?\s+phase?\s+(\d{2}-\w+)',
            r'phase?\s+(\d{2}-\w+)',
            r'(\d{2}-\w+)\s+phase?',
            r'deploy\s+(\d{2}-\w+)',
            r'modificar?\s+(\d{2}-\w+)'
        ]
        
        for pattern in phase_patterns:
            match = re.search(pattern, request_lower)
            if match:
                phase_name = match.group(1)
                return self._check_phase_exists(phase_name, user_request)
        
        return None
    
    def _check_phase_exists(self, phase_name: str, original_request: str) -> Dict:
        """Verifica se a phase existe e retorna sugestões"""
        
        # Normalizar nome da phase
        normalized_name = phase_name.lower()
        
        # Procurar phase exata
        exact_match = None
        for existing_phase in self.existing_phases:
            if existing_phase.lower() == normalized_name:
                exact_match = existing_phase
                break
        
        if exact_match:
            return {
                'phase_detected': True,
                'phase_name': exact_match,
                'phase_exists': True,
                'phase_info': self.existing_phases[exact_match],
                'suggestion_type': 'existing_phase',
                'suggestions': self._generate_existing_phase_suggestions(exact_match, original_request)
            }
        
        # Procurar phases similares
        similar_phases = self._find_similar_phases(normalized_name)
        
        if similar_phases:
            return {
                'phase_detected': True,
                'phase_name': phase_name,
                'phase_exists': False,
                'similar_phases': similar_phases,
                'suggestion_type': 'similar_phases',
                'suggestions': self._generate_similar_phase_suggestions(similar_phases, original_request)
            }
        
        return {
            'phase_detected': True,
            'phase_name': phase_name,
            'phase_exists': False,
            'suggestion_type': 'new_phase',
            'suggestions': self._generate_new_phase_suggestions(phase_name, original_request)
        }
    
    def _find_similar_phases(self, phase_name: str) -> List[str]:
        """Encontra phases com nomes similares"""
        
        similar = []
        
        # Extrair keywords do nome da phase
        keywords = re.findall(r'\w+', phase_name)
        
        for existing_phase in self.existing_phases:
            existing_lower = existing_phase.lower()
            
            # Check for keyword matches
            for keyword in keywords:
                if keyword in existing_lower and len(keyword) > 2:
                    similar.append(existing_phase)
                    break
        
        return similar[:3]  # Máximo 3 sugestões
    
    def _generate_existing_phase_suggestions(self, phase_name: str, original_request: str) -> Dict:
        """Gera sugestões para phase existente"""
        
        phase_info = self.existing_phases[phase_name]
        
        return {
            'message': f"🎯 A phase **{phase_name}** já existe!",
            'details': f"📁 {phase_info['file_count']} arquivos, {phase_info['total_size']} bytes",
            'options': [
                {
                    'action': 'deploy',
                    'command': f'ialctl deploy {phase_name}',
                    'description': f'Fazer deploy da phase {phase_name} existente'
                },
                {
                    'action': 'modify',
                    'command': f'modificar phase {phase_name}',
                    'description': f'Modificar configurações da phase {phase_name}'
                },
                {
                    'action': 'view',
                    'command': f'mostrar phase {phase_name}',
                    'description': f'Ver detalhes da phase {phase_name}'
                }
            ],
            'recommendation': f"✅ **Recomendação:** Use `ialctl deploy {phase_name}` para fazer deploy da phase existente."
        }
    
    def _generate_similar_phase_suggestions(self, similar_phases: List[str], original_request: str) -> Dict:
        """Gera sugestões para phases similares"""
        
        return {
            'message': f"🤔 Não encontrei essa phase exata, mas encontrei phases similares:",
            'similar_phases': similar_phases,
            'options': [
                {
                    'action': 'deploy_similar',
                    'phases': similar_phases,
                    'description': 'Fazer deploy de uma das phases similares'
                },
                {
                    'action': 'create_new',
                    'description': 'Criar nova phase personalizada'
                }
            ],
            'recommendation': f"✅ **Sugestão:** Verifique se uma das phases similares atende sua necessidade."
        }
    
    def _generate_new_phase_suggestions(self, phase_name: str, original_request: str) -> Dict:
        """Gera sugestões para nova phase"""
        
        return {
            'message': f"🆕 A phase **{phase_name}** não existe.",
            'options': [
                {
                    'action': 'create_custom',
                    'description': f'Criar nova phase {phase_name} personalizada'
                },
                {
                    'action': 'view_existing',
                    'description': 'Ver todas as phases disponíveis'
                }
            ],
            'recommendation': f"💡 **Dica:** Use `ialctl list-phases` para ver todas as phases disponíveis."
        }
    
    def get_all_phases(self) -> Dict[str, Dict]:
        """Retorna todas as phases existentes"""
        return self.existing_phases
    
    def format_phase_suggestions(self, detection_result: Dict) -> str:
        """Formata sugestões de phase para o usuário"""
        
        if not detection_result.get('phase_detected'):
            return ""
        
        suggestions = detection_result.get('suggestions', {})
        message = suggestions.get('message', '')
        
        response = f"{message}\n\n"
        
        # Add details if available
        if 'details' in suggestions:
            response += f"{suggestions['details']}\n\n"
        
        # Add options
        options = suggestions.get('options', [])
        if options:
            response += "**Opções disponíveis:**\n"
            for i, option in enumerate(options, 1):
                if 'command' in option:
                    response += f"{i}. `{option['command']}` - {option['description']}\n"
                else:
                    response += f"{i}. {option['description']}\n"
            response += "\n"
        
        # Add recommendation
        if 'recommendation' in suggestions:
            response += f"{suggestions['recommendation']}\n"
        
        return response
