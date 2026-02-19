"""
Check what files are in the MichSetHowusu Fante folder
"""

import os
import pickle
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_service():
    """Get authenticated Drive service"""
    creds = None
    
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    
    return build('drive', 'v3', credentials=creds)

def check_michset_fante_train():
    """Check files in michsethowusu/fante_multispeaker_audio_transcribed/train"""
    
    service = get_service()
    
    # Navigate to the specific folder
    # Path: voice-lab-data/raw/michsethowusu/fante_multispeaker_audio_transcribed/train
    
    # First find voice-lab-data
    results = service.files().list(
        q="name='voice-lab-data' and mimeType='application/vnd.google-apps.folder'",
        spaces='drive',
        fields='files(id, name)'
    ).execute()
    
    if not results.get('files'):
        print("voice-lab-data not found")
        return
    
    base_id = results['files'][0]['id']
    
    # Navigate through the path
    path_parts = ['raw', 'michsethowusu', 'fante_multispeaker_audio_transcribed', 'train']
    current_id = base_id
    current_path = "voice-lab-data"
    
    for part in path_parts:
        results = service.files().list(
            q=f"'{current_id}' in parents and name='{part}'",
            spaces='drive',
            fields='files(id, name, mimeType)'
        ).execute()
        
        if not results.get('files'):
            print(f"Folder not found: {current_path}/{part}")
            return
        
        current_id = results['files'][0]['id']
        current_path = f"{current_path}/{part}"
    
    print(f"Found folder: {current_path}")
    print("=" * 60)
    
    # List all files in the train folder
    page_token = None
    all_files = []
    
    while True:
        results = service.files().list(
            q=f"'{current_id}' in parents",
            spaces='drive',
            fields='nextPageToken, files(id, name, mimeType, size)',
            pageSize=1000,
            pageToken=page_token
        ).execute()
        
        files = results.get('files', [])
        all_files.extend(files)
        
        page_token = results.get('nextPageToken')
        if not page_token:
            break
    
    print(f"Total files in train folder: {len(all_files)}")
    
    # Categorize files
    file_types = {}
    for file in all_files:
        if file['mimeType'] == 'application/vnd.google-apps.folder':
            continue
        
        ext = file['name'].split('.')[-1].lower() if '.' in file['name'] else 'no_extension'
        if ext not in file_types:
            file_types[ext] = []
        file_types[ext].append(file)
    
    print("\nFile types found:")
    for ext, files in sorted(file_types.items()):
        total_size = sum(int(f.get('size', 0)) for f in files) / (1024**2)  # MB
        print(f"  .{ext}: {len(files)} files ({total_size:.2f} MB)")
    
    # Show sample files
    print("\nSample files:")
    for file in all_files[:10]:
        if file['mimeType'] != 'application/vnd.google-apps.folder':
            size_kb = int(file.get('size', 0)) / 1024
            print(f"  - {file['name']} ({size_kb:.1f} KB)")
    
    # Check other MichSetHowusu folders
    print("\n" + "=" * 60)
    print("OTHER MICHSETHOWUSU FOLDERS:")
    
    # Go back to michsethowusu folder
    results = service.files().list(
        q="name='michsethowusu' and mimeType='application/vnd.google-apps.folder'",
        spaces='drive',
        fields='files(id)'
    ).execute()
    
    if results.get('files'):
        michset_id = results['files'][0]['id']
        
        results = service.files().list(
            q=f"'{michset_id}' in parents and mimeType='application/vnd.google-apps.folder'",
            spaces='drive',
            fields='files(name)',
            pageSize=20
        ).execute()
        
        folders = results.get('files', [])
        print(f"Found {len(folders)} folders in michsethowusu:")
        for folder in folders:
            print(f"  - {folder['name']}/")

if __name__ == "__main__":
    check_michset_fante_train()