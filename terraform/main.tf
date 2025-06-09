terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.0"
}

provider "aws" {
  region = var.aws_region
}

<<<<<<< HEAD
# S3 Bucket for file uploads with custom name
=======
# S3 Bucket for file uploads
>>>>>>> dev
resource "aws_s3_bucket" "file_upload_bucket" {
  bucket = "p3-lambda-file-processor-uploads"
  
  tags = {
    Name        = "P3-Lambda-File-Processor-Uploads"
    Environment = var.environment
    Project     = "P3-AWS-Lambda-File-Processor"
  }
}

# S3 Bucket versioning
resource "aws_s3_bucket_versioning" "file_upload_bucket_versioning" {
  bucket = aws_s3_bucket.file_upload_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket public access configuration
resource "aws_s3_bucket_public_access_block" "file_upload_bucket_pab" {
  bucket = aws_s3_bucket.file_upload_bucket.id
<<<<<<< HEAD

=======
>>>>>>> dev
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# S3 Bucket policy for public uploads
resource "aws_s3_bucket_policy" "file_upload_bucket_policy" {
  bucket = aws_s3_bucket.file_upload_bucket.id
<<<<<<< HEAD

=======
>>>>>>> dev
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicUploadAccess"
        Effect    = "Allow"
        Principal = "*"
        Action = [
          "s3:PutObject",
          "s3:GetObject"
        ]
        Resource = "${aws_s3_bucket.file_upload_bucket.arn}/*"
<<<<<<< HEAD
      },
      {
        Sid       = "PublicListAccess"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:ListBucket"
        Resource  = aws_s3_bucket.file_upload_bucket.arn
      }
    ]
  })

=======
      }
    ]
  })
>>>>>>> dev
  depends_on = [aws_s3_bucket_public_access_block.file_upload_bucket_pab]
}

# DynamoDB table for processing logs
resource "aws_dynamodb_table" "file_processing_log" {
  name           = "file-processing-log"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "processing_id"

  attribute {
    name = "processing_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  global_secondary_index {
<<<<<<< HEAD
    name     = "timestamp-index"
    hash_key = "timestamp"
=======
    name               = "timestamp-index"
    hash_key           = "timestamp"
    projection_type    = "ALL"
>>>>>>> dev
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = {
    Name        = "P3-File-Processing-Log"
    Environment = var.environment
    Project     = "P3-AWS-Lambda-File-Processor"
  }
}

# SNS Topic for notifications
resource "aws_sns_topic" "file_processing_notifications" {
  name = "p3-file-processing-notifications"
<<<<<<< HEAD

=======
>>>>>>> dev
  tags = {
    Name        = "P3-File-Processing-Notifications"
    Environment = var.environment
    Project     = "P3-AWS-Lambda-File-Processor"
  }
}

# SNS Topic subscription (email)
resource "aws_sns_topic_subscription" "email_notification" {
  topic_arn = aws_sns_topic.file_processing_notifications.arn
  protocol  = "email"
  endpoint  = var.notification_email
}

# IAM role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "P3-lambda-file-processor-role"
<<<<<<< HEAD

=======
>>>>>>> dev
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
<<<<<<< HEAD

=======
>>>>>>> dev
  tags = {
    Name        = "P3-Lambda-File-Processor-Role"
    Environment = var.environment
    Project     = "P3-AWS-Lambda-File-Processor"
  }
}

<<<<<<< HEAD
# Enhanced IAM policy for Lambda (includes DynamoDB and SNS permissions)
resource "aws_iam_role_policy" "lambda_policy" {
  name = "P3-lambda-file-processor-policy"
  role = aws_iam_role.lambda_role.id

=======
# Enhanced IAM policy for Lambda
resource "aws_iam_role_policy" "lambda_policy" {
  name = "P3-lambda-file-processor-policy"
  role = aws_iam_role.lambda_role.id
>>>>>>> dev
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.file_upload_bucket.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = aws_s3_bucket.file_upload_bucket.arn
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.file_processing_log.arn,
          "${aws_dynamodb_table.file_processing_log.arn}/index/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.file_processing_notifications.arn
      }
    ]
  })
}

# Attach basic execution policy to Lambda role
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/P3-lambda-file-processor"
  retention_in_days = 14
<<<<<<< HEAD

=======
>>>>>>> dev
  tags = {
    Name        = "P3-Lambda-Logs"
    Environment = var.environment
    Project     = "P3-AWS-Lambda-File-Processor"
  }
}

# Lambda function
resource "aws_lambda_function" "file_processor" {
  filename         = "../lambda-code/lambda_function.zip"
  function_name    = "P3-lambda-file-processor"
  role            = aws_iam_role.lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  runtime          = "python3.9"
  timeout          = 60
<<<<<<< HEAD

=======
>>>>>>> dev
  source_code_hash = filebase64sha256("../lambda-code/lambda_function.zip")

  environment {
    variables = {
      BUCKET_NAME = aws_s3_bucket.file_upload_bucket.bucket
      DYNAMODB_TABLE = aws_dynamodb_table.file_processing_log.name
      SNS_TOPIC_ARN = aws_sns_topic.file_processing_notifications.arn
    }
  }

  tags = {
    Name        = "P3-Lambda-File-Processor"
    Environment = var.environment
    Project     = "P3-AWS-Lambda-File-Processor"
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_iam_role_policy.lambda_policy,
    aws_cloudwatch_log_group.lambda_logs,
  ]
}

