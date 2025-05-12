# Encrypted In-Memory FileSystem

This is an **in-memory encrypted file system** implemented using FUSE (Filesystem in Userspace). All file contents are stored in memory and encrypted using AES-256, making it suitable for testing, educational purposes, or short-term sensitive data handling.

## Features

* Supports basic file system operations: create, read, write, delete, and truncate files/directories
* All file content is encrypted using AES-256-CFB mode
* Each file requires a separate 256-bit encryption key for access
* No files are stored on disk; everything resides in memory only

## System Requirements

### Operating System

* Linux (FUSE support required)

### Installation

#### Linux Packages

```bash
sudo apt-get install fuse libfuse-dev
```

#### Python Packages (Python 3.8+ recommended)

```bash
pip install fusepy cryptography
```

## Usage

### Mount the File System

```bash
python in_memory_fs.py <mountpoint>
```

Example:

```bash
mkdir /tmp/memfs
sudo python fuse_in_memory.py /tmp/memfs
```

### Test Flow Example (in Python)

```python
from fuse_in_memory import InMemoryFileSystem

fs = InMemoryFileSystem()
fs.create('/secret.txt', 0o644)
fs.set_key('/secret.txt', b'12345678901234567890123456789012')  # 32 bytes key
fs.write('/secret.txt', b'hello world', 0, None)
print(fs.read('/secret.txt', 11, 0, None))  # Output: b'hello world'
```

## Running Tests and Benchmark

You can run the built-in test and performance benchmark using the provided test script:

```bash
mkdir /tmp/memfs
sudo python3 fuse_in_memory_test.py /tmp/memfs
```

This script will:

* Automatically mount the in-memory file system
* Run encryption/decryption, access control, and directory operation tests
* Benchmark read/write performance (e.g., 100KB I/O latency)
* Automatically unmount the file system after testing

## Notes

* The encryption key must be **32 bytes (256 bits)**; otherwise, an exception will be raised.
* Read/write operations will be denied if a key is not set for the file.
* All files and data will be lost when the program exits (in-memory only).
