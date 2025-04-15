# Installing AWS Cost Explorer

This guide provides simple instructions for installing and running the AWS Cost Explorer package in various environments including Cursor and Claude Desktop.

## Quick Installation

For the easiest installation, run the following command in your terminal:

```bash
python easy_install.py
```

The installation script will:
1. Check prerequisites (Python 3.8+, pip)
2. Install required dependencies
3. Install the package in development mode
4. Help you set up AWS credentials (if needed)
5. Create and run a test script to verify installation

### Command-line Options

The installation script supports several options:
- `--skip-deps`: Skip dependency installation
- `--skip-aws`: Skip AWS credentials setup
- `--skip-test`: Skip installation test

```bash
python easy_install.py --skip-aws --skip-test
```

## Manual Installation

If you prefer manual installation, follow these steps:

### 1. Install Dependencies

```bash
pip install fastmcp>=0.8.0 pandas>=1.3.0 boto3>=1.20.0 plotly>=5.3.0 numpy>=1.20.0 flask>=2.0.0 requests>=2.25.0
```

### 2. Install the Package

```bash
pip install -e .
```

### 3. Set Up AWS Credentials

Create a credentials file at `~/.aws/credentials`:

```ini
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
```

Create a config file at `~/.aws/config`:

```ini
[default]
region = us-east-1
```

## Starting the Servers

The project provides multiple server interfaces that can be started using the unified start script:

```bash
# Start the MCP server with stdio transport (default)
python start.py mcp

# Start the MCP server with SSE transport (requires port)
python start.py mcp --transport sse --port 8000

# Start the HTTP API server
python start.py http

# Start the simple API server
python start.py simple
```

You can customize the port for any server, and the script will automatically find an available port if needed:

```bash
# Start the HTTP API server on port 8081
python start.py http --port 8081
```

### Transport Types

The MCP server supports two transport protocols:

1. **stdio** (default): Uses standard input/output for communication. This is preferred for local usage.
2. **sse**: Server-Sent Events over HTTP. This requires a port parameter and allows remote connections.

## Running Tests

To run the comprehensive test suite:

```bash
python comprehensive_test.py
```

## Data Visualization

The package includes a visualization tool that creates interactive charts of environmental impact data:

```bash
# First start the MCP server
python start.py mcp

# Then run the visualization tool
python visualize_data.py
```

This will create HTML charts in the `visualizations` directory.

## Troubleshooting

### Common Issues

1. **ImportError: No module named 'fastmcp'**
   - Ensure you've installed all dependencies: `pip install fastmcp>=0.8.0`

2. **Port already in use**
   - The script will automatically find an available port
   - Or specify a different port: `python start.py http --port 8081`

3. **Missing data files**
   - Ensure you're running the commands from the project root directory
   - Verify that the `data` directory exists and contains the necessary CSV files

4. **AWS credential errors**
   - Check your AWS credentials are set up correctly in `~/.aws/credentials`
   - Ensure you have the necessary permissions for the AWS services used

### Getting Help

If you encounter any issues not covered here:
1. Check the project documentation
2. Look for error messages in the terminal output
3. Contact the project maintainers

## Using with Cursor

Cursor works best with this package when you:
1. Install the package using the provided `easy_install.py` script
2. Open the project directory in Cursor
3. Use the built-in terminal to run the MCP server or tests

## Using with Claude Desktop

With Claude Desktop:
1. Use the provided `easy_install.py` script for installation
2. Run the server using `python start.py mcp`
3. The server will be available for local use with stdio transport 