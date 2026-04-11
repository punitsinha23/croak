import sqlite3
import os
import sys

# Patch sqlite3 to catch the "None" query
original_execute = sqlite3.Cursor.execute

def patched_execute(self, query, params=None):
    if "None" in str(query):
        print("\n" + "="*50)
        print("CATCHED SQL WITH 'None':")
        print(query)
        print("PARAMS:", params)
        print("="*50 + "\n")
    return original_execute(self, query, params or ())

sqlite3.Cursor.execute = patched_execute

# Now run the migration
import django
from django.core.management import call_command

os.environ['DJANGO_SETTINGS_MODULE'] = 'croak.settings'
django.setup()

try:
    # Use a memory DB for the check
    from django.conf import settings
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
    
    # Force full migration
    call_command('migrate', verbosity=1, interactive=False)
except Exception as e:
    print(f"Migration failed with error: {e}")
