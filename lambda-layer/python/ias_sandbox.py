#!/usr/bin/env python3
"""
IAS - Intent Validation Sandbox
Valida intenções NL ANTES de gerar YAML
"""

import json
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class SecurityRisk:
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str  # public_access, encryption, iam, network
    message: str
    recommendation: str


class IASandbox:
    """Intent Validation Sandbox - Valida segurança antes de gerar YAML"""
    
    def __init__(self):
        self.risk_patterns = self._load_risk_patterns()
    
    def _load_risk_patterns(self) -> Dict[str, List[str]]:
        """Padrões de risco em linguagem natural"""
        return {
            "public_access": [
                "público", "public", "internet", "aberto", "open",
                "qualquer um", "anyone", "world", "0.0.0.0/0"
            ],
            "no_encryption": [
                "sem criptografia", "no encryption", "unencrypted",
                "plain text", "texto plano"
            ],
            "admin_access": [
                "admin", "root", "full access", "acesso total",
                "*:*", "administrator"
            ],
            "no_backup": [
                "sem backup", "no backup", "sem snapshot",
                "no snapshot", "sem retenção"
            ]
        }
    
    def validate_intent(self, nl_intent: str) -> Dict[str, Any]:
        """
        Valida intenção em linguagem natural
        
        Returns:
            {
                "safe": bool,
                "risks": List[SecurityRisk],
                "severity_score": int (0-100),
                "recommendation": str
            }
        """
        risks = []
        nl_lower = nl_intent.lower()
        
        # 1. Check public access
        if any(pattern in nl_lower for pattern in self.risk_patterns["public_access"]):
            if "s3" in nl_lower or "bucket" in nl_lower:
                risks.append(SecurityRisk(
                    severity="CRITICAL",
                    category="public_access",
                    message="S3 bucket público detectado",
                    recommendation="Use bucket privado com CloudFront ou ALB"
                ))
            elif "rds" in nl_lower or "database" in nl_lower:
                risks.append(SecurityRisk(
                    severity="CRITICAL",
                    category="public_access",
                    message="Database público detectado",
                    recommendation="Use VPC privada com bastion host"
                ))
            elif "ec2" in nl_lower or "instância" in nl_lower:
                risks.append(SecurityRisk(
                    severity="HIGH",
                    category="public_access",
                    message="EC2 com acesso público detectado",
                    recommendation="Use VPC privada com NAT Gateway"
                ))
        
        # 2. Check encryption
        if any(pattern in nl_lower for pattern in self.risk_patterns["no_encryption"]):
            risks.append(SecurityRisk(
                severity="HIGH",
                category="encryption",
                message="Dados sem criptografia detectado",
                recommendation="Habilite encryption at rest (KMS)"
            ))
        
        # 3. Check admin access
        if any(pattern in nl_lower for pattern in self.risk_patterns["admin_access"]):
            risks.append(SecurityRisk(
                severity="HIGH",
                category="iam",
                message="Permissões administrativas detectadas",
                recommendation="Use least privilege (mínimo privilégio)"
            ))
        
        # 4. Check backup
        if any(pattern in nl_lower for pattern in self.risk_patterns["no_backup"]):
            risks.append(SecurityRisk(
                severity="MEDIUM",
                category="backup",
                message="Sem estratégia de backup detectado",
                recommendation="Configure automated backups"
            ))
        
        # Calculate severity score
        severity_weights = {"CRITICAL": 40, "HIGH": 25, "MEDIUM": 15, "LOW": 5}
        severity_score = sum(severity_weights.get(r.severity, 0) for r in risks)
        
        # Determine if safe
        safe = severity_score < 40  # Block if score >= 40
        
        return {
            "safe": safe,
            "risks": [
                {
                    "severity": r.severity,
                    "category": r.category,
                    "message": r.message,
                    "recommendation": r.recommendation
                }
                for r in risks
            ],
            "severity_score": severity_score,
            "recommendation": self._generate_recommendation(risks, safe)
        }
    
    def _generate_recommendation(self, risks: List[SecurityRisk], safe: bool) -> str:
        """Gera recomendação baseada nos riscos"""
        if not risks:
            return "✅ Nenhum risco de segurança detectado. Pode prosseguir."
        
        if not safe:
            critical = [r for r in risks if r.severity == "CRITICAL"]
            return f"🚫 BLOQUEADO: {len(critical)} risco(s) crítico(s) detectado(s). Corrija antes de prosseguir."
        
        return f"⚠️ {len(risks)} risco(s) detectado(s). Revise antes de prosseguir."
    
    def simulate_deployment(self, nl_intent: str) -> Dict[str, Any]:
        """Simula deployment para detectar problemas"""
        # Simplified simulation
        resources = []
        
        nl_lower = nl_intent.lower()
        
        if "vpc" in nl_lower or "network" in nl_lower:
            resources.append({"type": "AWS::EC2::VPC", "estimated_cost": 0.0})
        
        if "ec2" in nl_lower or "instância" in nl_lower:
            resources.append({"type": "AWS::EC2::Instance", "estimated_cost": 50.0})
        
        if "rds" in nl_lower or "database" in nl_lower:
            resources.append({"type": "AWS::RDS::DBInstance", "estimated_cost": 100.0})
        
        if "s3" in nl_lower or "bucket" in nl_lower:
            resources.append({"type": "AWS::S3::Bucket", "estimated_cost": 5.0})
        
        return {
            "resources": resources,
            "total_resources": len(resources),
            "estimated_monthly_cost": sum(r["estimated_cost"] for r in resources)
        }
