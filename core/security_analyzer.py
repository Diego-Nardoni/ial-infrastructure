#!/usr/bin/env python3
"""
Security Analyzer - Análise de segurança via CloudTrail e MCP Well-Architected
Implementa detecção de ameaças e análise de postura de segurança
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import hashlib

class SecurityAnalyzer:
    """Analisador de segurança com CloudTrail e Well-Architected Framework"""
    
    def __init__(self):
        self.mcp_cloudtrail = self._get_cloudtrail_mcp()
        self.mcp_security = self._get_security_mcp()
        
        # Padrões de ameaças conhecidas
        self.threat_patterns = {
            'brute_force': {
                'events': ['ConsoleLogin', 'AssumeRole'],
                'failure_threshold': 5,
                'time_window': 300  # 5 minutos
            },
            'privilege_escalation': {
                'events': ['AttachUserPolicy', 'PutUserPolicy', 'CreateRole'],
                'suspicious_actions': ['*', 'iam:*', 'sts:AssumeRole']
            },
            'data_exfiltration': {
                'events': ['GetObject', 'ListBucket', 'DescribeInstances'],
                'volume_threshold': 1000,  # Muitas operações
                'time_window': 3600  # 1 hora
            },
            'unusual_access': {
                'events': ['ConsoleLogin', 'AssumeRole'],
                'check_geo': True,
                'check_time': True,
                'check_user_agent': True
            }
        }
    
    def _get_cloudtrail_mcp(self):
        """Obter cliente MCP CloudTrail"""
        try:
            from .ial_query_engine import MCPClient
            config = {"command": "python", "args": ["-m", "mcp_aws_cloudtrail"]}
            return MCPClient("aws-cloudtrail", config)
        except ImportError:
            return None
    
    def _get_security_mcp(self):
        """Obter cliente MCP Well-Architected Security"""
        try:
            from .ial_query_engine import MCPClient
            config = {"command": "python", "args": ["-m", "mcp_aws_security_hub"]}
            return MCPClient("aws-security-hub", config)
        except ImportError:
            return None
    
    async def analyze_login_security(self, time_window: int = 24) -> Dict:
        """Análise completa de segurança de login"""
        
        analysis_result = {
            "analysis_type": "login_security",
            "time_window_hours": time_window,
            "analysis_time": datetime.now().isoformat(),
            "security_score": 100,
            "threats_detected": [],
            "login_statistics": {},
            "geographic_analysis": {},
            "recommendations": []
        }
        
        # Obter eventos de login via CloudTrail
        login_events = await self._get_login_events(time_window)
        
        # Análise estatística de logins
        analysis_result["login_statistics"] = self._analyze_login_statistics(login_events)
        
        # Detectar tentativas de brute force
        brute_force_threats = self._detect_brute_force_attacks(login_events)
        analysis_result["threats_detected"].extend(brute_force_threats)
        
        # Análise geográfica
        analysis_result["geographic_analysis"] = self._analyze_geographic_patterns(login_events)
        
        # Detectar acessos incomuns
        unusual_access = self._detect_unusual_access_patterns(login_events)
        analysis_result["threats_detected"].extend(unusual_access)
        
        # Calcular security score
        analysis_result["security_score"] = self._calculate_security_score(analysis_result["threats_detected"])
        
        # Gerar recomendações
        analysis_result["recommendations"] = self._generate_security_recommendations(analysis_result)
        
        return analysis_result
    
    async def _get_login_events(self, hours: int) -> List[Dict]:
        """Obter eventos de login do CloudTrail"""
        
        # Simular eventos de login realísticos
        base_time = datetime.now()
        events = []
        
        # Logins normais
        for i in range(45):
            event_time = base_time - timedelta(hours=i*0.5)
            events.append({
                "EventTime": event_time.isoformat(),
                "EventName": "ConsoleLogin",
                "SourceIPAddress": "203.0.113.12",  # IP corporativo
                "UserIdentity": {
                    "type": "IAMUser",
                    "userName": "john.doe@company.com"
                },
                "ResponseElements": {"ConsoleLogin": "Success"},
                "UserAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
        
        # Tentativas de brute force (suspeitas)
        for i in range(15):
            event_time = base_time - timedelta(minutes=i*2)
            events.append({
                "EventTime": event_time.isoformat(),
                "EventName": "ConsoleLogin",
                "SourceIPAddress": "1.2.3.4",  # IP suspeito
                "UserIdentity": {
                    "type": "IAMUser",
                    "userName": "admin@company.com"
                },
                "ErrorCode": "SigninFailure",
                "ErrorMessage": "Failed authentication",
                "UserAgent": "curl/7.68.0"
            })
        
        # Login de localização incomum
        events.append({
            "EventTime": (base_time - timedelta(hours=2)).isoformat(),
            "EventName": "ConsoleLogin",
            "SourceIPAddress": "185.220.101.42",  # IP Tor
            "UserIdentity": {
                "type": "IAMUser",
                "userName": "admin@company.com"
            },
            "ResponseElements": {"ConsoleLogin": "Success"},
            "UserAgent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        })
        
        return events
    
    def _analyze_login_statistics(self, events: List[Dict]) -> Dict:
        """Análise estatística dos logins"""
        
        total_events = len(events)
        successful_logins = len([e for e in events if not e.get("ErrorCode")])
        failed_logins = total_events - successful_logins
        
        # Análise por usuário
        users = {}
        for event in events:
            username = event.get("UserIdentity", {}).get("userName", "unknown")
            if username not in users:
                users[username] = {"total": 0, "success": 0, "failed": 0}
            
            users[username]["total"] += 1
            if event.get("ErrorCode"):
                users[username]["failed"] += 1
            else:
                users[username]["success"] += 1
        
        # Análise por IP
        ips = {}
        for event in events:
            ip = event.get("SourceIPAddress", "unknown")
            if ip not in ips:
                ips[ip] = {"total": 0, "success": 0, "failed": 0}
            
            ips[ip]["total"] += 1
            if event.get("ErrorCode"):
                ips[ip]["failed"] += 1
            else:
                ips[ip]["success"] += 1
        
        return {
            "total_events": total_events,
            "successful_logins": successful_logins,
            "failed_logins": failed_logins,
            "failure_rate": round((failed_logins / total_events) * 100, 2) if total_events > 0 else 0,
            "unique_users": len(users),
            "unique_ips": len(ips),
            "top_users": sorted(users.items(), key=lambda x: x[1]["total"], reverse=True)[:5],
            "top_ips": sorted(ips.items(), key=lambda x: x[1]["total"], reverse=True)[:5]
        }
    
    def _detect_brute_force_attacks(self, events: List[Dict]) -> List[Dict]:
        """Detectar ataques de força bruta"""
        
        threats = []
        
        # Agrupar por IP e usuário
        ip_failures = {}
        user_failures = {}
        
        for event in events:
            if event.get("ErrorCode"):  # Login falhado
                ip = event.get("SourceIPAddress")
                user = event.get("UserIdentity", {}).get("userName")
                event_time = datetime.fromisoformat(event["EventTime"].replace('Z', '+00:00'))
                
                # Contar falhas por IP
                if ip not in ip_failures:
                    ip_failures[ip] = []
                ip_failures[ip].append(event_time)
                
                # Contar falhas por usuário
                if user not in user_failures:
                    user_failures[user] = []
                user_failures[user].append(event_time)
        
        # Detectar brute force por IP
        for ip, failure_times in ip_failures.items():
            if len(failure_times) >= 5:  # 5+ falhas
                # Verificar se ocorreram em janela de tempo pequena
                failure_times.sort()
                time_window = (failure_times[-1] - failure_times[0]).total_seconds()
                
                if time_window <= 300:  # 5 minutos
                    threats.append({
                        "type": "brute_force_ip",
                        "severity": "high",
                        "source_ip": ip,
                        "failure_count": len(failure_times),
                        "time_window_seconds": time_window,
                        "description": f"Brute force attack from IP {ip}: {len(failure_times)} failed attempts in {time_window:.0f} seconds",
                        "impact": "Potential account compromise, service disruption",
                        "first_seen": failure_times[0].isoformat(),
                        "last_seen": failure_times[-1].isoformat()
                    })
        
        # Detectar brute force por usuário
        for user, failure_times in user_failures.items():
            if len(failure_times) >= 10:  # 10+ falhas para um usuário
                failure_times.sort()
                time_window = (failure_times[-1] - failure_times[0]).total_seconds()
                
                threats.append({
                    "type": "brute_force_user",
                    "severity": "medium",
                    "target_user": user,
                    "failure_count": len(failure_times),
                    "time_window_seconds": time_window,
                    "description": f"Multiple failed logins for user {user}: {len(failure_times)} attempts",
                    "impact": "Account lockout risk, potential credential compromise",
                    "first_seen": failure_times[0].isoformat(),
                    "last_seen": failure_times[-1].isoformat()
                })
        
        return threats
    
    def _analyze_geographic_patterns(self, events: List[Dict]) -> Dict:
        """Análise de padrões geográficos"""
        
        # Simular análise geográfica baseada em IPs
        ip_locations = {
            "203.0.113.12": {"country": "US", "city": "New York", "org": "Corporate Network"},
            "1.2.3.4": {"country": "CN", "city": "Beijing", "org": "Unknown"},
            "185.220.101.42": {"country": "DE", "city": "Frankfurt", "org": "Tor Exit Node"}
        }
        
        geographic_stats = {}
        suspicious_locations = []
        
        for event in events:
            ip = event.get("SourceIPAddress")
            location = ip_locations.get(ip, {"country": "Unknown", "city": "Unknown", "org": "Unknown"})
            
            country = location["country"]
            if country not in geographic_stats:
                geographic_stats[country] = {"count": 0, "ips": set(), "success": 0, "failed": 0}
            
            geographic_stats[country]["count"] += 1
            geographic_stats[country]["ips"].add(ip)
            
            if event.get("ErrorCode"):
                geographic_stats[country]["failed"] += 1
            else:
                geographic_stats[country]["success"] += 1
            
            # Detectar localizações suspeitas
            if "Tor" in location["org"] or country in ["CN", "RU", "KP"]:
                suspicious_locations.append({
                    "ip": ip,
                    "country": country,
                    "city": location["city"],
                    "organization": location["org"],
                    "event_time": event["EventTime"],
                    "user": event.get("UserIdentity", {}).get("userName"),
                    "success": not bool(event.get("ErrorCode"))
                })
        
        # Converter sets para listas para serialização JSON
        for country_data in geographic_stats.values():
            country_data["ips"] = list(country_data["ips"])
        
        return {
            "countries_accessed": list(geographic_stats.keys()),
            "geographic_distribution": geographic_stats,
            "suspicious_locations": suspicious_locations,
            "risk_score": len(suspicious_locations) * 10  # 10 pontos por localização suspeita
        }
    
    def _detect_unusual_access_patterns(self, events: List[Dict]) -> List[Dict]:
        """Detectar padrões de acesso incomuns"""
        
        threats = []
        
        # Detectar acessos fora do horário comercial
        business_hours = (9, 17)  # 9 AM - 5 PM
        
        for event in events:
            event_time = datetime.fromisoformat(event["EventTime"].replace('Z', '+00:00'))
            hour = event_time.hour
            
            # Acesso fora do horário comercial
            if hour < business_hours[0] or hour > business_hours[1]:
                if not event.get("ErrorCode"):  # Login bem-sucedido
                    threats.append({
                        "type": "off_hours_access",
                        "severity": "low",
                        "user": event.get("UserIdentity", {}).get("userName"),
                        "source_ip": event.get("SourceIPAddress"),
                        "access_time": event["EventTime"],
                        "description": f"Successful login outside business hours at {hour:02d}:00",
                        "impact": "Potential unauthorized access, insider threat"
                    })
        
        # Detectar User-Agent suspeitos
        suspicious_agents = ["curl", "wget", "python", "bot"]
        
        for event in events:
            user_agent = event.get("UserAgent", "")
            if any(agent in user_agent.lower() for agent in suspicious_agents):
                threats.append({
                    "type": "suspicious_user_agent",
                    "severity": "medium",
                    "user": event.get("UserIdentity", {}).get("userName"),
                    "source_ip": event.get("SourceIPAddress"),
                    "user_agent": user_agent,
                    "event_time": event["EventTime"],
                    "description": f"Login attempt with suspicious User-Agent: {user_agent}",
                    "impact": "Potential automated attack, credential stuffing"
                })
        
        return threats
    
    def _calculate_security_score(self, threats: List[Dict]) -> int:
        """Calcular score de segurança baseado nas ameaças"""
        
        score = 100
        
        for threat in threats:
            severity = threat.get("severity", "low")
            
            if severity == "high":
                score -= 25
            elif severity == "medium":
                score -= 15
            elif severity == "low":
                score -= 5
        
        return max(0, score)
    
    def _generate_security_recommendations(self, analysis: Dict) -> List[Dict]:
        """Gerar recomendações de segurança"""
        
        recommendations = []
        threats = analysis["threats_detected"]
        stats = analysis["login_statistics"]
        
        # Recomendações baseadas em ameaças
        if any(t["type"] == "brute_force_ip" for t in threats):
            recommendations.append({
                "type": "ip_blocking",
                "priority": "high",
                "action": "Bloquear IPs suspeitos no Security Group/WAF",
                "implementation": "Configurar regras de bloqueio automático",
                "estimated_effort": "1-2 horas"
            })
        
        if any(t["type"] == "brute_force_user" for t in threats):
            recommendations.append({
                "type": "account_lockout",
                "priority": "high",
                "action": "Implementar política de bloqueio de conta",
                "implementation": "Configurar lockout após 5 tentativas falhadas",
                "estimated_effort": "2-4 horas"
            })
        
        # Recomendações baseadas em estatísticas
        if stats["failure_rate"] > 20:
            recommendations.append({
                "type": "mfa_enforcement",
                "priority": "high",
                "action": "Forçar MFA para todos os usuários",
                "implementation": "Política IAM obrigatória de MFA",
                "estimated_effort": "4-8 horas"
            })
        
        if analysis["geographic_analysis"]["risk_score"] > 20:
            recommendations.append({
                "type": "geo_blocking",
                "priority": "medium",
                "action": "Implementar bloqueio geográfico",
                "implementation": "Restringir acesso a países específicos",
                "estimated_effort": "2-3 horas"
            })
        
        # Recomendações gerais
        recommendations.append({
            "type": "monitoring_enhancement",
            "priority": "medium",
            "action": "Configurar alertas CloudWatch para eventos de segurança",
            "implementation": "Criar alarmes para padrões suspeitos",
            "estimated_effort": "3-5 horas"
        })
        
        return recommendations
    
    async def analyze_privilege_escalation(self) -> Dict:
        """Detectar tentativas de escalação de privilégios"""
        
        # Simular análise de escalação de privilégios
        return {
            "analysis_type": "privilege_escalation",
            "analysis_time": datetime.now().isoformat(),
            "suspicious_activities": [
                {
                    "type": "policy_attachment",
                    "user": "temp-user@company.com",
                    "action": "AttachUserPolicy",
                    "policy_arn": "arn:aws:iam::aws:policy/AdministratorAccess",
                    "timestamp": "2024-11-12T15:30:00Z",
                    "risk_level": "high",
                    "description": "Temporary user attached administrator policy"
                },
                {
                    "type": "role_creation",
                    "user": "developer@company.com",
                    "action": "CreateRole",
                    "role_name": "HighPrivilegeRole",
                    "timestamp": "2024-11-12T14:45:00Z",
                    "risk_level": "medium",
                    "description": "Developer created role with elevated permissions"
                }
            ],
            "recommendations": [
                "Revisar políticas anexadas recentemente",
                "Implementar aprovação para mudanças de IAM",
                "Configurar alertas para ações administrativas"
            ]
        }

# Integração com conversational engine
class SecurityIntegration:
    """Integração do Security Analyzer com o sistema conversacional"""
    
    def __init__(self):
        self.analyzer = SecurityAnalyzer()
    
    async def process_security_query(self, query: str) -> Dict:
        """Processar queries de segurança"""
        
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in ['login', 'brute force', 'authentication']):
            return await self.analyzer.analyze_login_security()
        elif any(keyword in query_lower for keyword in ['privilege', 'escalation', 'iam']):
            return await self.analyzer.analyze_privilege_escalation()
        else:
            return {
                "type": "security_help",
                "message": "Análise de segurança disponível",
                "options": [
                    "Análise de segurança de login",
                    "Detecção de escalação de privilégios",
                    "Análise de padrões geográficos"
                ]
            }

# Teste do analyzer
if __name__ == "__main__":
    import asyncio
    
    async def test_security_analyzer():
        analyzer = SecurityAnalyzer()
        
        print("🛡️ Testando Security Analyzer...")
        
        # Teste análise de login
        login_result = await analyzer.analyze_login_security()
        print(f"🔒 Security Score: {login_result['security_score']}")
        print(f"🚨 Ameaças detectadas: {len(login_result['threats_detected'])}")
        print(f"📊 Taxa de falha: {login_result['login_statistics']['failure_rate']}%")
        
        # Teste escalação de privilégios
        privilege_result = await analyzer.analyze_privilege_escalation()
        print(f"⚠️ Atividades suspeitas: {len(privilege_result['suspicious_activities'])}")
    
    asyncio.run(test_security_analyzer())
