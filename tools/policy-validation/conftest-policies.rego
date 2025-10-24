package ial.security

# Policy as Code - IAM Security Rules for IaL

# Deny wildcard permissions in production
deny[msg] {
    input.Resources[_].Type == "AWS::IAM::Role"
    policy := input.Resources[_].Properties.Policies[_]
    statement := policy.PolicyDocument.Statement[_]
    statement.Effect == "Allow"
    statement.Action[_] == "*"
    msg := "IAM policy contains wildcard (*) permissions - use specific actions instead"
}

# Require MFA for sensitive actions
deny[msg] {
    input.Resources[_].Type == "AWS::IAM::Role"
    policy := input.Resources[_].Properties.Policies[_]
    statement := policy.PolicyDocument.Statement[_]
    statement.Effect == "Allow"
    sensitive_actions := ["iam:CreateRole", "iam:DeleteRole", "iam:AttachRolePolicy"]
    statement.Action[_] == sensitive_actions[_]
    not statement.Condition.Bool["aws:MultiFactorAuthPresent"]
    msg := sprintf("Sensitive IAM action %v requires MFA condition", [statement.Action[_]])
}

# Require resource-specific permissions
deny[msg] {
    input.Resources[_].Type == "AWS::IAM::Role"
    policy := input.Resources[_].Properties.Policies[_]
    statement := policy.PolicyDocument.Statement[_]
    statement.Effect == "Allow"
    statement.Resource == "*"
    not statement.Action[_] == "sts:GetCallerIdentity"
    msg := "IAM policy uses wildcard resource (*) - specify exact resources instead"
}

# Require encryption for S3 buckets
deny[msg] {
    input.Resources[_].Type == "AWS::S3::Bucket"
    bucket := input.Resources[_]
    not bucket.Properties.BucketEncryption
    msg := "S3 bucket must have encryption enabled"
}

# Require versioning for S3 buckets
warn[msg] {
    input.Resources[_].Type == "AWS::S3::Bucket"
    bucket := input.Resources[_]
    not bucket.Properties.VersioningConfiguration.Status == "Enabled"
    msg := "S3 bucket should have versioning enabled for data protection"
}

# Require deletion protection for RDS
deny[msg] {
    input.Resources[_].Type == "AWS::RDS::DBCluster"
    cluster := input.Resources[_]
    not cluster.Properties.DeletionProtection == true
    msg := "RDS cluster must have deletion protection enabled"
}

# Require encryption for RDS
deny[msg] {
    input.Resources[_].Type == "AWS::RDS::DBCluster"
    cluster := input.Resources[_]
    not cluster.Properties.StorageEncrypted == true
    msg := "RDS cluster must have storage encryption enabled"
}

# Require KMS encryption for Secrets Manager
deny[msg] {
    input.Resources[_].Type == "AWS::SecretsManager::Secret"
    secret := input.Resources[_]
    not secret.Properties.KmsKeyId
    msg := "Secrets Manager secret must use KMS encryption"
}

# Require rotation for Secrets Manager
warn[msg] {
    input.Resources[_].Type == "AWS::SecretsManager::Secret"
    secret := input.Resources[_]
    not secret.Properties.GenerateSecretString
    msg := "Secrets Manager secret should use automatic password generation"
}

# Require private subnets for databases
deny[msg] {
    input.Resources[_].Type == "AWS::RDS::DBInstance"
    instance := input.Resources[_]
    instance.Properties.PubliclyAccessible == true
    msg := "RDS instance must not be publicly accessible"
}

# Require SSL/TLS for database connections
warn[msg] {
    input.Resources[_].Type == "AWS::RDS::DBCluster"
    cluster := input.Resources[_]
    not cluster.Properties.EnableCloudwatchLogsExports
    msg := "RDS cluster should enable CloudWatch logs for monitoring"
}

# Cost optimization rules
warn[msg] {
    input.Resources[_].Type == "AWS::EC2::Instance"
    instance := input.Resources[_]
    expensive_types := ["m5.large", "m5.xlarge", "c5.large", "c5.xlarge"]
    instance.Properties.InstanceType == expensive_types[_]
    msg := sprintf("EC2 instance type %v may be oversized - consider smaller instance", [instance.Properties.InstanceType])
}

# Require tags for cost tracking
deny[msg] {
    resource_types := ["AWS::EC2::Instance", "AWS::RDS::DBCluster", "AWS::S3::Bucket"]
    input.Resources[_].Type == resource_types[_]
    resource := input.Resources[_]
    not resource.Properties.Tags
    msg := sprintf("Resource %v must have tags for cost tracking", [resource.Type])
}

# Require Project tag
deny[msg] {
    resource_types := ["AWS::EC2::Instance", "AWS::RDS::DBCluster", "AWS::S3::Bucket"]
    input.Resources[_].Type == resource_types[_]
    resource := input.Resources[_]
    tags := resource.Properties.Tags
    not [tag | tag := tags[_]; tag.Key == "Project"]
    msg := "Resource must have 'Project' tag for cost allocation"
}
