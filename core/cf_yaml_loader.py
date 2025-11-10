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

# Register CloudFormation intrinsic functions
CloudFormationLoader.add_multi_constructor('!', cf_constructor)

def load_cf_yaml(stream):
    """Load CloudFormation YAML with intrinsic function support"""
    return yaml.load(stream, Loader=CloudFormationLoader)
