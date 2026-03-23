#!/bin/bash

# Commands to push the MCP server to GitHub

# 1. Initialize git repository (if not already done)
git init

# 2. Add the remote repository
git remote add origin https://github.com/DMontgomery40/mcp-BirdNET-Pi-server.git

# 3. Create and switch to a new branch
git checkout -b main

# 4. Add all files
git add .

# 5. Commit changes
git commit -m "Initial commit: BirdNet-Pi MCP server implementation

- Added BirdNet-Pi data integration and analysis
- Added visualization capabilities
- Added reporting functionality
- Added setup scripts
- Added comprehensive documentation"

# 6. Push to GitHub
git push -u origin main

echo "Done! Check your GitHub repository at https://github.com/DMontgomery40/mcp-BirdNET-Pi-server"