#!/bin/bash
# Pre-removal script for ialctl packages

echo "🗑️ Preparing to remove ialctl..."

# Remove symlink
if [ -L /usr/bin/ialctl ]; then
    rm -f /usr/bin/ialctl
fi

# Remove bash completion
if [ -f /etc/bash_completion.d/ialctl ]; then
    rm -f /etc/bash_completion.d/ialctl
fi

echo "✅ ialctl cleanup completed"
