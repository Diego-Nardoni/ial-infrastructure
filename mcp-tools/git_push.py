#!/usr/bin/env python3
"""
MCP Tool: git_push
Pushes commits to remote Git repository for IaL v2.0
"""

import subprocess
import json


def git_push(remote: str = "origin", branch: str = "main") -> dict:
    """
    Push commits to remote repository
    
    Args:
        remote: Remote name (default: "origin")
        branch: Branch name (default: "main")
    
    Returns:
        Dictionary with status and output
    """
    try:
        # Git push
        result = subprocess.run(
            ['git', 'push', remote, branch],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return {
                "status": "success",
                "remote": remote,
                "branch": branch,
                "message": f"Successfully pushed to {remote}/{branch}",
                "output": result.stdout.strip() or result.stderr.strip()
            }
        else:
            return {
                "status": "error",
                "remote": remote,
                "branch": branch,
                "message": f"Git push failed: {result.stderr}",
                "output": result.stderr.strip()
            }
    
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "message": f"Git command failed: {e.stderr}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error pushing to Git: {str(e)}"
        }


# MCP Tool metadata
TOOL_METADATA = {
    "name": "git_push",
    "description": "Push commits to remote Git repository",
    "parameters": {
        "remote": {
            "type": "string",
            "description": "Remote name (default: origin)",
            "required": False,
            "default": "origin"
        },
        "branch": {
            "type": "string",
            "description": "Branch name (default: main)",
            "required": False,
            "default": "main"
        }
    }
}


if __name__ == "__main__":
    # Test the tool
    import sys
    
    remote = sys.argv[1] if len(sys.argv) > 1 else "origin"
    branch = sys.argv[2] if len(sys.argv) > 2 else "main"
    
    result = git_push(remote=remote, branch=branch)
    print(json.dumps(result, indent=2))
