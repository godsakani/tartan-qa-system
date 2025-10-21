#!/usr/bin/env python3
"""
Script to clear ChromaDB data to resolve dimension conflicts
"""
import os
import shutil

def clear_chroma_db():
    """Clear the ChromaDB directory"""
    data_dir = os.getenv("DATA_DIR", "./data")
    chroma_dir = os.path.join(data_dir, "chroma_db")
    
    if os.path.exists(chroma_dir):
        print(f"Clearing ChromaDB directory: {chroma_dir}")
        shutil.rmtree(chroma_dir)
        print("✅ ChromaDB cleared successfully")
    else:
        print("ℹ️  ChromaDB directory doesn't exist")
    
    # Recreate the directory
    os.makedirs(chroma_dir, exist_ok=True)
    print("✅ ChromaDB directory recreated")

if __name__ == "__main__":
    clear_chroma_db()
    print("\n🎉 ChromaDB cleared! You can now restart your server.")