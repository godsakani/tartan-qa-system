#!/usr/bin/env python3
"""
Script to completely clean up the vector store
"""

import os
import shutil
from chroma_utils import vectorstore

def cleanup_vectorstore():
    """Completely clean the vector store"""
    try:
        # Method 1: Try to delete all documents
        print("Attempting to delete all documents from vector store...")
        all_docs = vectorstore.get()
        if all_docs['ids']:
            print(f"Found {len(all_docs['ids'])} documents to delete")
            vectorstore.delete(ids=all_docs['ids'])
            print("Deleted all documents from vector store")
        else:
            print("No documents found in vector store")
            
    except Exception as e:
        print(f"Error deleting from vector store: {e}")
        
    try:
        # Method 2: Delete the entire chroma_db directory
        print("Attempting to delete chroma_db directory...")
        if os.path.exists("./chroma_db"):
            shutil.rmtree("./chroma_db")
            print("Deleted chroma_db directory")
        else:
            print("chroma_db directory not found")
            
    except Exception as e:
        print(f"Error deleting chroma_db directory: {e}")

if __name__ == "__main__":
    cleanup_vectorstore()
    print("Cleanup complete! You can now restart your server and upload documents fresh.")