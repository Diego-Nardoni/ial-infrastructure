#!/usr/bin/env python3
"""
MCP Tool: update_yaml_file
Updates YAML infrastructure files for IaL v2.0
"""

import yaml
import json
from pathlib import Path


def update_yaml_file(file_path: str, yaml_path: str, action: str, value: any) -> dict:
    """
    Update YAML file with new values
    
    Args:
        file_path: Path to YAML file (e.g., "phases/03-networking.yaml")
        yaml_path: Dot-notation path (e.g., "security_group_alb.ingress")
        action: "append", "remove", or "replace"
        value: Value to add/remove/replace
    
    Returns:
        Dictionary with status and details
    """
    try:
        # Read YAML file
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            return {
                "status": "error",
                "message": f"File not found: {file_path}"
            }
        
        with open(file_path_obj, 'r') as f:
            data = yaml.safe_load(f)
        
        # Navigate to the specified path
        keys = yaml_path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        final_key = keys[-1]
        
        # Apply the action
        if action == 'append':
            if final_key not in current:
                current[final_key] = []
            elif not isinstance(current[final_key], list):
                current[final_key] = [current[final_key]]
            
            current[final_key].append(value)
            change_description = f"Appended {value} to {yaml_path}"
        
        elif action == 'remove':
            if final_key in current and isinstance(current[final_key], list):
                if value in current[final_key]:
                    current[final_key].remove(value)
                    change_description = f"Removed {value} from {yaml_path}"
                else:
                    return {
                        "status": "error",
                        "message": f"Value {value} not found in {yaml_path}"
                    }
            else:
                return {
                    "status": "error",
                    "message": f"{yaml_path} is not a list or doesn't exist"
                }
        
        elif action == 'replace':
            current[final_key] = value
            change_description = f"Replaced {yaml_path} with {value}"
        
        else:
            return {
                "status": "error",
                "message": f"Invalid action: {action}. Use 'append', 'remove', or 'replace'"
            }
        
        # Write back to file
        with open(file_path_obj, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        
        return {
            "status": "success",
            "file": str(file_path),
            "yaml_path": yaml_path,
            "action": action,
            "value": value,
            "message": change_description
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error updating YAML: {str(e)}"
        }


# MCP Tool metadata
TOOL_METADATA = {
    "name": "update_yaml_file",
    "description": "Update YAML infrastructure files",
    "parameters": {
        "file_path": {
            "type": "string",
            "description": "Path to YAML file (e.g., phases/03-networking.yaml)",
            "required": True
        },
        "yaml_path": {
            "type": "string",
            "description": "Dot-notation path to field (e.g., security_group_alb.ingress)",
            "required": True
        },
        "action": {
            "type": "string",
            "description": "Action to perform: append, remove, or replace",
            "required": True,
            "enum": ["append", "remove", "replace"]
        },
        "value": {
            "type": "any",
            "description": "Value to add/remove/replace",
            "required": True
        }
    }
}


if __name__ == "__main__":
    # Test the tool
    import sys
    
    if len(sys.argv) < 5:
        print("Usage: python update_yaml_file.py <file_path> <yaml_path> <action> <value>")
        sys.exit(1)
    
    result = update_yaml_file(
        file_path=sys.argv[1],
        yaml_path=sys.argv[2],
        action=sys.argv[3],
        value=json.loads(sys.argv[4]) if sys.argv[4].startswith('{') or sys.argv[4].startswith('[') else sys.argv[4]
    )
    
    print(json.dumps(result, indent=2))
