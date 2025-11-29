#!/usr/bin/env python3
"""
Production preparation script
Checks and prepares the application for production deployment
"""

import os
import sys
import secrets

def check_env_file():
    """Check if .env file exists and has required variables"""
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        print("   Create one from: cp .env.production .env")
        return False
    
    with open('.env', 'r') as f:
        content = f.read()
    
    checks = {
        'FLASK_DEBUG': False,
        'SECRET_KEY': '',
        'MODEL_API_URL': ''
    }
    
    print("\n🔍 Checking .env configuration...")
    print("-" * 70)
    
    for line in content.split('\n'):
        if line.startswith('FLASK_DEBUG='):
            value = line.split('=')[1].strip()
            checks['FLASK_DEBUG'] = value
            if value.lower() == 'false':
                print("✅ FLASK_DEBUG=False (production mode)")
            else:
                print("❌ FLASK_DEBUG=True (MUST be False for production)")
        
        elif line.startswith('SECRET_KEY='):
            value = line.split('=')[1].strip()
            checks['SECRET_KEY'] = value
            if value and len(value) > 20:
                print("✅ SECRET_KEY is set")
            else:
                print("❌ SECRET_KEY not set or too short")
                print("   Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\"")
        
        elif line.startswith('MODEL_API_URL='):
            value = line.split('=')[1].strip()
            checks['MODEL_API_URL'] = value
            if value:
                print(f"✅ MODEL_API_URL: {value}")
            else:
                print("❌ MODEL_API_URL not set")
    
    all_ok = (
        checks['FLASK_DEBUG'].lower() == 'false' and
        checks['SECRET_KEY'] and len(checks['SECRET_KEY']) > 20 and
        checks['MODEL_API_URL']
    )
    
    return all_ok

def check_dependencies():
    """Check if all dependencies are installed"""
    print("\n📦 Checking dependencies...")
    print("-" * 70)
    
    required = [
        ('flask', 'Flask'),
        ('requests', 'requests'),
        ('dotenv', 'python-dotenv'),
        ('ebooklib', 'ebooklib'),
        ('bs4', 'beautifulsoup4')
    ]
    
    all_ok = True
    for module, package in required:
        try:
            __import__(module)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} not installed")
            all_ok = False
    
    if not all_ok:
        print("\nInstall missing dependencies:")
        print("  pip install -r requirements.txt")
    
    return all_ok

def check_directories():
    """Check required directories"""
    print("\n📁 Checking directories...")
    print("-" * 70)
    
    if os.path.exists('uploads'):
        print("✅ uploads/ directory exists")
        return True
    else:
        print("⚠️  uploads/ directory will be created on first run")
        return True

def check_gunicorn():
    """Check if gunicorn is installed"""
    print("\n🚀 Checking production server...")
    print("-" * 70)
    
    try:
        __import__('gunicorn')
        print("✅ Gunicorn is installed")
        return True
    except ImportError:
        print("⚠️  Gunicorn not installed (recommended for production)")
        print("   Install with: pip install gunicorn")
        return False

def generate_secret_key():
    """Generate a new secret key"""
    return secrets.token_hex(32)

def offer_fixes():
    """Offer to fix common issues"""
    print("\n" + "="*70)
    print("ISSUES FOUND - WOULD YOU LIKE TO FIX THEM?")
    print("="*70)
    
    if not os.path.exists('.env'):
        response = input("\nCreate .env from .env.production? (y/n): ")
        if response.lower() == 'y':
            if os.path.exists('.env.production'):
                with open('.env.production', 'r') as f:
                    content = f.read()
                with open('.env', 'w') as f:
                    f.write(content)
                print("✅ Created .env")
            else:
                print("❌ .env.production not found")
                return
    
    with open('.env', 'r') as f:
        lines = f.readlines()
    
    modified = False
    
    for i, line in enumerate(lines):
        if line.startswith('FLASK_DEBUG=True'):
            response = input("\nSet FLASK_DEBUG=False? (y/n): ")
            if response.lower() == 'y':
                lines[i] = 'FLASK_DEBUG=False\n'
                modified = True
        
        elif line.startswith('SECRET_KEY=') and not line.split('=')[1].strip():
            response = input("\nGenerate SECRET_KEY? (y/n): ")
            if response.lower() == 'y':
                key = generate_secret_key()
                lines[i] = f'SECRET_KEY={key}\n'
                modified = True
                print(f"✅ Generated SECRET_KEY: {key[:20]}...")
    
    if modified:
        with open('.env', 'w') as f:
            f.writelines(lines)
        print("\n✅ .env updated")

def print_production_command():
    """Print the production deployment command"""
    print("\n" + "="*70)
    print("PRODUCTION DEPLOYMENT COMMAND")
    print("="*70)
    print("\nRun with Gunicorn (recommended):")
    print("  gunicorn -w 4 -b 0.0.0.0:5000 --timeout 3600 app:app")
    print("\nOr with Flask (development only):")
    print("  python app.py")
    print()

def main():
    print("="*70)
    print("PRODUCTION READINESS CHECK")
    print("="*70)
    
    env_ok = check_env_file()
    deps_ok = check_dependencies()
    dirs_ok = check_directories()
    gunicorn_ok = check_gunicorn()
    
    print("\n" + "="*70)
    
    if env_ok and deps_ok and dirs_ok:
        print("✅ APPLICATION IS READY FOR PRODUCTION")
        if not gunicorn_ok:
            print("⚠️  Consider installing Gunicorn for production")
        print_production_command()
        print("\n📖 See PRODUCTION_CHECKLIST.md for complete deployment guide")
        return 0
    else:
        print("❌ ISSUES FOUND - NOT READY FOR PRODUCTION")
        
        if not env_ok:
            offer_fixes()
        
        if not deps_ok:
            print("\nInstall dependencies:")
            print("  pip install -r requirements.txt")
        
        print("\n📖 See PRODUCTION_CHECKLIST.md for complete checklist")
        return 1

if __name__ == '__main__':
    sys.exit(main())
