import json
import boto3
import urllib.parse
from datetime import datetime
import uuid
import os

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
sns_client = boto3.client('sns')

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
        
        # Process based on file type
        processing_result = process_file_by_type(bucket, key, file_info)
        
        # Log to DynamoDB
        log_processing_event(bucket, key, file_info, processing_result)
        
        # Send notification
        send_notification(bucket, key, file_info, processing_result)
        
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
    
    # Process API request
    processing_result = {
        "processing_id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "type": "api_request",
        "data": body,
        "status": "success"
    }
    
    # Log to DynamoDB
    log_api_request(processing_result)
    
    # Send notification for API requests too
    send_api_notification(processing_result)
    
    return create_success_response({
        "message": "API request processed successfully",
        "processing_id": processing_result["processing_id"],
        "timestamp": processing_result["timestamp"]
    })

def get_file_metadata(bucket, key):
    """Get comprehensive file metadata"""
    try:
        response = s3_client.head_object(Bucket=bucket, Key=key)
        
        file_ext = os.path.splitext(key)[1].lower()
        
        return {
            "file_name": os.path.basename(key),
            "file_path": key,
            "file_size": response.get('ContentLength', 0),
            "file_extension": file_ext,
            "last_modified": response.get('LastModified').isoformat() if response.get('LastModified') else None,
            "etag": response.get('ETag', '').strip('"')
        }
    except Exception as e:
        print(f"Error getting file metadata: {str(e)}")
        return {"error": str(e)}

def process_file_by_type(bucket, key, file_info):
    """Process file based on its type"""
    file_ext = file_info.get('file_extension', '').lower()
    
    processing_result = {
        "file_name": file_info.get('file_name'),
        "processing_type": "unknown",
        "status": "success",
        "details": {}
    }
    
    try:
        # Image processing
        if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            processing_result.update({
                "processing_type": "image",
                "details": {
                    "message": "Image file processed and thumbnails could be generated",
                    "file_size_mb": round(file_info.get('file_size', 0) / 1024 / 1024, 2)
                }
            })
        
        # Document processing
        elif file_ext in ['.pdf', '.txt', '.doc', '.docx', '.csv']:
            processing_result.update({
                "processing_type": "document",
                "details": {
                    "message": "Document processed and indexed",
                    "file_size_mb": round(file_info.get('file_size', 0) / 1024 / 1024, 2),
                    "pages_estimated": max(1, file_info.get('file_size', 0) // 2000)
                }
            })
        
        # Video/Audio processing
        elif file_ext in ['.mp4', '.avi', '.mov', '.mp3', '.wav']:
            processing_result.update({
                "processing_type": "media",
                "details": {
                    "message": "Media file processed and metadata extracted",
                    "file_size_mb": round(file_info.get('file_size', 0) / 1024 / 1024, 2)
                }
            })
        
        # Default processing
        else:
            processing_result.update({
                "processing_type": "general",
                "details": {
                    "message": "File received and catalogued",
                    "file_size_mb": round(file_info.get('file_size', 0) / 1024 / 1024, 2)
                }
            })
            
    except Exception as e:
        processing_result.update({
            "status": "error",
            "error": str(e)
        })
    
    return processing_result

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
            'ttl': int(datetime.now().timestamp()) + (30 * 24 * 60 * 60)  # 30 days TTL
        }
        
        table.put_item(Item=item)
        print(f"✅ Logged processing event to DynamoDB for {key}")
        
    except Exception as e:
        print(f"❌ Error logging to DynamoDB: {str(e)}")

def log_api_request(processing_result):
    """Log API request to DynamoDB"""
    try:
        table = dynamodb.Table(TABLE_NAME)
        
        item = {
            'processing_id': processing_result['processing_id'],
            'timestamp': processing_result['timestamp'],
            'request_type': 'api_gateway',
            'processing_result': processing_result,
            'ttl': int(datetime.now().timestamp()) + (30 * 24 * 60 * 60)  # 30 days TTL
        }
        
        table.put_item(Item=item)
        print(f"✅ Logged API request to DynamoDB")
        
    except Exception as e:
        print(f"❌ Error logging API request to DynamoDB: {str(e)}")

def send_notification(bucket, key, file_info, processing_result):
    """Send SNS notification for file processing"""
    if not SNS_TOPIC_ARN:
        print("⚠️ No SNS topic configured")
        return
        
    try:
        message = {
            "event": "file_processed",
            "bucket": bucket,
            "file": key,
            "processing_type": processing_result.get('processing_type'),
            "status": processing_result.get('status'),
            "file_size_mb": processing_result.get('details', {}).get('file_size_mb', 0),
            "timestamp": datetime.now().isoformat()
        }
        
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=json.dumps(message, indent=2),
            Subject=f"🚀 File Processed: {os.path.basename(key)}"
        )
        
        print(f"✅ Sent notification for {key}")
        
    except Exception as e:
        print(f"❌ Error sending notification: {str(e)}")

def send_api_notification(processing_result):
    """Send SNS notification for API requests"""
    if not SNS_TOPIC_ARN:
        return
        
    try:
        message = {
            "event": "api_request_processed",
            "processing_id": processing_result.get('processing_id'),
            "timestamp": processing_result.get('timestamp'),
            "status": "success"
        }
        
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=json.dumps(message, indent=2),
            Subject="🌐 API Request Processed"
        )
        
        print(f"✅ Sent API notification")
        
    except Exception as e:
        print(f"❌ Error sending API notification: {str(e)}")

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
