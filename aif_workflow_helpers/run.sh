#!/bin/bash

# Azure AI Agents Workflow Helper Runner
# This script sets up the environment and runs the agent management tools

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Azure AI Agents Workflow Helper${NC}"
echo "=================================="

# Check if we're in the right directory
if [ ! -f "requirements.txt" ] || [ ! -d "aif_workflow_helpers" ]; then
    echo -e "${RED}❌ Error: Please run this script from the aif_workflow_helpers directory${NC}"
    echo "   cd /workspaces/AIFoundry_CICD/aif_workflow_helpers"
    exit 1
fi

# Check environment variables
if [ -z "$AZURE_TENANT_ID" ] || [ -z "$AIF_ENDPOINT" ]; then
    echo -e "${RED}❌ Missing required environment variables${NC}"
    echo "Please set:"
    echo "   export AZURE_TENANT_ID='your-tenant-id'"
    echo "   export AIF_ENDPOINT='your-ai-foundry-endpoint'"
    echo ""
    echo "Example:"
    echo "   export AZURE_TENANT_ID='16b3c013-d300-468d-ac64-7eda0820b6d3'"
    echo "   export AIF_ENDPOINT='https://peroden-2927-resource.services.ai.azure.com/api/projects/peroden-2927'"
    exit 1
fi

echo -e "${GREEN}✅ Environment variables configured${NC}"
echo "   Tenant: $AZURE_TENANT_ID"
echo "   Endpoint: $AIF_ENDPOINT"

# Activate virtual environment if available
if [ -f "/workspaces/AIFoundry_CICD/.venv/bin/activate" ]; then
    echo -e "${YELLOW}🔄 Activating virtual environment...${NC}"
    source /workspaces/AIFoundry_CICD/.venv/bin/activate
else
    echo -e "${YELLOW}⚠️  No virtual environment found, using system Python${NC}"
fi

# Set Python path
export PYTHONPATH="/workspaces/AIFoundry_CICD/aif_workflow_helpers"

# Check if packages are installed
echo -e "${YELLOW}🔍 Checking dependencies...${NC}"
python -c "import azure.ai.agents; print('✅ Azure AI Agents package found')" 2>/dev/null || {
    echo -e "${RED}❌ Azure packages not found, installing...${NC}"
    pip install -r requirements.txt
}

# Run the main script
echo -e "${GREEN}🚀 Running Azure AI Agents workflow...${NC}"
echo ""

python -c "from aif_workflow_helpers.upload_download_agents_helpers import main; main()"

echo ""
echo -e "${GREEN}🎉 Workflow completed!${NC}"