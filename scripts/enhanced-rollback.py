#!/usr/bin/env python3
"""Enhanced Rollback Script with Professional Management"""

import sys
import argparse
from pathlib import Path

# Import professional utilities
sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import get_logger
from utils.rollback_manager import rollback_manager

logger = get_logger(__name__)

def main():
    """Enhanced rollback with professional management"""
    
    parser = argparse.ArgumentParser(description='Professional IaL Rollback Management')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create checkpoint command
    checkpoint_parser = subparsers.add_parser('checkpoint', help='Create rollback checkpoint')
    checkpoint_parser.add_argument('--description', help='Checkpoint description')
    
    # List checkpoints command
    list_parser = subparsers.add_parser('list', help='List available checkpoints')
    list_parser.add_argument('--limit', type=int, default=10, help='Number of checkpoints to show')
    
    # Rollback command
    rollback_parser = subparsers.add_parser('rollback', help='Rollback to checkpoint')
    rollback_parser.add_argument('checkpoint_id', help='Checkpoint ID to rollback to')
    rollback_parser.add_argument('--no-validate', action='store_true', help='Skip validation')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Cleanup old checkpoints')
    cleanup_parser.add_argument('--keep', type=int, default=10, help='Number of checkpoints to keep')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'checkpoint':
            checkpoint_id = rollback_manager.create_checkpoint(args.description)
            logger.info(f"Checkpoint created: {checkpoint_id}")
            print(f"✅ Checkpoint created: {checkpoint_id}")
            
        elif args.command == 'list':
            checkpoints = rollback_manager.list_checkpoints(args.limit)
            if not checkpoints:
                print("No checkpoints found")
                return
            
            print(f"\n📋 Available Checkpoints ({len(checkpoints)}):")
            print("-" * 80)
            for cp in checkpoints:
                print(f"ID: {cp['checkpoint_id']}")
                print(f"Time: {cp['timestamp']}")
                print(f"Description: {cp['description']}")
                print(f"Git Commit: {cp['git_commit'][:8]}")
                print("-" * 80)
                
        elif args.command == 'rollback':
            validate = not args.no_validate
            success = rollback_manager.rollback_to_checkpoint(args.checkpoint_id, validate)
            
            if success:
                print(f"✅ Rollback completed: {args.checkpoint_id}")
            else:
                print(f"❌ Rollback failed: {args.checkpoint_id}")
                sys.exit(1)
                
        elif args.command == 'cleanup':
            rollback_manager.cleanup_old_checkpoints(args.keep)
            print(f"✅ Cleanup completed, kept {args.keep} checkpoints")
            
    except Exception as e:
        logger.error(f"Rollback operation failed: {e}", exc_info=True)
        print(f"❌ Operation failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
