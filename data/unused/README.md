---
noteId: "f6c2c7d0192511f08dba87bd7218dd44"
tags: []

---

# Data Directory

This directory contains all the CSV files and other data sources used by the AWS Cost Explorer & Carbon Impact Analysis toolkit.

## CSV Files

### AWS Bedrock Carbon Calculator Data

These files are used by the AWS Bedrock Carbon Calculator to estimate carbon footprints:

- **model_energy_consumption.csv**: Energy consumption per token for different AWS Bedrock models
  - Format: `model_id,input_energy_wh,output_energy_wh`
  - Contains the estimated energy consumption per input and output token for each model

- **model_training_footprint.csv**: Amortized training emissions data for models
  - Format: `model_id,total_emissions_gco2e,expected_inferences`
  - Contains the estimated total training emissions and expected lifetime inferences for amortizing training costs

- **region_carbon_intensity.csv**: Carbon intensity data for AWS regions
  - Format: `region,carbon_intensity_gco2e_kwh,category`
  - Contains the carbon intensity (gCO2e/kWh) for each AWS region and its sustainability category

### EC2 Carbon Analysis Data

These files are used for EC2 carbon footprint analysis:

- **sample_ec2_data.csv**: Sample EC2 instance usage data
  - Format: `instance_id,instance_type,region,usage_hours`
  - Contains sample EC2 instance data for testing the carbon analyzer

### General Carbon Intensity Data

These files provide general carbon intensity data for calculations:

- **US_2024_yearly.csv**: US average yearly carbon intensity
  - Contains the yearly average carbon intensity for the US electrical grid
  - Used as a baseline for regions without specific data

- **US_2024_hourly.csv**: US hourly carbon intensity data
  - Contains hourly carbon intensity data for more granular calculations

### AWS Region Data

These files contain AWS region metadata:

- **Cloud_Region_Metadata.csv**: Cloud provider region metadata
  - Contains detailed metadata about cloud regions including carbon intensity
  - Used for cross-cloud provider comparisons

### AI Model Data

- **notable_ai_models (1).csv**: AI model parameters and specifications
  - Contains detailed information about AI models including parameter counts
  - Used by the BedrockModelMapper to map models to their energy profiles

### AWS Sustainability Data

- **AWS_renewable_energy_2023.csv**: AWS renewable energy data from 2023
  - Contains information about AWS's renewable energy projects and commitments

- **Amazon-Carbon-Free-Energy-Projects-2024.csv**: Amazon's carbon-free energy projects
  - Contains data about Amazon's investments in carbon-free energy

## Updating Data

To update the data files with new information:

1. Replace the CSV files with updated versions maintaining the same columns and format
2. The code will automatically use the updated data on next run

## Adding New Data

If adding new models or regions:

1. Add new rows to the appropriate CSV files
2. Ensure the format matches the existing entries
3. The code will automatically incorporate the new data 