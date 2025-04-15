#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Sample script to demonstrate usage of the AWS Cost Explorer data converter.
This script converts AWS Cost Explorer CSV data to MCP format and adds environmental metrics.
"""

import os
import sys
import argparse
import logging

# Add parent directory to path to import module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.tools.convert_aws_data import process_aws_cost_data


def main():
    """Main function for the AWS cost data converter example."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Convert AWS Cost Explorer CSV data to MCP format'
    )
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Path to AWS Cost Explorer CSV file'
    )
    parser.add_argument(
        '--output', '-o',
        default='mcp_cost_data.json',
        help='Path to save MCP formatted data (default: mcp_cost_data.json)'
    )
    parser.add_argument(
        '--env-metrics', '-e',
        help='Path to environmental metrics JSON file (optional)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Set logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Log the start of processing
        logger.info("Starting AWS cost data conversion")
        logger.info(f"Input file: {args.input}")
        logger.info(f"Output file: {args.output}")
        
        # Process the AWS cost data
        output_file = process_aws_cost_data(
            args.input,
            args.output,
            args.env_metrics
        )
        
        # Log successful completion
        logger.info(f"Successfully converted AWS cost data to MCP format")
        logger.info(f"Output saved to: {output_file}")
        
        # Print example usage instructions
        print("\nExample commands to analyze the converted data:")
        print(f"python -m core.tools.analyze_mcp_data --input {output_file} --chart cost-by-service")
        print(f"python -m core.tools.analyze_mcp_data --input {output_file} --chart cost-by-region")
        
        if args.env_metrics:
            print(f"python -m core.tools.analyze_mcp_data --input {output_file} --chart carbon-intensity-by-region")
        
    except Exception as e:
        logger.error(f"Error converting AWS cost data: {str(e)}", exc_info=True)
        sys.exit(1)
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 