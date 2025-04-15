#!/usr/bin/env python3
"""
AWS Cost Explorer - Data Visualization Tool

This script connects to the AWS Cost Explorer MCP server and generates
visualizations of the environmental impact data.
"""

import argparse
import json
import os
import sys
from typing import Dict, List, Any, Optional, Tuple

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd

try:
    from fastmcp.client import FastMCPClient
except ImportError:
    print("Error: fastmcp library not found. Please install it with pip install fastmcp>=0.8.0")
    sys.exit(1)

def connect_to_server(port: int = 8000, transport: str = "sse") -> FastMCPClient:
    """Connect to the MCP server."""
    try:
        client = FastMCPClient(transport=transport, port=port)
        client.connect()
        print(f"Connected to AWS Cost Explorer MCP server on port {port}")
        return client
    except Exception as e:
        print(f"Error connecting to MCP server: {e}")
        sys.exit(1)

def get_region_data(client: FastMCPClient) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Retrieve region emissions and water data."""
    try:
        emissions_data = client.call("get_region_emissions_data")
        # Convert to a list of dictionaries if it's not already
        if isinstance(emissions_data, list) and isinstance(emissions_data[0], dict):
            emissions_dict = {item["region"]: item for item in emissions_data}
        else:
            emissions_dict = emissions_data
            
        # Try to get water data if available
        try:
            water_data = client.call("get_region_water_data")
            if isinstance(water_data, list) and isinstance(water_data[0], dict):
                water_dict = {item["region"]: item for item in water_data}
            else:
                water_dict = water_data
        except Exception:
            # Create empty water dict if not available
            water_dict = {region: {"water_usage_liters_per_kwh": 0, "water_stress_level": "Unknown"} 
                          for region in emissions_dict.keys()}
            
        return emissions_dict, water_dict
    except Exception as e:
        print(f"Error retrieving region data: {e}")
        sys.exit(1)

def create_carbon_intensity_chart(emissions_data: Dict[str, Any]) -> go.Figure:
    """Create a bar chart of carbon intensity by region."""
    # Convert to DataFrame
    df = pd.DataFrame([
        {"region": region, 
         "carbon_intensity": data.get("carbon_intensity_gco2e_per_kwh", 0),
         "region_name": data.get("region_name", region)}
        for region, data in emissions_data.items()
    ])
    
    # Sort by carbon intensity
    df = df.sort_values("carbon_intensity")
    
    # Create the chart
    fig = px.bar(
        df,
        x="region_name",
        y="carbon_intensity",
        title="Carbon Intensity by AWS Region (gCO2e/kWh)",
        labels={"region_name": "AWS Region", "carbon_intensity": "Carbon Intensity (gCO2e/kWh)"},
        color="carbon_intensity",
        color_continuous_scale=px.colors.sequential.Viridis
    )
    
    # Update layout
    fig.update_layout(
        xaxis_tickangle=-45,
        yaxis_title="Carbon Intensity (gCO2e/kWh)",
        coloraxis_showscale=False
    )
    
    return fig

def create_water_usage_chart(water_data: Dict[str, Any], emissions_data: Dict[str, Any]) -> go.Figure:
    """Create a bar chart of water usage by region."""
    # Convert to DataFrame
    df = pd.DataFrame([
        {"region": region, 
         "water_usage": water_data.get(region, {}).get("water_usage_liters_per_kwh", 0),
         "region_name": emissions_data.get(region, {}).get("region_name", region)}
        for region in water_data.keys()
    ])
    
    # Sort by water usage
    df = df.sort_values("water_usage")
    
    # Create the chart
    fig = px.bar(
        df,
        x="region_name",
        y="water_usage",
        title="Water Usage by AWS Region (Liters/kWh)",
        labels={"region_name": "AWS Region", "water_usage": "Water Usage (Liters/kWh)"},
        color="water_usage",
        color_continuous_scale=px.colors.sequential.Blues
    )
    
    # Update layout
    fig.update_layout(
        xaxis_tickangle=-45,
        yaxis_title="Water Usage (Liters/kWh)",
        coloraxis_showscale=False
    )
    
    return fig

def create_regional_comparison_chart(emissions_data: Dict[str, Any], water_data: Dict[str, Any]) -> go.Figure:
    """Create a scatter plot comparing carbon intensity and water usage."""
    # Convert to DataFrame
    df = pd.DataFrame([
        {"region": region, 
         "carbon_intensity": data.get("carbon_intensity_gco2e_per_kwh", 0),
         "water_usage": water_data.get(region, {}).get("water_usage_liters_per_kwh", 0),
         "region_name": data.get("region_name", region)}
        for region, data in emissions_data.items()
    ])
    
    # Create the chart
    fig = px.scatter(
        df,
        x="carbon_intensity",
        y="water_usage",
        title="Carbon Intensity vs Water Usage by AWS Region",
        labels={
            "carbon_intensity": "Carbon Intensity (gCO2e/kWh)", 
            "water_usage": "Water Usage (Liters/kWh)",
            "region_name": "AWS Region"
        },
        size="carbon_intensity",
        color="water_usage",
        hover_name="region_name",
        color_continuous_scale=px.colors.sequential.Viridis
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title="Carbon Intensity (gCO2e/kWh)",
        yaxis_title="Water Usage (Liters/kWh)"
    )
    
    return fig

def create_model_comparison_chart(client: FastMCPClient) -> Optional[go.Figure]:
    """Create a chart comparing AI model energy consumption."""
    try:
        models = client.call("get_supported_models")
        
        if not models:
            return None
        
        # Prepare data for the chart
        df = pd.DataFrame([
            {"model_id": model["model_id"], 
             "energy_per_token": model.get("inference_energy_kwh_per_1k_tokens", 0) * 1000}
            for model in models
        ])
        
        # Sort by energy consumption
        df = df.sort_values("energy_per_token")
        
        # Create the chart
        fig = px.bar(
            df,
            x="model_id",
            y="energy_per_token",
            title="Energy Consumption by AI Model (Wh per token)",
            labels={"model_id": "Model ID", "energy_per_token": "Energy (Wh per token)"},
            color="energy_per_token",
            color_continuous_scale=px.colors.sequential.Plasma
        )
        
        # Update layout
        fig.update_layout(
            xaxis_tickangle=-45,
            yaxis_title="Energy Consumption (Wh per token)",
            coloraxis_showscale=False
        )
        
        return fig
    except Exception as e:
        print(f"Warning: Could not retrieve model comparison data: {e}")
        return None

def generate_visualizations(client: FastMCPClient, output_dir: str) -> None:
    """Generate all visualizations and save to HTML files."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get region data
    emissions_data, water_data = get_region_data(client)
    
    # Create and save visualizations
    carbon_fig = create_carbon_intensity_chart(emissions_data)
    carbon_fig.write_html(os.path.join(output_dir, "carbon_intensity.html"))
    
    water_fig = create_water_usage_chart(water_data, emissions_data)
    water_fig.write_html(os.path.join(output_dir, "water_usage.html"))
    
    comparison_fig = create_regional_comparison_chart(emissions_data, water_data)
    comparison_fig.write_html(os.path.join(output_dir, "region_comparison.html"))
    
    model_fig = create_model_comparison_chart(client)
    if model_fig:
        model_fig.write_html(os.path.join(output_dir, "model_comparison.html"))
    
    # Create an index file
    create_index_file(output_dir)
    
    print(f"Visualizations saved to {output_dir}")
    print(f"Open {os.path.join(output_dir, 'index.html')} in your browser to view them.")

