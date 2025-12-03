#!/usr/bin/env python3
"""
Test script to verify .env file is working correctly
"""

from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

print("=" * 60)
print("🧪 TESTING .ENV FILE CONFIGURATION")
print("=" * 60)
print()

# List of required environment variables
required_vars = {
    'MCTIME_API_KEY': 'McTime API Key',
    'SMTP_SERVER': 'SMTP Server',
    'SMTP_PORT': 'SMTP Port',
    'SMTP_USERNAME': 'SMTP Username',
    'SMTP_PASSWORD': 'SMTP Password',
    'SENDER_EMAIL': 'Sender Email',
    'USE_TLS': 'Use TLS',
}

all_set = True
missing_vars = []

for var_name, description in required_vars.items():
    value = os.getenv(var_name)
    
    if value:
        # Mask sensitive information
        if 'PASSWORD' in var_name or 'KEY' in var_name:
            if len(value) > 8:
                display_value = value[:3] + '...' + value[-3:]
            else:
                display_value = '***'
        else:
            display_value = value
        
        print(f"✅ {description:20} ({var_name})")
        print(f"   Value: {display_value}")
    else:
        print(f"❌ {description:20} ({var_name})")
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
