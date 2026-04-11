import os
import re

def search_migrations():
    backend_dir = r"c:\Users\punit\OneDrive\Desktop\Croak\backend"
    for root, dirs, files in os.walk(backend_dir):
        if "migrations" in root:
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    path = os.path.join(root, file)
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if "default=None" in content or "Default=None" in content:
                                print(f"Found default=None in {path}")
                            # Also check for other weird patterns
                            if re.search(r"['\"]None['\"]", content):
                                 print(f"Found string 'None' in {path}")
                    except Exception as e:
                        # Try with other encodings if utf-8 fails
                        try:
                            with open(path, 'r', encoding='latin-1') as f:
                                content = f.read()
                                if "default=None" in content:
                                    print(f"Found default=None in {path}")
                        except:
                            print(f"Failed to read {path}: {e}")

if __name__ == "__main__":
    search_migrations()
