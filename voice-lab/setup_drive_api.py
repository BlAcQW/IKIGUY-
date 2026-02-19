#!/usr/bin/env python3
"""
Setup script for Google Drive API integration
"""

import subprocess
import sys
from pathlib import Path
import json

def install_requirements():
    """Install required packages"""
    print("📦 Installing required packages...")
    
    requirements_file = Path(__file__).parent / 'requirements_drive_api.txt'
    
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)
        ])
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}")
        return False

def create_credentials_template():
    """Create template credentials.json structure"""
    credentials_dir = Path('./credentials')
    credentials_dir.mkdir(exist_ok=True)
    
    template_path = credentials_dir / 'credentials_template.json'
    
    template = {
        "installed": {
            "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
            "project_id": "your-project-id", 
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": "YOUR_CLIENT_SECRET",
            "redirect_uris": ["http://localhost"]
        }
    }
    
    with open(template_path, 'w') as f:
        json.dump(template, f, indent=2)
    
    print(f"📋 Credentials template created: {template_path}")
    return template_path

def print_setup_instructions():
    """Print detailed setup instructions"""
    print(f"\n{'='*60}")
    print(f"🚀 GOOGLE DRIVE API SETUP COMPLETE")
    print(f"{'='*60}")
    
    print(f"\n📋 Next Steps:")
    print(f"\n1. 🌐 Enable Google Drive API:")
    print(f"   • Go to: https://console.cloud.google.com/")
    print(f"   • Create a new project or select existing")
    print(f"   • Go to 'APIs & Services' > 'Library'")
    print(f"   • Search for 'Google Drive API'")
    print(f"   • Click 'Enable'")
    
    print(f"\n2. 🔐 Create OAuth Credentials:")
    print(f"   • Go to 'APIs & Services' > 'Credentials'")
    print(f"   • Click 'Create Credentials' > 'OAuth 2.0 Client ID'")
    print(f"   • Application type: 'Desktop application'")
    print(f"   • Name: 'Voice Lab Data Manager'")
    print(f"   • Click 'Create'")
    
    print(f"\n3. 📁 Download and Setup Credentials:")
    print(f"   • Click 'Download JSON' for your OAuth client")
    print(f"   • Rename the file to 'credentials.json'")
    print(f"   • Place it in: ./credentials/credentials.json")
    
    print(f"\n4. 🏃‍♂️ Run the Data Manager:")
    print(f"   python local_drive_api_manager.py")
    
    print(f"\n📧 Account: alfred.anyan@gmail.com")
    print(f"📁 Expected Google Drive path: /voice-lab-data/")
    
    print(f"\n⚠️  Important Notes:")
    print(f"   • First run will open browser for OAuth authorization")
    print(f"   • Grant permissions to access your Google Drive")
    print(f"   • Credentials will be saved for future runs")
    
    print(f"\n🔒 Security:")
    print(f"   • Your credentials stay on your local machine")
    print(f"   • No data is stored externally")
    print(f"   • You can revoke access anytime in Google Account settings")

def main():
    """Main setup function"""
    print("🚀 Setting up Google Drive API for Voice Lab...")
    
    # Install requirements
    if not install_requirements():
        print("❌ Setup failed due to package installation issues")
        return False
    
    # Create credentials template
    template_path = create_credentials_template()
    
    # Print setup instructions
    print_setup_instructions()
    
    print(f"\n✅ Setup script completed!")
    print(f"📋 Follow the instructions above to complete the setup")
    
    return True

if __name__ == "__main__":
    main()