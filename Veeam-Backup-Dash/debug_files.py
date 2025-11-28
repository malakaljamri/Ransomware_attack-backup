# debug_files.py
import json

def check_file_encoding(filepath):
    print(f"\n=== Checking {filepath} ===")
    
    # Try to read as binary first to see the actual content
    with open(filepath, 'rb') as f:
        raw_content = f.read()
        print(f"First 100 bytes: {raw_content[:100]}")
    
    # Try different encodings
    encodings = ['utf-8', 'utf-16', 'utf-16-le', 'utf-16-be', 'latin-1']
    
    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                content = f.read()
                print(f"\n✅ SUCCESS with {encoding}:")
                print(f"First 200 chars: {content[:200]}")
    
                # Try to parse as JSON
                try:
                    data = json.loads(content)
                    print(f"✅ JSON parsed successfully!")
                    print(f"Data type: {type(data)}")
                    if isinstance(data, list) and len(data) > 0:
                        print(f"First item: {data[0]}")
                    return data
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error: {e}")
                    
        except UnicodeDecodeError as e:
            print(f"❌ Failed with {encoding}: {e}")
    
    return None

# Check all files
files = ['data/backup_sessions.json', 'data/backup_jobs.json', 'data/storage_info.json']

for file in files:
    try:
        check_file_encoding(file)
    except Exception as e:
        print(f"Error checking {file}: {e}")