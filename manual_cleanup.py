#!/usr/bin/env python3
"""
Manual cleanup script - run this when server is stopped
"""

import os
import shutil

def manual_cleanup():
    """Manually delete the chroma_db directory"""
    
    print("Manual cleanup starting...")
    
    # Check if chroma_db exists
    if os.path.exists("./chroma_db"):
        print("Found chroma_db directory")
        
        try:
            # Try to remove individual files first
            for root, dirs, files in os.walk("./chroma_db"):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        os.chmod(file_path, 0o777)  # Make writable
                        os.remove(file_path)
                        print(f"Deleted: {file_path}")
                    except Exception as e:
                        print(f"Could not delete {file_path}: {e}")
            
            # Remove empty directories
            shutil.rmtree("./chroma_db", ignore_errors=True)
            print("Successfully deleted chroma_db directory")
            
        except Exception as e:
            print(f"Error during cleanup: {e}")
    else:
        print("chroma_db directory not found")
    
    print("Manual cleanup complete!")
    print("\nNext steps:")
    print("1. Restart your server: uvicorn main:app --reload")
    print("2. Upload your handbook.pdf again")
    print("3. Test the search")

if __name__ == "__main__":
    manual_cleanup()