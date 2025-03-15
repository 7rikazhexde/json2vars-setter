#!/bin/bash

# Function to display help message
show_help() {
  echo "Usage: $0 [OPTIONS]"
  echo ""
  echo "This script interacts with GitHub Actions caches in the current repository using the GitHub API."
  echo "It requires a GitHub Personal Access Token set as the GITHUB_TOKEN environment variable."
  echo "The repository is dynamically fetched using 'gh repo view'."
  echo ""
  echo "Options:"
  echo "  --help         Display this help message and exit"
  echo "  --list         List all caches without deleting them"
  echo "  --delete       Delete all caches"
  echo "  --delete-id ID Delete a specific cache by its ID (e.g., 75555748)"
  echo ""
  echo "Requirements:"
  echo "  - gh: GitHub CLI (install with 'brew install gh' or similar)"
  echo "  - jq: A command-line JSON processor (install with 'sudo apt install jq' or similar)"
  echo "  - GITHUB_TOKEN: A valid GitHub Personal Access Token with appropriate permissions"
  echo ""
  echo "How to set GITHUB_TOKEN:"
  echo "  - For Fine-grained Personal Access Token:"
  echo "    1. Generate at GitHub Settings > Developer settings > Personal access tokens > Fine-grained tokens"
  echo "    2. Set Repository access to 'Only select repositories' and choose the target repository"
  echo "    3. Grant 'Actions: Read and write' permission"
  echo "    4. Run: export GITHUB_TOKEN=github_pat_xxx"
  echo "  - For Classic Personal Access Token:"
  echo "    1. Generate at GitHub Settings > Developer settings > Personal access tokens > Tokens (classic)"
  echo "    2. Select the 'repo' scope"
  echo "    3. Run: export GITHUB_TOKEN=ghp_xxx"
  echo ""
  echo "Examples:"
  echo "  # List caches"
  echo "  export GITHUB_TOKEN=github_pat_xxx"
  echo "  ./$(basename "$0") --list"
  echo "  # Delete all caches"
  echo "  ./$(basename "$0") --delete"
  echo "  # Delete a specific cache by ID"
  echo "  ./$(basename "$0") --delete-id 75555748"
}

# Check if gh is installed
if ! command -v gh &> /dev/null; then
  echo "Error: gh (GitHub CLI) is required. Please install it (e.g., 'brew install gh')."
  exit 1
fi

# Dynamically fetch the current repository name (e.g., "owner/repo")
if ! REPO=$(gh repo view --json nameWithOwner -q '.nameWithOwner' 2>/dev/null) || [ -z "$REPO" ]; then
  echo "Error: Failed to fetch repository name with 'gh repo view'. Ensure you are in a git repository and authenticated with 'gh auth login'."
  exit 1
fi

# Fetch GitHub Personal Access Token from environment variable
TOKEN="${GITHUB_TOKEN}"

# Function to list caches
list_caches() {
  echo "Fetching cache list from $REPO via GitHub API..."
  curl -s -H "Authorization: token $TOKEN" \
       -H "Accept: application/vnd.github.v3+json" \
       "https://api.github.com/repos/$REPO/actions/caches?per_page=100" | jq -r '.actions_caches[] | [.id, .key] | join(" - ")'
}

# Function to delete all caches
delete_all_caches() {
  echo "Fetching cache list from $REPO via GitHub API..."
  CACHE_DATA=$(curl -s -H "Authorization: token $TOKEN" \
                    -H "Accept: application/vnd.github.v3+json" \
                    "https://api.github.com/repos/$REPO/actions/caches?per_page=100")

  # Verify API response is valid and not an error
  if [ -z "$CACHE_DATA" ] || echo "$CACHE_DATA" | grep -q "message"; then
    echo "Error: Failed to fetch cache list or no caches found."
    echo "Response: $CACHE_DATA"
    exit 1
  fi

  # Extract cache IDs
  CACHE_IDS=$(echo "$CACHE_DATA" | jq -r '.actions_caches[].id')
  if [ -z "$CACHE_IDS" ]; then
    echo "No caches found."
    exit 0
  fi

  # Display found caches
  echo "Found caches:"
  echo "$CACHE_DATA" | jq -r '.actions_caches[] | [.id, .key] | join(" - ")' | nl
  echo ""

  # Delete caches
  echo "Deleting caches..."
  echo "$CACHE_IDS" | while IFS= read -r ID; do
    KEY=$(echo "$CACHE_DATA" | jq -r ".actions_caches[] | select(.id==$ID) | .key")
    echo "Deleting cache: $KEY (ID: $ID)"
    if ! curl -s -X DELETE \
         -H "Authorization: token $TOKEN" \
         -H "Accept: application/vnd.github.v3+json" \
         "https://api.github.com/repos/$REPO/actions/caches/$ID" >/dev/null 2>&1; then
      DELETE_RESPONSE=$(curl -s -X DELETE \
           -H "Authorization: token $TOKEN" \
           -H "Accept: application/vnd.github.v3+json" \
           "https://api.github.com/repos/$REPO/actions/caches/$ID")
      echo "Failed to delete: $KEY (ID: $ID)"
      echo "Response: $DELETE_RESPONSE"
    else
      echo "Successfully deleted: $KEY (ID: $ID)"
    fi
  done

  echo "Cache deletion complete."
}

