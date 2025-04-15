from datetime import datetime, timedelta
from mock_aws import MockAWS
from aws_environmental_calculator import AWSEnvironmentalCalculator

def estimate_cost(service_type, usage_data):
    """Estimate cost for a service based on its usage data."""
    service_type_lower = service_type.lower()
    
    if 'ec2' in service_type_lower or 'compute' in service_type_lower:
        # EC2 cost calculation
        instance_type = usage_data.get('instance_type', 't3.micro')
        hours = usage_data.get('hours', 0)
        
        # EC2 pricing (simplified)
        ec2_prices = {
            't3.micro': 0.0104,  # per hour
            't3.small': 0.0208,  # per hour
            't3.medium': 0.0416,  # per hour
            'm5.large': 0.096,   # per hour
            'default': 0.05      # default price
        }
        
        hourly_rate = ec2_prices.get(instance_type, ec2_prices['default'])
        return hourly_rate * hours
        
    elif 'lambda' in service_type_lower:
        # Lambda cost calculation
        memory_gb = usage_data.get('memory_gb', 0.128)
        duration_seconds = usage_data.get('duration_seconds', 0)
        invocations = usage_data.get('invocations', 0)
        
        # Lambda pricing: $0.0000166667 per GB-second + $0.20 per million requests
        gb_seconds = memory_gb * duration_seconds * invocations
        compute_cost = gb_seconds * 0.0000166667
        request_cost = (invocations / 1000000) * 0.20
        
        return compute_cost + request_cost
        
    elif 'dynamodb' in service_type_lower:
        # DynamoDB cost calculation
        read_requests = usage_data.get('read_requests', 0)
        write_requests = usage_data.get('write_requests', 0)
        storage_gb = usage_data.get('storage_gb', 0)
        
        # DynamoDB pricing: $1.25 per million write requests, $0.25 per million read requests, $0.25 per GB-month
        write_cost = (write_requests / 1000000) * 1.25
        read_cost = (read_requests / 1000000) * 0.25
        storage_cost = storage_gb * 0.25
        
        return write_cost + read_cost + storage_cost
        
    elif 'bedrock' in service_type_lower:
        # Bedrock cost calculation
        model_id = usage_data.get('model_id', '')
        input_tokens = usage_data.get('input_tokens', 0)
        output_tokens = usage_data.get('output_tokens', 0)
        
        # Bedrock pricing (simplified)
        bedrock_prices = {
            'anthropic.claude-3-haiku-20240307-v1:0': {'input': 0.00025, 'output': 0.00125},
            'anthropic.claude-3-sonnet-20240229-v1:0': {'input': 0.00080, 'output': 0.00240},
            'anthropic.claude-3-opus-20240229-v1:0': {'input': 0.00150, 'output': 0.00750},
            'amazon.titan-text-express-v1:0': {'input': 0.00020, 'output': 0.00060},
            'default': {'input': 0.0005, 'output': 0.0015}
        }
        
        price_info = bedrock_prices.get(model_id, bedrock_prices['default'])
        input_cost = (input_tokens / 1000) * price_info['input']
        output_cost = (output_tokens / 1000) * price_info['output']
        
        return input_cost + output_cost
        
    elif 's3' in service_type_lower or 'storage' in service_type_lower:
        # S3 cost calculation
        storage_gb = usage_data.get('storage_gb', 0)
        
        # S3 pricing: $0.023 per GB-month for standard storage
        return storage_gb * 0.023
        
    elif 'rds' in service_type_lower or 'database' in service_type_lower:
        # RDS cost calculation
        db_instance_type = usage_data.get('db_instance_type', 'db.t3.micro')
        hours = usage_data.get('hours', 0)
        storage_gb = usage_data.get('storage_gb', 0)
        
        # RDS pricing (simplified)
        rds_prices = {
            'db.t3.micro': 0.017,  # per hour
            'db.t3.small': 0.034,  # per hour
            'db.t3.medium': 0.068,  # per hour
            'default': 0.05        # default price
        }
        
        hourly_rate = rds_prices.get(db_instance_type, rds_prices['default'])
        instance_cost = hourly_rate * hours
        storage_cost = storage_gb * 0.115  # $0.115 per GB-month for gp2 storage
        
        return instance_cost + storage_cost
    
    # Default cost estimate
    # Based on a generic hourly rate of $0.05 per hour for 720 hours (30 days)
    return 0.05 * 720  # $36 per month

