#!/bin/bash
# Post-installation script for ialctl packages

echo "🔧 Configuring ialctl..."

# Ensure binary is executable
chmod +x /usr/local/bin/ialctl

# Create symlink in /usr/bin if it doesn't exist
if [ ! -L /usr/bin/ialctl ] && [ ! -f /usr/bin/ialctl ]; then
    ln -s /usr/local/bin/ialctl /usr/bin/ialctl
fi

# Add completion (if bash-completion is available)
if [ -d /etc/bash_completion.d ]; then
    cat > /etc/bash_completion.d/ialctl << 'EOF'
# ialctl bash completion
_ialctl() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="--help --version interactive status deploy rollback"
    
    COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
    return 0
}
complete -F _ialctl ialctl
EOF
fi

echo "✅ ialctl configuration completed"
