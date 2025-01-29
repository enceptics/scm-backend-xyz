#!/bin/bash

# Exit on error
set -e

# Stage all changes
git add .

# Commit changes with a message (you can modify this to prompt for a message)
commit_message="Update changes"
git commit -m "$commit_message"

# Push to the 'main-templates-8' branch
git push origin main-templates-8

# Print success message
echo "Changes successfully pushed to 'main-templates-8'!"
