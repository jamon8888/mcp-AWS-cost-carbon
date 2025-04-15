"""
Visualization utilities for AWS cost and environmental impact data.
"""

import os
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Any, Tuple, Optional

def create_bar_chart(
    data: List[float],
    labels: List[str],
    title: str,
    xlabel: str,
    ylabel: str,
    color: str = "green",
    output_file: Optional[str] = None,
    figsize: Tuple[int, int] = (10, 6),
    rotation: int = 0
) -> plt.Figure:
    """
    Create a bar chart visualization.
    
    Args:
        data: List of data values
        labels: List of labels for the x-axis
        title: Chart title
        xlabel: Label for x-axis
        ylabel: Label for y-axis
        color: Color of the bars
        output_file: Path to save the chart (optional)
        figsize: Figure size as tuple (width, height)
        rotation: Rotation angle for x-axis labels
        
    Returns:
        Matplotlib figure object
    """
    fig = plt.figure(figsize=figsize)
    plt.bar(range(len(data)), data, color=color)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xticks(range(len(labels)), labels, rotation=rotation)
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file)
    
    return fig

def create_line_chart(
    data: List[float],
    labels: List[str],
    title: str,
    xlabel: str,
    ylabel: str,
    color: str = "blue",
    output_file: Optional[str] = None,
    figsize: Tuple[int, int] = (10, 6),
    marker: str = "o"
) -> plt.Figure:
    """
    Create a line chart visualization.
    
    Args:
        data: List of data values
        labels: List of labels for the x-axis
        title: Chart title
        xlabel: Label for x-axis
        ylabel: Label for y-axis
        color: Color of the line
        output_file: Path to save the chart (optional)
        figsize: Figure size as tuple (width, height)
        marker: Marker style for data points
        
    Returns:
        Matplotlib figure object
    """
    fig = plt.figure(figsize=figsize)
    plt.plot(range(len(data)), data, color=color, marker=marker)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xticks(range(len(labels)), labels)
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file)
    
    return fig

def create_multi_bar_chart(
    data_sets: List[List[float]],
    data_labels: List[str],
    x_labels: List[str],
    title: str,
    xlabel: str,
    ylabel: str,
    colors: Optional[List[str]] = None,
    output_file: Optional[str] = None,
    figsize: Tuple[int, int] = (12, 6),
    rotation: int = 0
) -> plt.Figure:
    """
    Create a multi-series bar chart.
    
    Args:
        data_sets: List of data series
        data_labels: Labels for each data series (for legend)
        x_labels: Labels for the x-axis categories
        title: Chart title
        xlabel: Label for x-axis
        ylabel: Label for y-axis
        colors: Colors for each data series
        output_file: Path to save the chart (optional)
        figsize: Figure size as tuple (width, height)
        rotation: Rotation angle for x-axis labels
        
    Returns:
        Matplotlib figure object
    """
    fig = plt.figure(figsize=figsize)
    
    # Set default colors if not provided
    if not colors:
        colors = plt.cm.tab10.colors[:len(data_sets)]
    
    x = np.arange(len(x_labels))
    width = 0.8 / len(data_sets)
    
    for i, data in enumerate(data_sets):
        offset = (i - len(data_sets)/2 + 0.5) * width
        plt.bar(x + offset, data, width, label=data_labels[i], color=colors[i])
    
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xticks(x, x_labels, rotation=rotation)
    plt.legend()
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file)
    
    return fig

def create_comparison_chart(
    data: Dict[str, Dict[str, float]],
    title: str,
    metric: str,
    output_file: Optional[str] = None,
    figsize: Tuple[int, int] = (12, 8)
) -> plt.Figure:
    """
    Create a comparison chart for different categories.
    
    Args:
        data: Nested dictionary with categories and values
        title: Chart title
        metric: The metric being compared (e.g., "Carbon Footprint (gCO2e)")
        output_file: Path to save the chart (optional)
        figsize: Figure size as tuple (width, height)
        
    Returns:
        Matplotlib figure object
    """
    categories = list(data.keys())
    metrics = list(data[categories[0]].keys())
    
    # Convert data to format for multi_bar_chart
    x_labels = categories
    data_labels = metrics
    data_sets = []
    
    for metric_name in metrics:
        data_sets.append([data[cat][metric_name] for cat in categories])
    
    return create_multi_bar_chart(
        data_sets=data_sets,
        data_labels=data_labels,
        x_labels=x_labels,
        title=title,
        xlabel="Categories",
        ylabel=metric,
        output_file=output_file,
        figsize=figsize,
        rotation=45
    ) 