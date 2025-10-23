# Contributing to AWS Internal Reference Pattern

Thank you for your interest in contributing to this AWS Internal Reference Pattern!

## Overview

This project demonstrates Infrastructure as Language (IaL) - a pure YAML + AWS CLI approach to infrastructure management. Contributions should maintain this philosophy and enhance the pattern's value as an internal AWS reference.

---

## IaL Philosophy

**Core Principles:**

1. **Pure YAML + AWS CLI** - No automation scripts, no "magic"
2. **Human-Readable** - Every command is explicit and understandable
3. **Educational** - Learn by reading and executing manually
4. **Parametrized** - Single codebase, multiple environments/regions/accounts
5. **Traceable** - Every resource creation is documented and auditable

**What IaL is NOT:**
- ❌ Infrastructure as Code (Terraform, CloudFormation)
- ❌ Automation framework (Ansible, Chef, Puppet)
- ❌ CI/CD pipeline (though it can be used in one)
- ❌ Configuration management tool

**What IaL IS:**
- ✅ Documentation-driven infrastructure
- ✅ Learning tool for AWS services
- ✅ Reference pattern for best practices
- ✅ Manual execution with full understanding

---

## How to Contribute

### 1. Types of Contributions

**Highly Welcomed:**
- New IaL phases for additional AWS services
- Documentation improvements
- Security enhancements
- Cost optimization strategies
- Multi-environment examples
- Troubleshooting guides
- Validation checklists

**Not Accepted:**
- Shell scripts that automate phase execution
- Infrastructure as Code templates (Terraform, CDK)
- Automation frameworks
- Anything that violates IaL principles

---

### 2. Contribution Workflow

#### Step 1: Fork and Clone

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/YOUR_USERNAME/ial-reference-pattern.git
cd ial-reference-pattern
```

#### Step 2: Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-fix-name
```

#### Step 3: Make Changes

Follow the guidelines below for your specific contribution type.

#### Step 4: Test Your Changes

```bash
# Load parameters
source parameters.env

# Test your phase manually
cat phases/XX-your-new-phase.yaml

# Execute commands one by one
# Verify each resource
# Document any issues
```

#### Step 5: Commit and Push

```bash
git add .
git commit -m "Add: Brief description of your changes"
git push origin feature/your-feature-name
```

#### Step 6: Create Pull Request

- Go to GitHub and create a Pull Request
- Fill out the PR template
- Link any related issues
- Wait for review

---

## Contribution Guidelines

### Adding a New Phase

**File Structure:**

```yaml
# phases/XX-service-name.yaml
---
phase_id: "XX-service-name"
phase_name: "Service Name"
description: "Brief description of what this phase does"
dependencies:
  - "YY-dependency-phase"
estimated_time: "5 minutes"
cost_impact: "$X/month"

resources:
  - resource_id: "resource-1"
    resource_type: "AWS::Service::Resource"
    description: "What this resource does"
    
    # AWS CLI command
    command: |
      aws service create-resource \
        --name {{PROJECT_NAME}}-resource \
        --parameter value \
        --tags Key=Project,Value={{PROJECT_NAME}} Key=ManagedBy,Value=IaL \
        --region {{AWS_REGION}}
    
    # Validation command
    validation: |
      aws service describe-resource \
        --name {{PROJECT_NAME}}-resource \
        --region {{AWS_REGION}}
    
    # Expected output
    expected_output: |
      {
        "Resource": {
          "Status": "ACTIVE"
        }
      }
    
    # Rollback command
    rollback: |
      aws service delete-resource \
        --name {{PROJECT_NAME}}-resource \
        --region {{AWS_REGION}}

notes:
  - "Important note about this phase"
  - "Security consideration"
  - "Cost optimization tip"

well_architected:
  security: "How this phase addresses security pillar"
  reliability: "How this phase addresses reliability pillar"
  performance: "How this phase addresses performance pillar"
  cost: "How this phase addresses cost optimization pillar"
  operational_excellence: "How this phase addresses operational excellence pillar"
```

**Requirements:**
- Use parametrized values: `{{PROJECT_NAME}}`, `{{AWS_REGION}}`, `{{AWS_ACCOUNT_ID}}`, `{{EXECUTOR_NAME}}`
- Include validation commands
- Include rollback commands
- Document dependencies
- Estimate time and cost
- Add Well-Architected considerations

---

### Improving Documentation

**Documentation Standards:**

- Use clear, concise language
- Include code examples
- Add validation commands
- Provide troubleshooting tips
- Link to AWS documentation
- Use proper markdown formatting

**File Locations:**
- General docs: `/docs/`
- Examples: `/examples/`
- Validation: `/validation/`

---

### Security Contributions

**Security Enhancements:**

- Must follow AWS security best practices
- Include validation commands
- Document security implications
- Reference AWS Well-Architected Security Pillar
- Add to security checklist

**Example:**

