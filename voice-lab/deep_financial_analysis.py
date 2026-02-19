#!/usr/bin/env python3
"""
Deep Financial Inclusion Dataset Analysis
Recursively explores the dataset structure to find actual audio files
"""

import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from pathlib import Path

def deep_folder_scan(service, folder_id, folder_name="", max_depth=4, current_depth=0):
    """Recursively scan a folder and all its subfolders"""
    if current_depth >= max_depth:
        return []
    
    print("  " * current_depth + f"📂 Scanning: {folder_name}")
    
    try:
        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="files(id, name, size, mimeType)",
            pageSize=1000
        ).execute()
        
        files = results.get('files', [])
        all_items = []
        
        audio_count = 0
        text_count = 0
        
        for file in files:
            file_name = file['name'].lower()
            file_size = int(file.get('size', 0)) if file.get('size') else 0
            
            item_info = {
                'id': file['id'],
                'name': file['name'],
                'size': file_size,
                'type': file['mimeType'],
                'path': f"{folder_name}/{file['name']}" if folder_name else file['name'],
                'depth': current_depth
            }
            
            if file['mimeType'] == 'application/vnd.google-apps.folder':
                # Recursively scan subfolder
                item_info['children'] = deep_folder_scan(
                    service, file['id'], 
                    f"{folder_name}/{file['name']}" if folder_name else file['name'],
                    max_depth, current_depth + 1
                )
                
                # Count audio/text files in children
                def count_in_children(children):
                    audio = text = 0
                    for child in children:
                        if child.get('children'):
                            child_audio, child_text = count_in_children(child['children'])
                            audio += child_audio
                            text += child_text
                        else:
                            child_name = child['name'].lower()
                            if any(ext in child_name for ext in ['.wav', '.mp3', '.m4a', '.flac']):
                                audio += 1
                            elif any(ext in child_name for ext in ['.txt', '.tsv', '.csv']):
                                text += 1
                    return audio, text
                
                child_audio, child_text = count_in_children(item_info['children'])
                item_info['audio_files'] = child_audio
                item_info['text_files'] = child_text
                
                audio_count += child_audio
                text_count += child_text
                
            else:
                # This is a file
                if any(ext in file_name for ext in ['.wav', '.mp3', '.m4a', '.flac']):
                    item_info['file_type'] = 'audio'
                    audio_count += 1
                elif any(ext in file_name for ext in ['.txt', '.tsv', '.csv']):
                    item_info['file_type'] = 'text'
                    text_count += 1
                else:
                    item_info['file_type'] = 'other'
            
            all_items.append(item_info)
        
        # Print summary for this level
        if audio_count > 0 or text_count > 0:
            print("  " * current_depth + f"  📊 Found: {audio_count} audio, {text_count} text files")
        
        return all_items
        
    except Exception as e:
        print("  " * current_depth + f"❌ Error scanning {folder_name}: {e}")
        return []

def main():
    """Deep analysis of financial inclusion dataset"""
    print("🔍 DEEP FINANCIAL INCLUSION ANALYSIS")
    print("="*60)
    
    # Setup Google Drive connection
    service_account_file = "./credentials/service_account.json"
    credentials = service_account.Credentials.from_service_account_file(
        service_account_file,
        scopes=['https://www.googleapis.com/auth/drive.readonly']
    )
    service = build('drive', 'v3', credentials=credentials)
    
    # Load connection info
    with open('./data/drive_connection_summary.json', 'r') as f:
        connection_info = json.load(f)
        raw_folder_id = connection_info['raw_folder_id']
    
    # Find financial_inclusion folder
    fi_results = service.files().list(
        q=f"name='financial_inclusion' and '{raw_folder_id}' in parents and trashed=false",
        fields="files(id, name)"
    ).execute()
    
    if not fi_results.get('files'):
        print("❌ Financial inclusion folder not found")
        return
    
    fi_folder_id = fi_results['files'][0]['id']
    print(f"✅ Found financial inclusion folder: {fi_folder_id}")
    
    # Deep scan of the entire structure
    print("\n📂 Deep scanning financial inclusion dataset...")
    structure = deep_folder_scan(service, fi_folder_id, "financial_inclusion", max_depth=5)
    
    # Analyze results
    def analyze_structure(items, level=0):
        total_audio = 0
        total_text = 0
        total_size = 0
        datasets = {}
        
        for item in items:
            if item.get('children'):
                # This is a folder
                child_audio, child_text, child_size, child_datasets = analyze_structure(item['children'], level + 1)
                total_audio += child_audio
                total_text += child_text
                total_size += child_size
                datasets.update(child_datasets)
                
                if child_audio > 0 or child_text > 0:
                    datasets[item['name']] = {
                        'audio_files': child_audio,
                        'text_files': child_text,
                        'size_mb': child_size / (1024*1024),
                        'path': item['path']
                    }
            else:
                # This is a file
                total_size += item['size']
                if item.get('file_type') == 'audio':
                    total_audio += 1
                elif item.get('file_type') == 'text':
                    total_text += 1
        
        return total_audio, total_text, total_size, datasets
    
    total_audio, total_text, total_size, datasets = analyze_structure(structure)
    
    print(f"\n📊 DEEP ANALYSIS RESULTS:")
    print(f"{'='*60}")
    print(f"🎵 Total audio files found: {total_audio:,}")
    print(f"📄 Total text files found: {total_text:,}")  
    print(f"💾 Total size: {total_size/(1024*1024):.1f} MB")
    print(f"📂 Datasets with content: {len(datasets)}")
    
    if datasets:
        print(f"\n📋 Dataset breakdown:")
        for name, info in datasets.items():
            print(f"  📁 {name}:")
            print(f"    🎵 Audio: {info['audio_files']} files")
            print(f"    📄 Text: {info['text_files']} files") 
            print(f"    💾 Size: {info['size_mb']:.1f} MB")
            print(f"    📂 Path: {info['path']}")
    
    # Save detailed analysis
    analysis_results = {
        'analysis_type': 'deep_recursive_scan',
        'total_audio_files': total_audio,
        'total_text_files': total_text,
        'total_size_bytes': total_size,
        'datasets': datasets,
        'full_structure': structure
    }
    
    output_file = Path('./data/metadata/financial_inclusion_deep_analysis.json')
    with open(output_file, 'w') as f:
        json.dump(analysis_results, f, indent=2)
    
    print(f"\n✅ Detailed analysis saved: {output_file}")
    
    if total_audio == 0:
        print(f"\n🤔 NO AUDIO FILES FOUND - Possible reasons:")
        print(f"  • Files might be in compressed archives (.zip, .tar.gz)")
        print(f"  • Files might have different extensions")
        print(f"  • Dataset might be text-only (transcripts)")
        print(f"  • Files might be in nested folders not scanned")
        
        print(f"\n📋 Found file types:")
        file_extensions = {}
        def collect_extensions(items):
            for item in items:
                if item.get('children'):
                    collect_extensions(item['children'])
                else:
                    if '.' in item['name']:
                        ext = '.' + item['name'].split('.')[-1].lower()
                        file_extensions[ext] = file_extensions.get(ext, 0) + 1
        
        collect_extensions(structure)
        for ext, count in sorted(file_extensions.items()):
            print(f"  {ext}: {count} files")

if __name__ == "__main__":
    main()