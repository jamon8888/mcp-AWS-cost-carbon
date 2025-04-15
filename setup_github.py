#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from setuptools import setup, find_packages

# Get the long description from the README file
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="aws-cost-explorer-mcp",
    version="0.1.0",
    author="Jamin",
    author_email="rubio.jamin@gmail.com",
    description="AWS Cost and Environmental Impact Explorer MCP Server",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jamon8888/aws-cost-explorer-mcp",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "fastmcp>=0.8.0",
        "pandas>=1.3.0",
        "boto3>=1.26.0",
        "plotly>=5.3.0",
        "numpy>=1.20.0",
        "flask>=2.0.0",
        "requests>=2.25.0",
    ],
    entry_points={
        "console_scripts": [
            "aws-cost-explorer-mcp=mcp_server:main",
        ],
    },
)