# Function to delete a specific cache by ID
delete_cache_by_id() {
  local ID="$1"
  echo "Fetching cache list from $REPO via GitHub API to verify ID $ID..."
  CACHE_DATA=$(curl -s -H "Authorization: token $TOKEN" \
                    -H "Accept: application/vnd.github.v3+json" \
                    "https://api.github.com/repos/$REPO/actions/caches?per_page=100")

  # Verify API response
  if [ -z "$CACHE_DATA" ] || echo "$CACHE_DATA" | grep -q "message"; then
    echo "Error: Failed to fetch cache list."
    echo "Response: $CACHE_DATA"
    exit 1
  fi

  # Check if the ID exists
  KEY=$(echo "$CACHE_DATA" | jq -r ".actions_caches[] | select(.id==$ID) | .key")
  if [ -z "$KEY" ]; then
    echo "Error: Cache with ID $ID not found in $REPO."
    exit 1
  fi

  # Delete the specific cache
  echo "Deleting cache: $KEY (ID: $ID)"
  if ! curl -s -X DELETE \
       -H "Authorization: token $TOKEN" \
       -H "Accept: application/vnd.github.v3+json" \
       "https://api.github.com/repos/$REPO/actions/caches/$ID" >/dev/null 2>&1; then
    DELETE_RESPONSE=$(curl -s -X DELETE \
         -H "Authorization: token $TOKEN" \
         -H "Accept: application/vnd.github.v3+json" \
         "https://api.github.com/repos/$REPO/actions/caches/$ID")
    echo "Failed to delete: $KEY (ID: $ID)"
    echo "Response: $DELETE_RESPONSE"
    exit 1
  else
    echo "Successfully deleted: $KEY (ID: $ID)"
  fi
}

# Check for options
case "$1" in
  "--help")
    show_help
    exit 0
    ;;
  "--list")
    # Check if TOKEN is set
    if [ -z "$TOKEN" ]; then
      echo "Error: GITHUB_TOKEN environment variable is not set."
      echo "Run '$0 --help' for instructions."
      exit 1
    fi
    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
      echo "Error: jq is required. Please install it (e.g., 'sudo apt install jq')."
      exit 1
    fi
    list_caches
    exit 0
    ;;
  "--delete")
    # Check if TOKEN is set
    if [ -z "$TOKEN" ]; then
      echo "Error: GITHUB_TOKEN environment variable is not set."
      echo "Run '$0 --help' for instructions."
      exit 1
    fi
    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
      echo "Error: jq is required. Please install it (e.g., 'sudo apt install jq')."
      exit 1
    fi
    delete_all_caches
    exit 0
    ;;
  "--delete-id")
    # Check if ID is provided
    if [ -z "$2" ]; then
      echo "Error: Cache ID is required with --delete-id."
      echo "Example: $0 --delete-id 75555748"
      exit 1
    fi
    # Check if TOKEN is set
    if [ -z "$TOKEN" ]; then
      echo "Error: GITHUB_TOKEN environment variable is not set."
      echo "Run '$0 --help' for instructions."
      exit 1
    fi
    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
      echo "Error: jq is required. Please install it (e.g., 'sudo apt install jq')."
      exit 1
    fi
    delete_cache_by_id "$2"
    exit 0
    ;;
  "")
    echo "Error: No option specified. Use --list, --delete, or --delete-id."
    echo "Run '$0 --help' for usage instructions."
    exit 1
    ;;
  *)
    echo "Error: Unknown option '$1'."
    echo "Run '$0 --help' for usage instructions."
    exit 1
    ;;
esac
