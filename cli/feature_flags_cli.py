#!/usr/bin/env python3
"""
Feature Flags CLI - Interface para gerenciar feature flags
"""

import argparse
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.feature_flags_manager import FeatureFlagsManager
from core.drift_flag import DriftState

def main():
    parser = argparse.ArgumentParser(description='IAL Feature Flags Management')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List flags
    list_parser = subparsers.add_parser('list', help='List all feature flags')
    list_parser.add_argument('--scope', default='global', help='Scope to list flags for')
    
    # Enable feature
    enable_parser = subparsers.add_parser('enable', help='Enable a feature flag')
    enable_parser.add_argument('feature', help='Feature name to enable')
    enable_parser.add_argument('--scope', default='global', help='Scope for the flag')
    enable_parser.add_argument('--reason', default='CLI enable', help='Reason for enabling')
    enable_parser.add_argument('--duration', type=int, default=0, help='Duration in hours (0 = permanent)')
    
    # Disable feature
    disable_parser = subparsers.add_parser('disable', help='Disable a feature flag')
    disable_parser.add_argument('feature', help='Feature name to disable')
    disable_parser.add_argument('--scope', default='global', help='Scope for the flag')
    disable_parser.add_argument('--reason', default='CLI disable', help='Reason for disabling')
    disable_parser.add_argument('--duration', type=int, default=0, help='Duration in hours (0 = permanent)')
    
    # Check feature
    check_parser = subparsers.add_parser('check', help='Check if feature is enabled')
    check_parser.add_argument('feature', help='Feature name to check')
    check_parser.add_argument('--scope', default='global', help='Scope to check')
    
    # Drift-specific commands
    drift_parser = subparsers.add_parser('drift', help='Drift detection commands')
    drift_subparsers = drift_parser.add_subparsers(dest='drift_command')
    
    # Pause drift
    pause_parser = drift_subparsers.add_parser('pause', help='Pause drift detection')
    pause_parser.add_argument('scope', help='Scope to pause drift for')
    pause_parser.add_argument('--duration', type=int, required=True, help='Duration in hours')
    pause_parser.add_argument('--reason', required=True, help='Reason for pausing')
    pause_parser.add_argument('--ticket', default='', help='Ticket number')
    
    # Resume drift
    resume_parser = drift_subparsers.add_parser('resume', help='Resume drift detection')
    resume_parser.add_argument('scope', help='Scope to resume drift for')
    resume_parser.add_argument('--reason', default='Manual resume', help='Reason for resuming')
    
    # Status drift
    status_parser = drift_subparsers.add_parser('status', help='Check drift status')
    status_parser.add_argument('scope', help='Scope to check drift status for')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        flags_manager = FeatureFlagsManager()
        
        if args.command == 'list':
            print(f"📋 Feature flags for scope: {args.scope}")
            # This would require a scan operation - simplified for now
            print("   Use 'check <feature>' to check specific flags")
            
        elif args.command == 'enable':
            result = flags_manager.set_flag(args.feature, True, args.scope, args.reason, args.duration)
            print(f"✅ Enabled {args.feature} for scope {args.scope}")
            if args.duration > 0:
                print(f"   Duration: {args.duration} hours")
            
        elif args.command == 'disable':
            result = flags_manager.set_flag(args.feature, False, args.scope, args.reason, args.duration)
            print(f"❌ Disabled {args.feature} for scope {args.scope}")
            if args.duration > 0:
                print(f"   Duration: {args.duration} hours")
            
        elif args.command == 'check':
            enabled = flags_manager.is_enabled(args.feature, args.scope)
            status = "✅ ENABLED" if enabled else "❌ DISABLED"
            print(f"{status}: {args.feature} (scope: {args.scope})")
            
        elif args.command == 'drift':
            if args.drift_command == 'pause':
                result = flags_manager.pause_drift(args.scope, args.duration, args.reason, args.ticket)
                print(f"⏸️  Paused drift detection for {args.scope}")
                print(f"   Duration: {args.duration} hours")
                print(f"   Reason: {args.reason}")
                
            elif args.drift_command == 'resume':
                result = flags_manager.resume_drift(args.scope, args.reason)
                print(f"▶️  Resumed drift detection for {args.scope}")
                print(f"   Reason: {args.reason}")
                
            elif args.drift_command == 'status':
                enabled = flags_manager.is_drift_enabled(args.scope)
                state = flags_manager.drift_flag.get_drift_state(args.scope)
                print(f"🔍 Drift status for {args.scope}:")
                print(f"   Enabled: {'✅ YES' if enabled else '❌ NO'}")
                print(f"   State: {state.value}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
