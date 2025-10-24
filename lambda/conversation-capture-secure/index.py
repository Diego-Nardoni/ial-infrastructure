import json
import boto3
import os
import psycopg2
from datetime import datetime
import uuid

# AWS clients
s3 = boto3.client('s3')
secrets_manager = boto3.client('secretsmanager')

def lambda_handler(event, context):
    """Secure conversation capture with Secrets Manager integration"""
    
    print(f"Processing conversation capture: {json.dumps(event, default=str)}")
    
    try:
        # Extract conversation data
        conversation_data = {
            'conversation_id': event.get('conversation_id', str(uuid.uuid4())),
            'user_message': event.get('user_input', ''),
            'assistant_response': event.get('assistant_output', ''),
            'timestamp': datetime.utcnow(),
            'context': event.get('context', {}),
            'implementations': event.get('implementations', []),
            'user_id': event.get('user_id', 'anonymous')
        }
        
        # Store in S3
        s3_result = store_in_s3(conversation_data)
        
        # Store in Aurora PostgreSQL (secure)
        db_result = store_in_aurora(conversation_data)
        
        return {
            'statusCode': 200,
            'conversation_id': conversation_data['conversation_id'],
            's3_stored': s3_result,
            'db_stored': db_result,
            'timestamp': conversation_data['timestamp'].isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error in conversation capture: {str(e)}")
        return {
            'statusCode': 500,
            'error': str(e)
        }

def get_aurora_credentials():
    """Get Aurora credentials from Secrets Manager"""
    
    try:
        secret_name = f"{os.environ.get('PROJECT_NAME', 'ial')}-aurora-master-secret"
        
        response = secrets_manager.get_secret_value(SecretId=secret_name)
        secret = json.loads(response['SecretString'])
        
        return {
            'host': os.environ.get('AURORA_ENDPOINT'),
            'port': int(os.environ.get('AURORA_PORT', 5432)),
            'database': os.environ.get('DATABASE_NAME', 'ial_conversations'),
            'username': secret['username'],
            'password': secret['password']
        }
        
    except Exception as e:
        print(f"❌ Error getting Aurora credentials: {e}")
        return None

def store_in_s3(conversation_data):
    """Store conversation in S3 for vector processing"""
    
    try:
        bucket_name = os.environ.get('S3_CONVERSATIONS_BUCKET', 'ial-conversations-vector-store')
        
        # Create S3 key
        timestamp = conversation_data['timestamp']
        s3_key = f"conversations/{timestamp.year}/{timestamp.month:02d}/{timestamp.day:02d}/{conversation_data['conversation_id']}.json"
        
        # Prepare data for S3
        s3_data = {
            'conversation_id': conversation_data['conversation_id'],
            'user_message': conversation_data['user_message'],
            'assistant_response': conversation_data['assistant_response'],
            'timestamp': conversation_data['timestamp'].isoformat(),
            'context': conversation_data['context'],
            'implementations': conversation_data['implementations'],
            'user_id': conversation_data['user_id']
        }
        
        # Store in S3
        s3.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=json.dumps(s3_data, indent=2),
            ContentType='application/json',
            Metadata={
                'conversation-id': conversation_data['conversation_id'],
                'user-id': conversation_data['user_id'],
                'timestamp': conversation_data['timestamp'].isoformat()
            }
        )
        
        print(f"✅ Stored in S3: {s3_key}")
        return {'success': True, 's3_key': s3_key}
        
    except Exception as e:
        print(f"❌ Error storing in S3: {e}")
        return {'success': False, 'error': str(e)}

def store_in_aurora(conversation_data):
    """Store conversation in Aurora PostgreSQL using Secrets Manager"""
    
    try:
        # Get credentials
        creds = get_aurora_credentials()
        
        if not creds:
            raise Exception("Could not retrieve Aurora credentials")
        
        # Connect to Aurora
        conn = psycopg2.connect(
            host=creds['host'],
            port=creds['port'],
            database=creds['database'],
            user=creds['username'],
            password=creds['password'],
            sslmode='require'
        )
        
        cursor = conn.cursor()
        
        # Insert conversation
        cursor.execute("""
            INSERT INTO conversations (conversation_id, user_id, metadata, s3_key, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (conversation_id) DO UPDATE SET
                updated_at = EXCLUDED.updated_at,
                metadata = EXCLUDED.metadata;
        """, (
            conversation_data['conversation_id'],
            conversation_data['user_id'],
            json.dumps({
                'context': conversation_data['context'],
                'implementations_count': len(conversation_data['implementations'])
            }),
            f"conversations/{conversation_data['timestamp'].year}/{conversation_data['timestamp'].month:02d}/{conversation_data['timestamp'].day:02d}/{conversation_data['conversation_id']}.json",
            conversation_data['timestamp'],
            conversation_data['timestamp']
        ))
        
        # Insert user message
        if conversation_data['user_message']:
            cursor.execute("""
                INSERT INTO messages (message_id, conversation_id, role, content, timestamp, metadata)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, (
                f"{conversation_data['conversation_id']}-user",
                conversation_data['conversation_id'],
                'user',
                conversation_data['user_message'],
                conversation_data['timestamp'],
                json.dumps({'source': 'user_input'})
            ))
        
        # Insert assistant message
        if conversation_data['assistant_response']:
            cursor.execute("""
                INSERT INTO messages (message_id, conversation_id, role, content, timestamp, metadata)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, (
                f"{conversation_data['conversation_id']}-assistant",
                conversation_data['conversation_id'],
                'assistant',
                conversation_data['assistant_response'],
                conversation_data['timestamp'],
                json.dumps({'source': 'assistant_output'})
            ))
        
        # Insert implementations
        for i, impl in enumerate(conversation_data['implementations']):
            cursor.execute("""
                INSERT INTO implementations (implementation_id, conversation_id, file_path, implementation_type, functionality, code_snippet)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, (
                f"{conversation_data['conversation_id']}-impl-{i}",
                conversation_data['conversation_id'],
                impl.get('file_path', ''),
                impl.get('type', 'unknown'),
                impl.get('functionality', ''),
                impl.get('code_snippet', '')
            ))
        
        # Commit and close
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ Stored in Aurora: {conversation_data['conversation_id']}")
        return {'success': True, 'conversation_id': conversation_data['conversation_id']}
        
    except Exception as e:
        print(f"❌ Error storing in Aurora: {e}")
        return {'success': False, 'error': str(e)}

def create_tables_if_not_exist():
    """Create conversation tables if they don't exist"""
    
    try:
        creds = get_aurora_credentials()
        
        if not creds:
            return False
        
        conn = psycopg2.connect(
            host=creds['host'],
            port=creds['port'],
            database=creds['database'],
            user=creds['username'],
            password=creds['password'],
            sslmode='require'
        )
        
        cursor = conn.cursor()
        
        # Create tables (same as in aurora-secrets-helper.py)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id VARCHAR(255) PRIMARY KEY,
                user_id VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB,
                s3_key VARCHAR(500)
            );
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id VARCHAR(255) PRIMARY KEY,
                conversation_id VARCHAR(255) REFERENCES conversations(conversation_id),
                role VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB,
                tokens_used INTEGER
            );
        """)
        
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
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Tables created/verified")
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

# Initialize tables on Lambda cold start
create_tables_if_not_exist()
