#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Global AWS Mocker - A comprehensive mock implementation of AWS services
Includes mocking for EC2, S3, RDS, Lambda, Bedrock, and other AWS services
with realistic data generation and usage patterns.
"""

import pandas as pd
import json
from datetime import datetime, timedelta
import random
import uuid
import numpy as np
from typing import Dict, List, Optional, Union, Any
import string

class GlobalAWSMocker:
    def __init__(self):
        # Initialize base AWS mock data
        self.mock_aws = MockAWS()
        
        # Service pricing and usage tracking
        self.service_pricing = {
            'EC2': {
                't2.micro': 0.0116,
                't3.medium': 0.0416,
                'm5.large': 0.096,
                'c5.xlarge': 0.17,
                'r5.large': 0.126,
                'p3.2xlarge': 3.06
            },
            'RDS': {
                'db.t3.micro': 0.017,
                'db.t3.small': 0.034,
                'db.r5.large': 0.29,
                'db.r5.xlarge': 0.58
            },
            'Lambda': {
                'requests': 0.20,  # per 1M requests
                'duration': 0.0000166667  # per GB-second
            },
            'S3': {
                'storage': 0.023,  # per GB-month
                'requests': {
                    'PUT': 0.005,  # per 1000 requests
                    'GET': 0.0004,  # per 1000 requests
                    'DELETE': 0.0  # free
                },
                'data_transfer': 0.09  # per GB
            },
            'DynamoDB': {
                'write_units': 1.25,  # per million WCU
                'read_units': 0.25,  # per million RCU
                'storage': 0.25,  # per GB-month
                'backup': 0.10,  # per GB-month
                'restore': 0.15  # per GB
            },
            'ECS': {
                'fargate_vcpu': 0.04048,  # per vCPU-hour
                'fargate_memory': 0.004445  # per GB-hour
            },
            'EKS': {
                'cluster': 0.10,  # per hour
                'fargate_pod': 0.04048  # per vCPU-hour
            },
            'SageMaker': {
                'ml.t3.medium': 0.0464,
                'ml.c5.xlarge': 0.432,
                'ml.p3.2xlarge': 3.825,
                'endpoint': 0.0642  # per hour
            },
            'CloudFront': {
                'data_transfer': {
                    'us': 0.085,  # per GB
                    'europe': 0.085,
                    'asia': 0.114
                },
                'requests': {
                    'http': 0.0075,  # per 10,000
                    'https': 0.01  # per 10,000
                }
            },
            'Route53': {
                'hosted_zone': 0.50,  # per hosted zone per month
                'queries': 0.40  # per million queries
            },
            'ElastiCache': {
                'cache.t3.micro': 0.017,
                'cache.m5.large': 0.156,
                'cache.r5.xlarge': 0.384
            },
            'OpenSearch': {
                't3.small.search': 0.036,
                'm5.large.search': 0.139,
                'c5.2xlarge.search': 0.374
            },
            'MSK': {
                'kafka.t3.small': 0.0456,
                'kafka.m5.large': 0.144,
                'kafka.c5.2xlarge': 0.576
            }
        }
        
        # Usage patterns and metrics
        self.service_metrics = {
            'EC2': ['CPUUtilization', 'NetworkIn', 'NetworkOut', 'DiskReadOps', 'DiskWriteOps'],
            'RDS': ['CPUUtilization', 'DatabaseConnections', 'FreeStorageSpace', 'ReadIOPS', 'WriteIOPS'],
            'Lambda': ['Invocations', 'Duration', 'Errors', 'ConcurrentExecutions', 'Throttles'],
            'S3': ['BucketSizeBytes', 'NumberOfObjects', 'AllRequests', 'GetRequests', 'PutRequests'],
            'DynamoDB': ['ConsumedReadCapacityUnits', 'ConsumedWriteCapacityUnits', 'ReadThrottleEvents', 'WriteThrottleEvents'],
            'ECS': ['CPUUtilization', 'MemoryUtilization', 'RunningTaskCount', 'PendingTaskCount'],
            'EKS': ['cluster_failed_node_count', 'node_cpu_utilization', 'node_memory_utilization'],
            'SageMaker': ['CPUUtilization', 'MemoryUtilization', 'GPUUtilization', 'InvocationsPerInstance'],
            'CloudFront': ['Requests', 'BytesDownloaded', 'BytesUploaded', 'TotalErrorRate', '4xxErrorRate', '5xxErrorRate'],
            'Route53': ['DNSQueries', 'HealthCheckStatus'],
            'ElastiCache': ['CPUUtilization', 'SwapUsage', 'NetworkBytesIn', 'NetworkBytesOut', 'CurrConnections'],
            'OpenSearch': ['FreeStorageSpace', 'ClusterStatus.green', 'SearchableDocuments', 'CPUUtilization'],
            'MSK': ['BytesInPerSec', 'BytesOutPerSec', 'MessagesInPerSec', 'PartitionCount']
        }
        
        # EC2 instance state and metadata
        self.ec2_instances: Dict[str, Dict] = {}
        self.ec2_amis: Dict[str, Dict] = {}
        self.ec2_volumes: Dict[str, Dict] = {}
        self.ec2_snapshots: Dict[str, Dict] = {}
        
        # S3 buckets and objects
        self.s3_buckets: Dict[str, Dict] = {}
        self.s3_objects: Dict[str, Dict] = {}
        
        # RDS instances and snapshots
        self.rds_instances: Dict[str, Dict] = {}
        self.rds_snapshots: Dict[str, Dict] = {}
        
        # Lambda functions and versions
        self.lambda_functions: Dict[str, Dict] = {}
        self.lambda_versions: Dict[str, Dict] = {}
        
        # Additional service resources
        self.dynamodb_tables: Dict[str, Dict] = {}
        self.ecs_clusters: Dict[str, Dict] = {}
        self.eks_clusters: Dict[str, Dict] = {}
        self.sagemaker_endpoints: Dict[str, Dict] = {}
        self.cloudfront_distributions: Dict[str, Dict] = {}
        self.route53_zones: Dict[str, Dict] = {}
        self.elasticache_clusters: Dict[str, Dict] = {}
        self.opensearch_domains: Dict[str, Dict] = {}
        self.msk_clusters: Dict[str, Dict] = {}
        
        # Initialize mock data
        self._initialize_mock_data()

    def _initialize_mock_data(self):
        """Initialize mock data for all AWS services"""
        self._initialize_ec2()
        self._initialize_s3()
        self._initialize_rds()
        self._initialize_lambda()

    def _initialize_ec2(self):
        """Initialize EC2 instances, AMIs, volumes, and snapshots"""
        # Generate mock EC2 instances
        for region in self.mock_aws.regions:
            for family, instances in self.mock_aws.ec2_instance_types.items():
                for instance_type in instances:
                    num_instances = random.randint(1, 5)
                    for _ in range(num_instances):
                        instance_id = f"i-{self._generate_resource_id()}"
                        self.ec2_instances[instance_id] = {
                            'InstanceId': instance_id,
                            'InstanceType': instance_type,
                            'Region': region,
                            'State': random.choice(['running', 'stopped', 'terminated']),
                            'LaunchTime': (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
                            'Tags': self._generate_tags(),
                            'PublicIpAddress': self._generate_ip(),
                            'PrivateIpAddress': self._generate_ip(),
                            'Platform': random.choice(['Linux/UNIX', 'Windows']),
                            'VpcId': f"vpc-{self._generate_resource_id()}",
                            'SubnetId': f"subnet-{self._generate_resource_id()}",
                            'SecurityGroups': [
                                {'GroupId': f"sg-{self._generate_resource_id()}", 
                                 'GroupName': f"security-group-{random.randint(1, 100)}"}
                            ]
                        }

    def _initialize_s3(self):
        """Initialize S3 buckets and objects"""
        num_buckets = random.randint(5, 15)
        for _ in range(num_buckets):
            bucket_name = f"mock-bucket-{self._generate_resource_id().lower()}"
            self.s3_buckets[bucket_name] = {
                'Name': bucket_name,
                'CreationDate': (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
                'Region': random.choice(list(self.mock_aws.regions.keys())),
                'Tags': self._generate_tags(),
                'Versioning': random.choice(['Enabled', 'Suspended']),
                'Objects': {}
            }
            
            # Generate mock objects for each bucket
            num_objects = random.randint(10, 100)
            for _ in range(num_objects):
                key = f"folder{random.randint(1,5)}/mock-object-{self._generate_resource_id()}"
                self.s3_objects[f"{bucket_name}/{key}"] = {
                    'Key': key,
                    'Size': random.randint(1024, 1024*1024*100),  # 1KB to 100MB
                    'LastModified': (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                    'StorageClass': random.choice(['STANDARD', 'STANDARD_IA', 'GLACIER']),
                    'Metadata': {'mock-metadata': 'value'}
                }

    def _initialize_rds(self):
        """Initialize RDS instances and snapshots"""
        db_engines = ['mysql', 'postgres', 'aurora', 'sqlserver']
        instance_classes = ['db.t3.micro', 'db.t3.small', 'db.r5.large', 'db.r5.xlarge']
        
        for region in self.mock_aws.regions:
            num_instances = random.randint(1, 5)
            for _ in range(num_instances):
                instance_id = f"db-{self._generate_resource_id()}"
                engine = random.choice(db_engines)
                self.rds_instances[instance_id] = {
                    'DBInstanceIdentifier': instance_id,
                    'Engine': engine,
                    'EngineVersion': f"{random.randint(5, 14)}.{random.randint(0, 9)}",
                    'DBInstanceClass': random.choice(instance_classes),
                    'Region': region,
                    'Status': random.choice(['available', 'backing-up', 'maintenance']),
                    'Endpoint': {
                        'Address': f"{instance_id}.{region}.rds.amazonaws.com",
                        'Port': 3306 if engine == 'mysql' else 5432
                    },
                    'AllocatedStorage': random.randint(20, 1000),
                    'Tags': self._generate_tags()
                }

    def _initialize_lambda(self):
        """Initialize Lambda functions and versions"""
        runtimes = ['python3.8', 'python3.9', 'nodejs16.x', 'nodejs18.x', 'java11']
        memory_sizes = [128, 256, 512, 1024, 2048]
        
        for region in self.mock_aws.regions:
            num_functions = random.randint(5, 15)
            for _ in range(num_functions):
                function_name = f"lambda-{self._generate_resource_id()}"
                self.lambda_functions[function_name] = {
                    'FunctionName': function_name,
                    'FunctionArn': f"arn:aws:lambda:{region}:123456789012:function:{function_name}",
                    'Runtime': random.choice(runtimes),
                    'Role': f"arn:aws:iam::123456789012:role/lambda-role-{random.randint(1, 100)}",
                    'Handler': 'index.handler',
                    'CodeSize': random.randint(1024, 1024*1024),  # 1KB to 1MB
                    'Description': f"Mock Lambda function {function_name}",
                    'Timeout': random.randint(3, 900),
                    'MemorySize': random.choice(memory_sizes),
                    'LastModified': (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                    'Version': str(random.randint(1, 10)),
                    'Environment': {
                        'Variables': {
                            'ENV': random.choice(['dev', 'staging', 'prod']),
                            'REGION': region
                        }
                    },
                    'Tags': self._generate_tags()
                }

    def _generate_resource_id(self, length: int = 8) -> str:
        """Generate a random resource ID"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

    def _generate_ip(self) -> str:
        """Generate a random IP address"""
        return '.'.join(str(random.randint(0, 255)) for _ in range(4))

    def _generate_tags(self) -> Dict[str, str]:
        """Generate random AWS tags"""
        num_tags = random.randint(1, 5)
        tags = {}
        for tag_key, tag_values in list(self.mock_aws.tags.items())[:num_tags]:
            tags[tag_key] = random.choice(tag_values)
        return tags

    # EC2 Methods
    def describe_instances(self, region: str = None, filters: List[Dict] = None) -> Dict:
        """Mock EC2 describe instances API"""
        instances = []
        for instance in self.ec2_instances.values():
            if region and instance['Region'] != region:
                continue
            if filters:
                match = True
                for filter_dict in filters:
                    if filter_dict['Name'] == 'instance-state-name':
                        if instance['State'] not in filter_dict['Values']:
                            match = False
                    # Add more filter implementations as needed
                if not match:
                    continue
            instances.append(instance)
        return {'Reservations': [{'Instances': instances}]}

    # S3 Methods
    def list_buckets(self) -> Dict:
        """Mock S3 list buckets API"""
        return {
            'Buckets': [
                {
                    'Name': bucket['Name'],
                    'CreationDate': bucket['CreationDate']
                }
                for bucket in self.s3_buckets.values()
            ],
            'Owner': {
                'DisplayName': 'MockOwner',
                'ID': '123456789012'
            }
        }

    def list_objects_v2(self, bucket: str, prefix: str = None) -> Dict:
        """Mock S3 list objects v2 API"""
        objects = []
        for obj_key, obj in self.s3_objects.items():
            if obj_key.startswith(f"{bucket}/"):
                if prefix and not obj['Key'].startswith(prefix):
                    continue
                objects.append({
                    'Key': obj['Key'],
                    'Size': obj['Size'],
                    'LastModified': obj['LastModified'],
                    'StorageClass': obj['StorageClass']
                })
        return {
            'Contents': objects,
            'Name': bucket,
            'Prefix': prefix or '',
            'KeyCount': len(objects),
            'MaxKeys': 1000,
            'IsTruncated': False
        }

    # RDS Methods
    def describe_db_instances(self, db_instance_identifier: str = None) -> Dict:
        """Mock RDS describe DB instances API"""
        instances = []
        for instance in self.rds_instances.values():
            if db_instance_identifier and instance['DBInstanceIdentifier'] != db_instance_identifier:
                continue
            instances.append(instance)
        return {'DBInstances': instances}

    # Lambda Methods
    def list_functions(self, region: str = None) -> Dict:
        """Mock Lambda list functions API"""
        functions = []
        for function in self.lambda_functions.values():
            if region and function['FunctionArn'].split(':')[3] != region:
                continue
            functions.append(function)
        return {'Functions': functions}

    # Bedrock Methods (inherited from MockAWS)
    def generate_bedrock_logs(self, days: int = 7, region: str = 'us-east-1') -> pd.DataFrame:
        """Generate Bedrock invocation logs (inherited from MockAWS)"""
        return self.mock_aws.generate_bedrock_logs(days, region)

    # Cost and Usage Methods (inherited from MockAWS)
    def get_cost_and_usage(self, **kwargs) -> Dict:
        """Get cost and usage data (inherited from MockAWS)"""
        return self.mock_aws.generate_cost_and_usage_response(**kwargs)

    def get_cost_forecast(self, **kwargs) -> Dict:
        """Get cost forecast (inherited from MockAWS)"""
        return self.mock_aws.generate_cost_forecast(**kwargs)

    def calculate_service_cost(self, service: str, resource_type: str, usage: float, region: str = 'us-east-1') -> float:
        """Calculate cost for a specific service and resource type based on usage"""
        # Get base pricing
        pricing = self.service_pricing.get(service, {})
        
        # Apply regional pricing factor
        region_factors = {
            'us-east-1': 1.0,
            'us-west-2': 1.05,
            'eu-west-1': 1.1,
            'ap-northeast-1': 1.15
        }
        region_factor = region_factors.get(region, 1.0)
        
        # Calculate cost based on service type
        if service == 'EC2':
            return pricing.get(resource_type, 0.0) * usage * region_factor
        elif service == 'RDS':
            return pricing.get(resource_type, 0.0) * usage * region_factor
        elif service == 'Lambda':
            if resource_type == 'requests':
                return (usage / 1_000_000) * pricing['requests']
            else:  # duration
                return usage * pricing['duration']
        elif service == 'S3':
            if resource_type == 'storage':
                return usage * pricing['storage']
            elif resource_type in pricing['requests']:
                return (usage / 1000) * pricing['requests'][resource_type]
            else:
                return usage * pricing['data_transfer']
        elif service == 'DynamoDB':
            return pricing.get(resource_type, 0.0) * usage
        elif service == 'ECS':
            return pricing.get(resource_type, 0.0) * usage
        elif service == 'EKS':
            return pricing.get(resource_type, 0.0) * usage
        elif service == 'SageMaker':
            return pricing.get(resource_type, 0.0) * usage * region_factor
        elif service == 'CloudFront':
            if 'data_transfer' in resource_type:
                region = resource_type.split('_')[-1]
                return usage * pricing['data_transfer'].get(region, pricing['data_transfer']['us'])
            else:
                return (usage / 10000) * pricing['requests'].get(resource_type, 0.0)
        elif service == 'Route53':
            return pricing.get(resource_type, 0.0) * usage
        elif service == 'ElastiCache':
            return pricing.get(resource_type, 0.0) * usage * region_factor
        elif service == 'OpenSearch':
            return pricing.get(resource_type, 0.0) * usage * region_factor
        elif service == 'MSK':
            return pricing.get(resource_type, 0.0) * usage * region_factor
        
        return 0.0

    def generate_service_metrics(self, service: str, resource_id: str, start_time: datetime, end_time: datetime, 
                               period: int = 300) -> List[Dict]:
        """Generate mock CloudWatch metrics for a service"""
        metrics = self.service_metrics.get(service, [])
        result = []
        
        current_time = start_time
        while current_time < end_time:
            for metric in metrics:
                # Generate realistic metric values based on service and metric type
                if 'CPU' in metric:
                    value = random.uniform(10, 80)
                elif 'Memory' in metric:
                    value = random.uniform(20, 70)
                elif 'Count' in metric:
                    value = random.randint(1, 100)
                elif 'Bytes' in metric:
                    value = random.uniform(1024, 1024*1024*10)
                elif 'IOPS' in metric:
                    value = random.uniform(100, 1000)
                else:
                    value = random.uniform(0, 100)
                
                result.append({
                    'MetricName': metric,
                    'Timestamp': current_time.isoformat(),
                    'Value': value,
                    'Unit': self._get_metric_unit(metric),
                    'ResourceId': resource_id
                })
            
            current_time += timedelta(seconds=period)
        
        return result

    def _get_metric_unit(self, metric: str) -> str:
        """Determine the appropriate unit for a metric"""
        if 'CPU' in metric:
            return 'Percent'
        elif 'Bytes' in metric:
            return 'Bytes'
        elif 'Count' in metric:
            return 'Count'
        elif 'IOPS' in metric:
            return 'Count/Second'
        elif 'Memory' in metric:
            return 'Bytes'
        elif 'Time' in metric:
            return 'Milliseconds'
        else:
            return 'None'

# Example usage
if __name__ == "__main__":
    # Create mocker instance
    mocker = GlobalAWSMocker()
    
    # Example: List EC2 instances
    print("\nEC2 Instances:")
    instances = mocker.describe_instances()
    print(json.dumps(instances['Reservations'][0]['Instances'][:2], indent=2))
    
    # Example: List S3 buckets
    print("\nS3 Buckets:")
    buckets = mocker.list_buckets()
    print(json.dumps(buckets['Buckets'][:2], indent=2))
    
    # Example: List RDS instances
    print("\nRDS Instances:")
    rds = mocker.describe_db_instances()
    print(json.dumps(rds['DBInstances'][:2], indent=2))
    
    # Example: List Lambda functions
    print("\nLambda Functions:")
    functions = mocker.list_functions()
    print(json.dumps(functions['Functions'][:2], indent=2))
    
    # Example: Generate Bedrock logs
    print("\nBedrock Logs:")
    logs_df = mocker.generate_bedrock_logs(days=1)
    print(logs_df.head(2).to_json(orient='records', indent=2)) 