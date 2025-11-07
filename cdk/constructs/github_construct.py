"""
GitHub Construct
Creates GitHub OIDC integration for IAL
"""

from aws_cdk import (
    aws_iam as iam
)
from constructs import Construct

class GitHubConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str,
                 project_name: str, github_user: str, github_repo: str,
                 iam_roles, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        
        # Use existing OIDC provider from IAM construct
        self.oidc_provider = iam_roles.github_oidc_provider
        self.oidc_role = iam_roles.github_actions_role
