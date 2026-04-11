import os
import re

def search_none_in_migrations():
    backend_dir = r"c:\Users\punit\OneDrive\Desktop\Croak\backend"
    found = []
    for root, dirs, files in os.walk(backend_dir):
        if "venv" in root or "__pycache__" in root:
            continue
        if "migrations" in root:
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    path = os.path.join(root, file)
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # Search for "None" as a whole word
                            if re.search(r"\bNone\b", content):
                                found.append(path)
                    except:
                        pass
    for f in found:
        print(f"Found 'None' in: {f}")

if __name__ == "__main__":
    search_none_in_migrations()
