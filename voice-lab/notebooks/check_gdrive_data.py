"""
Script to connect to Google Drive and check raw data directories
Requires: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
"""

import os
import json
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle

# If modifying these scopes, delete the token file.
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def authenticate_google_drive():
    """Authenticate and return Google Drive service"""
    creds = None
    token_file = 'token.pickle'
    
    # Check for existing token
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Look for credentials.json in multiple locations
            cred_paths = [
                'credentials.json',
                '../credentials.json', 
                'google_credentials.json',
                '../google_credentials.json',
                os.path.expanduser('~/credentials.json')
            ]
            
            cred_file = None
            for path in cred_paths:
                if os.path.exists(path):
                    cred_file = path
                    print(f"Found credentials at: {path}")
                    break
            
            if not cred_file:
                print("[ERROR] No Google credentials file found!")
                print("\nTo connect to Google Drive, you need to:")
                print("1. Go to https://console.cloud.google.com/")
                print("2. Create a new project or select existing")
                print("3. Enable Google Drive API")
                print("4. Create credentials (OAuth 2.0 Client ID)")
                print("5. Download credentials as 'credentials.json'")
                print("6. Place it in this directory")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file(cred_file, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)
    
    return build('drive', 'v3', credentials=creds)

def find_voice_lab_folder(service):
    """Find the voice-lab-data folder in Google Drive"""
    try:
        # Search for voice-lab-data folder
        results = service.files().list(
            q="name='voice-lab-data' and mimeType='application/vnd.google-apps.folder'",
            spaces='drive',
            fields='files(id, name, parents)'
        ).execute()
        
        items = results.get('files', [])
        
        if not items:
            print('[WARNING] No voice-lab-data folder found in Google Drive')
            return None
        
        folder_id = items[0]['id']
        print(f"[OK] Found voice-lab-data folder: {items[0]['name']} (ID: {folder_id})")
        return folder_id
        
    except HttpError as error:
        print(f'[ERROR] An error occurred: {error}')
        return None

def list_folder_contents(service, folder_id, folder_name="", max_depth=3, current_depth=0):
    """Recursively list contents of a folder"""
    if current_depth >= max_depth:
        return
    
    try:
        # List all items in the folder
        results = service.files().list(
            q=f"'{folder_id}' in parents",
            spaces='drive',
            fields='files(id, name, mimeType, size)',
            pageSize=1000
        ).execute()
        
        items = results.get('files', [])
        
        if not items:
            print(f"{'  ' * current_depth}  (empty)")
            return
        
        # Separate folders and files
        folders = [item for item in items if item['mimeType'] == 'application/vnd.google-apps.folder']
        files = [item for item in items if item['mimeType'] != 'application/vnd.google-apps.folder']
        
        # Display folders first
        for folder in folders:
            print(f"{'  ' * current_depth}[DIR] {folder['name']}/")
            
            # Recursively list subfolder contents for important directories
            if current_depth < max_depth - 1 and folder['name'] in ['raw', 'processed', 'metadata']:
                list_folder_contents(service, folder['id'], folder['name'], max_depth, current_depth + 1)
        
        # Display file count summary for each file type
        if files:
            file_types = {}
            total_size = 0
            for file in files:
                ext = Path(file['name']).suffix.lower()
                if ext not in file_types:
                    file_types[ext] = {'count': 0, 'size': 0}
                file_types[ext]['count'] += 1
                file_types[ext]['size'] += int(file.get('size', 0))
                total_size += int(file.get('size', 0))
            
            for ext, info in sorted(file_types.items()):
                size_mb = info['size'] / (1024 * 1024)
                print(f"{'  ' * current_depth}  {info['count']} {ext} files ({size_mb:.1f} MB)")
                
    except HttpError as error:
        print(f'[ERROR] An error occurred: {error}')

