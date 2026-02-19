"""
Recursively scan Google Drive folders for audio files
"""

import os
import pickle
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from collections import defaultdict

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

def scan_folder_recursive(service, folder_id, folder_path="", max_depth=5, current_depth=0):
    """Recursively scan folder for all files"""
    
    if current_depth >= max_depth:
        return []
    
    all_files = []
    
    try:
        # Get all items in current folder
        page_token = None
        while True:
            results = service.files().list(
                q=f"'{folder_id}' in parents",
                spaces='drive',
                fields='nextPageToken, files(id, name, mimeType, size)',
                pageSize=1000,
                pageToken=page_token
            ).execute()
            
            items = results.get('files', [])
            
            for item in items:
                item_path = f"{folder_path}/{item['name']}" if folder_path else item['name']
                
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    # Recursively scan subfolder
                    subfolder_files = scan_folder_recursive(
                        service, item['id'], item_path, max_depth, current_depth + 1
                    )
                    all_files.extend(subfolder_files)
                else:
                    # Add file info
                    all_files.append({
                        'path': item_path,
                        'name': item['name'],
                        'size': int(item.get('size', 0)),
                        'id': item['id']
                    })
            
            page_token = results.get('nextPageToken')
            if not page_token:
                break
                
    except HttpError as error:
        print(f"Error scanning {folder_path}: {error}")
    
    return all_files

def main():
    print("="*60)
    print("RECURSIVE GOOGLE DRIVE SCAN FOR AUDIO FILES")
    print("="*60)
    
    service = get_service()
    
    # Find voice-lab-data folder
    results = service.files().list(
        q="name='voice-lab-data' and mimeType='application/vnd.google-apps.folder'",
        spaces='drive',
        fields='files(id, name)'
    ).execute()
    
    folders = results.get('files', [])
    if not folders:
        print("[ERROR] voice-lab-data folder not found")
        return
    
    base_folder_id = folders[0]['id']
    
    # Find raw folder
    results = service.files().list(
        q=f"'{base_folder_id}' in parents and name='raw' and mimeType='application/vnd.google-apps.folder'",
        spaces='drive',
        fields='files(id, name)'
    ).execute()
    
    raw_folders = results.get('files', [])
    if not raw_folders:
        print("[ERROR] No raw folder found")
        return
    
    raw_folder_id = raw_folders[0]['id']
    
    # Get all datasets in raw folder
    results = service.files().list(
        q=f"'{raw_folder_id}' in parents and mimeType='application/vnd.google-apps.folder'",
        spaces='drive',
        fields='files(id, name)'
    ).execute()
    
    datasets = results.get('files', [])
    
    print(f"\n[INFO] Scanning {len(datasets)} datasets recursively...")
    print("="*60)
    
    audio_extensions = {'.mp3', '.wav', '.flac', '.m4a', '.ogg', '.opus', '.aac', '.mp4', '.webm'}
    text_extensions = {'.txt', '.csv', '.tsv', '.json', '.xml'}
    
    total_audio = 0
    total_text = 0
    total_size = 0
    
    # Scan each dataset
    for dataset in datasets:
        print(f"\n[SCANNING] {dataset['name']}...")
        
        files = scan_folder_recursive(service, dataset['id'], dataset['name'], max_depth=5)
        
        audio_files = []
        text_files = []
        other_files = []
        dataset_size = 0
        
        for f in files:
            ext = Path(f['name']).suffix.lower()
            dataset_size += f['size']
            
            if ext in audio_extensions:
                audio_files.append(f)
                total_audio += 1
            elif ext in text_extensions:
                text_files.append(f)
                total_text += 1
            else:
                other_files.append(f)
        
        total_size += dataset_size
        
        print(f"  Total files found: {len(files)}")
        print(f"  Audio files: {len(audio_files)}")
        print(f"  Text files: {len(text_files)}")
        print(f"  Other files: {len(other_files)}")
        print(f"  Total size: {dataset_size / (1024**3):.2f} GB")
        
        # Show sample audio files
        if audio_files:
            print(f"  Sample audio files:")
            for f in audio_files[:3]:
                print(f"    - {f['path']} ({f['size'] / (1024**2):.1f} MB)")
        
        # Show sample text files
        if text_files:
            print(f"  Sample text files:")
            for f in text_files[:3]:
                print(f"    - {f['path']}")
        
        # Show directory structure
        if files:
            dirs = set()
            for f in files:
                parts = f['path'].split('/')
                if len(parts) > 1:
                    dirs.add('/'.join(parts[:-1]))
            
            if dirs:
                print(f"  Subdirectories found:")
                for d in sorted(list(dirs))[:5]:
                    print(f"    - {d}/")
    
    # Final summary
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    print(f"Total audio files found: {total_audio:,}")
    print(f"Total text files found: {total_text:,}")
    print(f"Total size: {total_size / (1024**3):.2f} GB")
    
    if total_audio == 0:
        print("\n[CRITICAL] No audio files found!")
        print("\nPossible reasons:")
        print("1. Audio files are in Google Drive shortcuts (not actual files)")
        print("2. Files need to be downloaded/extracted first")
        print("3. Data was not properly uploaded to Google Drive")
        print("\nSolution:")
        print("1. Upload actual audio files (not shortcuts) to Google Drive")
        print("2. Or download datasets locally and upload to Drive")
        print("3. Ensure files are in supported formats (.mp3, .wav, etc.)")
    elif total_audio < 1000:
        print("\n[WARNING] Insufficient audio files for training")
        print(f"Found: {total_audio} files")
        print("Recommended: 1,000+ files minimum")
    else:
        print("\n[OK] Sufficient audio files for training!")
        print("You can now run the processing notebook")

if __name__ == "__main__":
    main()