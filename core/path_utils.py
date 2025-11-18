"""
Utilitários para resolução de caminhos dinâmicos
Funciona tanto em desenvolvimento quanto em binário instalado
"""
import sys
import os
from pathlib import Path

def get_base_path():
    """Retorna o caminho base do sistema IAL"""
    if getattr(sys, 'frozen', False):
        # Executável PyInstaller - usa diretório temporário
        return sys._MEIPASS
    else:
        # Desenvolvimento - usa diretório do script atual
        return Path(__file__).parent.parent.absolute()

def get_config_path(config_file: str):
    """Retorna caminho completo para arquivo de configuração"""
    base_path = get_base_path()
    return os.path.join(base_path, "config", config_file)

def get_phases_path():
    """Retorna caminho para diretório de fases"""
    base_path = get_base_path()
    return os.path.join(base_path, "phases")
