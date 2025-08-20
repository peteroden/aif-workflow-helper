from setuptools import setup, find_packages

setup(
    name="aif_workflow_helpers",
    version="0.1.0",
    description="Azure AI Foundry workflow helpers for agent management",
    packages=find_packages(),
    install_requires=[
        "azure-ai-projects",
        "azure-ai-agents", 
        "azure-identity",
        "pyyaml",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
        ],
    },
    python_requires=">=3.8",
)