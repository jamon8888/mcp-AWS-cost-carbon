from datetime import datetime, timedelta
from mock.mock_aws import MockAWS
from core.aws_environmental_calculator import AWSEnvironmentalCalculator
import json
import os

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

def compare_regions_impact(output_file="region_comparison_results.json", metric="both"):
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
              f"{carbon_intensities.get(region, 0):.1f} gCO2e/kWh    "
              f"{pue_values.get(region, 0):.2f}      "
              f"{water_usage_values.get(region, 0):.1f} L/kWh     "
              f"{water_stress_levels.get(region, 'Unknown')}")
    
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
    
    # Find best and worst regions for carbon emissions
    print("\nCarbon Intensity Analysis:")
    print("-" * 40)
    
    if metric in ["carbon", "both"]:
        for service_type, service_results in results.items():
            print(f"\n{service_type} Carbon Emissions by Region:")
            
            # Sort regions by carbon emissions
            sorted_regions = sorted(
                service_results.items(),
                key=lambda x: x[1]['carbon_emissions']
            )
            
            best_region = sorted_regions[0][0]
            worst_region = sorted_regions[-1][0]
            
            for region, data in sorted_regions:
                print(f"  {region_names[region]:<25}: {data['carbon_emissions']:.3f} kg CO2e")
            
            # Calculate potential savings
            potential_savings = service_results[worst_region]['carbon_emissions'] - service_results[best_region]['carbon_emissions']
            savings_percentage = (potential_savings / service_results[worst_region]['carbon_emissions']) * 100
            
            print(f"\n  Potential carbon reduction by moving from {region_names[worst_region]} to {region_names[best_region]}:")
            print(f"  {potential_savings:.3f} kg CO2e ({savings_percentage:.1f}% reduction)")
    
    # Find best and worst regions for water usage
    if metric in ["water", "both"]:
        print("\nWater Usage Analysis:")
        print("-" * 40)
        
        for service_type, service_results in results.items():
            print(f"\n{service_type} Water Usage by Region:")
            
            # Sort regions by water usage
            sorted_regions = sorted(
                service_results.items(),
                key=lambda x: x[1]['water_usage']
            )
            
            best_region = sorted_regions[0][0]
            worst_region = sorted_regions[-1][0]
            
            for region, data in sorted_regions:
                print(f"  {region_names[region]:<25}: {data['water_usage']:.3f} liters")
            
            # Calculate potential savings
            potential_savings = service_results[worst_region]['water_usage'] - service_results[best_region]['water_usage']
            if service_results[worst_region]['water_usage'] > 0:
                savings_percentage = (potential_savings / service_results[worst_region]['water_usage']) * 100
            else:
                savings_percentage = 0
            
            print(f"\n  Potential water reduction by moving from {region_names[worst_region]} to {region_names[best_region]}:")
            print(f"  {potential_savings:.3f} liters ({savings_percentage:.1f}% reduction)")
    
    # Analyze PUE efficiency
    print("\nPUE Efficiency Analysis:")
    print("-" * 40)
    
    # Sort regions by PUE (lower is better)
    sorted_pue_regions = sorted(
        pue_values.items(),
        key=lambda x: x[1]
    )
    
    for region, pue in sorted_pue_regions:
        print(f"  {region_names[region]:<25}: {pue:.2f}")
    
    # Calculate PUE inefficiency impact
    best_pue_region = sorted_pue_regions[0][0]
    worst_pue_region = sorted_pue_regions[-1][0]
    pue_difference = pue_values[worst_pue_region] - pue_values[best_pue_region]
    pue_percentage = (pue_difference / pue_values[worst_pue_region]) * 100
    
    print(f"\n  PUE efficiency gain by moving from {region_names[worst_pue_region]} to {region_names[best_pue_region]}:")
    print(f"  {pue_difference:.2f} ({pue_percentage:.1f}% improvement in energy efficiency)")
    
    # Analyze water stress levels
    print("\nWater Stress Analysis:")
    print("-" * 40)
    
    # Define stress level numeric mapping
    stress_level_map = {
        'Low': 1,
        'Low-Medium': 2,
        'Medium': 3,
        'Medium-High': 4,
        'High': 5,
        'Extremely High': 6,
        'Unknown': 7
    }
    
    # Convert text stress levels to numeric for sorting
    numeric_stress = {region: stress_level_map.get(stress, 7) for region, stress in water_stress_levels.items()}
    
    # Sort regions by water stress (lower is better)
    sorted_stress_regions = sorted(
        numeric_stress.items(),
        key=lambda x: x[1]
    )
    
    for region, _ in sorted_stress_regions:
        print(f"  {region_names[region]:<25}: {water_stress_levels.get(region, 'Unknown')}")
    
    # Save results to file
    output_data = {
        "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "regions_analyzed": [{"region_code": r, "region_name": region_names[r]} for r in regions],
        "region_characteristics": {
            region: {
                "carbon_intensity_gco2e_kwh": carbon_intensities.get(region, 0),
                "pue": pue_values.get(region, 0),
                "water_usage_l_kwh": water_usage_values.get(region, 0),
                "water_stress": water_stress_levels.get(region, "Unknown")
            } for region in regions
        },
        "services_analyzed": [s['service_type'] for s in test_services],
        "results": results
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\nResults saved to {output_file}")
    
    return output_data

if __name__ == "__main__":
    compare_regions_impact() 