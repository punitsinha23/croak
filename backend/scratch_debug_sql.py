import os
import django
from django.conf import settings
from django.test.utils import get_runner

def run_tests_with_logging():
    os.environ['DJANGO_SETTINGS_MODULE'] = 'croak.settings'
    django.setup()
    
    import logging
    l = logging.getLogger('django.db.backends')
    l.setLevel(logging.DEBUG)
    l.addHandler(logging.StreamHandler())
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["users"])
    return failures

if __name__ == "__main__":
    run_tests_with_logging()
