#!/usr/bin/env python3
"""Aurora Secrets Manager Helper - Secure Database Connections"""

import boto3
import json
import psycopg2
import os
from datetime import datetime

def get_aurora_credentials(secret_name=None, region='us-east-1'):
    """Get Aurora credentials from Secrets Manager"""
    
    if not secret_name:
        secret_name = f"{os.environ.get('PROJECT_NAME', 'ial')}-aurora-master-secret"
    
    try:
        # Create Secrets Manager client
        secrets_client = boto3.client('secretsmanager', region_name=region)
        
        # Get secret value
        response = secrets_client.get_secret_value(SecretId=secret_name)
        
        # Parse secret
        secret = json.loads(response['SecretString'])
        
        return {
            'username': secret['username'],
            'password': secret['password'],
            'engine': secret.get('engine', 'postgres'),
            'host': secret.get('host'),
            'port': secret.get('port', 5432),
            'dbname': secret.get('dbname', 'ial_conversations')
        }
        
    except Exception as e:
        print(f"❌ Error retrieving Aurora credentials: {e}")
        return None

def get_aurora_connection(secret_name=None, region='us-east-1'):
    """Get PostgreSQL connection using Secrets Manager credentials"""
    
    try:
        # Get credentials
        creds = get_aurora_credentials(secret_name, region)
        
        if not creds:
            raise Exception("Could not retrieve credentials")
        
        # Get cluster endpoint if not in secret
        if not creds.get('host'):
            creds['host'] = get_aurora_endpoint()
        
        # Create connection
        connection = psycopg2.connect(
            host=creds['host'],
            port=creds['port'],
            database=creds['dbname'],
            user=creds['username'],
            password=creds['password'],
            sslmode='require'  # Force SSL
        )
        
        print(f"✅ Connected to Aurora PostgreSQL: {creds['host']}")
        return connection
        
    except Exception as e:
        print(f"❌ Error connecting to Aurora: {e}")
        return None

def get_aurora_endpoint(cluster_name=None):
    """Get Aurora cluster endpoint from CloudFormation exports"""
    
    if not cluster_name:
        cluster_name = f"{os.environ.get('PROJECT_NAME', 'ial')}-aurora-endpoint"
    
    try:
        cf_client = boto3.client('cloudformation')
        
        # Get exported value
        response = cf_client.list_exports()
        
        for export in response.get('Exports', []):
            if export['Name'] == cluster_name:
                return export['Value']
        
        # Fallback: describe RDS clusters
        rds_client = boto3.client('rds')
        clusters = rds_client.describe_db_clusters()
        
        for cluster in clusters.get('DBClusters', []):
            if 'ial' in cluster['DBClusterIdentifier']:
                return cluster['Endpoint']
        
        raise Exception(f"Aurora endpoint not found: {cluster_name}")
        
    except Exception as e:
        print(f"❌ Error getting Aurora endpoint: {e}")
        return None

def test_aurora_connection():
    """Test Aurora connection and basic operations"""
    
    print("🔍 Testing Aurora connection with Secrets Manager...")
    
    try:
        # Get connection
        conn = get_aurora_connection()
        
        if not conn:
            return False
        
        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        
        print(f"✅ PostgreSQL version: {version}")
        
        # Test table creation
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS connection_test (
                id SERIAL PRIMARY KEY,
                test_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                message TEXT
            );
        """)
        
        # Test insert
        cursor.execute(
            "INSERT INTO connection_test (message) VALUES (%s);",
            (f"Connection test at {datetime.utcnow()}",)
        )
        
        # Test select
        cursor.execute("SELECT COUNT(*) FROM connection_test;")
        count = cursor.fetchone()[0]
        
        print(f"✅ Test table has {count} records")
        
        # Commit and close
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Aurora connection test successful")
        return True
        
    except Exception as e:
        print(f"❌ Aurora connection test failed: {e}")
        return False

def create_conversation_tables():
    """Create tables for conversation storage"""
    
    print("📊 Creating conversation storage tables...")
    
    try:
        conn = get_aurora_connection()
        
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Conversations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id VARCHAR(255) PRIMARY KEY,
                user_id VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB,
                s3_key VARCHAR(500),
                vector_embedding VECTOR(1536)  -- For embeddings
            );
        """)
        
        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id VARCHAR(255) PRIMARY KEY,
                conversation_id VARCHAR(255) REFERENCES conversations(conversation_id),
                role VARCHAR(50) NOT NULL,  -- 'user' or 'assistant'
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB,
                tokens_used INTEGER
            );
        """)
        
        # Implementations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS implementations (
                implementation_id VARCHAR(255) PRIMARY KEY,
                conversation_id VARCHAR(255) REFERENCES conversations(conversation_id),
                file_path VARCHAR(500),
                implementation_type VARCHAR(100),
                functionality TEXT,
                code_snippet TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_implementations_conversation_id ON implementations(conversation_id);")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Conversation tables created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating conversation tables: {e}")
        return False

def rotate_secret_now(secret_name=None):
    """Manually trigger secret rotation"""
    
    if not secret_name:
        secret_name = f"{os.environ.get('PROJECT_NAME', 'ial')}-aurora-master-secret"
    
    try:
        secrets_client = boto3.client('secretsmanager')
        
        response = secrets_client.rotate_secret(
            SecretId=secret_name,
            ForceRotateSecrets=True
        )
        
        print(f"✅ Secret rotation initiated: {response['ARN']}")
        print(f"Version ID: {response['VersionId']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error rotating secret: {e}")
        return False

def main():
    """Main function for testing"""
    
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'test':
            test_aurora_connection()
        elif command == 'create-tables':
            create_conversation_tables()
        elif command == 'rotate':
            rotate_secret_now()
        elif command == 'credentials':
            creds = get_aurora_credentials()
            if creds:
                # Mask password for security
                creds['password'] = '***MASKED***'
                print(json.dumps(creds, indent=2))
        else:
            print(f"Unknown command: {command}")
    else:
        print("Usage:")
        print("  python3 aurora-secrets-helper.py test           # Test connection")
        print("  python3 aurora-secrets-helper.py create-tables # Create conversation tables")
        print("  python3 aurora-secrets-helper.py rotate        # Rotate secret")
        print("  python3 aurora-secrets-helper.py credentials   # Show credentials (masked)")

if __name__ == "__main__":
    main()