```yaml
# Security enhancement for Phase 05
- resource_id: "iam-policy-boundary"
  resource_type: "AWS::IAM::Policy"
  description: "Permissions boundary for ECS task role"
  
  command: |
    aws iam create-policy \
      --policy-name {{PROJECT_NAME}}-permissions-boundary \
      --policy-document file://permissions-boundary.json \
      --description "Permissions boundary for {{PROJECT_NAME}}" \
      --region {{AWS_REGION}}
```

---

### Cost Optimization

**Cost Optimization Contributions:**

- Must maintain functionality
- Document cost savings
- Include before/after comparison
- Provide implementation steps
- Note any trade-offs

**Example:**

```markdown
## Optimization: Replace NAT Gateway with VPC Endpoints

**Current Cost:** $32/month (2 NAT Gateways)
**Optimized Cost:** $14/month (2 VPC Endpoints)
**Savings:** $18/month (56%)

**Trade-offs:**
- VPC endpoints only work for AWS services
- No internet access from private subnets

**Implementation:**
[Detailed steps...]
```

---

## Code Style

### YAML Style

```yaml
# Use 2-space indentation
resources:
  - resource_id: "example"
    resource_type: "AWS::Service::Resource"
    
    # Use pipe for multi-line strings
    command: |
      aws service create-resource \
        --name value \
        --region {{AWS_REGION}}
    
    # Use proper quoting
    description: "This is a description"
    
    # Use lists for multiple items
    tags:
      - Key: Project
        Value: {{PROJECT_NAME}}
      - Key: ManagedBy
        Value: IaL
```

---

### Markdown Style

```markdown
# Use ATX-style headers

## Second level

### Third level

- Use hyphens for lists
- Not asterisks or plus signs

**Bold text** for emphasis

`Code` for inline code

\`\`\`bash
# Code blocks with language
aws s3 ls
\`\`\`

[Links](https://example.com) with descriptive text
```

---

### AWS CLI Style

```bash
# Use long-form options
aws service create-resource \
  --name value \
  --region {{AWS_REGION}}

# Not short-form
aws service create-resource -n value -r {{AWS_REGION}}

# Use backslash for line continuation
aws service create-resource \
  --parameter1 value1 \
  --parameter2 value2 \
  --region {{AWS_REGION}}

# Use parametrized values
--name {{PROJECT_NAME}}-resource
--region {{AWS_REGION}}
--account-id {{AWS_ACCOUNT_ID}}
```

---

## Testing

### Manual Testing

Before submitting a PR:

1. **Load parameters:**
   ```bash
   source parameters.env
   ```

2. **Test each command:**
   ```bash
   # Read the phase
   cat phases/XX-your-phase.yaml
   
   # Execute each command manually
   # Verify output
   # Check AWS Console
   ```

3. **Test validation:**
   ```bash
   # Run validation commands
   # Verify expected output
   ```

4. **Test rollback:**
   ```bash
   # Run rollback commands
   # Verify resource deletion
   ```

5. **Test in clean environment:**
   - Use a separate AWS account or region
   - Deploy from scratch
   - Document any issues

---

### Documentation Testing

- Check all links work
- Verify code examples execute correctly
- Test commands in multiple regions
- Validate markdown rendering

---

## Pull Request Process

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] New phase
- [ ] Documentation improvement
- [ ] Security enhancement
- [ ] Cost optimization
- [ ] Bug fix
- [ ] Other (specify)

## Testing
- [ ] Tested manually in AWS account
- [ ] Validated all commands work
- [ ] Tested rollback procedure
- [ ] Updated documentation
- [ ] Added validation commands

## Checklist
- [ ] Follows IaL principles
- [ ] Uses parametrized values
- [ ] Includes validation commands
- [ ] Includes rollback commands
- [ ] Documentation updated
- [ ] No automation scripts added
- [ ] Security considerations documented
- [ ] Cost impact documented

## Related Issues
Fixes #123
```

---

### Review Process

1. **Automated Checks:**
   - YAML syntax validation
   - Markdown linting
   - Link checking

2. **Manual Review:**
   - IaL principles compliance
   - Security best practices
   - Documentation quality
   - Code style

3. **Testing:**
   - Reviewer tests in their AWS account
   - Validates all commands work
   - Checks rollback procedure

4. **Approval:**
   - At least 1 approval required
   - All checks must pass
   - No unresolved comments

---

## Community

### Communication Channels

- **GitHub Issues:** Bug reports, feature requests
- **GitHub Discussions:** Questions, ideas, general discussion
- **Pull Requests:** Code contributions

### Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Help others learn
- Follow AWS best practices
- Maintain professional communication

---

## Recognition

Contributors will be recognized in:
- README.md Contributors section
- Release notes
- Documentation credits

---

## Questions?

- Open a GitHub Discussion
- Check existing documentation
- Review closed issues and PRs
- Contact maintainers

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

## Thank You!

Your contributions help make this reference pattern better for everyone. Thank you for taking the time to contribute!
