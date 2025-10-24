#!/usr/bin/env python3
"""CloudFormation YAML Loader - Handle CF intrinsic functions"""

import yaml

class CloudFormationLoader(yaml.SafeLoader):
    """Custom YAML loader that handles CloudFormation intrinsic functions"""
    pass

def cf_constructor(loader, tag_suffix, node):
    """Generic constructor for CloudFormation tags"""
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    elif isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    elif isinstance(node, yaml.MappingNode):
        return loader.construct_mapping(node)
    else:
        return None

# Register constructors for common CloudFormation intrinsic functions
cf_tags = [
    '!Ref', '!GetAtt', '!Sub', '!Join', '!Select', '!Split',
    '!Base64', '!GetAZs', '!ImportValue', '!FindInMap',
    '!Condition', '!If', '!Not', '!Equals', '!And', '!Or'
]

for tag in cf_tags:
    CloudFormationLoader.add_constructor(tag, lambda loader, node, tag=tag: cf_constructor(loader, tag, node))

def load_cf_yaml(file_path):
    """Load CloudFormation YAML file safely"""
    try:
        with open(file_path, 'r') as f:
            return yaml.load(f, Loader=CloudFormationLoader)
    except Exception as e:
        print(f"⚠️ Error processing {file_path}: {e}")
        return None
