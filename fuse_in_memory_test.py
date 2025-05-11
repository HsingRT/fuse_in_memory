import base64
import os
import time

def generate_random_key():
    # Generate a random 32-byte key
    key = os.urandom(32)
    # Encode the key in Base64 for display
    encoded_key = base64.b64encode(key).decode('utf-8')
    return key, encoded_key

def list_directory_contents(path):
    # Print current directory contents
    try:
        contents = os.listdir(path)
        print(f"Contents of {path}: {contents}")
    except Exception as e:
        print(f"Error listing contents of {path}: {e}")

def test_encryption_decryption(mountpoint):
    # Test encryption and decryption behaviors
    key, encoded_key = generate_random_key()
    print(f"Generated Base64 Encoded Key: {encoded_key}")

    testfile_path = os.path.join(mountpoint, "testfile")
    
    # Write plaintext to file
    with open(testfile_path, 'w') as f:
        f.write("Hello, world!")
    
    # Read raw (encrypted) file data
    with open(testfile_path, 'rb') as f:
        encrypted_data = f.read()
    print(f"Encrypted data: {encrypted_data}")
    
    # Read decrypted file content
    with open(testfile_path, 'r') as f:
        data = f.read()
        print(f"Decrypted data: {data}")

    list_directory_contents(mountpoint)

    # Truncate file content to 5 bytes
    with open(testfile_path, 'r+') as f:
        f.truncate(5)
    
    # Read raw (encrypted) truncated data
    with open(testfile_path, 'rb') as f:
        raw_data = f.read()
        print(f"Raw encrypted truncated data: {raw_data}")
    
    # Read truncated plaintext
    with open(testfile_path, 'r') as f:
        data = f.read()
        print(f"Decrypted truncated data: {data}")

    # Delete file
    os.remove(testfile_path)
    print("File deleted successfully.")
    
    list_directory_contents(mountpoint)

def test_key_management(mountpoint):
    # Test different keys per file and invalid key access
    key1, encoded_key1 = generate_random_key()
    key2, encoded_key2 = generate_random_key()
    print(f"Key for /file1: {encoded_key1}")
    print(f"Key for /file2: {encoded_key2}")

    file1_path = os.path.join(mountpoint, "file1")
    file2_path = os.path.join(mountpoint, "file2")
    
    # Write plaintext data to files
    with open(file1_path, 'w') as f:
        f.write("Data for file1")
    
    with open(file2_path, 'w') as f:
        f.write("Data for file2")
    
    list_directory_contents(mountpoint)
    
    # Read encrypted raw data
    with open(file1_path, 'rb') as f:
        raw_data = f.read()
        print(f"Raw encrypted data for /file1: {raw_data}")
    
    with open(file2_path, 'rb') as f:
        raw_data = f.read()
        print(f"Raw encrypted data for /file2: {raw_data}")

    # Read plaintext from files
    with open(file1_path, 'r') as f:
        data = f.read()
        print(f"Decrypted data for /file1: {data}")
    
    with open(file2_path, 'r') as f:
        data = f.read()
        print(f"Decrypted data for /file2: {data}")
    
    # Attempt decryption with incorrect key
    wrong_key, encoded_wrong_key = generate_random_key()
    print(f"Using wrong key for /file1: {encoded_wrong_key}")
    try:
        with open(file1_path, 'r') as f:
            data = f.read()
            print(f"Decrypted data with wrong key for /file1: {data}")
    except Exception as e:
        print(f"Error decrypting with wrong key: {e}")

    # Delete files
    os.remove(file1_path)
    os.remove(file2_path)
    print("Files deleted successfully.")
    
    list_directory_contents(mountpoint)

if __name__ == "__main__":
    mountpoint = './mountpoint'

    print("Testing encryption and decryption functionality...")
    test_encryption_decryption(mountpoint)
    
    print("\n" + "=" * 50 + "\n")

    print("Testing key management functionality...")
    test_key_management(mountpoint)