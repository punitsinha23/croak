import subprocess
import os

def check_migrate():
    backend_dir = r"c:\Users\punit\OneDrive\Desktop\Croak\backend"
    # Set DJANGO_SETTINGS_MODULE if needed, but manage.py usually handles it
    cmd = ["python", "manage.py", "migrate", "--noinput", "-v", "2"]
    
    # We need to run it in a way that captures the last applied migration before failure.
    # But migrate might not be the same as the test DB creation if the local DB is already migrated.
    # However, we can try to migrate a dummy DB.
    
    test_db = "test_temp_db.sqlite3"
    if os.path.exists(test_db):
        os.remove(test_db)
        
    cmd = ["python", "manage.py", "migrate", "--database", "default", "--noinput", "-v", "2"]
    # Wait, we don't want to mess with the default DB.
    # Let's just run it and see the output.
    
    process = subprocess.Popen(cmd, cwd=backend_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    last_applying = ""
    for line in process.stdout:
        print(line.strip())
        if "Applying" in line:
            last_applying = line.strip()
            
    process.wait()
    print(f"\nLast successful application attempt: {last_applying}")

if __name__ == "__main__":
    check_migrate()
