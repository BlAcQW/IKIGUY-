import json
import sys

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('002_phase1_data_processing_enhanced_executed.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Check for execution outputs
code_cells = [cell for cell in nb['cells'] if cell['cell_type'] == 'code']
cells_with_output = [cell for cell in code_cells if cell.get('outputs', [])]

print(f"Total code cells: {len(code_cells)}")
print(f"Cells with execution outputs: {len(cells_with_output)}")

# Check last few outputs for completion messages
print("\n=== CHECKING FOR COMPLETION INDICATORS ===")
for cell in cells_with_output[-3:]:
    for output in cell.get('outputs', []):
        if 'text' in output:
            text = ''.join(output['text'])
            if any(keyword in text.lower() for keyword in ['complete', 'processed', 'saved', 'total', 'success']):
                print(f"\nFound output: {text[:500]}")

# Check for Google Drive references
print("\n=== CHECKING GOOGLE DRIVE REFERENCES ===")
gdrive_refs = []
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if 'drive' in source.lower() or 'gdrive' in source.lower():
            gdrive_refs.append(source[:200])

print(f"Found {len(gdrive_refs)} cells with Google Drive references")

# Check final output
if cells_with_output:
    last_cell = cells_with_output[-1]
    print("\n=== LAST EXECUTED CELL OUTPUT ===")
    for output in last_cell.get('outputs', []):
        if 'text' in output:
            text = ''.join(output['text'])
            print(text[:1000])