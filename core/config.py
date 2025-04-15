import os

# Data directory configuration
DEFAULT_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# Default values for missing data
DEFAULT_CARBON_INTENSITY = 500.0  # gCO2e/kWh
DEFAULT_PUE = 1.5
DEFAULT_WATER_USAGE = 1.8  # liters/kWh
DEFAULT_WATER_STRESS = "Medium"

# AWS regions for analysis
AWS_REGIONS = [
    "us-east-1", "us-east-2", "us-west-1", "us-west-2",
    "eu-west-1", "eu-west-2", "eu-west-3", "eu-central-1", "eu-north-1",
    "ap-northeast-1", "ap-northeast-2", "ap-northeast-3",
    "ap-southeast-1", "ap-southeast-2", "ap-south-1",
    "sa-east-1", "ca-central-1", "me-south-1"
]

# Service categories
SERVICE_CATEGORIES = {
    "compute": ["ec2", "lambda", "ecs", "eks", "batch"],
    "storage": ["s3", "ebs", "efs", "glacier"],
    "database": ["rds", "dynamodb", "elasticache", "redshift"],
    "ai_ml": ["bedrock", "sagemaker", "comprehend", "rekognition", "textract"],
    "network": ["vpc", "elb", "cloudfront", "route53"]
}

# Default API settings
API_SETTINGS = {
    "host": "0.0.0.0",
    "port": 8000,
    "allowed_transports": ["stdio", "sse"],
    "default_transport": "stdio"
}

# Logging configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
} 