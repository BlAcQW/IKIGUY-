#!/usr/bin/env python3
"""
Upload Local Voice Lab Files to Google Drive
Pushes processed datasets and notebooks to Google Drive for backup and sharing
"""

import json
import os
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from tqdm import tqdm
from typing import Dict, List, Optional
import mimetypes

class GoogleDriveUploader:
    """Upload local files to Google Drive with folder structure preservation"""
    
    def __init__(self, service_account_path: str = "./credentials/service_account.json"):
        self.service_account_path = service_account_path
        self.service = None
        self.setup_drive_connection()
        
        # Track uploaded files to avoid duplicates
        self.uploaded_files = {}
        
    def setup_drive_connection(self):
        """Setup Google Drive connection"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_path,
                scopes=['https://www.googleapis.com/auth/drive']
            )
            self.service = build('drive', 'v3', credentials=credentials)
            print("✅ Google Drive connection established")
        except Exception as e:
            print(f"❌ Could not connect to Google Drive: {e}")
            raise
    
    def create_folder(self, folder_name: str, parent_id: str = None) -> str:
        """Create folder in Google Drive"""
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        if parent_id:
            file_metadata['parents'] = [parent_id]
        
        # Check if folder already exists
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        
        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        existing_folders = results.get('files', [])
        
        if existing_folders:
            print(f"📁 Folder '{folder_name}' already exists")
            return existing_folders[0]['id']
        
        folder = self.service.files().create(body=file_metadata, fields='id').execute()
        folder_id = folder.get('id')
        print(f"📁 Created folder: {folder_name} ({folder_id})")
        return folder_id
    
    def upload_file(self, local_path: Path, drive_folder_id: str, 
                   drive_filename: str = None) -> Optional[str]:
        """Upload single file to Google Drive"""
        try:
            if not local_path.exists():
                print(f"❌ File not found: {local_path}")
                return None
            
            filename = drive_filename or local_path.name
            
            # Check if file already exists
            query = f"name='{filename}' and '{drive_folder_id}' in parents and trashed=false"
            results = self.service.files().list(q=query, fields="files(id, name)").execute()
            existing_files = results.get('files', [])
            
            if existing_files:
                print(f"📄 File '{filename}' already exists, skipping...")
                return existing_files[0]['id']
            
            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(str(local_path))
            if not mime_type:
                mime_type = 'application/octet-stream'
            
            file_metadata = {
                'name': filename,
                'parents': [drive_folder_id]
            }
            
            media = MediaFileUpload(str(local_path), mimetype=mime_type, resumable=True)
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            file_id = file.get('id')
            size_mb = local_path.stat().st_size / (1024*1024)
            print(f"✅ Uploaded: {filename} ({size_mb:.1f}MB) -> {file_id}")
            return file_id
            
        except Exception as e:
            print(f"❌ Error uploading {local_path}: {e}")
            return None
    
    def upload_directory(self, local_dir: Path, drive_parent_id: str, 
                        exclude_patterns: List[str] = None) -> Dict:
        """Upload entire directory structure to Google Drive"""
        if exclude_patterns is None:
            exclude_patterns = [
                '__pycache__',
                '.git', 
                '.DS_Store',
                '*.pyc',
                'node_modules',
                '.env'
            ]
        
        print(f"📂 Uploading directory: {local_dir}")
        
        # Create main folder
        folder_id = self.create_folder(local_dir.name, drive_parent_id)
        
        uploaded_files = []
        skipped_files = []
        errors = []
        
        # Get all files recursively
        all_files = []
        for root, dirs, files in os.walk(local_dir):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if not any(
                d.startswith(pattern.rstrip('*')) for pattern in exclude_patterns
            )]
            
            for file in files:
                file_path = Path(root) / file
                
                # Check exclusion patterns
                should_skip = False
                for pattern in exclude_patterns:
                    if pattern.endswith('*'):
                        if file.endswith(pattern[:-1]):
                            should_skip = True
                            break
                    elif pattern in str(file_path):
                        should_skip = True
                        break
                
                if not should_skip:
                    all_files.append(file_path)
                else:
                    skipped_files.append(file_path)
        
        print(f"📊 Found {len(all_files)} files to upload ({len(skipped_files)} skipped)")
        
        # Upload files with progress bar
        with tqdm(total=len(all_files), desc="Uploading") as pbar:
            for file_path in all_files:
                try:
                    # Create nested folder structure if needed
                    relative_path = file_path.relative_to(local_dir)
                    current_folder_id = folder_id
                    
                    # Create nested folders
                    if relative_path.parent != Path('.'):
                        folder_parts = relative_path.parent.parts
                        for folder_name in folder_parts:
                            current_folder_id = self.create_folder(folder_name, current_folder_id)
                    
                    # Upload file
                    file_id = self.upload_file(file_path, current_folder_id)
                    
                    if file_id:
                        uploaded_files.append({
                            'local_path': str(file_path),
                            'drive_id': file_id,
                            'relative_path': str(relative_path)
                        })
                    else:
                        errors.append(str(file_path))
                        
                except Exception as e:
                    errors.append(f"{file_path}: {e}")
                    
                pbar.update(1)
        
        return {
            'folder_id': folder_id,
            'uploaded_files': uploaded_files,
            'skipped_files': [str(f) for f in skipped_files],
            'errors': errors
        }
    
    def create_voice_lab_structure(self) -> Dict[str, str]:
        """Create the main voice-lab folder structure in Google Drive"""
        print("🏗️ Creating voice-lab folder structure...")
        
        # Create main voice-lab folder
        voice_lab_id = self.create_folder("voice-lab-data")
        
        # Create subfolders
        structure = {
            'voice_lab_root': voice_lab_id,
            'raw': self.create_folder('raw', voice_lab_id),
            'processed': self.create_folder('processed', voice_lab_id),
            'notebooks': self.create_folder('notebooks', voice_lab_id),
            'models': self.create_folder('models', voice_lab_id),
            'scripts': self.create_folder('scripts', voice_lab_id),
            'metadata': self.create_folder('metadata', voice_lab_id),
            'splits': self.create_folder('splits', voice_lab_id)
        }
        
        # Save structure for reference
        with open('./drive_structure.json', 'w') as f:
            json.dump(structure, f, indent=2)
        
        print("✅ Voice-lab structure created and saved to drive_structure.json")
        return structure

def main():
    """Upload voice lab files to Google Drive"""
    print("🚀 UPLOADING VOICE LAB FILES TO GOOGLE DRIVE")
    print("=" * 60)
    
    uploader = GoogleDriveUploader()
    
    # Create folder structure
    structure = uploader.create_voice_lab_structure()
    
    # Define what to upload
    upload_tasks = [
        {
            'local_path': Path('./notebooks'),
            'drive_folder_id': structure['notebooks'],
            'description': 'Jupyter notebooks'
        },
        {
            'local_path': Path('./data/processed'),
            'drive_folder_id': structure['processed'],
            'description': 'Processed datasets'
        },
        {
            'local_path': Path('./data/raw/common_voice_twi'),
            'drive_folder_id': structure['raw'],
            'description': 'Common Voice Twi dataset'
        },
        {
            'local_path': Path('./data/metadata'),
            'drive_folder_id': structure['metadata'],
            'description': 'Dataset metadata'
        },
        {
            'local_path': Path('./data/splits'),
            'drive_folder_id': structure['splits'],
            'description': 'Train/val/test splits'
        }
    ]
    
    # Upload individual files
    individual_files = [
        {
            'local_path': Path('./000_enhanced_twi_processor.py'),
            'drive_folder_id': structure['scripts'],
            'description': 'Enhanced Twi processor'
        },
        {
            'local_path': Path('./comprehensive_audio_pipeline.py'),
            'drive_folder_id': structure['scripts'],
            'description': 'Audio processing pipeline'
        },
        {
            'local_path': Path('./upload_to_drive.py'),
            'drive_folder_id': structure['scripts'],
            'description': 'This upload script'
        }
    ]
    
    # Execute uploads
    all_results = []
    
    print("\n📂 Uploading directories...")
    for task in upload_tasks:
        if task['local_path'].exists():
            print(f"\n📁 Uploading {task['description']}: {task['local_path']}")
            result = uploader.upload_directory(
                task['local_path'], 
                task['drive_folder_id'],
                exclude_patterns=['__pycache__', '.git', '*.pyc', '.DS_Store']
            )
            result['description'] = task['description']
            all_results.append(result)
        else:
            print(f"⚠️ Directory not found: {task['local_path']}")
    
    print("\n📄 Uploading individual files...")
    for file_task in individual_files:
        if file_task['local_path'].exists():
            file_id = uploader.upload_file(
                file_task['local_path'],
                file_task['drive_folder_id']
            )
            if file_id:
                print(f"✅ {file_task['description']}: {file_id}")
        else:
            print(f"⚠️ File not found: {file_task['local_path']}")
    
    # Create comprehensive summary
    summary = {
        'upload_date': pd.Timestamp.now().isoformat(),
        'drive_structure': structure,
        'upload_results': all_results,
        'total_directories': len([r for r in all_results if 'uploaded_files' in r]),
        'total_files_uploaded': sum(len(r.get('uploaded_files', [])) for r in all_results),
        'total_errors': sum(len(r.get('errors', [])) for r in all_results)
    }
    
    # Save summary
    with open('./drive_upload_summary.json', 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    print("\n" + "=" * 60)
    print("📊 UPLOAD SUMMARY")
    print("=" * 60)
    print(f"📁 Directories uploaded: {summary['total_directories']}")
    print(f"📄 Files uploaded: {summary['total_files_uploaded']}")
    print(f"❌ Errors: {summary['total_errors']}")
    
    print(f"\n🔗 Google Drive Structure:")
    print(f"  📂 voice-lab-data: {structure['voice_lab_root']}")
    for folder_name, folder_id in structure.items():
        if folder_name != 'voice_lab_root':
            print(f"    📁 {folder_name}: {folder_id}")
    
    print(f"\n📋 Detailed summary saved to: drive_upload_summary.json")
    print(f"🏗️ Drive structure saved to: drive_structure.json")
    
    if summary['total_errors'] > 0:
        print(f"\n⚠️ Some files had errors. Check drive_upload_summary.json for details.")
    else:
        print(f"\n🎉 ALL FILES UPLOADED SUCCESSFULLY!")
        print(f"Your voice lab project is now backed up to Google Drive.")

if __name__ == "__main__":
    # Import required dependencies
    import pandas as pd
    main()