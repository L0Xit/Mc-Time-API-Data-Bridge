#!/usr/bin/env python3
"""
Test script to verify .env file is working correctly
Uses the centralized config module
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings, get_settings


def test_env_configuration():
    """Test environment variable configuration"""
    
    print("=" * 60)
    print("🧪 TESTING .ENV FILE CONFIGURATION")
    print("=" * 60)
    print()
    
    settings = get_settings()
    
    # List of settings to check
    checks = [
        ('MCTIME_API_KEY', settings.MCTIME_API_KEY, True),
        ('SMTP_SERVER', settings.SMTP_SERVER, False),
        ('SMTP_PORT', str(settings.SMTP_PORT), False),
        ('SMTP_USERNAME', settings.SMTP_USERNAME, False),
        ('SMTP_PASSWORD', settings.SMTP_PASSWORD, True),
        ('SENDER_EMAIL', settings.SENDER_EMAIL, False),
        ('USE_TLS', str(settings.USE_TLS), False),
    ]
    
    all_set = True
    missing_vars = []
    
    for var_name, value, is_sensitive in checks:
        if value and value != '0':
            # Mask sensitive information
            if is_sensitive:
                if len(str(value)) > 8:
                    display_value = str(value)[:3] + '...' + str(value)[-3:]
                else:
                    display_value = '***'
            else:
                display_value = value
            
            print(f"✅ {var_name:20}")
            print(f"   Value: {display_value}")
        else:
            print(f"❌ {var_name:20}")
            print(f"   Value: NOT SET")
            all_set = False
            missing_vars.append(var_name)
        
        print()
    
    print("=" * 60)
    
    if all_set:
        print("🎉 SUCCESS! All environment variables are set correctly!")
        print("   Your .env file is working properly.")
    else:
        print(f"⚠️  WARNING! {len(missing_vars)} variable(s) missing:")
        for var in missing_vars:
            print(f"   - {var}")
        print()
        print("   Please add these to your .env file.")
    
    print("=" * 60)
    
    # Additional validation
    print()
    validation = Settings.validate()
    if validation['valid']:
        print("✅ Core settings validation passed!")
    else:
        print("❌ Core settings validation failed:")
        for issue in validation['issues']:
            print(f"   - {issue}")
    
    print()
    if Settings.is_email_configured():
        print("✅ Email settings are configured")
    else:
        print("⚠️  Email settings are not fully configured")


if __name__ == '__main__':
    test_env_configuration()
