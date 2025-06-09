output "s3_bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.file_upload_bucket.bucket
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.file_upload_bucket.arn
}

output "s3_bucket_url" {
  description = "URL of the S3 bucket"
  value       = "https://${aws_s3_bucket.file_upload_bucket.bucket}.s3.${var.aws_region}.amazonaws.com"
}

output "api_gateway_url" {
  description = "URL of the API Gateway"
  value       = "https://${aws_api_gateway_rest_api.file_processor_api.id}.execute-api.${var.aws_region}.amazonaws.com/${aws_api_gateway_stage.processor_stage.stage_name}/process"
}

output "api_gateway_id" {
  description = "ID of the API Gateway"
  value       = aws_api_gateway_rest_api.file_processor_api.id
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.file_processor.function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.file_processor.arn
}

output "iam_role_name" {
  description = "Name of the IAM role"
  value       = aws_iam_role.lambda_role.name
}

# Summary output for easy testing
output "testing_instructions" {
  description = "Instructions for testing the deployment"
  value = <<EOT

=== TESTING INSTRUCTIONS ===

1. Test S3 Upload Trigger:
   aws s3 cp test-file.txt s3://${aws_s3_bucket.file_upload_bucket.bucket}/

2. Test API Gateway:
   curl -X POST "https://${aws_api_gateway_rest_api.file_processor_api.id}.execute-api.${var.aws_region}.amazonaws.com/${aws_api_gateway_stage.processor_stage.stage_name}/process" \
        -H "Content-Type: application/json" \
        -d '{"test": "data"}'

3. Check Lambda Logs:
   aws logs describe-log-groups --query 'logGroups[?contains(logGroupName, `P3-lambda-file-processor`)]'

4. S3 Bucket URL: https://${aws_s3_bucket.file_upload_bucket.bucket}.s3.${var.aws_region}.amazonaws.com

EOT
}
