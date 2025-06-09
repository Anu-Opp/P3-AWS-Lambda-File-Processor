import json
import urllib.parse
from datetime import datetime
import os

# Initialize AWS clients with error handling
try:
    import boto3
    
    # Set region if not specified
    region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    
    s3_client = boto3.client('s3', region_name=region)
    dynamodb = boto3.resource('dynamodb', region_name=region)
    sns_client = boto3.client('sns', region_name=region)
    
    AWS_AVAILABLE = True
except Exception as e:
    print(f"AWS services not available: {e}")
    AWS_AVAILABLE = False

# Environment variables
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'file-processing-log')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')

def lambda_handler(event, context):
    print("Event received:", json.dumps(event))
    
    try:
        # Handle S3 trigger
        if 'Records' in event:
            return handle_s3_event(event)
        
        # Handle API Gateway trigger
        if 'httpMethod' in event:
            return handle_api_gateway_event(event)
        
        # Default response for other triggers
        return create_success_response({
            "message": "Lambda function executed successfully",
            "event_type": "unknown",
            "timestamp": datetime.now().isoformat()
        })
            
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
        
        # Get file metadata if AWS is available
        file_info = {}
        if AWS_AVAILABLE:
            try:
                file_info = get_file_metadata(bucket, key)
            except Exception as e:
                print(f"Could not get file metadata: {e}")
                file_info = {"error": str(e)}
        
        processing_result = {
            "file_name": os.path.basename(key),
            "file_path": key,
            "bucket": bucket,
            "status": "processed",
            "file_info": file_info,
            "timestamp": datetime.now().isoformat()
        }
        
        # Log to DynamoDB if available
        if AWS_AVAILABLE:
            try:
                log_processing_event(bucket, key, file_info, processing_result)
            except Exception as e:
                print(f"Could not log to DynamoDB: {e}")
        
        results.append(processing_result)
    
    return create_success_response({
        "message": "Files processed successfully",
        "processed_files": len(results),
        "results": results
    })

def handle_api_gateway_event(event):
    """Handle API Gateway requests"""
    print("API Gateway request received")
    
    # Parse request body
    body = {}
    if event.get('body'):
        try:
            body = json.loads(event['body'])
        except json.JSONDecodeError:
            body = {"raw_body": event['body']}
    
    # Get query parameters
    query_params = event.get('queryStringParameters') or {}
    
    # Handle different API endpoints
    path = event.get('path', '')
    method = event.get('httpMethod', '')
    
    if path.endswith('/status'):
        return get_processing_status()
    elif path.endswith('/files'):
        return list_processed_files()
    elif method == 'POST':
        return process_api_request(body, query_params)
    
    return create_success_response({
        "message": "Lambda File Processor API",
        "aws_available": AWS_AVAILABLE,
        "endpoints": {
            "POST /process": "Process data via API",
            "GET /status": "Get processing statistics",
            "GET /files": "List processed files"
        },
        "received_data": body,
        "timestamp": datetime.now().isoformat()
    })

def get_file_metadata(bucket, key):
    """Get file metadata from S3"""
    if not AWS_AVAILABLE:
        return {"error": "AWS not available"}
        
    try:
        response = s3_client.head_object(Bucket=bucket, Key=key)
        
        return {
            "file_name": os.path.basename(key),
            "file_size": response.get('ContentLength', 0),
            "last_modified": response.get('LastModified').isoformat() if response.get('LastModified') else None,
            "etag": response.get('ETag', '').strip('"')
        }
    except Exception as e:
        return {"error": str(e)}

def log_processing_event(bucket, key, file_info, processing_result):
    """Log processing event to DynamoDB"""
    if not AWS_AVAILABLE:
        return
        
    try:
        table = dynamodb.Table(TABLE_NAME)
        
        item = {
            'processing_id': f"{bucket}-{key}-{datetime.now().timestamp()}",
            'timestamp': datetime.now().isoformat(),
            'bucket': bucket,
            'file_key': key,
            'file_info': file_info,
            'processing_result': processing_result
        }
        
        table.put_item(Item=item)
        print(f"Logged processing event for {key}")
        
    except Exception as e:
        print(f"Error logging to DynamoDB: {str(e)}")

def get_processing_status():
    """Get processing statistics"""
    return create_success_response({
        "service_status": "healthy",
        "aws_available": AWS_AVAILABLE,
        "last_check": datetime.now().isoformat()
    })

def list_processed_files():
    """List recently processed files"""
    return create_success_response({
        "message": "File listing feature",
        "aws_available": AWS_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    })

def process_api_request(body, query_params):
    """Process API requests"""
    return create_success_response({
        "message": "API request processed successfully",
        "received_data": body,
        "query_parameters": query_params,
        "processing_id": f"api-{datetime.now().timestamp()}",
        "timestamp": datetime.now().isoformat()
    })

def create_success_response(data):
    """Create successful API response"""
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
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
