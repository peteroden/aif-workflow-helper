#!/usr/bin/env python3
from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path
from azure.ai.agents import AgentsClient
from azure.identity import DefaultAzureCredential
from logging import getLevelNamesMapping

from aif_workflow_helpers import (
    configure_logging,
    download_agent,
    download_agents,
    create_or_update_agents_from_files,
    create_or_update_agent_from_file
)


def process_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AI Foundry Agent Helper CLI")
    parser.add_argument(
        "--agents-dir",
        default="agents",
        help="Directory to use to upload or download agent definition files (default: agents)",
    )
    parser.add_argument(
        "--download-all-agents",
        action="store_true",
        help="Download existing agents instead of creating/updating from local definitions",
    )
    parser.add_argument(
        "--download-agent",
        default="",
        help="Download existing agents instead of creating/updating from local definitions",
    )
    parser.add_argument(
        "--upload-all-agents",
        action="store_true",
        help="Create/update agents from local definitions",
    )
    parser.add_argument(
        "--upload-agent",
        default="",
        help="Create/update agents from local definitions",
    )
    parser.add_argument(
        "--prefix",
        default="",
        help="Add a prefix to the Agent name when uploading or downloading",
    )
    parser.add_argument(
        "--suffix",
        default="",
        help="Add a suffix to the Agent name when uploading or downloading",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["CRITICAL","ERROR","WARNING","INFO","DEBUG","NOTSET"],
        help="Logging level for helper operations (default: INFO)",
    )

    args = parser.parse_args()
    return args

def setup_logging(log_level_name: str) -> None:
    # Initialize logging once
    try:
        log_levels = getLevelNamesMapping()
        level = log_levels.get(log_level_name.upper())
        configure_logging(level=level, propagate=True)
    except Exception:  # pragma: no cover
        configure_logging()

def get_agent_client() -> AgentsClient:
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
        endpoint=endpoint)
    
    return agent_client

def handle_download_agent_arg(args: argparse.Namespace, agent_client: AgentsClient) -> None:
    if args.download_agent != "":
        agents_dir = Path(args.agents_dir)
        agents_dir.mkdir(parents=True, exist_ok=True)
        try:
            agent_name = args.download_agent
            print("Connecting...")
            agents = list(agent_client.list_agents())
            print(f"Connected. Found {len(agents)} existing agents")

            print(f"Downloading agent {agent_name}...")
            download_agent(agent_name=agent_name, agent_client=agent_client,file_path=agents_dir,prefix=args.prefix,suffix=args.suffix)
        except Exception as e:
            print(f"Unhandled error in downloading agent: {e}")
    else:
        print("Agent name not provided")  

def handle_download_all_agents_arg(args: argparse.Namespace, agent_client: AgentsClient) -> None:
        agents_dir = Path(args.agents_dir)
        agents_dir.mkdir(parents=True, exist_ok=True)
        try:
            print("Connecting...")
            agents = list(agent_client.list_agents())
            print(f"Connected. Found {len(agents)} existing agents")

            print("Downloading agents...")
            download_agents(agent_client, file_path=agents_dir, prefix=args.prefix, suffix=args.suffix)
        except Exception as e:
            print(f"Unhandled error in downloading agents: {e}")

def handle_upload_agent_arg(args: argparse.Namespace, agent_client: AgentsClient) -> None:
    agents_dir = Path(args.agents_dir)
    if not agents_dir.exists() or not agents_dir.is_dir():
        print(f"ERROR: Agents directory not found: {agents_dir}", file=sys.stderr)
        sys.exit(1)

    agent_name = args.upload_agent

    try:
        create_or_update_agent_from_file(agent_name=agent_name, path=agents_dir, agent_client=agent_client, prefix=args.prefix, suffix=args.suffix)
    except Exception as e:
        print(f"Error uploading agent {agent_name}: {e}")

def handle_upload_all_agents_arg(args: argparse.Namespace, agent_client: AgentsClient) -> None:
    agents_dir = Path(args.agents_dir)
    if not agents_dir.exists() or not agents_dir.is_dir():
        print(f"ERROR: Agents directory not found: {agents_dir}", file=sys.stderr)
        sys.exit(1)

    try:
        create_or_update_agents_from_files(path=agents_dir, agent_client=agent_client, prefix=args.prefix, suffix=args.suffix)

    except Exception as e:
        print(f"Error uploading agent files: {e}")

def main():
    args = process_args()

    setup_logging(log_level_name=args.log_level)

    if args.download_all_agents or args.upload_all_agents or args.download_agent or args.upload_agent:
        agent_client = get_agent_client()

    if args.download_agent:
        handle_download_agent_arg(args=args, agent_client=agent_client)

    if args.download_all_agents:
        handle_download_all_agents_arg(args=args, agent_client=agent_client)

    if args.upload_agent:
        handle_upload_agent_arg(args=args, agent_client=agent_client)
    
    if args.upload_all_agents:
        handle_upload_all_agents_arg(args=args, agent_client=agent_client)

if __name__ == "__main__":
    main()