def compare_regions_impact():
    print("\n=== Regional Impact Comparison ===")
    print("Analyzing same workload across different AWS regions to identify environmental and cost impact\n")
    
    # Initialize the calculator
    calculator = AWSEnvironmentalCalculator()
    
    # Target services for comparison
    test_services = [
        {
            'service_type': 'EC2',
            'resource_id': 't3.micro',
            'usage_data': {'hours': 720}
        },
        {
            'service_type': 'Bedrock',
            'resource_id': 'anthropic.claude-3-haiku-20240307-v1:0',
            'usage_data': {
                'input_tokens': 1000000,
                'output_tokens': 500000
            }
        }
    ]
    
    # Regions to compare (mix of high and low carbon intensity)
    regions = [
        'us-east-1',      # Higher carbon intensity (379.1 gCO2e/kWh)
        'us-west-2',      # Lower carbon intensity (136.5 gCO2e/kWh)
        'eu-west-1',      # Medium carbon intensity (316.0 gCO2e/kWh)
        'eu-north-1',     # Very low carbon intensity (8.0 gCO2e/kWh)
        'ap-southeast-2'  # High carbon intensity (660.0 gCO2e/kWh)
    ]
    
    # Map regions to friendly names
    region_names = {
        'us-east-1': 'US East (N. Virginia)',
        'us-west-2': 'US West (Oregon)',
        'eu-west-1': 'EU West (Ireland)',
        'eu-north-1': 'EU North (Stockholm)',
        'ap-southeast-2': 'Asia Pacific (Sydney)'
    }
    
    # Get carbon intensities for reference
    carbon_intensities = {}
    pue_values = {}
    water_usage_values = {}
    water_stress_levels = {}
    
    for region in regions:
        try:
            carbon_intensities[region] = calculator.bedrock_calculator.get_carbon_intensity(region)
            pue_values[region] = calculator.bedrock_calculator.get_pue(region)
            water_usage_values[region] = calculator.bedrock_calculator.get_water_usage(region)
            water_stress_levels[region] = calculator.bedrock_calculator.get_water_stress(region)
        except Exception as e:
            print(f"Error getting region data for {region}: {str(e)}")
    
    # Print region characteristics
    print("Region Characteristics:")
    print(f"{'Region':<25} {'Carbon Intensity':<20} {'PUE':<10} {'Water Usage':<15} {'Water Stress':<15}")
    print("-" * 85)
    
    for region in regions:
        print(f"{region_names[region]:<25} "
              f"{carbon_intensities[region]:.1f} gCO2e/kWh    "
              f"{pue_values[region]:.2f}      "
              f"{water_usage_values[region]:.1f} L/kWh     "
              f"{water_stress_levels[region]}")
    
    # Calculate impact for each service in each region
    results = {}
    
    for service in test_services:
        service_type = service['service_type']
        if service_type not in results:
            results[service_type] = {}
        
        for region in regions:
            try:
                metrics = calculator.calculate_total_footprint(
                    service_type,
                    service['resource_id'],
                    region,
                    service['usage_data']
                )
                
                cost = estimate_cost(service_type, service['usage_data'])
                
                results[service_type][region] = {
                    'carbon_emissions': metrics.carbon_footprint,
                    'water_usage': metrics.water_usage,
                    'energy_consumption': metrics.energy_kwh,
                    'cost': cost
                }
            except Exception as e:
                print(f"Error calculating metrics for {service_type} in {region}: {str(e)}")
    
    # Print results by service type
    for service_type, region_data in results.items():
        print(f"\n{service_type} Service Comparison:")
        print(f"{'Region':<25} {'Carbon (kg CO2e)':<20} {'Water (L)':<15} {'Energy (kWh)':<15} {'Cost ($)':<10}")
        print("-" * 85)
        
        # Find region with highest emissions as baseline
        baseline_region = max(region_data.items(), key=lambda x: x[1]['carbon_emissions'])[0]
        baseline_emissions = region_data[baseline_region]['carbon_emissions']
        baseline_water = region_data[baseline_region]['water_usage']
        
        for region in regions:
            if region in region_data:
                data = region_data[region]
                
                # Calculate savings percentage compared to baseline
                emissions_savings = 100 * (1 - (data['carbon_emissions'] / baseline_emissions))
                water_savings = 100 * (1 - (data['water_usage'] / baseline_water))
                
                # Print with savings percentage
                print(f"{region_names[region]:<25} "
                      f"{data['carbon_emissions']:.2f} "
                      f"({'Same' if region == baseline_region else f'-{emissions_savings:.1f}%':<8}) "
                      f"{data['water_usage']:.2f} "
                      f"({'Same' if region == baseline_region else f'-{water_savings:.1f}%':<8}) "
                      f"{data['energy_consumption']:.2f}        "
                      f"${data['cost']:.2f}")
    
    # Calculate overall potential savings
    print("\nPotential Environmental Impact Reduction:")
    print("-" * 85)
    
    # Find lowest carbon region
    lowest_carbon_region = min(regions, key=lambda r: carbon_intensities[r])
    highest_carbon_region = max(regions, key=lambda r: carbon_intensities[r])
    
    # Calculate total emissions for each region across all services
    region_totals = {region: 0 for region in regions}
    region_water_totals = {region: 0 for region in regions}
    
    for service_type, region_data in results.items():
        for region, data in region_data.items():
            region_totals[region] += data['carbon_emissions']
            region_water_totals[region] += data['water_usage']
    
    # Print potential savings moving from highest to lowest carbon region
    high_to_low_emissions_savings = (
        (region_totals[highest_carbon_region] - region_totals[lowest_carbon_region]) / 
        region_totals[highest_carbon_region] * 100
    )
    
    high_to_low_water_savings = (
        (region_water_totals[highest_carbon_region] - region_water_totals[lowest_carbon_region]) / 
        region_water_totals[highest_carbon_region] * 100
    )
    
    print(f"Moving workloads from {region_names[highest_carbon_region]} to {region_names[lowest_carbon_region]}:")
    print(f"  - Carbon emissions reduction: {high_to_low_emissions_savings:.1f}%")
    print(f"  - Water usage reduction: {high_to_low_water_savings:.1f}%")
    print(f"  - Absolute carbon savings: {region_totals[highest_carbon_region] - region_totals[lowest_carbon_region]:.2f} kg CO2e per month")
    
    # Calculate environmental equivalents of the savings
    carbon_saved = region_totals[highest_carbon_region] - region_totals[lowest_carbon_region]
    trees_equivalent = carbon_saved * 0.039  # Trees needed for offset
    car_miles_equivalent = carbon_saved * 2.481  # Car miles driven
    
    print(f"\nMonthly environmental impact savings equivalent to:")
    print(f"  - {trees_equivalent:.1f} trees planted")
    print(f"  - {car_miles_equivalent:.1f} car miles not driven")
    
    # Compare cost differences
    print("\nCost Comparison:")
    for service_type, region_data in results.items():
        print(f"\n{service_type} Service:")
        base_cost = region_data['us-east-1']['cost']  # Using US East 1 as price reference
        
        for region in regions:
            if region in region_data:
                cost_diff_pct = ((region_data[region]['cost'] / base_cost) - 1) * 100
                print(f"  {region_names[region]}: ${region_data[region]['cost']:.2f} "
                      f"({'Same' if region == 'us-east-1' else f'{cost_diff_pct:+.1f}%'})")

if __name__ == "__main__":
    compare_regions_impact() 