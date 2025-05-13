import os
import sys
import errno
from fuse import FUSE, FuseOSError, Operations
from fuse_in_memory import InMemoryFileSystem
import secrets
import base64
import threading
import time


def generate_random_key():
    key = os.urandom(32)
    encoded_key = base64.b64encode(key).decode('utf-8')
    return key, encoded_key


def list_directory_contents(path):
    try:
        contents = os.listdir(path)
        print(f"Contents of {path}: {contents}")
    except Exception as e:
        print(f"Error listing contents of {path}: {e}")


def test_encryption_decryption(fs, mountpoint):
    key, encoded_key = generate_random_key()
    print(f"Generated Base64 Encoded Key: {encoded_key}")

    fs.set_key("/testfile", key)
    fs.create("/testfile", 0o644)

    try:
        fs.open("/testfile", os.O_RDWR)
    except FuseOSError as e:
        print(f"Error: {e}")

    fs.write("/testfile", b"Hello, world!", 0, None)

    list_directory_contents(mountpoint)

    encrypted_data = fs.data["/testfile"]
    print(f"Encrypted data: {encrypted_data}")

    data = fs.read("/testfile", 13, 0, None)
    print(f"Decrypted data: {data}")

    fs.truncate("/testfile", 5)
    data = fs.read("/testfile", 5, 0, None)
    print(f"Decrypted truncated data: {data}")

    fs.unlink("/testfile")
    try:
        fs.getattr("/testfile")
    except FuseOSError as e:
        print(f"File not found as expected: {e}")

    list_directory_contents(mountpoint)


def test_key_validation(fs, mountpoint):
    key1, encoded_key1 = generate_random_key()
    key2, encoded_key2 = generate_random_key()
    print(f"Key for /file1: {encoded_key1}")
    print(f"Key for /file2: {encoded_key2}")

    fs.set_key("/file1", key1)
    fs.set_key("/file2", key2)

    fs.create("/file1", 0o644)
    fs.create("/file2", 0o644)

    try:
        fs.open("/file1", os.O_RDWR)
        fs.open("/file2", os.O_RDWR)
    except FuseOSError as e:
        print(f"Error: {e}")

    fs.write("/file1", b"Data for file1", 0, None)
    fs.write("/file2", b"Data for file2", 0, None)

    list_directory_contents(mountpoint)

    encrypted_data1 = fs.data["/file1"]
    encrypted_data2 = fs.data["/file2"]
    print(f"Encrypted data for /file1: {encrypted_data1}")
    print(f"Encrypted data for /file2: {encrypted_data2}")

    data = fs.read("/file1", 14, 0, None)
    print(f"Decrypted data for /file1: {data}")
    data = fs.read("/file2", 14, 0, None)
    print(f"Decrypted data for /file2: {data}")

    try:
        wrong_key = generate_random_key()[0]
        data = fs.decrypt(wrong_key, fs.data["/file1"])
        print(f"Decrypted data with wrong key for /file1: {data}")
    except Exception as e:
        print(f"Error decrypting with wrong key for /file1: {e}")

    fs.unlink("/file1")
    fs.unlink("/file2")
    try:
        fs.getattr("/file1")
    except FuseOSError as e:
        print(f"File not found as expected: {e}")
    try:
        fs.getattr("/file2")
    except FuseOSError as e:
        print(f"File not found as expected: {e}")

    list_directory_contents(mountpoint)


def test_directory_creation_deletion(fs, mountpoint):
    # Create a directory
    print("Creating directory /testdir...")
    fs.mkdir("/testdir", 0o755)
    list_directory_contents(mountpoint)

    # Confirm that the directory was created
    try:
        attrs = fs.getattr("/testdir")
        print(f"Attributes of /testdir: {attrs}")
    except FuseOSError as e:
        print(f"Error: {e}")

    # Remove the directory
    print("Removing directory /testdir...")
    fs.rmdir("/testdir")
    list_directory_contents(mountpoint)

    # Confirm that the directory was removed
    try:
        attrs = fs.getattr("/testdir")
        print(f"Attributes of /testdir: {attrs}")
    except FuseOSError as e:
        print(f"Directory not found as expected: {e}")


def benchmark_io_performance(fs, mountpoint):
    print("Benchmarking I/O performance...")

    key, _ = generate_random_key()
    fs.set_key("/benchfile", key)
    fs.create("/benchfile", 0o644)
    fs.open("/benchfile", os.O_RDWR)

    data_size = 1024 * 100  # 100KB
    data = b"A" * data_size

    start = time.time()
    fs.write("/benchfile", data, 0, None)
    write_elapsed = time.time() - start
    print(f"Write {data_size / 1024:.0f}KB took {write_elapsed:.4f} seconds")

    start = time.time()
    fs.read("/benchfile", data_size, 0, None)
    read_elapsed = time.time() - start
    print(f"Read {data_size / 1024:.0f}KB took {read_elapsed:.4f} seconds")

    fs.unlink("/benchfile")


def main(mountpoint):
    fs = InMemoryFileSystem()

    def mount_fs():
        print(f"Mounting filesystem at {mountpoint}")
        print("\n" + "="*50 + "\n")
        FUSE(fs, mountpoint, nothreads=True, foreground=True)
        print("\n" + "="*50 + "\n")
        print(f"Filesystem mounted successfully at {mountpoint}")

    mount_thread = threading.Thread(target=mount_fs)
    mount_thread.start()

    time.sleep(2)

    print("Testing encryption and decryption functionality...")
    test_encryption_decryption(fs, mountpoint)

    print("\n" + "="*50 + "\n")

    print("Testing key validation functionality...")
    test_key_validation(fs, mountpoint)

    print("\n" + "="*50 + "\n")

    print("Testing directory creation and deletion functionality...")
    test_directory_creation_deletion(fs, mountpoint)

    print("Benchmarking I/O performance...")
    benchmark_io_performance(fs, mountpoint)

    # Unmount the filesystem
    os.system(f"fusermount -u {mountpoint}")
    print("Filesystem unmounted successfully.")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("usage: %s <mountpoint>" % sys.argv[0])
        sys.exit(1)

    main(sys.argv[1])
