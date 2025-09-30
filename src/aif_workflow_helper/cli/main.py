#!/usr/bin/env python

import argparse
import os
import sys
from pathlib import Path
from azure.ai.agents import AgentsClient
from azure.identity import DefaultAzureCredential
import logging

# Direct imports from the flat structure modules
from aif_workflow_helper.core.upload import create_or_update_agents_from_files, create_or_update_agent_from_file
from aif_workflow_helper.core.download import download_agent, download_agents, get_agent_by_name
from aif_workflow_helper.core.formats import SUPPORTED_FORMATS
from aif_workflow_helper.utils.logging import configure_logging, logger

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
        "--get-agent-id",
        default="",
        help="Get the agent ID for a given agent name",
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
        "--format",
        default="json",
        choices=SUPPORTED_FORMATS,
        help="File format for agent definitions (default: json)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["CRITICAL","ERROR","WARNING","INFO","DEBUG","NOTSET"],
        help="Logging level for helper operations (default: INFO)",
    )
    parser.add_argument(
        "--azure-tenant-id",
        default="",
        help="Azure tenant ID (overrides AZURE_TENANT_ID environment variable)",
    )
    parser.add_argument(
        "--project-endpoint",
        default="",
        help="AI Foundry project endpoint URL (overrides PROJECT_ENDPOINT environment variable)",
    )

    args = parser.parse_args()
    return args

def setup_logging(log_level_name: str) -> None:
    # Initialize logging once
    try:
        # Python 3.11+ has getLevelNamesMapping(), earlier versions need getLevelName()
        if sys.version_info >= (3, 11):
            from logging import getLevelNamesMapping
            log_levels = getLevelNamesMapping()
            level = log_levels.get(log_level_name.upper())
        else:
            # For Python < 3.11, use getLevelName() which works in reverse
            level = logging.getLevelName(log_level_name.upper())
            # getLevelName returns the string if level is unknown, so check for int
            if not isinstance(level, int):
                level = None
        
        configure_logging(level=level, propagate=True)
    except Exception:  # pragma: no cover
        configure_logging()

def get_agent_client(args: argparse.Namespace) -> AgentsClient:
    # Use CLI parameters if provided, otherwise fall back to environment variables
    tenant_id = args.azure_tenant_id if args.azure_tenant_id else os.getenv("AZURE_TENANT_ID")
    if not tenant_id:
        logger.error("Azure tenant ID is required. Provide it via --azure-tenant-id or AZURE_TENANT_ID environment variable")
        sys.exit(1)

    endpoint = args.project_endpoint if args.project_endpoint else os.getenv("PROJECT_ENDPOINT")
    if not endpoint:
        logger.error("Project endpoint is required. Provide it via --project-endpoint or PROJECT_ENDPOINT environment variable")
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
            logger.info("Connecting...")
            agents = list(agent_client.list_agents())
            logger.info(f"Connected. Found {len(agents)} existing agents")

            logger.info(f"Downloading agent {agent_name}...")
            download_agent(agent_name=agent_name, agent_client=agent_client,file_path=agents_dir,prefix=args.prefix,suffix=args.suffix,format=args.format)
        except Exception as e:
            logger.error(f"Unhandled error in downloading agent: {e}")
    else:
        logger.info("Agent name not provided")

def handle_download_all_agents_arg(args: argparse.Namespace, agent_client: AgentsClient) -> None:
        agents_dir = Path(args.agents_dir)
        agents_dir.mkdir(parents=True, exist_ok=True)
        try:
            logger.info("Connecting...")
            agents = list(agent_client.list_agents())
            logger.info(f"Connected. Found {len(agents)} existing agents")

            logger.info("Downloading agents...")
            download_agents(agent_client, file_path=agents_dir, prefix=args.prefix, suffix=args.suffix, format=args.format)
        except Exception as e:
            logger.error(f"Unhandled error in downloading agents: {e}")

def handle_upload_agent_arg(args: argparse.Namespace, agent_client: AgentsClient) -> None:
    agents_dir = Path(args.agents_dir)
    if not agents_dir.exists() or not agents_dir.is_dir():
        logger.error(f"Agents directory not found: {agents_dir}")
        sys.exit(1)

    agent_name = args.upload_agent

    try:
        create_or_update_agent_from_file(agent_name=agent_name, path=agents_dir, agent_client=agent_client, prefix=args.prefix, suffix=args.suffix, format=args.format)
    except Exception as e:
        logger.error(f"Error uploading agent {agent_name}: {e}")

def handle_upload_all_agents_arg(args: argparse.Namespace, agent_client: AgentsClient) -> None:
    agents_dir = Path(args.agents_dir)
    if not agents_dir.exists() or not agents_dir.is_dir():
        logger.error(f"Agents directory not found: {agents_dir}")
        sys.exit(1)

    try:
        create_or_update_agents_from_files(path=agents_dir, agent_client=agent_client, prefix=args.prefix, suffix=args.suffix, format=args.format)

    except Exception as e:
        logger.error(f"Error uploading agent files: {e}")

def handle_get_agent_id_arg(args: argparse.Namespace, agent_client: AgentsClient) -> None:
    agent_name = args.get_agent_id
    if not agent_name:
        logger.error("Agent name is required for --get-agent-id")
        sys.exit(1)

    try:
        logger.info(f"Looking up agent: {agent_name}")
        agent = get_agent_by_name(agent_name=agent_name, agent_client=agent_client)
        
        if agent:
            print(agent.id)
            logger.info(f"Agent '{agent_name}' has ID: {agent.id}")
        else:
            logger.error(f"Agent '{agent_name}' not found")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error getting agent ID for '{agent_name}': {e}")
        sys.exit(1)

def main():
    args = process_args()

    setup_logging(log_level_name=args.log_level)

    if args.download_all_agents or args.upload_all_agents or args.download_agent or args.upload_agent or args.get_agent_id:
        agent_client = get_agent_client(args)

    if args.download_agent:
        handle_download_agent_arg(args=args, agent_client=agent_client)

    if args.download_all_agents:
        handle_download_all_agents_arg(args=args, agent_client=agent_client)

    if args.upload_agent:
        handle_upload_agent_arg(args=args, agent_client=agent_client)
    
    if args.upload_all_agents:
        handle_upload_all_agents_arg(args=args, agent_client=agent_client)

    if args.get_agent_id:
        handle_get_agent_id_arg(args=args, agent_client=agent_client)

if __name__ == "__main__":
    main()
