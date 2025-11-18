#!/usr/bin/env python3
"""
LLM Provider with Circuit Breaker and Async Support
"""

import asyncio
import yaml
import json
import time
import aiohttp
from pathlib import Path
from typing import Dict, List, Optional, Any
from core.circuit_breaker import CircuitBreaker

from core.path_utils import get_config_path

class LLMProvider:
    def __init__(self, config_path: str = None):
        # CORREÇÃO: Usar caminho dinâmico
        if config_path is None:
            config_path = get_config_path("llm_providers.yaml")
            
        self.config_path = config_path
        self.config = self._load_config()
        self.current_provider = self.config.get('default_provider', 'bedrock')
        self.fallback_order = self.config.get('fallback_order', ['deepseek', 'openai', 'pattern'])
        self.circuit_breakers = {}
        self._init_circuit_breakers()
        
    def _load_config(self) -> Dict:
        """Load LLM providers configuration"""
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                    return config
        except Exception as e:
            print(f"⚠️ Erro carregando LLM config: {e}")
        
        # URGENTE: Fallback configuration com Bedrock
        print("🔧 Usando configuração embedded para LLM")
        return {
            'default_provider': 'bedrock',
            'providers': {
                'bedrock': {
                    'chat_model': 'anthropic.claude-3-sonnet-20240229-v1:0',
                    'embed_model': 'amazon.titan-embed-text-v2:0',
                    'region': 'us-east-1',
                    'cost_per_1k_tokens': 0.003
                },
                'pattern': {'cost_per_1k_tokens': 0.0}
            },
            'fallback_order': ['bedrock', 'pattern']
        }
        
    def _init_circuit_breakers(self):
        """Initialize circuit breakers for each provider"""
        for provider in self.config.get('providers', {}):
            self.circuit_breakers[provider] = CircuitBreaker(
                failure_threshold=5,
                timeout=60,
                name=f"llm-{provider}"
            )
            
    async def process_natural_language_async(self, text: str) -> Dict:
        """Async processing with circuit breaker protection"""
        # Try current provider first
        if self.current_provider in self.circuit_breakers:
            circuit = self.circuit_breakers[self.current_provider]
            if circuit.can_execute():
                try:
                    result = await self._call_provider_async(self.current_provider, text)
                    circuit.record_success()
                    return result
                except Exception as e:
                    circuit.record_failure()
                    print(f"⚠️ LLM {self.current_provider} falhou: {e}")
        
        # Try fallback providers
        for provider in self.fallback_order:
            if provider in self.circuit_breakers:
                circuit = self.circuit_breakers[provider]
                if circuit.can_execute():
                    try:
                        result = await self._call_provider_async(provider, text)
                        circuit.record_success()
                        return result
                    except Exception as e:
                        circuit.record_failure()
                        print(f"⚠️ LLM fallback {provider} falhou: {e}")
                        continue
                        
        # Final fallback to pattern matching
        return self._pattern_fallback(text)
        
    async def _call_provider_async(self, provider: str, text: str) -> Dict:
        """Async call to specific LLM provider"""
        if provider == "bedrock":
            return await self._call_bedrock_async(text)
        elif provider == "deepseek":
            return await self._call_deepseek_async(text)
        elif provider == "openai":
            return await self._call_openai_async(text)
        else:
            return self._pattern_fallback(text)
            
    async def _call_bedrock_async(self, text: str) -> Dict:
        """Call AWS Bedrock async"""
        try:
            # Simulate Bedrock call
            await asyncio.sleep(0.1)  # Simulate API latency
            
            # Detect intent based on context enrichment
            intent = 'create_infrastructure'  # default
            if 'NAO gerar templates YAML' in text or 'NÃO gerar' in text:
                intent = 'list_information'
            elif 'LISTAR as fases' in text or 'VER/LISTAR' in text:
                intent = 'list_information'
            elif 'Consultar GitHub para listar' in text:
                intent = 'list_information'
                
            return {
                'provider': 'bedrock',
                'processed_text': text,
                'intent': intent,
                'entities': self._extract_entities(text),
                'confidence': 0.9
            }
        except Exception as e:
            raise Exception(f"Bedrock API error: {e}")
            
    async def _call_deepseek_async(self, text: str) -> Dict:
        """Call DeepSeek async"""
        try:
            # Simulate DeepSeek call
            await asyncio.sleep(0.2)  # Simulate API latency
            return {
                'provider': 'deepseek',
                'processed_text': text,
                'intent': 'create_infrastructure',
                'entities': self._extract_entities(text),
                'confidence': 0.8
            }
        except Exception as e:
            raise Exception(f"DeepSeek API error: {e}")
            
    async def _call_openai_async(self, text: str) -> Dict:
        """Call OpenAI async"""
        try:
            # Simulate OpenAI call
            await asyncio.sleep(0.3)  # Simulate API latency
            return {
                'provider': 'openai',
                'processed_text': text,
                'intent': 'create_infrastructure',
                'entities': self._extract_entities(text),
                'confidence': 0.85
            }
        except Exception as e:
            raise Exception(f"OpenAI API error: {e}")
            
    def _pattern_fallback(self, text: str) -> Dict:
        """Pattern matching fallback"""
        return {
            'provider': 'pattern',
            'processed_text': text,
            'intent': 'create_infrastructure',
            'entities': self._extract_entities(text),
            'confidence': 0.6
        }
        
    def _extract_entities(self, text: str) -> List[str]:
        """Extract entities from text using simple pattern matching"""
        text_lower = text.lower()
        entities = []
        
        # Common AWS services
        services = ['ecs', 'rds', 'lambda', 's3', 'ec2', 'vpc', 'elb', 'alb', 'dynamodb']
        for service in services:
            if service in text_lower:
                entities.append(service)
                
        return entities
        
    def get_metrics(self) -> Dict:
        """Get metrics from all circuit breakers"""
        metrics = {}
        for provider, circuit in self.circuit_breakers.items():
            metrics[provider] = circuit.get_metrics()
        return metrics
