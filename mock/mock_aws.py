import pandas as pd
import json
from datetime import datetime, timedelta
import random
import uuid
import numpy as np

class MockAWS:
    def __init__(self):
        # EC2 instance types by family
        self.ec2_instance_types = {
            'General Purpose': ['t2.micro', 't2.small', 't3.medium', 'm5.large', 'm6g.xlarge', 'm7g.2xlarge'],
            'Compute Optimized': ['c5.large', 'c5.xlarge', 'c5.2xlarge', 'c6g.4xlarge', 'c7g.8xlarge'],
            'Memory Optimized': ['r5.large', 'r5.xlarge', 'r6g.2xlarge', 'r6g.4xlarge', 'x2gd.8xlarge'],
            'Storage Optimized': ['i3.large', 'i3.xlarge', 'i4i.2xlarge', 'd3.4xlarge'],
            'Accelerated Computing': ['p3.2xlarge', 'p4d.24xlarge', 'g4dn.xlarge', 'g5.2xlarge']
        }
        
        # AWS Regions with their actual names
        self.regions = {
            'us-east-1': 'US East (N. Virginia)',
            'us-east-2': 'US East (Ohio)',
            'us-west-1': 'US West (N. California)',
            'us-west-2': 'US West (Oregon)',
            'eu-west-1': 'EU (Ireland)',
            'eu-central-1': 'EU (Frankfurt)',
            'ap-northeast-1': 'Asia Pacific (Tokyo)',
            'ap-southeast-1': 'Asia Pacific (Singapore)',
            'ap-southeast-2': 'Asia Pacific (Sydney)',
            'sa-east-1': 'South America (São Paulo)'
        }
        
        # Comprehensive service list
        self.services = {
            'Compute': [
                'Amazon Elastic Compute Cloud - Compute',
                'AWS Lambda',
                'Amazon Elastic Container Service',
                'Amazon EKS',
                'AWS Fargate',
                'Amazon Lightsail',
                'AWS Batch',
                'Amazon EC2 Spot Instances',
                'AWS Elastic Beanstalk'
            ],
            'Storage': [
                'Amazon Simple Storage Service',
                'Amazon Elastic Block Store',
                'Amazon Elastic File System',
                'Amazon FSx',
                'Amazon S3 Glacier',
                'AWS Storage Gateway',
                'AWS Backup',
                'Amazon FSx for Windows File Server',
                'Amazon FSx for Lustre'
            ],
            'Database': [
                'Amazon RDS Service',
                'Amazon DynamoDB',
                'Amazon ElastiCache',
                'Amazon Redshift',
                'Amazon DocumentDB',
                'Amazon Neptune',
                'Amazon Timestream',
                'Amazon Aurora',
                'Amazon Keyspaces',
                'Amazon MemoryDB for Redis',
                'Amazon QLDB'
            ],
            'Networking': [
                'Amazon Virtual Private Cloud',
                'AWS Direct Connect',
                'Elastic Load Balancing',
                'Amazon CloudFront',
                'Amazon Route 53',
                'AWS Transit Gateway',
                'AWS Global Accelerator',
                'AWS PrivateLink',
                'AWS App Mesh',
                'AWS Cloud Map'
            ],
            'Analytics': [
                'Amazon Athena',
                'Amazon EMR',
                'AWS Glue',
                'Amazon Kinesis',
                'Amazon QuickSight',
                'Amazon OpenSearch Service',
                'Amazon Redshift Spectrum',
                'AWS Data Exchange',
                'Amazon FinSpace',
                'AWS Clean Rooms'
            ],
            'AI/ML': [
                'Amazon Bedrock',
                'Amazon SageMaker',
                'Amazon Comprehend',
                'Amazon Forecast',
                'Amazon Polly',
                'Amazon Rekognition',
                'Amazon Textract',
                'Amazon Transcribe',
                'Amazon Translate',
                'Amazon CodeWhisperer',
                'Amazon Lex',
                'Amazon Personalize'
            ],
            'Security': [
                'AWS Identity and Access Management',
                'Amazon GuardDuty',
                'AWS Shield',
                'AWS WAF',
                'Amazon Inspector',
                'AWS Security Hub',
                'Amazon Detective',
                'AWS Firewall Manager',
                'Amazon Macie',
                'AWS Certificate Manager',
                'AWS Private Certificate Authority'
            ],
            'Developer Tools': [
                'AWS CodeCommit',
                'AWS CodeBuild',
                'AWS CodeDeploy',
                'AWS CodePipeline',
                'AWS Cloud9',
                'AWS CodeStar',
                'AWS X-Ray',
                'AWS Cloud Development Kit',
                'AWS CloudShell',
                'AWS Amplify'
            ],
            'Management': [
                'AWS CloudTrail',
                'Amazon CloudWatch',
                'AWS Config',
                'AWS Organizations',
                'AWS Systems Manager',
                'AWS Control Tower',
                'AWS Service Catalog',
                'AWS License Manager',
                'AWS Managed Services',
                'AWS Proton'
            ],
            'IoT': [
                'AWS IoT Core',
                'AWS IoT Greengrass',
                'AWS IoT Analytics',
                'AWS IoT Events',
                'AWS IoT SiteWise',
                'AWS IoT TwinMaker'
            ],
            'Media Services': [
                'Amazon Elastic Transcoder',
                'AWS Elemental MediaConvert',
                'AWS Elemental MediaLive',
                'AWS Elemental MediaPackage',
                'AWS Elemental MediaStore'
            ],
            'Application Integration': [
                'Amazon Simple Queue Service',
                'Amazon Simple Notification Service',
                'Amazon EventBridge',
                'AWS Step Functions',
                'Amazon MQ',
                'Amazon AppFlow'
            ],
            'Business Applications': [
                'Amazon Connect',
                'Amazon WorkMail',
                'Amazon Chime',
                'Amazon WorkSpaces',
                'Amazon WorkDocs'
            ]
        }
        
        # Flatten the services list
        self.all_services = [service for category in self.services.values() for service in category]
        
        # Bedrock models with their pricing
        self.bedrock_models = {
            'anthropic.claude-3-haiku-20240307-v1:0': {'input': 0.00025, 'output': 0.00125},
            'anthropic.claude-3-sonnet-20240229-v1:0': {'input': 0.003, 'output': 0.015},
            'anthropic.claude-3-opus-20240229-v1:0': {'input': 0.015, 'output': 0.075},
            'amazon.titan-text-express-v1': {'input': 0.0002, 'output': 0.0008},
            'amazon.titan-text-lite-v1': {'input': 0.0001, 'output': 0.0002},
            'meta.llama3-70b-instruct-v1:0': {'input': 0.0009, 'output': 0.0009},
            'mistral.mistral-7b-instruct-v0:2': {'input': 0.0002, 'output': 0.0002}
        }
        
        # IAM Users and Roles
        self.users = [
            'arn:aws:iam::123456789012:user/developer1',
            'arn:aws:iam::123456789012:user/developer2',
            'arn:aws:iam::123456789012:user/datascientist1',
            'arn:aws:iam::123456789012:user/datascientist2',
            'arn:aws:iam::123456789012:user/admin',
            'arn:aws:iam::123456789012:role/LambdaExecutionRole',
            'arn:aws:iam::123456789012:role/EC2InstanceRole',
            'arn:aws:iam::123456789012:role/MLModelTrainingRole',
            'arn:aws:iam::123456789012:role/DataProcessingRole'
        ]
        
        # Resource tags for cost allocation
        self.tags = {
            'Environment': ['dev', 'test', 'staging', 'prod'],
            'Project': ['frontend', 'backend', 'data-pipeline', 'ml-models', 'analytics'],
            'Department': ['engineering', 'data-science', 'marketing', 'operations', 'finance'],
            'CostCenter': ['cc-1234', 'cc-5678', 'cc-9012', 'cc-3456', 'cc-7890']
        }
        
        # Pricing models
        self.pricing_models = ['On-Demand', 'Reserved Instance', 'Savings Plan', 'Spot']
        
        # Usage types
        self.usage_types = {
            'EC2': ['BoxUsage', 'DataTransfer-In', 'DataTransfer-Out', 'EBS:VolumeUsage'],
            'S3': ['TimedStorage-ByteHrs', 'Requests-Tier1', 'Requests-Tier2', 'DataTransfer-Out'],
            'RDS': ['InstanceUsage', 'StorageUsage', 'BackupUsage', 'PIOPS'],
            'Lambda': ['Request', 'Duration-GB-Second'],
            'DynamoDB': ['ReadCapacityUnit-Hrs', 'WriteCapacityUnit-Hrs', 'PayPerRequest-Requests'],
            'ECS': ['EC2-CPU-Usage', 'EC2-Memory-Usage', 'Fargate-vCPU-Hours', 'Fargate-Memory-GB-Hours'],
            'EKS': ['Cluster-Hours', 'Fargate-Pod-vCPU-Hours', 'Fargate-Pod-Memory-GB-Hours'],
            'SageMaker': ['Instance-Hours', 'Storage-GB-Hours', 'Training-Minutes', 'Inference-Minutes'],
            'Bedrock': ['Input-Tokens', 'Output-Tokens', 'Training-Hours'],
            'CloudFront': ['DataTransfer-Out', 'Requests-Tier1', 'Requests-Tier2', 'SSL-Cert'],
            'Route53': ['Hosted-Zone', 'DNS-Queries', 'Health-Checks', 'Traffic-Flow'],
            'ElastiCache': ['Node-Hours', 'Storage-GB-Hours', 'Backup-GB'],
            'Redshift': ['Node-Hours', 'Backup-GB', 'Concurrency-Scaling-Seconds'],
            'OpenSearch': ['Instance-Hours', 'Storage-GB', 'UltraWarm-Instance-Hours'],
            'SNS': ['Requests', 'DeliveredMessages', 'HTTP-Notifications', 'Email-Notifications'],
            'SQS': ['Requests', 'Messages', 'Extended-Message-Retention'],
            'Kinesis': ['Shard-Hours', 'PutRecord-Units', 'Extended-Retention', 'Enhanced-Fanout'],
            'IoT': ['Messages', 'Rules-Engine-Execution', 'Device-Shadow', 'Registry-Operations'],
            'Connect': ['Active-Minutes', 'Phone-Numbers', 'DID-Minutes', 'Chat-Messages']
        }
        
        # Operation types
        self.operations = {
            'EC2': ['RunInstances', 'StopInstances', 'TerminateInstances'],
            'S3': ['PutObject', 'GetObject', 'ListBucket', 'DeleteObject'],
            'DynamoDB': ['GetItem', 'PutItem', 'Query', 'Scan'],
            'Lambda': ['Invoke', 'InvokeAsync'],
            'RDS': ['CreateDBInstance', 'ModifyDBInstance', 'DeleteDBInstance', 'CreateSnapshot'],
            'ECS': ['RunTask', 'StartTask', 'StopTask', 'UpdateService'],
            'EKS': ['CreateCluster', 'CreateNodegroup', 'DeleteCluster', 'UpdateClusterVersion'],
            'SageMaker': ['CreateTrainingJob', 'CreateEndpoint', 'InvokeEndpoint', 'CreateNotebookInstance'],
            'Bedrock': ['InvokeModel', 'CreateCustomModel', 'ListFoundationModels'],
            'CloudFront': ['CreateDistribution', 'UpdateDistribution', 'DeleteDistribution', 'CreateInvalidation'],
            'Route53': ['ChangeResourceRecordSets', 'ListHostedZones', 'CreateHealthCheck'],
            'ElastiCache': ['CreateCacheCluster', 'ModifyCacheCluster', 'DeleteCacheCluster'],
            'Redshift': ['CreateCluster', 'ModifyCluster', 'DeleteCluster', 'ResizeCluster'],
            'OpenSearch': ['CreateDomain', 'UpdateDomain', 'DeleteDomain', 'UpgradeDomain'],
            'SNS': ['Publish', 'Subscribe', 'Unsubscribe', 'CreateTopic'],
            'SQS': ['SendMessage', 'ReceiveMessage', 'DeleteMessage', 'CreateQueue'],
            'Kinesis': ['PutRecord', 'GetRecords', 'CreateStream', 'UpdateShardCount'],
            'IoT': ['CreateThing', 'UpdateThing', 'DeleteThing', 'Publish'],
            'Connect': ['StartContactRecording', 'StopContactRecording', 'CreateUser', 'UpdateContactFlowContent']
        }
        
        # Credits
        self.credits = [
            'Free Tier', 'AWSPromotionalCredit', 'MarketplacePromotion', 
            'EnterpriseDiscount', 'VolumeDiscount'
        ]

    def generate_cost_and_usage_response(self, start_date, end_date, granularity, filter_key=None, filter_values=None, group_by=None, metrics=None):
        """Generate comprehensive mock Cost Explorer response"""
        if not metrics:
            metrics = ['UnblendedCost']
            
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Determine time periods based on granularity
        time_periods = []
        current_date = start
        
        if granularity == 'DAILY':
            while current_date < end:
                next_date = current_date + timedelta(days=1)
                time_periods.append((current_date, next_date))
                current_date = next_date
        elif granularity == 'MONTHLY':
            while current_date < end:
                # Move to the 1st of next month
                year = current_date.year + (current_date.month == 12)
                month = (current_date.month % 12) + 1
                next_date = datetime(year, month, 1)
                time_periods.append((current_date, next_date))
                current_date = next_date
        elif granularity == 'HOURLY':
            # Only supported for up to 14 days
            days_diff = (end - start).days
            if days_diff > 14:
                # Limit to 14 days
                end = start + timedelta(days=14)
                
            while current_date < end:
                next_date = current_date + timedelta(hours=1)
                time_periods.append((current_date, next_date))
                current_date = next_date
                
        results_by_time = []
        
        # Filter services if needed
        filtered_services = self.all_services
        if filter_key == 'SERVICE' and filter_values:
            filtered_services = [s for s in self.all_services if any(s.startswith(v) for v in filter_values)]
        
        # Generate data for each time period
        for period_start, period_end in time_periods:
            time_period = {
                'Start': period_start.strftime('%Y-%m-%d'),
                'End': period_end.strftime('%Y-%m-%d')
            }
            
            # Create groups based on group_by parameters
            groups = []
            
            if group_by:
                if len(group_by) == 1:
                    key_type = group_by[0]['Type']
                    key_name = group_by[0]['Key']
                    
                    if key_type == 'DIMENSION':
                        if key_name == 'INSTANCE_TYPE':
                            # EC2 instance types
                            for category, instances in self.ec2_instance_types.items():
                                for instance in instances:
                                    # Create more realistic distribution - t2.micro more common than p4d.24xlarge
                                    if 'micro' in instance or 'small' in instance:
                                        scale = random.uniform(0.5, 10.0)
                                    elif 'large' in instance:
                                        scale = random.uniform(10.0, 50.0)
                                    elif 'xlarge' in instance:
                                        scale = random.uniform(20.0, 100.0)
                                    else:
                                        scale = random.uniform(50.0, 200.0)
                                    
                                    # Higher costs for larger instances
                                    cost = round(random.uniform(0.5, scale), 4)
                                    # More usage for smaller instances
                                    usage = round(random.uniform(1, 720 if 'micro' in instance else 200), 2)
                                    
                                    metrics_data = {}
                                    for metric in metrics:
                                        if metric == 'UnblendedCost':
                                            metrics_data[metric] = {'Amount': str(cost), 'Unit': 'USD'}
                                        elif metric == 'UsageQuantity':
                                            metrics_data[metric] = {'Amount': str(usage), 'Unit': 'Hrs'}
                                        elif metric == 'NormalizedUsageAmount':
                                            normalized = usage * (0.5 if 'micro' in instance else 
                                                               1.0 if 'small' in instance else 
                                                               2.0 if 'medium' in instance else
                                                               4.0 if 'large' in instance else
                                                               8.0 if 'xlarge' in instance else 16.0)
                                            metrics_data[metric] = {'Amount': str(round(normalized, 2)), 'Unit': 'Normalized Hours'}
                                            
                                    groups.append({
                                        'Keys': [instance],
                                        'Metrics': metrics_data
                                    })
                        
                        elif key_name == 'SERVICE':
                            # Service breakdown
                            for service in filtered_services:
                                # Determine cost based on service category
                                if any(s in service.lower() for s in ['ec2', 'compute']):
                                    base_cost = random.uniform(100.0, 1000.0)
                                elif any(s in service.lower() for s in ['s3', 'storage']):
                                    base_cost = random.uniform(10.0, 200.0)
                                elif any(s in service.lower() for s in ['rds', 'database']):
                                    base_cost = random.uniform(50.0, 500.0)
                                elif any(s in service.lower() for s in ['lambda']):
                                    base_cost = random.uniform(5.0, 50.0)
                                elif any(s in service.lower() for s in ['bedrock', 'sagemaker']):
                                    base_cost = random.uniform(20.0, 300.0)
                                else:
                                    base_cost = random.uniform(1.0, 100.0)
                                
                                cost = round(base_cost, 4)
                                
                                metrics_data = {}
                                for metric in metrics:
                                    if metric == 'UnblendedCost':
                                        metrics_data[metric] = {'Amount': str(cost), 'Unit': 'USD'}
                                    elif metric == 'UsageQuantity':
                                        metrics_data[metric] = {'Amount': str(round(random.uniform(1, 1000), 2)), 'Unit': 'Count'}
                                
                                groups.append({
                                    'Keys': [service],
                                    'Metrics': metrics_data
                                })
                                
                        elif key_name == 'REGION':
                            # Region breakdown
                            for region_code in self.regions.keys():
                                # Higher costs in popular regions
                                if region_code in ['us-east-1', 'us-west-2', 'eu-west-1']:
                                    cost = round(random.uniform(500.0, 2000.0), 4)
                                else:
                                    cost = round(random.uniform(50.0, 500.0), 4)
                                
                                metrics_data = {'UnblendedCost': {'Amount': str(cost), 'Unit': 'USD'}}
                                groups.append({
                                    'Keys': [region_code],
                                    'Metrics': metrics_data
                                })
                                
                        elif key_name == 'USAGE_TYPE':
                            # Usage type breakdown
                            for service, usage_types in self.usage_types.items():
                                for usage_type in usage_types:
                                    cost = round(random.uniform(1.0, 100.0), 4)
                                    groups.append({
                                        'Keys': [f"{random.choice(list(self.regions.keys()))}:{usage_type}:{service}"],
                                        'Metrics': {'UnblendedCost': {'Amount': str(cost), 'Unit': 'USD'}}
                                    })
                    
                    elif key_type == 'TAG':
                        # Tag-based grouping
                        tag_key = key_name.split('$')[-1]  # Extract the actual tag name from 'TAG$Environment'
                        if tag_key in self.tags:
                            for tag_value in self.tags[tag_key]:
                                cost = round(random.uniform(50.0, 500.0), 4)
                                groups.append({
                                    'Keys': [tag_value],
                                    'Metrics': {'UnblendedCost': {'Amount': str(cost), 'Unit': 'USD'}}
                                })
                
                elif len(group_by) == 2:
                    # Handle two-dimensional grouping
                    key_type1 = group_by[0]['Type']
                    key_name1 = group_by[0]['Key']
                    key_type2 = group_by[1]['Type']
                    key_name2 = group_by[1]['Key']
                    
                    if key_type1 == 'DIMENSION' and key_name1 == 'REGION' and key_type2 == 'DIMENSION' and key_name2 == 'SERVICE':
                        # Region and service breakdown
                        for region_code in self.regions.keys():
                            for service in filtered_services:
                                # Not all services in all regions
                                if random.random() > 0.3:
                                    # Service category affects cost
                                    if any(s in service.lower() for s in ['ec2', 'compute']):
                                        base_cost = random.uniform(50.0, 500.0)
                                    elif any(s in service.lower() for s in ['bedrock', 'sagemaker']):
                                        base_cost = random.uniform(10.0, 200.0)
                                    else:
                                        base_cost = random.uniform(1.0, 100.0)
                                    
                                    # Popular regions have higher usage
                                    if region_code in ['us-east-1', 'us-west-2', 'eu-west-1']:
                                        region_multiplier = random.uniform(1.5, 3.0)
                                    else:
                                        region_multiplier = random.uniform(0.5, 1.5)
                                    
                                    cost = round(base_cost * region_multiplier, 4)
                                    
                                    groups.append({
                                        'Keys': [region_code, service],
                                        'Metrics': {'UnblendedCost': {'Amount': str(cost), 'Unit': 'USD'}}
                                    })
            
            # Calculate total
            total_cost = sum(float(g['Metrics']['UnblendedCost']['Amount']) for g in groups) if groups else 0
            
            # Create time period data
            time_data = {
                'TimePeriod': time_period,
                'Groups': groups,
                'Estimated': period_end.date() >= datetime.now().date(),  # Today and future are estimated
                'Total': {
                    'UnblendedCost': {'Amount': str(total_cost), 'Unit': 'USD'}
                }
            }
            
            results_by_time.append(time_data)
            
        return {
            'GroupDefinitions': group_by if group_by else [],
            'ResultsByTime': results_by_time
        }
    
    def generate_cost_forecast(self, start_date, end_date, granularity='MONTHLY', metric='UNBLENDED_COST'):
        """Generate mock cost forecast"""
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        forecast_results = []
        current_date = start
        
        # Determine increment based on granularity
        if granularity == 'DAILY':
            increment = timedelta(days=1)
        elif granularity == 'MONTHLY':
            # Approximate a month
            increment = timedelta(days=30)
        elif granularity == 'HOURLY':
            increment = timedelta(hours=1)
            
        # Base monthly cost with some randomness
        base_monthly_cost = random.uniform(8000, 12000)
        monthly_growth_rate = random.uniform(0.02, 0.08)  # 2-8% growth per month
        
        # Start with current month's base cost
        current_month_cost = base_monthly_cost
        last_month = start.month
        
        while current_date < end:
            next_date = current_date + increment
            
            # Check if we moved to a new month
            if current_date.month != last_month:
                # Apply growth rate for the new month
                current_month_cost *= (1 + monthly_growth_rate)
                last_month = current_date.month
            
            # Daily/hourly fluctuation
            if granularity == 'DAILY':
                # Weekends cost less
                if current_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
                    daily_factor = random.uniform(0.6, 0.8)
                else:
                    daily_factor = random.uniform(0.9, 1.1)
                
                daily_cost = (current_month_cost / 30.0) * daily_factor
                mean = daily_cost
                
            elif granularity == 'HOURLY':
                # Business hours cost more
                hour = current_date.hour
                if 9 <= hour <= 17:  # 9 AM to 5 PM
                    hourly_factor = random.uniform(1.2, 1.5)
                elif 0 <= hour <= 5:  # Night hours
                    hourly_factor = random.uniform(0.5, 0.7)
                else:
                    hourly_factor = random.uniform(0.8, 1.1)
                
                daily_cost = current_month_cost / 30.0
                mean = (daily_cost / 24.0) * hourly_factor
                
            else:  # MONTHLY
                mean = current_month_cost
            
            # Add some randomness with a normal distribution
            cost = np.random.normal(mean, mean * 0.1)  # 10% standard deviation
            
            # Ensure cost is positive
            cost = max(0.01, cost)
            
            forecast_results.append({
                'TimePeriod': {
                    'Start': current_date.strftime('%Y-%m-%d'),
                    'End': next_date.strftime('%Y-%m-%d')
                },
                'MeanValue': str(round(cost, 2)),
                'PredictionIntervalLowerBound': str(round(cost * 0.8, 2)),  # 20% lower bound
                'PredictionIntervalUpperBound': str(round(cost * 1.2, 2))   # 20% upper bound
            })
            
            current_date = next_date
            
        return {
            'TimePeriod': {
                'Start': start_date,
                'End': end_date
            },
            'Granularity': granularity,
            'Metric': metric,
            'ForecastResultsByTime': forecast_results
        }
    
    def generate_bedrock_logs(self, days=7, region='us-east-1'):
        """Generate detailed mock Bedrock invocation logs"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        logs = []
        current_time = start_time
        
        # Usage patterns by hour of day (24-hour format)
        hourly_patterns = {
            0: 0.2,  # 12 AM - low usage
            1: 0.1,
            2: 0.1,
            3: 0.1,
            4: 0.1,
            5: 0.2,
            6: 0.3,
            7: 0.5,
            8: 0.7,
            9: 0.9,  # 9 AM - high usage during business hours
            10: 1.0,
            11: 1.0,
            12: 0.8,  # Lunch hour
            13: 0.9,
            14: 1.0,
            15: 1.0,
            16: 0.9,
            17: 0.7,  # 5 PM - tapering off
            18: 0.5,
            19: 0.4,
            20: 0.3,
            21: 0.2,
            22: 0.2,
            23: 0.2
        }
        
        # Usage patterns by day of week (0=Monday, 6=Sunday)
        weekday_patterns = {
            0: 1.0,  # Monday
            1: 1.1,  # Tuesday
            2: 1.2,  # Wednesday
            3: 1.1,  # Thursday
            4: 0.9,  # Friday
            5: 0.3,  # Saturday
            6: 0.2   # Sunday
        }
        
        # Generate hourly entries with realistic patterns
        while current_time < end_time:
            hour_factor = hourly_patterns[current_time.hour]
            day_factor = weekday_patterns[current_time.weekday()]
            
            # Combine factors for overall usage level
            usage_factor = hour_factor * day_factor
            
            # Base number of entries per hour with some randomness
            base_entries = 15  # Average entries per hour at peak
            num_entries = int(random.normalvariate(base_entries * usage_factor, base_entries * 0.2))
            num_entries = max(0, num_entries)  # Ensure non-negative
            
            # Model distribution (weighted by popularity/cost)
            model_weights = {
                'anthropic.claude-3-haiku-20240307-v1:0': 0.5,    # Most common
                'anthropic.claude-3-sonnet-20240229-v1:0': 0.25,  # Medium usage
                'anthropic.claude-3-opus-20240229-v1:0': 0.05,    # Rare (expensive)
                'amazon.titan-text-express-v1': 0.1,
                'amazon.titan-text-lite-v1': 0.05,
                'meta.llama3-70b-instruct-v1:0': 0.03,
                'mistral.mistral-7b-instruct-v0:2': 0.02
            }
            
            # User distribution (weighted)
            user_weights = {
                'arn:aws:iam::123456789012:user/developer1': 0.2,
                'arn:aws:iam::123456789012:user/developer2': 0.15,
                'arn:aws:iam::123456789012:user/datascientist1': 0.25,
                'arn:aws:iam::123456789012:user/datascientist2': 0.2,
                'arn:aws:iam::123456789012:user/admin': 0.05,
                'arn:aws:iam::123456789012:role/LambdaExecutionRole': 0.1,
                'arn:aws:iam::123456789012:role/MLModelTrainingRole': 0.05
            }
            
            for _ in range(num_entries):
                # Select model based on weights
                model = random.choices(
                    list(model_weights.keys()), 
                    weights=list(model_weights.values()), 
                    k=1
                )[0]
                
                # Select user based on weights
                user = random.choices(
                    list(user_weights.keys()), 
                    weights=list(user_weights.values()), 
                    k=1
                )[0]
                
                # Token counts depend on model
                if 'haiku' in model:
                    input_tokens = int(random.normalvariate(500, 200))  # Smaller prompt for cheaper model
                elif 'opus' in model:
                    input_tokens = int(random.normalvariate(2000, 800))  # Larger prompt for premium model
                else:
                    input_tokens = int(random.normalvariate(1000, 400))
                
                # Ensure reasonable values
                input_tokens = max(10, min(10000, input_tokens))
                
                # Output tokens are generally proportional to input tokens
                output_ratio = random.uniform(1.5, 3.0)
                output_tokens = int(input_tokens * output_ratio)
                
                # Generate timestamp with microsecond precision
                timestamp = current_time + timedelta(minutes=random.randint(0, 59), seconds=random.randint(0, 59))
                
                # Calculate cost based on token counts and model pricing
                input_cost = input_tokens / 1000 * self.bedrock_models[model]['input']
                output_cost = output_tokens / 1000 * self.bedrock_models[model]['output']
                total_cost = input_cost + output_cost
                
                log_entry = {
                    "timestamp": timestamp.isoformat(),
                    "region": region,
                    "modelId": model,
                    "userId": user,
                    "inputTokens": input_tokens,
                    "completionTokens": output_tokens,
                    "totalTokens": input_tokens + output_tokens,
                    "cost": round(total_cost, 6)
                }
                logs.append(log_entry)
            
            current_time += timedelta(hours=1)
        
        if logs:
            df = pd.DataFrame(logs)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp")
            return df
        else:
            return None


# Create mock boto3 client
class MockBoto3Client:
    def __init__(self, service_name, **kwargs):
        self.service_name = service_name
        self.region_name = kwargs.get('region_name', 'us-east-1')
        self.mock_aws = MockAWS()
        self.exceptions = type('Exceptions', (), {
            'ResourceNotFoundException': type('ResourceNotFoundException', (Exception,), {}),
            'ValidationException': type('ValidationException', (Exception,), {}),
            'InvalidNextTokenException': type('InvalidNextTokenException', (Exception,), {})
        })
    
    def get_cost_and_usage(self, **kwargs):
        return self.mock_aws.generate_cost_and_usage_response(
            kwargs.get('TimePeriod', {}).get('Start'),
            kwargs.get('TimePeriod', {}).get('End'),
            kwargs.get('Granularity'),
            filter_key=kwargs.get('Filter', {}).get('Dimensions', {}).get('Key'),
            filter_values=kwargs.get('Filter', {}).get('Dimensions', {}).get('Values'),
            group_by=kwargs.get('GroupBy'),
            metrics=kwargs.get('Metrics', ['UnblendedCost'])
        )
    
    def get_cost_forecast(self, **kwargs):
        return self.mock_aws.generate_cost_forecast(
            kwargs.get('TimePeriod', {}).get('Start'),
            kwargs.get('TimePeriod', {}).get('End'),
            granularity=kwargs.get('Granularity', 'MONTHLY'),
            metric=kwargs.get('Metric', 'UNBLENDED_COST')
        )
    
    def get_paginator(self, operation_name):
        if operation_name == "filter_log_events":
            return MockPaginator(self.mock_aws, self.region_name)
        return None


class MockPaginator:
    def __init__(self, mock_aws, region_name):
        self.mock_aws = mock_aws
        self.region_name = region_name
    
    def paginate(self, **kwargs):
        # Extract parameters
        log_group_name = kwargs.get("logGroupName")
        start_time_ms = kwargs.get("startTime")
        end_time_ms = kwargs.get("endTime")
        
        # Calculate days from milliseconds
        now_ms = int(datetime.now().timestamp() * 1000)
        days = 7  # Default
        if start_time_ms:
            days = int((now_ms - start_time_ms) / (1000 * 60 * 60 * 24)) + 1
        
        # Generate mock bedrock logs
        df = self.mock_aws.generate_bedrock_logs(days=days, region=self.region_name)
        
        # Convert to events format for CloudWatch Logs
        events = []
        if df is not None:
            for _, row in df.iterrows():
                # Create sample prompt text based on the model
                if 'claude' in row["modelId"].lower():
                    sample_prompts = [
                        "Help me analyze this data from our customers.",
                        "Can you write a function to parse JSON responses?",
                        "Explain the differences between various database technologies.",
                        "Draft an email to our enterprise customers about the new features.",
                        "What's the best way to optimize our AWS costs?"
                    ]
                elif 'titan' in row["modelId"].lower():
                    sample_prompts = [
                        "Generate a product description for our new software.",
                        "Summarize these quarterly results.",
                        "Create a list of potential blog topics for our tech website.",
                        "What are the key features of AWS Lambda?"
                    ]
                else:
                    sample_prompts = [
                        "Translate this text to Spanish.",
                        "Extract the key information from this document.",
                        "Write a short story about cloud computing."
                    ]
                
                # Format the data as a CloudWatch log event with structure matching real logs
                message = {
                    "timestamp": row["timestamp"].isoformat(),
                    "region": row["region"],
                    "modelId": row["modelId"],
                    "requestId": str(uuid.uuid4()),
                    "identity": {"arn": row["userId"]},
                    "input": {
                        "inputTokenCount": row["inputTokens"],
                        "inputBodyJson": {
                            "messages": [
                                {"role": "user", "content": [{"text": random.choice(sample_prompts)}]}
                            ]
                        }
                    },
                    "output": {
                        "outputTokenCount": row["completionTokens"],
                        "outputBodyJson": {
                            "content": [{"text": "This would be the model's response text."}],
                            "role": "assistant"
                        }
                    }
                }
                
                events.append({
                    "message": json.dumps(message),
                    "timestamp": int(row["timestamp"].timestamp() * 1000),
                    "logStreamName": "aws/bedrock/modelinvocations",
                    "eventId": f"{row['timestamp'].timestamp()}-{str(uuid.uuid4())[:8]}"
                })
        
        # Return a single page with all events
        yield {"events": events} 