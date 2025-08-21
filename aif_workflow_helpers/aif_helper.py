#!/usr/bin/env python3
from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path

from aif_workflow_helpers.upload_download_agents_helpers import (
    configure_logging,
    download_agents,
    read_agent_files,
    create_or_update_agents,
)
from azure.ai.agents import AgentsClient
from azure.identity import DefaultAzureCredential

def main():
    parser = argparse.ArgumentParser(description="AI Foundry Agent Helper CLI")
    parser.add_argument(
        "--agents-dir",
        default="agents",
        help="Directory to use to upload or download agent definition files (default: agents)",
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download existing agents instead of creating/updating from local definitions",
    )
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Create/update agents from local definitions",
    )

    args = parser.parse_args()

    if args.download or args.upload:
        # Basic environment validation
        tenant_id = os.getenv("AZURE_TENANT_ID")
        if not tenant_id:
            print("ERROR: AZURE_TENANT_ID environment variable is required", file=sys.stderr)
            sys.exit(1)

        endpoint = os.getenv("AIF_ENDPOINT")
        if not endpoint:
            print("ERROR: AIF_ENDPOINT environment variable is required", file=sys.stderr)
            sys.exit(1)

        agent_client = AgentsClient(
            credential=DefaultAzureCredential(
                exclude_interactive_browser_credential=False,
                interactive_tenant_id=tenant_id
            ),
            endpoint=endpoint
    )

    if args.download:
        agents_dir = Path(args.agents_dir)
        agents_dir.mkdir(parents=True, exist_ok=True)

        try:
            configure_logging()
            print("Testing connection...")
            agents = list(agent_client.list_agents())
            print(f"Connected. Found {len(agents)} existing agents")

            print("Downloading agents...")
            download_agents(agent_client,file_path=agents_dir)
        except Exception as e:
            print(f"Unhandled error in downloading agents: {e}")
    
    if args.upload:
        # Collect agent definition files
        agents_dir = Path(args.agents_dir)
        if not agents_dir.exists() or not agents_dir.is_dir():
            print(f"ERROR: Agents directory not found: {agents_dir}", file=sys.stderr)
            sys.exit(1)

        try:
            print("Reading agent files...")
            agents_data = read_agent_files(agents_dir)
            print(f"Found {len(agents_data)} agents")
            
            if agents_data:
                print("Creating/updating agents...")
                create_or_update_agents(agents_data, agent_client)
            else:
                print("No agent files found to process")

        except Exception as e:
            print(f"Error uploading agent files: {e}")

if __name__ == "__main__":
    main()
