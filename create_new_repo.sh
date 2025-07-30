#!/bin/bash

# Script to create a new repository with clean commit history
# Run this from the parent directory of pixel-detector

echo "Creating new pixel-detector repository with clean history..."

# Configuration
NEW_REPO_NAME="pixel-detector-v2"
GIT_EMAIL="ming@users.noreply.github.com"
GIT_NAME="Ming Yang"

# Create new directory
if [ -d "$NEW_REPO_NAME" ]; then
    echo "Error: $NEW_REPO_NAME already exists. Please remove it first."
    exit 1
fi

# Copy all files except .git
echo "Copying files..."
cp -r pixel-detector "$NEW_REPO_NAME"
cd "$NEW_REPO_NAME"
rm -rf .git

# Initialize new repository
echo "Initializing new repository..."
git init

# Configure git for this repository only
echo "Configuring git settings..."
git config user.email "$GIT_EMAIL"
git config user.name "$GIT_NAME"

# Add all files
echo "Adding files to repository..."
git add .

# Create initial commit
echo "Creating initial commit..."
git commit -m "Initial commit: Healthcare pixel tracking detection system

A tool to detect tracking pixels on healthcare websites that may violate HIPAA compliance.

Features:
- Detects 8 major tracking platforms (Meta, Google, TikTok, etc.)
- Multiple detection methods (network, DOM, JavaScript, cookies)
- Concurrent batch scanning
- Smart URL normalization
- Comprehensive reporting

See README.md for detailed documentation."

# Create tags
echo "Creating version tags..."
git tag -a v0.1.0 -m "Initial release with core functionality" --date="2025-07-20T12:00:00"
git tag -a v0.2.0 -m "Enhanced URL handling and domain resolution"

echo ""
echo "✅ New repository created successfully at: $NEW_REPO_NAME"
echo ""
echo "Next steps:"
echo "1. cd $NEW_REPO_NAME"
echo "2. Create a new GitHub repository on github.com"
echo "3. git remote add origin https://github.com/YOUR_USERNAME/pixel-detector.git"
echo "4. git push -u origin main --tags"
echo ""
echo "Git config for this repo:"
echo "  Email: $GIT_EMAIL (GitHub no-reply email)"
echo "  Name: $GIT_NAME"
echo ""
echo "After verifying everything looks good, you can remove the old pixel-detector directory."