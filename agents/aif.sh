#!/bin/bash
# filepath: /workspaces/AIFoundry_CICD/agents/aif.sh

set -euo pipefail

readonly SCRIPT_NAME="$(basename "$0")"
readonly DEFAULT_API_VERSION="v1"
readonly AZURE_RESOURCE="https://ai.azure.com"

RESOURCE_URL="${AIF_RESOURCE_URL:-}"
API_VERSION="${AIF_API_VERSION:-$DEFAULT_API_VERSION}"
BRANCH_NAME=""
PROJECT_ID=""
VERBOSE=false

log() {
    echo "[$SCRIPT_NAME] $*" >&2
}

error() {
    echo "[$SCRIPT_NAME] ERROR: $*" >&2
    exit 1
}

debug() {
    if [[ "$VERBOSE" == true ]]; then
        echo "[$SCRIPT_NAME] DEBUG: $*" >&2
    fi
}

usage() {
    cat << EOF
Usage: $SCRIPT_NAME [OPTIONS]

OPTIONS:
    -g              Get/serialize agents from remote project
    -p              Create/update agents in remote project
    -r URL          Specify resource URL
    -v              Enable verbose output
    -h              Show this help message

ENVIRONMENT VARIABLES:
    AIF_RESOURCE_URL    Override default resource URL
    AIF_API_VERSION     Override default API version (default: v1)

EXAMPLES:
    $SCRIPT_NAME -g -r "https://my-resource.services.ai.azure.com/api/projects/my-project"
    $SCRIPT_NAME -p
    AIF_RESOURCE_URL="https://prod.ai.azure.com/api/projects/prod" $SCRIPT_NAME -g

EOF
}

validate_dependencies() {
    local deps=("az" "jq" "curl" "git")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            error "Required dependency '$dep' not found in PATH"
        fi
    done
}

validate_resource_url() {
    if [[ -z "$RESOURCE_URL" ]]; then
        error "Resource URL not provided. Use -r option or set AIF_RESOURCE_URL environment variable"
    fi
    
    if [[ ! "$RESOURCE_URL" =~ ^https://.*\.services\.ai\.azure\.com/api/projects/.+ ]]; then
        error "Invalid resource URL format: $RESOURCE_URL"
    fi
}

login() {
    debug "Attempting Azure login..."
    
    if ! az account show &> /dev/null; then
        log "Not logged in to Azure. Attempting login..."
        if ! az login; then
            error "Azure login failed"
        fi
    fi
    
    debug "Getting access token..."
    if ! AF_ACCESSTOKEN=$(az account get-access-token --resource "$AZURE_RESOURCE" --query accessToken --output tsv 2>/dev/null); then
        error "Failed to get access token"
    fi
    
    if [[ -z "$AF_ACCESSTOKEN" || "$AF_ACCESSTOKEN" == "null" ]]; then
        error "Invalid access token received"
    fi
    
    debug "Access token obtained successfully"
}

get_git_branch() {
    if git rev-parse --git-dir &> /dev/null; then
        BRANCH_NAME=$(git branch --show-current 2>/dev/null || echo "unknown")
        debug "Current git branch: $BRANCH_NAME"
    else
        debug "Not in a git repository"
        BRANCH_NAME="no-git"
    fi
}

serialize_agents() {
    validate_resource_url
    login
    get_git_branch
    
    log "Serializing agents from: $RESOURCE_URL"
    
    # Get API response and process agents directly (like the working version)
    curl --silent --fail \
        --request GET \
        --url "$RESOURCE_URL/assistants?api-version=$API_VERSION" \
        --header "authorization: Bearer $AF_ACCESSTOKEN" \
        --header 'content-type: application/json' | \
    jq -c '.data[]' | while read -r line; do
        local name filename
        name=$(echo "$line" | jq -r '.name')
        filename="${name}.agent"
        
        debug "Exporting: $name -> $filename"
        echo "$line" | jq '.' > "$filename"
        log "✅ Exported: $filename"
    done
    
    # Count the actual files created since the while loop runs in a subshell
    local count
    count=$(find . -name "*.agent" -type f | wc -l)
    log "Exported $count agent(s)"
}

deserialize_agents() {
    validate_resource_url
    login
    get_git_branch
    
    log "Deserializing agents to: $RESOURCE_URL"
    
    local agent_files=(*.agent)
    debug "Found agent files: ${agent_files[*]}"
    
    for agent_file in *.agent; do
        local agent_data
        if ! agent_data=$(jq 'del(.id) | del(.created_at) | del(.updated_at) | del(.object)' "$agent_file"); then
            debug "jq command failed for: $agent_file"
            continue
        fi
        
        local response
        if ! response=$(curl --silent --write-out "\n%{http_code}" \
            --request POST \
            --url "$RESOURCE_URL/assistants?api-version=$API_VERSION" \
            --header "authorization: Bearer $AF_ACCESSTOKEN" \
            --header "content-type: application/json" \
            --data "$agent_data"); then
            continue
        fi
        
        local http_code
        http_code=$(echo "$response" | tail -n1)
        
        if [[ "$http_code" -eq 201 || "$http_code" -eq 200 ]]; then
            local agent_name
            agent_name=$(echo "$response" | head -n -1 | jq -r '.name')
            log "✅ Created: $agent_name"
        else
            log "❌ Failed: $agent_file (HTTP $http_code)"
        fi
    done
}

create_project() {
    error "Project creation functionality not yet implemented"
}

get_project() {
    error "Project retrieval functionality not yet implemented"
}

main() {
    validate_dependencies
    
    local action=""
    
    while getopts "gpr:vh" opt; do
        case $opt in
            g) action="serialize" ;;
            p) action="deserialize" ;;
            r) RESOURCE_URL="$OPTARG" ;;
            v) VERBOSE=true ;;
            h) usage; exit 0 ;;
            \?) error "Invalid option. Use -h for help." ;;
        esac
    done
    
    if [[ -z "$action" ]]; then
        error "No action specified. Use -g (serialize) or -p (deserialize). Use -h for help."
    fi
    
    case "$action" in
        serialize) serialize_agents ;;
        deserialize) deserialize_agents ;;
        *) error "Unknown action: $action" ;;
    esac
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi