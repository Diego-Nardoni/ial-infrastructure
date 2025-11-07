#!/usr/bin/env python3
"""
IAL Foundation CDK App
Bootstrap infrastructure for IAL system
"""

import aws_cdk as cdk
from stacks.ial_foundation_stack import IALFoundationStack

app = cdk.App()

# Get context variables
project_name = app.node.try_get_context("project_name") or "ial"
aws_account = app.node.try_get_context("aws_account") or app.account
aws_region = app.node.try_get_context("aws_region") or app.region
executor_name = app.node.try_get_context("executor_name") or "IAL-User"
github_user = app.node.try_get_context("github_user")
github_repo = app.node.try_get_context("github_repo")

# Create IAL Foundation Stack
IALFoundationStack(
    app, 
    f"{project_name}-foundation",
    project_name=project_name,
    executor_name=executor_name,
    github_user=github_user,
    github_repo=github_repo,
    env=cdk.Environment(
        account=aws_account,
        region=aws_region
    ),
    description=f"IAL Foundation Infrastructure for {project_name}"
)

app.synth()
