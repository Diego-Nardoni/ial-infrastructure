#!/usr/bin/env python3
"""MCP Server for IaL Tools"""
import sys
import json
from update_yaml_file import UpdateYamlFileTool
from git_commit import GitCommitTool
from git_push import GitPushTool
import subprocess

class SetupIaLTool:
    """Setup IaL infrastructure automatically"""
    name = "setup_ial"
    
    def execute(self):
        result = subprocess.run(['python3', '/home/ial/mcp-tools/setup_ial.py'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            return {'status': 'error', 'message': result.stderr}

def main():
    tools = {
        'setup_ial': SetupIaLTool(),
        'update_yaml_file': UpdateYamlFileTool(),
        'git_commit': GitCommitTool(),
        'git_push': GitPushTool()
    }
    
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'No tool specified'}))
        sys.exit(1)
    
    tool_name = sys.argv[1]
    if tool_name not in tools:
        print(json.dumps({'error': f'Unknown tool: {tool_name}'}))
        sys.exit(1)
    
    args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    result = tools[tool_name].execute(**args)
    print(json.dumps(result))

if __name__ == '__main__':
    main()
