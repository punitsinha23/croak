import os
import subprocess

def check_sql_migrate():
    backend_dir = r"c:\Users\punit\OneDrive\Desktop\Croak\backend"
    apps = ["users", "ribbits", "communities"]
    
    for app in apps:
        migration_dir = os.path.join(backend_dir, app, "migrations")
        if not os.path.exists(migration_dir):
            continue
            
        migrations = sorted([f[:-3] for f in os.listdir(migration_dir) if f.endswith(".py") and f != "__init__.py"])
        
        for mig in migrations:
            # Extract the 4-digit number
            mig_num = mig.split("_")[0]
            print(f"Checking {app} {mig_num}...")
            
            cmd = ["python", "manage.py", "sqlmigrate", app, mig_num]
            try:
                result = subprocess.run(cmd, cwd=backend_dir, capture_output=True, text=True, check=True)
                if "None" in result.stdout:
                    print(f"!!! FOUND 'None' in SQL for {app} {mig_num} !!!")
                    print(result.stdout)
            except subprocess.CalledProcessError as e:
                print(f"Error running sqlmigrate for {app} {mig_num}: {e}")
                # print(e.stderr)

if __name__ == "__main__":
    check_sql_migrate()
