#!/usr/bin/env python3
"""
MCP Tool: git_commit
Commits changes to Git repository for IaL v2.0
"""

import subprocess
import json
from typing import List


def git_commit(files: List[str], message: str) -> dict:
    """
    Commit changes to Git repository
    
    Args:
        files: List of files to commit
        message: Commit message
    
    Returns:
        Dictionary with status and commit hash
    """
    try:
        # Git add files
        for file in files:
            result = subprocess.run(
                ['git', 'add', file],
                capture_output=True,
                text=True,
                check=True
            )
        
        # Git commit
        result = subprocess.run(
            ['git', 'commit', '-m', message],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            # Extract commit hash from output
            commit_hash = None
            if result.stdout:
                # Output format: "[branch commit_hash] message"
                parts = result.stdout.split()
                if len(parts) >= 2:
                    commit_hash = parts[1].strip(']')
            
            return {
                "status": "success",
                "files": files,
                "message": message,
                "commit_hash": commit_hash,
                "output": result.stdout.strip()
            }
        else:
            # Check if it's "nothing to commit"
            if "nothing to commit" in result.stdout:
                return {
                    "status": "success",
                    "files": files,
                    "message": "No changes to commit",
                    "commit_hash": None
                }
            else:
                return {
                    "status": "error",
                    "message": f"Git commit failed: {result.stderr}",
                    "output": result.stdout
                }
    
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "message": f"Git command failed: {e.stderr}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error committing to Git: {str(e)}"
        }


# MCP Tool metadata
TOOL_METADATA = {
    "name": "git_commit",
    "description": "Commit changes to Git repository",
    "parameters": {
        "files": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of files to commit",
            "required": True
        },
        "message": {
            "type": "string",
            "description": "Commit message",
            "required": True
        }
    }
}


if __name__ == "__main__":
    # Test the tool
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python git_commit.py <file1,file2,...> <message>")
        sys.exit(1)
    
    files = sys.argv[1].split(',')
    message = sys.argv[2]
    
    result = git_commit(files=files, message=message)
    print(json.dumps(result, indent=2))
