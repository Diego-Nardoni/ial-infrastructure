"""
S3 Construct
Creates all S3 buckets needed by IAL
"""

from aws_cdk import (
    aws_s3 as s3,
    Duration,
    RemovalPolicy
)
from constructs import Construct

class S3Construct(Construct):
    def __init__(self, scope: Construct, construct_id: str, project_name: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        
        # Main storage bucket (11-ial-s3-storage.yaml)
        self.storage_bucket = s3.Bucket(
            self, "StorageBucket",
            bucket_name=f"{project_name}-storage-{scope.account}-{scope.region}",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteIncompleteMultipartUploads",
                    abort_incomplete_multipart_upload_after=Duration.days(7)
                )
            ]
        )
        
        # RAG storage bucket (08-rag-storage.yaml)
        self.rag_bucket = s3.Bucket(
            self, "RAGBucket",
            bucket_name=f"{project_name}-rag-{scope.account}-{scope.region}",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.RETAIN
        )
        
        # Backup bucket (04-backup-strategy.yaml)
        self.backup_bucket = s3.Bucket(
            self, "BackupBucket",
            bucket_name=f"{project_name}-backups-{scope.account}-{scope.region}",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="ArchiveOldBackups",
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(30)
                        )
                    ]
                )
            ]
        )
