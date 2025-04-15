# AWS Cost and Environmental Impact Explorer

A comprehensive tool for analyzing AWS costs and environmental impact (carbon emissions and water usage) of cloud services.

## Features

- **Cost Analysis**: Track and analyze AWS cloud spending by service, region, and time
- **Carbon Footprint**: Calculate carbon emissions from AWS services
- **Water Usage**: Estimate water consumption of cloud resources
- **Region Comparison**: Compare environmental impacts across AWS regions
- **AI Model Analysis**: Assess environmental footprint of AI model usage
- **S3 Storage Analysis**: Analyze environmental impact of S3 storage classes across regions

## Quick Start

### Windows Installation

```bash
# Double-click install.bat
# Or run in command prompt:
install.bat
```

### Linux/macOS Installation

```bash
# Make the script executable (if needed)
chmod +x install.sh

# Run the script
./install.sh
```

### Manual Installation

For detailed installation instructions, see [INSTALL.md](INSTALL.md).

## Starting the MCP Server

### Quick Start Scripts

We've added simple scripts to start the MCP server:

**Windows:**
```bash
# Double-click start_mcp_server.bat
# Or run in command prompt:
start_mcp_server.bat
```

**Linux/macOS:**
```bash
# Make the script executable (if needed)
chmod +x start_mcp_server.sh

# Run the script
./start_mcp_server.sh
```

### Manual Start Options

Use the unified start script to launch any of the available servers:

```bash
# Start the MCP server (default - stdio transport)
python start.py mcp

# Start the HTTP API server (default port 8080)
python start.py http --port 8080

# Start the simple API server (default port 8090)
python start.py simple

# Use SSE transport (requires port parameter)
python start.py mcp --transport sse --port 8001
```

The servers will be available at their respective ports:
- MCP Server with stdio: Uses standard input/output (no port needed)
- MCP Server with SSE: http://localhost:8000 (or custom port)
- HTTP API: http://localhost:8080 (or custom port)
- Simple API: http://localhost:8090 (or custom port)

Note: The start script will automatically find an available port if the default is already in use.

## Example Usage

### S3 Environmental Impact Analysis

Analyze the environmental impact of S3 storage across regions and storage classes:

```bash
# Basic usage
python examples/s3_environmental_impact.py

# Compare storage impact across regions
python examples/s3_environmental_impact.py --compare-regions

# Compare different storage classes
python examples/s3_environmental_impact.py --compare-classes

# Specify specific regions to analyze
python examples/s3_environmental_impact.py --regions us-east-1,eu-west-1,ap-northeast-1

# Analyze different storage sizes
python examples/s3_environmental_impact.py --storage-sizes 100,1000,10000,100000
```

### Using the Python Client

```python
from fastmcp.client import FastMCPClient

# Connect to the server (if using SSE transport)
client = FastMCPClient(transport="sse", port=8000)
client.connect()

# Or for stdio transport (recommended for local usage)
# client = FastMCPClient(transport="stdio")
# client.connect()

# Get supported AI models
models = client.call("get_supported_models")
print(f"Supported models: {models}")

# Get region emissions data
regions = client.call("get_region_emissions_data")
print(f"Lowest carbon regions: {regions[:5]}")

# Calculate S3 storage environmental impact
s3_impact = client.call("calculate_environmental_impact", {
    "service_type": "s3:Standard", 
    "resource_id": "Standard",
    "region": "us-east-1",
    "usage_data": {"storage_gb": 1000, "get_requests": 10000, "put_requests": 1000}
})
print(f"S3 Storage Impact: {s3_impact}")
```

### Running the Comprehensive Test

```bash
python comprehensive_test.py
```

### Visualizing Data

The repository includes a visualization tool to create interactive charts:

```bash
# First start the MCP server
python start.py mcp

# Then in a separate terminal, run the visualization tool
python visualize_data.py

# Open the visualizations in a web browser
# Check the output directory (default: visualizations/)
```

## Repository Maintenance

### Cleaning Up

To clean the repository of unnecessary files:

```bash
python cleanup_repo.py
```

## Documentation

For detailed documentation on available methods and parameters, see the source code documentation or run:

```bash
python mcp_server.py --help
```




## Data Sources

- AWS pricing data (via AWS Price List API)
- Carbon intensity data for AWS regions
- Water usage and stress levels by region
- AI model energy consumption data

## License

MIT

## Contributors

- AWS Cost Explorer Team