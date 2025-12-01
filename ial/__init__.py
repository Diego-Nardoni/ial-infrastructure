"""
IAL - Infrastructure Assistant Layer
Versão consolidada e organizada
"""

__version__ = "6.30.0"
__author__ = "IAL Team"

# Importações principais
try:
    from .core.logging.error_logger import log_error, log_warning, log_info, log_debug
except ImportError:
    # Fallback se logging não disponível
    def log_error(msg, exc_info=None): print(f"ERROR: {msg}")
    def log_warning(msg): print(f"WARNING: {msg}")
    def log_info(msg): print(f"INFO: {msg}")
    def log_debug(msg): print(f"DEBUG: {msg}")

__all__ = ['log_error', 'log_warning', 'log_info', 'log_debug']
