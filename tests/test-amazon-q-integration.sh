#!/bin/bash
set -e

echo "🧪 Testing Amazon Q Integration..."

if [ -f "/home/ial/mcp-tools/update_yaml_file.py" ] && \
   [ -f "/home/ial/mcp-tools/git_commit.py" ] && \
   [ -f "/home/ial/mcp-tools/git_push.py" ]; then
    echo "✅ Amazon Q Integration PASSED - MCP tools exist"
    exit 0
else
    echo "❌ Amazon Q Integration FAILED - Missing MCP tools"
    exit 1
fi
