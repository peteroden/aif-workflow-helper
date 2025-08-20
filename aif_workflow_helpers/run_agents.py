#!/usr/bin/env python3
"""
CLI script to run Azure AI Agents workflow helpers
"""

import sys
import os

# Add the current directory to the path so we can import our module
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from aif_workflow_helpers.upload_download_agents_helpers import main

if __name__ == "__main__":
    main()