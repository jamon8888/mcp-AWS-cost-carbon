#!/usr/bin/env python3
"""
AWS Cost Explorer MCP Server - Unified Start Script
This script provides a unified interface to start different server types.
"""

import argparse
import os
import sys
import socket
import subprocess
import time

def find_available_port(start_port, max_attempts=10):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
    return start_port  # Return the start port if no available port found

def start_mcp_server(args):
    """Start the MCP server"""
    cmd = ["python", "mcp_server.py"]
    
    if args.transport == "sse":
        port = args.port if args.port else 8000
        available_port = find_available_port(port)
        if available_port != port:
            print(f"Port {port} is in use. Using port {available_port} instead.")
            port = available_port
        
        cmd.extend(["--transport", "sse", "--port", str(port)])
    else:
        cmd.extend(["--transport", "stdio"])
    
    if args.mock:
        cmd.append("--mock")
    
    if args.data_dir:
        cmd.extend(["--data-dir", args.data_dir])
    
    print(f"Starting MCP server with command: {' '.join(cmd)}")
    subprocess.run(cmd)

def start_http_server(args):
    """Start the HTTP API server"""
    port = args.port if args.port else 8080
    available_port = find_available_port(port)
    if available_port != port:
        print(f"Port {port} is in use. Using port {available_port} instead.")
        port = available_port
    
    cmd = ["python", "api/http_api_wrapper.py", "--port", str(port)]
    
    if args.mock:
        cmd.append("--mock")
    
    if args.data_dir:
        cmd.extend(["--data-dir", args.data_dir])
    
    print(f"Starting HTTP API server with command: {' '.join(cmd)}")
    subprocess.run(cmd)

def start_simple_server(args):
    """Start the simple API server"""
    port = args.port if args.port else 8090
    available_port = find_available_port(port)
    if available_port != port:
        print(f"Port {port} is in use. Using port {available_port} instead.")
        port = available_port
    
    cmd = ["python", "api/simple_api.py", "--port", str(port)]
    
    if args.mock:
        cmd.append("--mock")
    
    if args.data_dir:
        cmd.extend(["--data-dir", args.data_dir])
    
    print(f"Starting simple API server with command: {' '.join(cmd)}")
    subprocess.run(cmd)

def main():
    """Main function to parse arguments and start the appropriate server"""
    parser = argparse.ArgumentParser(description="AWS Cost Explorer Server Launcher")
    subparsers = parser.add_subparsers(dest="server_type", help="Server type to start")
    
    # MCP server parser
    mcp_parser = subparsers.add_parser("mcp", help="Start the MCP server")
    mcp_parser.add_argument("--transport", type=str, default="stdio", 
                           choices=["stdio", "sse"], 
                           help="Transport type (stdio, sse)")
    mcp_parser.add_argument("--port", type=int, help="Port to run the server on (required for sse transport)")
    mcp_parser.add_argument("--mock", action="store_true", help="Use mock data")
    mcp_parser.add_argument("--data-dir", type=str, help="Directory containing data files")
    
    # HTTP API server parser
    http_parser = subparsers.add_parser("http", help="Start the HTTP API server")
    http_parser.add_argument("--port", type=int, help="Port to run the server on")
    http_parser.add_argument("--mock", action="store_true", help="Use mock data")
    http_parser.add_argument("--data-dir", type=str, help="Directory containing data files")
    
    # Simple API server parser
    simple_parser = subparsers.add_parser("simple", help="Start the simple API server")
    simple_parser.add_argument("--port", type=int, help="Port to run the server on")
    simple_parser.add_argument("--mock", action="store_true", help="Use mock data")
    simple_parser.add_argument("--data-dir", type=str, help="Directory containing data files")
    
    args = parser.parse_args()
    
    if args.server_type == "mcp":
        if args.transport == "sse" and not args.port:
            print("Error: Port is required for sse transport")
            mcp_parser.print_help()
            return 1
        start_mcp_server(args)
    elif args.server_type == "http":
        start_http_server(args)
    elif args.server_type == "simple":
        start_simple_server(args)
    else:
        parser.print_help()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
