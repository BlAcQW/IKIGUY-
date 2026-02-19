"""
Deep scan of michsethowusu and financial_inclusion folders in Google Drive
"""

import os
import pickle
from pathlib import Path
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

def deep_scan_folder(service, folder_id, folder_path="", max_depth=4, current_depth=0, show_samples=True):
    """Recursively scan folder showing all structure"""
    
    if current_depth >= max_depth:
        return []
    
    all_files = []
    indent = "  " * current_depth
    
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
                    print(f"{indent}[DIR] {item['name']}/")
                    # Recursively scan subfolder
                    subfolder_files = deep_scan_folder(
                        service, item['id'], item_path, max_depth, current_depth + 1, show_samples
                    )
                    all_files.extend(subfolder_files)
                else:
                    # It's a file
                    size_mb = int(item.get('size', 0)) / (1024**2)
                    file_info = {
                        'path': item_path,
                        'name': item['name'],
                        'size': int(item.get('size', 0)),
                        'id': item['id']
                    }
                    all_files.append(file_info)
                    
                    # Show audio files
                    if any(item['name'].lower().endswith(ext) for ext in ['.mp3', '.wav', '.flac', '.ogg', '.m4a']):
                        print(f"{indent}  [AUDIO] {item['name']} ({size_mb:.1f} MB)")
                    elif show_samples and current_depth > 0:  # Show other files at deeper levels
                        if item['name'].lower().endswith(('.txt', '.csv', '.json')):
                            print(f"{indent}  [TEXT] {item['name']}")
            
            page_token = results.get('nextPageToken')
            if not page_token:
                break
                
    except HttpError as error:
        print(f"{indent}Error scanning: {error}")
    
    return all_files

def main():
    print("="*60)
    print("DEEP SCAN: MICHSETHOWUSU & FINANCIAL INCLUSION")
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
        q=f"'{base_folder_id}' in parents and name='raw'",
        spaces='drive',
        fields='files(id, name)'
    ).execute()
    
    raw_folders = results.get('files', [])
    if not raw_folders:
        print("[ERROR] No raw folder found")
        return
    
    raw_folder_id = raw_folders[0]['id']
    
    # 1. CHECK MICHSETHOWUSU
    print("\n" + "="*60)
    print("1. MICHSETHOWUSU FOLDER STRUCTURE")
    print("="*60)
    
    results = service.files().list(
        q=f"'{raw_folder_id}' in parents and name='michsethowusu'",
        spaces='drive',
        fields='files(id, name)'
    ).execute()
    
    michset_folders = results.get('files', [])
    if michset_folders:
        michset_id = michset_folders[0]['id']
        print("\nScanning michsethowusu/")
        michset_files = deep_scan_folder(service, michset_id, "michsethowusu", max_depth=4)
        
        # Count audio files
        audio_files = [f for f in michset_files if any(f['name'].lower().endswith(ext) 
                      for ext in ['.mp3', '.wav', '.flac', '.ogg', '.m4a'])]
        text_files = [f for f in michset_files if any(f['name'].lower().endswith(ext)
                     for ext in ['.txt', '.csv', '.tsv', '.json'])]
        
        print(f"\nMICHSETHOWUSU SUMMARY:")
        print(f"  Total files: {len(michset_files)}")
        print(f"  Audio files: {len(audio_files)}")
        print(f"  Text files: {len(text_files)}")
        
        if audio_files:
            print(f"\n  Sample audio paths:")
            for f in audio_files[:5]:
                print(f"    {f['path']} ({f['size'] / (1024**2):.1f} MB)")
    else:
        print("michsethowusu folder not found")
    
    # 2. CHECK FINANCIAL INCLUSION
    print("\n" + "="*60)
    print("2. FINANCIAL INCLUSION FOLDER STRUCTURE")
    print("="*60)
    
    results = service.files().list(
        q=f"'{raw_folder_id}' in parents and name='financial_inclusion'",
        spaces='drive',
        fields='files(id, name)'
    ).execute()
    
    fi_folders = results.get('files', [])
    if fi_folders:
        fi_id = fi_folders[0]['id']
        print("\nScanning financial_inclusion/")
        fi_files = deep_scan_folder(service, fi_id, "financial_inclusion", max_depth=4)
        
        # Count audio files
        audio_files = [f for f in fi_files if any(f['name'].lower().endswith(ext) 
                      for ext in ['.mp3', '.wav', '.flac', '.ogg', '.m4a'])]
        text_files = [f for f in fi_files if any(f['name'].lower().endswith(ext)
                     for ext in ['.txt', '.csv', '.tsv', '.json'])]
        
        print(f"\nFINANCIAL INCLUSION SUMMARY:")
        print(f"  Total files: {len(fi_files)}")
        print(f"  Audio files: {len(audio_files)}")
        print(f"  Text files: {len(text_files)}")
        
        if audio_files:
            print(f"\n  Sample audio paths:")
            for f in audio_files[:5]:
                print(f"    {f['path']} ({f['size'] / (1024**2):.1f} MB)")
    else:
        print("financial_inclusion folder not found")
    
    # 3. RECOMMENDATIONS
    print("\n" + "="*60)
    print("RECOMMENDATIONS")
    print("="*60)
    
    print("\nBased on the scan above:")
    print("1. If audio files are found, note their exact paths")
    print("2. The notebook may need to be updated to look in the correct subfolders")
    print("3. If no audio files found, the data may need to be:")
    print("   - Extracted from archives")
    print("   - Downloaded and uploaded")
    print("   - Moved to the correct location")

if __name__ == "__main__":
    main()