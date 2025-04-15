---
noteId: "409810b0192411f08dba87bd7218dd44"
tags: []

---

# Data Files for AWS Mock Client

This directory contains the necessary CSV data files for the AWS mock client:

## Main Data Files

- `model_energy_consumption.csv`: Energy consumption per token for different AWS Bedrock models
- `model_training_footprint.csv`: Amortized training emissions data for models
- `region_carbon_intensity.csv`: Carbon intensity data for AWS regions
- `region_water_usage.csv`: Water usage effectiveness (WUE) for AWS regions
- `region_pue.csv`: Power usage effectiveness (PUE) for AWS regions
- `region_water_stress.csv`: Water stress level data for AWS regions

## Additional Data Files

- `AWS_renewable_energy_2023.csv`: Renewable energy data for AWS regions
- `Amazon-Carbon-Free-Energy-Projects-2024.csv`: Carbon-free energy projects by Amazon
- `Cloud_Region_Metadata.csv`: Metadata about cloud regions
- `sample_ec2_data.csv`: Sample EC2 instance data
- `US_2024_yearly.csv` and `US_2024_hourly.csv`: US grid carbon intensity data

## Data File Formats

### model_energy_consumption.csv
```
model_id,input_energy_wh_per_token,output_energy_wh_per_token
anthropic.claude-3-opus-20240229-v1:0,0.0003,0.0015
...
```

### model_training_footprint.csv
```
model_id,total_emissions_gco2e,expected_inferences
anthropic.claude-3-opus-20240229-v1:0,1250000000,10000000000
...
```

### region_carbon_intensity.csv
```
region,carbon_intensity_gco2e_kwh,category
us-east-1,379.0,high
...
```

### region_water_usage.csv
```
region,water_usage_liters_per_kwh
us-east-1,1.8
eu-west-1,1.5
...
```

### region_pue.csv
```
region,pue
us-east-1,1.20
eu-north-1,1.07
...
```

### region_water_stress.csv
```
region,water_stress_level
us-east-1,Medium
ap-south-1,Very High
...
``` 