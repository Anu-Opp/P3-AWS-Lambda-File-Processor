import json
import boto3
import urllib.parse
from datetime import datetime
import uuid
import os
import mimetypes

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Environment variables
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'file-processing-log')

def lambda_handler(event, context):
    print("Event received:", json.dumps(event))
    
    try:
        # Handle S3 trigger
        if 'Records' in event:
            return handle_s3_event(event)
        
        # Handle API Gateway trigger
        if 'httpMethod' in event:
            return handle_api_gateway_event(event)
            
    except Exception as e:
        print(f"Error processing event: {str(e)}")
        return create_error_response(str(e))

def handle_s3_event(event):
    """Process S3 file upload events"""
    results = []
    
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(record['s3']['object']['key'])
        
        print(f"Processing file: {key} from bucket: {bucket}")
        
        # Get file metadata
        file_info = get_file_metadata(bucket, key)
        
        # Process based on file type (without Pillow)
        processing_result = process_file_basic(bucket, key, file_info)
        
        # Log to DynamoDB
        log_processing_event(bucket, key, file_info, processing_result)
        
        results.append(processing_result)
    
    return create_success_response({
        "message": "Files processed successfully",
        "processed_files": len(results),
        "results": results
    })

def handle_api_gateway_event(event):
    """Handle API Gateway requests"""
    body = {}
    if event.get('body'):
        try:
            body = json.loads(event['body'])
        except json.JSONDecodeError:
            body = {"raw_body": event['body']}
    
    query_params = event.get('queryStringParameters') or {}
    
    return create_success_response({
        "message": "API request processed successfully",
        "received_data": body,
        "query_parameters": query_params,
        "processing_id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat()
    })

def get_file_metadata(bucket, key):
    """Get file metadata"""
    try:
        response = s3_client.head_object(Bucket=bucket, Key=key)
        file_ext = os.path.splitext(key)[1].lower()
        mime_type, _ = mimetypes.guess_type(key)
        
        return {
            "file_name": os.path.basename(key),
            "file_path": key,
            "file_size": response.get('ContentLength', 0),
            "file_extension": file_ext,
            "mime_type": mime_type,
            "last_modified": response.get('LastModified').isoformat() if response.get('LastModified') else None,
            "etag": response.get('ETag', '').strip('"')
        }
    except Exception as e:
        print(f"Error getting file metadata: {str(e)}")
        return {"error": str(e)}

def process_file_basic(bucket, key, file_info):
    """Basic file processing without image manipulation"""
    file_ext = file_info.get('file_extension', '').lower()
    mime_type = file_info.get('mime_type', '')
    
    if mime_type and mime_type.startswith('image/') or file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
        processing_type = "image"
        details = {
            "message": "Image file detected - thumbnail creation requires additional setup",
            "file_size_mb": int(file_info.get('file_size', 0) // (1024 * 1024)),
            "format": file_ext.replace('.', '').upper()
        }
    elif file_ext in ['.pdf', '.txt', '.doc', '.docx']:
        processing_type = "document"
        details = {
            "message": "Document processed and catalogued",
            "file_size_mb": int(file_info.get('file_size', 0) // (1024 * 1024))
        }
    else:
        processing_type = "general"
        details = {
            "message": "File received and catalogued",
            "file_size_mb": int(file_info.get('file_size', 0) // (1024 * 1024))
        }
    
    return {
        "file_name": file_info.get('file_name'),
        "processing_type": processing_type,
        "status": "success",
        "details": details
    }

def log_processing_event(bucket, key, file_info, processing_result):
    """Log processing event to DynamoDB"""
    try:
        table = dynamodb.Table(TABLE_NAME)
        
        item = {
            'processing_id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'bucket': bucket,
            'file_key': key,
            'file_info': file_info,
            'processing_result': processing_result,
            'ttl': int(datetime.now().timestamp()) + (30 * 24 * 60 * 60)
        }
        
        table.put_item(Item=item)
        print(f"Logged processing event for {key}")
        
    except Exception as e:
        print(f"Error logging to DynamoDB: {str(e)}")

def create_success_response(data):
    """Create successful API response"""
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(data)
    }

def create_error_response(error_message):
    """Create error API response"""
    return {
        "statusCode": 500,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps({
            "error": error_message,
            "timestamp": datetime.now().isoformat()
        })
    }
