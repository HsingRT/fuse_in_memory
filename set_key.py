import sys
import base64
import os

if len(sys.argv) != 3:
    print("Usage: set_key.py <file_path> <base64_key>")
    sys.exit(1)

file_path = sys.argv[1]
base64_key = sys.argv[2]

# Decode the Base64 key
key = base64.b64decode(base64_key)

# Interact with the file system to set the key
# For this example, we'll simulate the interaction
from fuse_in_memory import InMemoryFileSystem

fs = InMemoryFileSystem()
fs.set_key(file_path, key)
print(f"Key for {file_path} set successfully.")