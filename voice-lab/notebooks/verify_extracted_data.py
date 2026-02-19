"""
Verify extracted audio data in Google Drive
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

def check_extracted_folders(service):
    """Check the extracted BibleTTS folders for audio files"""
    
    print("="*60)
    print("CHECKING EXTRACTED AUDIO DATA")
    print("="*60)
    
    # Navigate to bibletts folder
    results = service.files().list(
        q="name='voice-lab-data' and mimeType='application/vnd.google-apps.folder'",
        spaces='drive',
        fields='files(id, name)'
    ).execute()
    
    base_folder = results.get('files', [])[0]
    
    results = service.files().list(
        q=f"'{base_folder['id']}' in parents and name='raw'",
        spaces='drive',
        fields='files(id)'
    ).execute()
    
    raw_folder = results.get('files', [])[0]
    
    results = service.files().list(
        q=f"'{raw_folder['id']}' in parents and name='bibletts'",
        spaces='drive',
        fields='files(id)'
    ).execute()
    
    bibletts_folder = results.get('files', [])[0]
    
    # Check for extracted folders
    extracted_folders = ['akuapem-twi', 'asante-twi']
    
    for folder_name in extracted_folders:
        print(f"\n[CHECKING] {folder_name}/")
        
        # Find the folder
        results = service.files().list(
            q=f"'{bibletts_folder['id']}' in parents and name='{folder_name}'",
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        folders = results.get('files', [])
        
        if not folders:
            print(f"  [WARNING] {folder_name} folder not found")
            continue
        
        folder_id = folders[0]['id']
        
        # Count audio files recursively
        audio_count = 0
        text_count = 0
        total_size = 0
        sample_files = []
        
        def scan_folder(fid, depth=0, max_depth=3):
            nonlocal audio_count, text_count, total_size, sample_files
            
            if depth > max_depth:
                return
            
            try:
                page_token = None
                while True:
                    results = service.files().list(
                        q=f"'{fid}' in parents",
                        spaces='drive',
                        fields='nextPageToken, files(id, name, mimeType, size)',
                        pageSize=1000,
                        pageToken=page_token
                    ).execute()
                    
                    items = results.get('files', [])
                    
                    for item in items:
                        if item['mimeType'] == 'application/vnd.google-apps.folder':
                            scan_folder(item['id'], depth + 1, max_depth)
                        else:
                            name = item['name'].lower()
                            size = int(item.get('size', 0))
                            
                            if name.endswith(('.mp3', '.wav', '.flac', '.m4a', '.ogg')):
                                audio_count += 1
                                total_size += size
                                if len(sample_files) < 5:
                                    sample_files.append((item['name'], size))
                            elif name.endswith(('.txt', '.csv', '.tsv', '.json')):
                                text_count += 1
                    
                    page_token = results.get('nextPageToken')
                    if not page_token:
                        break
                        
            except HttpError as e:
                print(f"    Error scanning: {e}")
        
        # Scan the folder
        scan_folder(folder_id)
        
        print(f"  [OK] Found {audio_count:,} audio files")
        print(f"  [OK] Found {text_count:,} text/metadata files")
        print(f"  [OK] Total size: {total_size / (1024**3):.2f} GB")
        
        if sample_files:
            print(f"  Sample audio files:")
            for name, size in sample_files:
                print(f"    - {name} ({size / (1024**2):.1f} MB)")

def check_all_datasets(service):
    """Check all datasets in raw folder for audio content"""
    
    print("\n" + "="*60)
    print("CHECKING ALL RAW DATASETS")
    print("="*60)
    
    # Get to raw folder
    results = service.files().list(
        q="name='voice-lab-data' and mimeType='application/vnd.google-apps.folder'",
        spaces='drive',
        fields='files(id)'
    ).execute()
    base = results.get('files', [])[0]
    
    results = service.files().list(
        q=f"'{base['id']}' in parents and name='raw'",
        spaces='drive',
        fields='files(id)'
    ).execute()
    raw = results.get('files', [])[0]
    
    # Get all dataset folders
    results = service.files().list(
        q=f"'{raw['id']}' in parents and mimeType='application/vnd.google-apps.folder'",
        spaces='drive',
        fields='files(id, name)',
        pageSize=20
    ).execute()
    
    datasets = results.get('files', [])
    
    total_audio_files = 0
    datasets_with_audio = []
    
    for dataset in datasets:
        # Quick check for audio files (first level only for speed)
        results = service.files().list(
            q=f"'{dataset['id']}' in parents",
            spaces='drive',
            fields='files(name, mimeType)',
            pageSize=100
        ).execute()
        
        items = results.get('files', [])
        
        # Check for audio files or promising subfolders
        audio_files = [f for f in items if any(f['name'].lower().endswith(ext) 
                      for ext in ['.mp3', '.wav', '.flac', '.m4a'])]
        
        audio_folders = [f for f in items if f['mimeType'] == 'application/vnd.google-apps.folder' 
                        and any(keyword in f['name'].lower() 
                        for keyword in ['audio', 'wav', 'mp3', 'clips', 'recordings', 'twi', 'asante', 'akuapem'])]
        
        if audio_files:
            print(f"\n[OK] {dataset['name']}: Found {len(audio_files)} audio files (first level)")
            total_audio_files += len(audio_files)
            datasets_with_audio.append(dataset['name'])
        elif audio_folders:
            print(f"\n[INFO] {dataset['name']}: Has {len(audio_folders)} potential audio subfolders:")
            for folder in audio_folders[:3]:
                print(f"    - {folder['name']}/")
            datasets_with_audio.append(dataset['name'] + " (subfolders)")
        else:
            print(f"\n[EMPTY] {dataset['name']}: No obvious audio content")
    
    return total_audio_files, datasets_with_audio

def main():
    print("="*60)
    print("GOOGLE DRIVE EXTRACTED DATA VERIFICATION")
    print("="*60)
    
    service = get_service()
    
    # Check BibleTTS extracted folders
    check_extracted_folders(service)
    
    # Check all datasets
    total_files, datasets_with_audio = check_all_datasets(service)
    
    # Final summary
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    
    print(f"\nDatasets with audio content: {len(datasets_with_audio)}")
    for ds in datasets_with_audio:
        print(f"  - {ds}")
    
    print("\n[PROCESSING READINESS CHECK]")
    
    if 'bibletts' in ' '.join(datasets_with_audio).lower() or total_files > 0:
        print("[OK] Audio data is available for processing!")
        print("\nNext steps:")
        print("1. Open Google Colab")
        print("2. Upload/open: 002_phase1_data_processing_enhanced.ipynb")
        print("3. Mount Google Drive:")
        print("   from google.colab import drive")
        print("   drive.mount('/content/drive')")
        print("4. Run all cells in the notebook")
        print("5. The notebook should now find and process:")
        print("   - BibleTTS akuapem-twi audio files")
        print("   - BibleTTS asante-twi audio files")
        print("   - Any other available datasets")
        print("\n[IMPORTANT] Make sure the notebook paths match:")
        print("   BASE_DIR = Path('/content/drive/MyDrive/voice-lab-data')")
        print("   The 'MyDrive' part might need adjustment based on your setup")
    else:
        print("[WARNING] Limited audio data found")
        print("You may need to:")
        print("1. Extract more compressed archives")
        print("2. Upload more audio datasets")
        print("3. Check folder permissions")

if __name__ == "__main__":
    main()