# CloudWatch Alarm for Lambda errors
resource "aws_cloudwatch_metric_alarm" "lambda_error_alarm" {
  alarm_name          = "p3-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "60"
  statistic           = "Sum"
  threshold           = "1"
  alarm_description   = "This metric monitors lambda errors"
  alarm_actions       = [aws_sns_topic.file_processing_notifications.arn]

  dimensions = {
    FunctionName = aws_lambda_function.file_processor.function_name
  }

  tags = {
    Name        = "P3-Lambda-Error-Alarm"
    Environment = var.environment
    Project     = "P3-AWS-Lambda-File-Processor"
  }
}

# API Gateway REST API
resource "aws_api_gateway_rest_api" "file_processor_api" {
  name        = "P3-lambda-file-processor-api"
  description = "API Gateway for P3 Lambda File Processor"
<<<<<<< HEAD

=======
>>>>>>> dev
  tags = {
    Name        = "P3-Lambda-File-Processor-API"
    Environment = var.environment
    Project     = "P3-AWS-Lambda-File-Processor"
  }
}

# API Gateway Resource
resource "aws_api_gateway_resource" "processor_resource" {
  rest_api_id = aws_api_gateway_rest_api.file_processor_api.id
  parent_id   = aws_api_gateway_rest_api.file_processor_api.root_resource_id
  path_part   = "process"
}

# API Gateway POST Method
resource "aws_api_gateway_method" "processor_method" {
  rest_api_id   = aws_api_gateway_rest_api.file_processor_api.id
  resource_id   = aws_api_gateway_resource.processor_resource.id
  http_method   = "POST"
  authorization = "NONE"
}

# API Gateway POST Integration
resource "aws_api_gateway_integration" "lambda_integration" {
  rest_api_id = aws_api_gateway_rest_api.file_processor_api.id
  resource_id = aws_api_gateway_resource.processor_resource.id
  http_method = aws_api_gateway_method.processor_method.http_method
<<<<<<< HEAD

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.file_processor.invoke_arn
}

# API Gateway GET Method (for browser testing)
resource "aws_api_gateway_method" "processor_get_method" {
  rest_api_id   = aws_api_gateway_rest_api.file_processor_api.id
  resource_id   = aws_api_gateway_resource.processor_resource.id
  http_method   = "GET"
  authorization = "NONE"
}

# API Gateway GET Integration
resource "aws_api_gateway_integration" "lambda_get_integration" {
  rest_api_id = aws_api_gateway_rest_api.file_processor_api.id
  resource_id = aws_api_gateway_resource.processor_resource.id
  http_method = aws_api_gateway_method.processor_get_method.http_method

=======
>>>>>>> dev
  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.file_processor.invoke_arn
}

# Lambda permission for API Gateway
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.file_processor.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.file_processor_api.execution_arn}/*/*"
}

# API Gateway Deployment
resource "aws_api_gateway_deployment" "processor_deployment" {
  depends_on = [
    aws_api_gateway_method.processor_method,
    aws_api_gateway_integration.lambda_integration,
<<<<<<< HEAD
    aws_api_gateway_method.processor_get_method,
    aws_api_gateway_integration.lambda_get_integration,
  ]

  rest_api_id = aws_api_gateway_rest_api.file_processor_api.id

  lifecycle {
    create_before_destroy = true
  }

=======
  ]
  rest_api_id = aws_api_gateway_rest_api.file_processor_api.id
  lifecycle {
    create_before_destroy = true
  }
>>>>>>> dev
  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.processor_resource.id,
      aws_api_gateway_method.processor_method.id,
      aws_api_gateway_integration.lambda_integration.id,
<<<<<<< HEAD
      aws_api_gateway_method.processor_get_method.id,
      aws_api_gateway_integration.lambda_get_integration.id,
=======
>>>>>>> dev
    ]))
  }
}

# API Gateway Stage
resource "aws_api_gateway_stage" "processor_stage" {
  deployment_id = aws_api_gateway_deployment.processor_deployment.id
  rest_api_id   = aws_api_gateway_rest_api.file_processor_api.id
  stage_name    = var.environment
<<<<<<< HEAD

=======
>>>>>>> dev
  tags = {
    Name        = "P3-Lambda-File-Processor-Stage"
    Environment = var.environment
    Project     = "P3-AWS-Lambda-File-Processor"
  }
}

# Lambda permission for S3
resource "aws_lambda_permission" "s3_trigger" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.file_processor.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.file_upload_bucket.arn
}

# S3 bucket notification
resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.file_upload_bucket.id
<<<<<<< HEAD

=======
>>>>>>> dev
  lambda_function {
    lambda_function_arn = aws_lambda_function.file_processor.arn
    events              = ["s3:ObjectCreated:*"]
  }
<<<<<<< HEAD

=======
>>>>>>> dev
  depends_on = [aws_lambda_permission.s3_trigger]
}
