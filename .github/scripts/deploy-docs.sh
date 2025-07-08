#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# This script deploys the custom 404.html page to the root of the gh-pages branch.
# It's designed to be called from the GitHub Actions workflow.
#
# It expects one argument:
# $1: The GitHub repository name (e.g., "a2aproject/A2A").
#
# The script assumes that the git user name and email are already configured.

# --- Validate Input ---
if [ -z "$1" ]; then
  echo "Error: Missing required argument. Please provide the repository name (e.g., owner/repo)."
  exit 1
fi

REPO_NAME=$1

echo "Deploying custom 404 page for repository: $REPO_NAME"

# --- Deployment Logic ---
# Clone the gh-pages branch into a temporary directory
git clone --branch=gh-pages --single-branch --depth=1 "https://github.com/${REPO_NAME}" gh-pages-deploy

# Copy the 404 page from the main branch checkout into the gh-pages clone
cp docs/404.html gh-pages-deploy/404.html

# Navigate into the cloned directory
cd gh-pages-deploy

# Add the 404 page to the staging area
git add 404.html

# Commit and push only if the 404 page has actually changed
if git diff --staged --quiet; then
  echo "404.html is up-to-date. No new commit needed."
else
  echo "Committing and pushing updated 404.html..."
  git commit -m "docs: deploy custom 404.html for redirects"
  git push
fi

echo "404 page deployment complete."
