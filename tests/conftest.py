"""
Pytest configuration and fixtures for interview-ai tests.
Sets up the required config files before tests run using the CLI setup.
"""
import os
import sys
import shutil
import atexit
import importlib.util

# Setup config directory at module load time (before test collection)
_test_interview_dir = os.path.join(os.getcwd(), "interview_ai")
_cleanup_needed = False

if not os.path.isdir(_test_interview_dir):
    # Import the CLI setup module directly to avoid triggering full package import
    setup_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "src", "interview_ai", "cli", "setup.py"
    )
    
    spec = importlib.util.spec_from_file_location("cli_setup", setup_path)
    cli_setup_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli_setup_module)
    
    from io import StringIO
    from contextlib import redirect_stdout
    
    # Suppress output during setup
    with redirect_stdout(StringIO()):
        try:
            cli_setup_module.main()
            _cleanup_needed = True
        except FileExistsError:
            pass  # Already exists, that's fine

def _cleanup():
    """Remove the test config directory after tests complete."""
    global _cleanup_needed
    if _cleanup_needed and os.path.isdir(_test_interview_dir):
        shutil.rmtree(_test_interview_dir)

# Register cleanup to run when Python exits
atexit.register(_cleanup)
