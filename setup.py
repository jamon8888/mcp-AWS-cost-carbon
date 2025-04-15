from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="aws-cost-explorer",
    version="0.1.0",
    author="AWS Cost Explorer Team",
    author_email="example@example.com",
    description="AWS Cost and Environmental Impact Explorer",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/aws-cost-explorer-mcp-server",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "fastmcp>=0.1.0",
        "pandas>=1.3.0",
        "boto3>=1.24.0",
        "plotly>=5.0.0",
        "numpy>=1.20.0",
        "flask>=2.0.0",
        "requests>=2.25.0",
    ],
    entry_points={
        "console_scripts": [
            "aws-cost-explorer=aws_cost_explorer:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["data/*.csv", "data/*.json"],
    },
) 