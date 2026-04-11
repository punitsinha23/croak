import subprocess
import os

def check_migrate():
    backend_dir = r"c:\Users\punit\OneDrive\Desktop\Croak\backend"
    
    # We want a fresh DB to see all migrations run.
    test_db = os.path.join(backend_dir, "repro_db.sqlite3")
    if os.path.exists(test_db):
        os.remove(test_db)
        
    # We'll use a temporary settings override via environment variable if we can,
    # or just use --database if we had one defined.
    # Actually, let's just use a custom settings file.
    
    settings_content = """
from croak.settings import *
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'repro_db.sqlite3',
    }
}
"""
    settings_file = os.path.join(backend_dir, "temp_settings.py")
    with open(settings_file, 'w') as f:
        f.write(settings_content)
        
    env = os.environ.copy()
    env['DJANGO_SETTINGS_MODULE'] = 'temp_settings'
    
    cmd = ["python", "manage.py", "migrate", "--noinput", "-v", "2"]
    
    process = subprocess.Popen(cmd, cwd=backend_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
    
    last_applying = ""
    for line in process.stdout:
        print(line.strip())
        if "Applying" in line:
            last_applying = line.strip()
            
    process.wait()
    print(f"\nFinal status: {process.returncode}")
    print(f"Last migration attempt: {last_applying}")
    
    # Cleanup
    if os.path.exists(settings_file): os.remove(settings_file)
    if os.path.exists(test_db): os.remove(test_db)

if __name__ == "__main__":
    check_migrate()
