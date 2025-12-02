#!/usr/bin/env python3
"""
IAL Configuration Management - Feature Flags
"""

import sys
import argparse
from core.feature_flags import feature_flags

def handle_config_command(args):
    """Handle ialctl config commands"""
    
    if args.action == 'set':
        flag_name, value = args.flag_value.split('=', 1)
        enabled = value.lower() in ['true', '1', 'yes', 'on']
        
        # Special handling for security services
        if flag_name == 'SECURITY_SERVICES_ENABLED':
            if not enabled:
                print("⚠️  WARNING: Disabling Security Services")
                print("   💰 This will save ~$24/month on future deployments")
                print("   🔒 Existing security resources will remain active and billing")
                print("   📋 Affected services: GuardDuty, Security Hub, Inspector, Access Analyzer, Macie")
                print("")
                print("   To remove existing security resources:")
                print("   ialctl destroy security-services")
                print("")
                
                confirm = input("Continue? (y/N): ").lower()
                if confirm != 'y':
                    print("❌ Cancelled")
                    return
        
        success = feature_flags.set_flag(flag_name, enabled)
        if success:
            print(f"✅ {flag_name} = {enabled}")
        else:
            print(f"❌ Failed to set {flag_name}")
    
    elif args.action == 'get':
        if args.flag_name:
            value = feature_flags.get_flag(args.flag_name)
            print(f"{args.flag_name} = {value}")
        else:
            # Show all flags
            all_flags = feature_flags.get_all_flags()
            print("🔧 IAL Feature Flags:")
            print("=" * 40)
            
            for flag_name, enabled in all_flags.items():
                status = "ENABLED" if enabled else "DISABLED"
                cost_info = ""
                
                if flag_name == 'SECURITY_SERVICES_ENABLED':
                    cost_info = " (~$24/month)" if enabled else " (saves $24/month)"
                
                print(f"  {flag_name}: {status}{cost_info}")
    
    elif args.action == 'reset':
        print("🔄 Resetting feature flags to defaults...")
        feature_flags.initialize_defaults()
        print("✅ Feature flags reset")

def main():
    parser = argparse.ArgumentParser(description='IAL Configuration Management')
    subparsers = parser.add_subparsers(dest='action', help='Available actions')
    
    # ialctl config set FLAG=VALUE
    set_parser = subparsers.add_parser('set', help='Set feature flag')
    set_parser.add_argument('flag_value', help='FLAG=VALUE (e.g., SECURITY_SERVICES_ENABLED=false)')
    
    # ialctl config get [FLAG]
    get_parser = subparsers.add_parser('get', help='Get feature flag(s)')
    get_parser.add_argument('flag_name', nargs='?', help='Flag name (optional, shows all if omitted)')
    
    # ialctl config reset
    reset_parser = subparsers.add_parser('reset', help='Reset to defaults')
    
    args = parser.parse_args()
    
    if not args.action:
        parser.print_help()
        return
    
    handle_config_command(args)

if __name__ == '__main__':
    main()
