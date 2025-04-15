---
noteId: "e924fe50194c11f089d649f56517318d"
tags: []

---

# AWS Cost Explorer MCP Server Example Scripts

This directory contains example scripts that demonstrate how to use the AWS Cost Explorer MCP Server to analyze environmental impacts of your AWS services.

## Available Examples

### 1. Model Inference Impact Analysis
The `model_inference_impact.py` script analyzes the environmental impact of AI model inferences, helping you understand the carbon footprint and water usage of your AI workloads.

```bash
# Analyze impact of specific AI models
python model_inference_impact.py --models gpt-4,claude-3-opus,llama-3 --regions us-east-1,eu-west-1

# Specify custom inference count
python model_inference_impact.py --inference-count 1000000 --output-dir results/model_impact
```

### 2. EC2 Environmental Impact Analysis
The `ec2_environmental_impact.py` script compares the environmental impacts of different EC2 instance types, helping you select the most sustainable options for your workloads.

```bash
# Compare different EC2 instance types in a specific region
python ec2_environmental_impact.py --instance-types t3.micro,t3.small,t3.medium --region us-east-1

# Compare the same instance type across different regions
python ec2_environmental_impact.py --instance-type t3.xlarge --compare-regions
```

### 3. S3 Environmental Impact Analysis
The `s3_environmental_impact.py` script analyzes the environmental impact of S3 storage across different regions and storage classes, helping you make more sustainable storage choices.

```bash
# Compare S3 storage impact across different regions
python s3_environmental_impact.py --compare-regions --storage-sizes 100,1000,10000

# Compare impact of different storage classes
python s3_environmental_impact.py --compare-classes --storage-classes Standard,Standard-IA,Glacier,Glacier-Deep-Archive

# Analyze with different access patterns
python s3_environmental_impact.py --access-pattern heavy --regions us-east-1,eu-west-1
```

Key features:
- Calculates carbon footprint and water usage for S3 storage
- Compares environmental metrics across different AWS regions
- Analyzes impact of different storage classes (Standard, IA, Glacier, etc.)
- Considers various storage sizes and access patterns
- Generates detailed HTML reports with visualizations

### 4. Region Impact Comparison
The `region_comparison.py` script analyzes environmental metrics across different AWS regions to help you make more sustainable choices for your deployments.

```bash
# Compare carbon intensity across regions
python region_comparison.py --metric carbon_intensity

# Generate full comparison report
python region_comparison.py --output-dir region_reports --generate-report
```

### 5. AWS Cost Data Converter
The `aws_cost_converter.py` script converts AWS Cost and Usage Reports into a format suitable for environmental impact analysis.

```bash
# Convert Cost and Usage Report to MCP format
python aws_cost_converter.py --input cost_report.csv --output mcp_data.json

# Convert and analyze in one step
python aws_cost_converter.py --input cost_report.csv | python region_comparison.py
```

## Getting Started
Each script includes detailed help and command-line options. Run any script with the `--help` flag to see all available options.

```bash
python s3_environmental_impact.py --help
```

## Additional Resources

- Check the project documentation for more details on available tools and features
- See the `tests` directory for examples of unit tests that can also serve as usage examples 