def check_raw_datasets(service, parent_folder_id):
    """Check specifically for raw dataset directories"""
    print("\n" + "="*60)
    print("CHECKING RAW DATASETS")
    print("="*60)
    
    try:
        # First find the raw folder
        results = service.files().list(
            q=f"'{parent_folder_id}' in parents and name='raw' and mimeType='application/vnd.google-apps.folder'",
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        raw_folders = results.get('files', [])
        
        if not raw_folders:
            print("[ERROR] No 'raw' folder found in voice-lab-data")
            return
        
        raw_folder_id = raw_folders[0]['id']
        print(f"[OK] Found raw data folder")
        
        # Expected datasets
        expected_datasets = [
            'common_voice_twi',
            'african_whisper',
            'afrispeech_200',
            'lingua_libre',
            'jw300',
            'bibletis',
            'financial_inclusion',
            'michsethowusu'
        ]
        
        # List all datasets in raw folder
        results = service.files().list(
            q=f"'{raw_folder_id}' in parents",
            spaces='drive',
            fields='files(id, name, mimeType, size)',
            pageSize=1000
        ).execute()
        
        items = results.get('files', [])
        
        print(f"\nDatasets found in /raw directory:")
        found_datasets = []
        
        for item in items:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                found_datasets.append(item['name'])
                
                # Count files in each dataset folder
                dataset_results = service.files().list(
                    q=f"'{item['id']}' in parents",
                    spaces='drive',
                    fields='files(id, size)',
                    pageSize=1000
                ).execute()
                
                dataset_files = dataset_results.get('files', [])
                total_size = sum(int(f.get('size', 0)) for f in dataset_files) / (1024*1024*1024)  # GB
                
                status = "[OK]" if item['name'].lower() in [d.lower() for d in expected_datasets] else "[UNKNOWN]"
                print(f"  {status} {item['name']}: {len(dataset_files)} files ({total_size:.2f} GB)")
        
        print(f"\nDataset availability summary:")
        for dataset in expected_datasets:
            if dataset.lower() in [d.lower() for d in found_datasets]:
                print(f"  [OK] {dataset}")
            else:
                print(f"  [MISSING] {dataset}")
                
        print(f"\nTotal datasets found: {len(found_datasets)}/{len(expected_datasets)}")
        
        if len(found_datasets) >= 5:
            print("\n[OK] Sufficient datasets available for processing!")
            print("     Ready to run the processing notebook on Google Colab")
        else:
            print("\n[WARNING] Some datasets may be missing")
            print("          You may need to upload more data before processing")
            
    except HttpError as error:
        print(f'[ERROR] An error occurred: {error}')

def main():
    print("="*60)
    print("GOOGLE DRIVE DATA VERIFICATION")
    print("="*60)
    
    # Authenticate
    print("\nAuthenticating with Google Drive...")
    service = authenticate_google_drive()
    
    if not service:
        print("\n[ERROR] Failed to authenticate with Google Drive")
        print("\nAlternative: Use Google Colab directly")
        print("1. Open Google Colab")
        print("2. Mount drive with: from google.colab import drive; drive.mount('/content/drive')")
        print("3. Navigate to: /content/drive/MyDrive/voice-lab-data/")
        print("4. Check the raw/ directory for datasets")
        return
    
    # Find voice-lab-data folder
    folder_id = find_voice_lab_folder(service)
    
    if not folder_id:
        print("\n[ERROR] voice-lab-data folder not found in Google Drive")
        print("        Please ensure the folder exists in your Google Drive")
        return
    
    # List folder structure
    print("\n" + "="*60)
    print("FOLDER STRUCTURE")
    print("="*60)
    print("\nvoice-lab-data/")
    list_folder_contents(service, folder_id, "voice-lab-data", max_depth=2, current_depth=1)
    
    # Check raw datasets specifically
    check_raw_datasets(service, folder_id)
    
    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    print("1. If datasets are available, run the processing notebook on Google Colab")
    print("2. Ensure Google Drive is mounted in Colab")
    print("3. Run all cells in the notebook")
    print("4. Check for success messages and processed file counts")

if __name__ == "__main__":
    main()