#!/usr/bin/env python3
"""
Version Manager - Sistema de Versionamento Avançado
Gerencia versões do desired state com rollback e diff
"""

import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import difflib
import hashlib

class VersionManager:
    def __init__(self, versions_dir: str = "./reports/versions"):
        self.versions_dir = Path(versions_dir)
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_file = Path("./reports/desired_spec.json")
        self.versions_index_file = self.versions_dir / "versions_index.json"
        
        # Carregar índice de versões
        self.versions_index = self._load_versions_index()
    
    def _load_versions_index(self) -> Dict:
        """Carrega índice de versões"""
        if self.versions_index_file.exists():
            try:
                with open(self.versions_index_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Erro ao carregar índice de versões: {e}")
        
        return {
            'versions': [],
            'current_version': None,
            'created_at': datetime.utcnow().isoformat()
        }
    
    def _save_versions_index(self):
        """Salva índice de versões"""
        try:
            with open(self.versions_index_file, 'w') as f:
                json.dump(self.versions_index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Erro ao salvar índice de versões: {e}")
    
    def create_version(self, spec: Dict, version_name: Optional[str] = None, 
                      description: Optional[str] = None) -> str:
        """Cria nova versão do desired state"""
        
        # Gerar nome da versão se não fornecido
        if not version_name:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            spec_hash = hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()[:8]
            version_name = f"v{timestamp}_{spec_hash}"
        
        # Criar entrada da versão
        version_entry = {
            'version': version_name,
            'created_at': datetime.utcnow().isoformat(),
            'description': description or f"Versão criada automaticamente em {datetime.utcnow().isoformat()}",
            'spec_hash': spec.get('metadata', {}).get('spec_hash'),
            'total_resources': len(spec.get('resources', [])),
            'total_domains': len(spec.get('domains', {})),
            'file_path': f"versions/{version_name}.json"
        }
        
        # Salvar arquivo da versão
        version_file = self.versions_dir / f"{version_name}.json"
        try:
            with open(version_file, 'w') as f:
                json.dump(spec, f, indent=2, ensure_ascii=False)
            
            # Atualizar índice
            self.versions_index['versions'].append(version_entry)
            self.versions_index['current_version'] = version_name
            self.versions_index['updated_at'] = datetime.utcnow().isoformat()
            
            self._save_versions_index()
            
            print(f"📦 Versão criada: {version_name}")
            print(f"  📄 Arquivo: {version_file}")
            print(f"  📊 Recursos: {version_entry['total_resources']}")
            print(f"  🏗️ Domínios: {version_entry['total_domains']}")
            
            return version_name
            
        except Exception as e:
            print(f"❌ Erro ao criar versão {version_name}: {e}")
            return None
    
    def list_versions(self) -> List[Dict]:
        """Lista todas as versões disponíveis"""
        return sorted(
            self.versions_index.get('versions', []),
            key=lambda v: v['created_at'],
            reverse=True
        )
    
    def get_version(self, version_name: str) -> Optional[Dict]:
        """Recupera especificação de uma versão específica"""
        version_file = self.versions_dir / f"{version_name}.json"
        
        if not version_file.exists():
            print(f"❌ Versão não encontrada: {version_name}")
            return None
        
        try:
            with open(version_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Erro ao carregar versão {version_name}: {e}")
            return None
    
    def get_current_version(self) -> Optional[Dict]:
        """Recupera versão atual"""
        current_version = self.versions_index.get('current_version')
        if current_version:
            return self.get_version(current_version)
        
        # Fallback para arquivo atual
        if self.current_file.exists():
            try:
                with open(self.current_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"❌ Erro ao carregar versão atual: {e}")
        
        return None
    
    def compare_versions(self, version1: str, version2: str) -> Dict:
        """Compara duas versões e retorna diferenças"""
        spec1 = self.get_version(version1)
        spec2 = self.get_version(version2)
        
        if not spec1 or not spec2:
            return {'error': 'Uma ou ambas as versões não foram encontradas'}
        
        # Converter para strings formatadas para comparação
        spec1_str = json.dumps(spec1, indent=2, sort_keys=True)
        spec2_str = json.dumps(spec2, indent=2, sort_keys=True)
        
        # Gerar diff
        diff_lines = list(difflib.unified_diff(
            spec1_str.splitlines(keepends=True),
            spec2_str.splitlines(keepends=True),
            fromfile=f"Version {version1}",
            tofile=f"Version {version2}",
            lineterm=''
        ))
        
        # Analisar mudanças estruturais
        resources1 = {r['id']: r for r in spec1.get('resources', [])}
        resources2 = {r['id']: r for r in spec2.get('resources', [])}
        
        added_resources = set(resources2.keys()) - set(resources1.keys())
        removed_resources = set(resources1.keys()) - set(resources2.keys())
        modified_resources = []
        
        for resource_id in set(resources1.keys()) & set(resources2.keys()):
            if resources1[resource_id] != resources2[resource_id]:
                modified_resources.append(resource_id)
        
        return {
            'version1': version1,
            'version2': version2,
            'diff_lines': diff_lines,
            'summary': {
                'added_resources': list(added_resources),
                'removed_resources': list(removed_resources),
                'modified_resources': modified_resources,
                'total_changes': len(added_resources) + len(removed_resources) + len(modified_resources)
            }
        }
    
    def rollback_to_version(self, version_name: str, create_backup: bool = True) -> bool:
        """Faz rollback para uma versão específica"""
        target_spec = self.get_version(version_name)
        if not target_spec:
            return False
        
        try:
            # Criar backup da versão atual se solicitado
            if create_backup and self.current_file.exists():
                current_spec = self.get_current_version()
                if current_spec:
                    backup_name = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                    self.create_version(current_spec, backup_name, "Backup antes do rollback")
            
            # Atualizar arquivo atual
            with open(self.current_file, 'w') as f:
                json.dump(target_spec, f, indent=2, ensure_ascii=False)
            
            # Atualizar índice
            self.versions_index['current_version'] = version_name
            self.versions_index['rollback_at'] = datetime.utcnow().isoformat()
            self._save_versions_index()
            
            print(f"🔄 Rollback realizado para versão: {version_name}")
            return True
            
        except Exception as e:
            print(f"❌ Erro no rollback para {version_name}: {e}")
            return False
    
    def cleanup_old_versions(self, keep_count: int = 10) -> int:
        """Remove versões antigas mantendo apenas as mais recentes"""
        versions = self.list_versions()
        
        if len(versions) <= keep_count:
            print(f"📦 Apenas {len(versions)} versões encontradas, nenhuma limpeza necessária")
            return 0
        
        # Manter versões mais recentes e versão atual
        current_version = self.versions_index.get('current_version')
        versions_to_keep = set()
        
        # Adicionar versão atual
        if current_version:
            versions_to_keep.add(current_version)
        
        # Adicionar versões mais recentes
        for version in versions[:keep_count]:
            versions_to_keep.add(version['version'])
        
        # Remover versões antigas
        removed_count = 0
        for version in versions[keep_count:]:
            version_name = version['version']
            
            if version_name not in versions_to_keep:
                version_file = self.versions_dir / f"{version_name}.json"
                
                try:
                    if version_file.exists():
                        version_file.unlink()
                    
                    # Remover do índice
                    self.versions_index['versions'] = [
                        v for v in self.versions_index['versions'] 
                        if v['version'] != version_name
                    ]
                    
                    removed_count += 1
                    print(f"🗑️ Versão removida: {version_name}")
                    
                except Exception as e:
                    print(f"⚠️ Erro ao remover versão {version_name}: {e}")
        
        if removed_count > 0:
            self._save_versions_index()
            print(f"🧹 Limpeza concluída: {removed_count} versões removidas")
        
        return removed_count
    
    def export_version_history(self, output_file: Optional[str] = None) -> str:
        """Exporta histórico de versões para arquivo"""
        if not output_file:
            output_file = f"version_history_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        output_path = Path(output_file)
        
        try:
            export_data = {
                'exported_at': datetime.utcnow().isoformat(),
                'versions_index': self.versions_index,
                'versions_details': {}
            }
            
            # Incluir detalhes de cada versão
            for version_info in self.versions_index.get('versions', []):
                version_name = version_info['version']
                version_spec = self.get_version(version_name)
                
                if version_spec:
                    export_data['versions_details'][version_name] = {
                        'info': version_info,
                        'spec': version_spec
                    }
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print(f"📤 Histórico exportado para: {output_path}")
            return str(output_path)
            
        except Exception as e:
            print(f"❌ Erro ao exportar histórico: {e}")
            return None
    
    def get_version_statistics(self) -> Dict:
        """Recupera estatísticas das versões"""
        versions = self.list_versions()
        
        if not versions:
            return {'total_versions': 0}
        
        # Calcular estatísticas
        total_resources = [v['total_resources'] for v in versions]
        total_domains = [v['total_domains'] for v in versions]
        
        stats = {
            'total_versions': len(versions),
            'current_version': self.versions_index.get('current_version'),
            'oldest_version': versions[-1]['version'] if versions else None,
            'newest_version': versions[0]['version'] if versions else None,
            'resource_stats': {
                'min': min(total_resources),
                'max': max(total_resources),
                'avg': sum(total_resources) / len(total_resources)
            },
            'domain_stats': {
                'min': min(total_domains),
                'max': max(total_domains),
                'avg': sum(total_domains) / len(total_domains)
            },
            'storage_info': {
                'versions_dir_size': sum(f.stat().st_size for f in self.versions_dir.glob('*.json')),
                'index_file_size': self.versions_index_file.stat().st_size if self.versions_index_file.exists() else 0
            }
        }
        
        return stats

def main():
    """Função principal para testes"""
    print("📦 IAL Version Manager v3.1")
    print("=" * 50)
    
    vm = VersionManager()
    
    # Mostrar estatísticas
    stats = vm.get_version_statistics()
    print(f"📊 Estatísticas:")
    print(f"  📦 Total de versões: {stats['total_versions']}")
    print(f"  🔄 Versão atual: {stats.get('current_version', 'N/A')}")
    
    if stats['total_versions'] > 0:
        print(f"  📈 Recursos (min/max/avg): {stats['resource_stats']['min']}/{stats['resource_stats']['max']}/{stats['resource_stats']['avg']:.1f}")
        print(f"  🏗️ Domínios (min/max/avg): {stats['domain_stats']['min']}/{stats['domain_stats']['max']}/{stats['domain_stats']['avg']:.1f}")
    
    # Listar versões recentes
    versions = vm.list_versions()
    if versions:
        print(f"\n📋 Versões recentes (últimas 5):")
        for version in versions[:5]:
            print(f"  📦 {version['version']} - {version['created_at']}")
            print(f"     📊 {version['total_resources']} recursos, {version['total_domains']} domínios")
    
    return 0

if __name__ == "__main__":
    exit(main())
