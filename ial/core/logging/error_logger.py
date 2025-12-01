#!/usr/bin/env python3
"""
IAL Error Logger - Sistema estruturado de logging
Substitui as supressões perigosas de erro por logging adequado
"""

import logging
import sys
import os
from datetime import datetime
from pathlib import Path

class IALLogger:
    """Logger estruturado para o IAL"""
    
    def __init__(self, name="ial", level=logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Evitar duplicação de handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Configurar handlers de logging"""
        
        # Handler para console (apenas erros críticos)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.ERROR)
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # Handler para arquivo (todos os logs)
        log_dir = Path("/home/ial/logs")
        log_dir.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(
            log_dir / f"ial_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    def error(self, message, exc_info=None):
        """Log de erro"""
        self.logger.error(message, exc_info=exc_info)
    
    def warning(self, message):
        """Log de warning"""
        self.logger.warning(message)
    
    def info(self, message):
        """Log de informação"""
        self.logger.info(message)
    
    def debug(self, message):
        """Log de debug"""
        self.logger.debug(message)

# Instância global do logger
ial_logger = IALLogger()

def log_error(message, exc_info=None):
    """Função conveniente para log de erro"""
    ial_logger.error(message, exc_info=exc_info)

def log_warning(message):
    """Função conveniente para log de warning"""
    ial_logger.warning(message)

def log_info(message):
    """Função conveniente para log de info"""
    ial_logger.info(message)

def log_debug(message):
    """Função conveniente para log de debug"""
    ial_logger.debug(message)

def setup_safe_error_handling():
    """
    Configurar tratamento seguro de erros
    Substitui as supressões perigosas por logging adequado
    """
    
    def safe_excepthook(exc_type, exc_value, exc_traceback):
        """Hook seguro para exceções não tratadas"""
        if issubclass(exc_type, KeyboardInterrupt):
            # Permitir Ctrl+C
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # Log da exceção ao invés de suprimir
        ial_logger.error(
            f"Uncaught exception: {exc_type.__name__}: {exc_value}",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
    
    # Substituir o hook de exceção por um seguro
    sys.excepthook = safe_excepthook
    
    # Configurar logging para warnings
    import warnings
    warnings.showwarning = lambda message, category, filename, lineno, file=None, line=None: \
        ial_logger.warning(f"{category.__name__}: {message} ({filename}:{lineno})")

# Configurar automaticamente quando importado
setup_safe_error_handling()