def create_index_file(output_dir: str) -> None:
    """Create an HTML index file to navigate the visualizations."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AWS Cost Explorer Visualizations</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f5f5f5;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                padding: 20px;
                border-radius: 5px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #232f3e;
                border-bottom: 2px solid #ff9900;
                padding-bottom: 10px;
            }
            ul {
                list-style-type: none;
                padding: 0;
            }
            li {
                margin: 10px 0;
            }
            a {
                display: block;
                padding: 10px 15px;
                background: #ff9900;
                color: white;
                text-decoration: none;
                border-radius: 3px;
                transition: background 0.3s;
            }
            a:hover {
                background: #e88a00;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>AWS Cost Explorer Visualizations</h1>
            <p>Click on the links below to view the visualizations:</p>
            <ul>
                <li><a href="carbon_intensity.html">Carbon Intensity by AWS Region</a></li>
                <li><a href="water_usage.html">Water Usage by AWS Region</a></li>
                <li><a href="region_comparison.html">Carbon Intensity vs Water Usage Comparison</a></li>
    """
    
    # Add model comparison link if it exists
    if os.path.exists(os.path.join(output_dir, "model_comparison.html")):
        html_content += '            <li><a href="model_comparison.html">AI Model Energy Consumption Comparison</a></li>\n'
    
    html_content += """
            </ul>
        </div>
    </body>
    </html>
    """
    
    with open(os.path.join(output_dir, "index.html"), "w") as f:
        f.write(html_content)

def main():
    parser = argparse.ArgumentParser(description="AWS Cost Explorer Data Visualization Tool")
    parser.add_argument("--port", type=int, default=8000, help="MCP server port (default: 8000)")
    parser.add_argument("--transport", type=str, default="sse", choices=["sse", "ws", "stdio"], 
                       help="MCP transport protocol (default: sse)")
    parser.add_argument("--output-dir", type=str, default="visualizations", 
                       help="Output directory for visualizations (default: visualizations)")
    
    args = parser.parse_args()
    
    # Connect to the server
    client = connect_to_server(args.port, args.transport)
    
    # Generate visualizations
    generate_visualizations(client, args.output_dir)

if __name__ == "__main__":
    main() 