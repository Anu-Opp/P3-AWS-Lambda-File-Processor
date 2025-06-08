# P3 AWS Lambda File Processor

## Project Overview
Sophisticated serverless file processing system with:
- Smart file type detection and processing
- Image thumbnail generation
- Document analysis capabilities
- DynamoDB logging and SNS notifications
- CloudWatch monitoring and alarms
- CI/CD pipeline with GitHub Actions

## Architecture
- **AWS Lambda**: Core file processing logic
- **S3**: File storage with public upload access
- **DynamoDB**: Processing metadata and logs
- **SNS**: Email notifications
- **API Gateway**: REST API endpoints
- **CloudWatch**: Monitoring and alerting

## API Endpoints
- `POST /process` - Process data via API
- `GET /status` - Get processing statistics
- `GET /files` - List recently processed files

## Deployment
Automated deployment via GitHub Actions with Terraform.
