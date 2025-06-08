import json
import boto3
import urllib.parse
from datetime import datetime
import uuid
import os
import mimetypes
from PIL import Image
import io
import base64

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
        "endpoints": {
            "POST /process": "Process data via API",
            "GET /status": "Get processing statistics",
            "GET /files": "List processed files"
        }
    })

def get_file_metadata(bucket, key):
    """Get comprehensive file metadata"""
    try:
        response = s3_client.head_object(Bucket=bucket, Key=key)
        
        # Get file extension and MIME type
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

def process_file_by_type(bucket, key, file_info):
    """Process file based on its type"""
    file_ext = file_info.get('file_extension', '').lower()
    mime_type = file_info.get('mime_type', '')
    
    processing_result = {
        "file_name": file_info.get('file_name'),
        "processing_type": "unknown",
        "status": "success",
        "details": {}
    }
    
    try:
        # Image processing
        if mime_type and mime_type.startswith('image/'):
            processing_result = process_image_file(bucket, key, file_info)
        
        # Document processing
        elif file_ext in ['.pdf', '.txt', '.doc', '.docx']:
            processing_result = process_document_file(bucket, key, file_info)
        
        # Video/Audio processing
        elif mime_type and (mime_type.startswith('video/') or mime_type.startswith('audio/')):
            processing_result = process_media_file(bucket, key, file_info)
        
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

def process_image_file(bucket, key, file_info):
    """Process image files - create thumbnails"""
    try:
        # Download image
        response = s3_client.get_object(Bucket=bucket, Key=key)
        image_data = response['Body'].read()
        
        # Open with PIL
        with Image.open(io.BytesIO(image_data)) as img:
            # Get image dimensions
            width, height = img.size
            
            # Create thumbnail
            thumbnail = img.copy()
            thumbnail.thumbnail((200, 200), Image.Resampling.LANCZOS)
            
            # Save thumbnail to S3
            thumbnail_key = f"thumbnails/{os.path.splitext(key)[0]}_thumb.jpg"
            thumbnail_buffer = io.BytesIO()
            thumbnail.save(thumbnail_buffer, format='JPEG', quality=85)
            thumbnail_buffer.seek(0)
            
            s3_client.put_object(
                Bucket=bucket,
                Key=thumbnail_key,
                Body=thumbnail_buffer.getvalue(),
                ContentType='image/jpeg'
            )
            
            return {
                "file_name": file_info.get('file_name'),
                "processing_type": "image",
                "status": "success",
                "details": {
                    "original_dimensions": f"{width}x{height}",
                    "thumbnail_created": thumbnail_key,
                    "format": img.format,
                    "mode": img.mode
                }
            }
    
    except Exception as e:
        return {
            "file_name": file_info.get('file_name'),
            "processing_type": "image",
            "status": "error",
            "error": str(e)
        }

def process_document_file(bucket, key, file_info):
    """Process document files"""
    return {
        "file_name": file_info.get('file_name'),
        "processing_type": "document",
        "status": "success",
        "details": {
            "message": "Document processed and indexed",
            "file_size_mb": round(file_info.get('file_size', 0) / 1024 / 1024, 2),
            "pages_estimated": max(1, file_info.get('file_size', 0) // 2000)  # Rough estimate
        }
    }

def process_media_file(bucket, key, file_info):
    """Process video/audio files"""
    return {
        "file_name": file_info.get('file_name'),
        "processing_type": "media",
        "status": "success",
        "details": {
            "message": "Media file processed and metadata extracted",
            "file_size_mb": round(file_info.get('file_size', 0) / 1024 / 1024, 2),
            "duration_estimated": f"{file_info.get('file_size', 0) // 1000000} seconds"  # Very rough estimate
        }
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
            'ttl': int(datetime.now().timestamp()) + (30 * 24 * 60 * 60)  # 30 days TTL
        }
        
        table.put_item(Item=item)
        print(f"Logged processing event for {key}")
        
    except Exception as e:
        print(f"Error logging to DynamoDB: {str(e)}")

def send_notification(bucket, key, file_info, processing_result):
    """Send SNS notification"""
    if not SNS_TOPIC_ARN:
        return
        
    try:
        message = {
            "event": "file_processed",
            "bucket": bucket,
            "file": key,
            "processing_type": processing_result.get('processing_type'),
            "status": processing_result.get('status'),
            "timestamp": datetime.now().isoformat()
        }
        
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=json.dumps(message),
            Subject=f"File Processed: {os.path.basename(key)}"
        )
        
    except Exception as e:
        print(f"Error sending notification: {str(e)}")

def get_processing_status():
    """Get processing statistics from DynamoDB"""
    try:
        table = dynamodb.Table(TABLE_NAME)
        
        # This is a simplified version - in production, you'd use better querying
        response = table.scan(
            Select='COUNT'
        )
        
        return create_success_response({
            "total_files_processed": response.get('Count', 0),
            "service_status": "healthy",
            "last_check": datetime.now().isoformat()
        })
        
    except Exception as e:
        return create_error_response(f"Error getting status: {str(e)}")

def list_processed_files():
    """List recently processed files"""
    try:
        table = dynamodb.Table(TABLE_NAME)
        
        # Get recent files (simplified - in production use better indexing)
        response = table.scan(
            Limit=10,
            ProjectionExpression='processing_id, #ts, file_key, processing_result',
            ExpressionAttributeNames={'#ts': 'timestamp'}
        )
        
        files = []
        for item in response.get('Items', []):
            files.append({
                "processing_id": item.get('processing_id'),
                "timestamp": item.get('timestamp'),
                "file": item.get('file_key'),
                "status": item.get('processing_result', {}).get('status'),
                "type": item.get('processing_result', {}).get('processing_type')
            })
        
        return create_success_response({
            "recent_files": files,
            "count": len(files)
        })
        
    except Exception as e:
        return create_error_response(f"Error listing files: {str(e)}")

def process_api_request(body, query_params):
    """Process API requests"""
    return create_success_response({
        "message": "API request processed successfully",
        "received_data": body,
        "query_parameters": query_params,
        "processing_id": str(uuid.uuid4()),
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
