variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "P3-lambda-file-processor"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "bucket_name" {
  description = "S3 bucket name"
  type        = string
  default     = "p3-lambda-file-processor-uploads"
}

variable "notification_email" {
  description = "Email address for notifications"
  type        = string
  default     = "anu.op@outlook.com"
}
