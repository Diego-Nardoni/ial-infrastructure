#!/usr/bin/env python3
"""
Phase CLI - Interface de linha de comando para gerenciar phases
"""

import argparse
import sys
from typing import Dict, Any
import json

try:
    from phase_deletion_manager import PhaseDeletionManager
    DELETION_AVAILABLE = True
except ImportError:
    DELETION_AVAILABLE = False

class PhaseCLI:
    """CLI para gerenciamento de phases"""
    
    def __init__(self):
        if DELETION_AVAILABLE:
            self.deletion_manager = PhaseDeletionManager()
        else:
            self.deletion_manager = None
    
    def delete_phase(self, phase_name: str, force: bool = False, confirm: bool = False) -> Dict[str, Any]:
        """Delete a phase with confirmation"""
        
        if not DELETION_AVAILABLE:
            return {'success': False, 'error': 'Phase deletion not available'}
        
        # Get phase info first
        phase_info = self.deletion_manager.get_phase_info(phase_name)
        
        if not phase_info['resources']:
            return {'success': False, 'error': f'Phase {phase_name} not found'}
        
        # Show phase info
        print(f"\n📋 Phase Information:")
        print(f"   Name: {phase_name}")
        print(f"   Resources: {phase_info['resource_count']}")
        print(f"   Safe to delete: {phase_info['safe_to_delete']}")
        
        if phase_info['blocking_dependencies']:
            print(f"   ⚠️ Blocking dependencies: {phase_info['blocking_dependencies']}")
        
        # Confirmation
        if not confirm and not force:
            response = input(f"\n❓ Delete phase '{phase_name}' and all {phase_info['resource_count']} resources? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                return {'success': False, 'error': 'Deletion cancelled by user'}
        
        # Execute deletion
        return self.deletion_manager.delete_phase(phase_name, force=force)
    
    def list_phases(self) -> Dict[str, Any]:
        """List all phases"""
        
        if not DELETION_AVAILABLE:
            return {'success': False, 'error': 'Phase management not available'}
        
        phases = self.deletion_manager.list_phases()
        
        print(f"\n📋 Available Phases ({len(phases)}):")
        for phase in phases:
            phase_info = self.deletion_manager.get_phase_info(phase)
            status = "✅ Safe" if phase_info['safe_to_delete'] else "⚠️ Has dependencies"
            print(f"   {phase} - {phase_info['resource_count']} resources - {status}")
        
        return {'success': True, 'phases': phases}
    
    def phase_info(self, phase_name: str) -> Dict[str, Any]:
        """Get detailed phase information"""
        
        if not DELETION_AVAILABLE:
            return {'success': False, 'error': 'Phase management not available'}
        
        phase_info = self.deletion_manager.get_phase_info(phase_name)
        
        print(f"\n📋 Phase: {phase_name}")
        print(f"   Resources: {phase_info['resource_count']}")
        print(f"   Safe to delete: {phase_info['safe_to_delete']}")
        
        if phase_info['resources']:
            print(f"\n   📦 Resources:")
            for resource in phase_info['resources']:
                print(f"      - {resource['id']} ({resource['type']})")
        
        if phase_info['blocking_dependencies']:
            print(f"\n   ⚠️ Blocking Dependencies:")
            for dep in phase_info['blocking_dependencies']:
                print(f"      - {dep}")
        
        return {'success': True, 'info': phase_info}

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description='IAL Phase Management CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all phases')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Get phase information')
    info_parser.add_argument('phase', help='Phase name')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a phase')
    delete_parser.add_argument('phase', help='Phase name to delete')
    delete_parser.add_argument('--force', action='store_true', help='Force deletion ignoring dependencies')
    delete_parser.add_argument('--yes', action='store_true', help='Skip confirmation')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = PhaseCLI()
    
    try:
        if args.command == 'list':
            result = cli.list_phases()
        elif args.command == 'info':
            result = cli.phase_info(args.phase)
        elif args.command == 'delete':
            result = cli.delete_phase(args.phase, force=args.force, confirm=args.yes)
        else:
            print(f"❌ Unknown command: {args.command}")
            return
        
        if not result['success']:
            print(f"❌ Error: {result['error']}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
