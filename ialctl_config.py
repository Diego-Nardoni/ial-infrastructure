#!/usr/bin/env python3
"""
IAL Configuration Management
"""

import sys

def main():
    """Main configuration handler"""
    if len(sys.argv) >= 2 and sys.argv[1] == 'set':
        # ialctl config set KEY=VALUE
        if len(sys.argv) >= 3:
            config_arg = sys.argv[2]
            if '=' in config_arg:
                key, value = config_arg.split('=', 1)
                
                # Handle budget limit
                if key == 'BUDGET_LIMIT':
                    try:
                        budget_value = float(value)
                        from core.budget_config import budget_config
                        budget_config.set_phase_limit('00-foundation', budget_value)
                        print(f"✅ Budget limit set to ${budget_value}/month")
                    except ValueError:
                        print(f"❌ Invalid budget value: {value}")
                        return
                
                # Handle feature flags
                elif key in ['BUDGET_ENFORCEMENT_ENABLED', 'SECURITY_SERVICES_ENABLED']:
                    flag_value = value.lower() in ['true', '1', 'yes', 'enabled']
                    from core.feature_flags import feature_flags
                    
                    if feature_flags.set_flag(key, flag_value):
                        print(f"✅ {key} set to {flag_value}")
                    else:
                        print(f"❌ Failed to set {key}")
                else:
                    print(f"❌ Unknown configuration key: {key}")
            else:
                print("❌ Invalid format. Use: ialctl config set KEY=VALUE")
        else:
            print("❌ Missing configuration. Use: ialctl config set KEY=VALUE")
    
    elif len(sys.argv) >= 2 and sys.argv[1] == 'get':
        # ialctl config get [KEY]
        if len(sys.argv) >= 3:
            key = sys.argv[2]
            if key == 'BUDGET_LIMIT':
                from core.budget_config import budget_config
                limit = budget_config.get_phase_limit('00-foundation')
                print(f"{key}=${limit}")
            elif key in ['BUDGET_ENFORCEMENT_ENABLED', 'SECURITY_SERVICES_ENABLED']:
                from core.feature_flags import feature_flags
                value = feature_flags.get_flag(key)
                print(f"{key}={value}")
            else:
                print(f"❌ Unknown configuration key: {key}")
        else:
            # Show all config
            from core.feature_flags import feature_flags
            from core.budget_config import budget_config
            
            print("📋 IAL Configuration:")
            print(f"BUDGET_LIMIT=${budget_config.get_phase_limit('00-foundation')}")
            
            flags = feature_flags.get_all_flags()
            for flag, value in flags.items():
                print(f"{flag}={value}")
    else:
        print("Usage:")
        print("  ialctl config get [KEY]     - Get configuration value(s)")
        print("  ialctl config set KEY=VALUE - Set configuration value")
        print("")
        print("Available keys:")
        print("  BUDGET_LIMIT               - Monthly budget limit (e.g., 100.0)")
        print("  BUDGET_ENFORCEMENT_ENABLED - Enable/disable budget enforcement")
        print("  SECURITY_SERVICES_ENABLED  - Enable/disable security services")

if __name__ == '__main__':
    main()
