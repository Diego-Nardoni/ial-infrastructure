#!/usr/bin/env python3
"""
IAL Phase Template Linter
Validates phase.yaml files against schema and enterprise rules
"""

import json
import sys
import glob
import os
from pathlib import Path

def load_json(path):
    """Load JSON file"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_yaml(path):
    """Load YAML file"""
    import yaml
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def validate_schema(doc, schema):
    """Validate document against JSON schema"""
    try:
        from jsonschema import Draft7Validator
        validator = Draft7Validator(schema)
        return list(validator.iter_errors(doc))
    except ImportError:
        print("Warning: jsonschema not available, skipping schema validation")
        return []

def validate_enterprise_rules(doc, file_path):
    """Validate enterprise-specific rules beyond schema"""
    errors = []
    
    # Get document sections
    metadata = doc.get("metadata", {})
    outputs_contract = doc.get("outputs_contract", {})
    
    # Rule 1: Name must start with NN-
    name = metadata.get("name", "")
    if not any(name.startswith(f"{i:02d}-") for i in range(0, 100)):
        errors.append({
            "file": file_path,
            "message": "metadata.name deve começar com NN- (ex: 01-networking)",
            "path": ["metadata", "name"]
        })
    
    # Rule 2: Minimum 3 WA pillars
    wa_pillars = metadata.get("wa_pillars", [])
    if len(wa_pillars) < 3:
        errors.append({
            "file": file_path,
            "message": "mínimo de 3 pilares Well-Architected necessários",
            "path": ["metadata", "wa_pillars"]
        })
    
    # Rule 3: outputs_contract.must_exist required
    must_exist = outputs_contract.get("must_exist", [])
    if len(must_exist) < 1:
        errors.append({
            "file": file_path,
            "message": "outputs_contract.must_exist precisa de pelo menos 1 item",
            "path": ["outputs_contract", "must_exist"]
        })
    
    # Rule 4: tags_must_include should contain ial:managed
    tags_include = outputs_contract.get("tags_must_include", [])
    if not any("ial:managed" in str(tag) for tag in tags_include):
        errors.append({
            "file": file_path,
            "message": "tags_must_include deve conter 'ial:managed'",
            "path": ["outputs_contract", "tags_must_include"]
        })
    
    return errors

def main():
    """Main linter function"""
    # Load schema
    schema_path = "schemas/phase.schema.json"
    if not os.path.exists(schema_path):
        print(f"Error: Schema not found at {schema_path}")
        sys.exit(1)
    
    schema = load_json(schema_path)
    all_errors = []
    
    # Find all phase.yaml files
    phase_files = []
    for pattern in ["phases/**/*.yaml", "phases/**/*.yml"]:
        phase_files.extend(glob.glob(pattern, recursive=True))
    
    if not phase_files:
        print("No phase files found to validate")
        return
    
    # Validate each file
    for yaml_file in sorted(phase_files):
        try:
            doc = load_yaml(yaml_file)
            if not doc:
                continue
                
            # Schema validation
            schema_errors = validate_schema(doc, schema)
            for error in schema_errors:
                all_errors.append({
                    "file": yaml_file,
                    "message": error.message,
                    "path": list(error.path) if error.path else []
                })
            
            # Enterprise rules validation
            enterprise_errors = validate_enterprise_rules(doc, yaml_file)
            all_errors.extend(enterprise_errors)
            
        except Exception as e:
            all_errors.append({
                "file": yaml_file,
                "message": f"Failed to parse YAML: {str(e)}",
                "path": []
            })
    
    # Generate report
    report = {
        "timestamp": "2025-11-03T17:42:50Z",
        "total_files": len(phase_files),
        "total_errors": len(all_errors),
        "errors": all_errors
    }
    
    # Save report
    os.makedirs("reports/validators", exist_ok=True)
    with open("reports/validators/phase_template_gate.json", "w") as f:
        json.dump(report, f, indent=2)
    
    # Output results
    if all_errors:
        print(json.dumps(report, indent=2))
        print(f"\n❌ Phase Template Gate: FAILED ({len(all_errors)} errors)")
        sys.exit(1)
    else:
        #print("✅ Phase Template Gate: OK")
        print(f"Validated {len(phase_files)} phase files successfully")

if __name__ == "__main__":
    main()
