# Encrypted In-Memory File System

An **in-memory encrypted file system** built with FUSE (Filesystem in Userspace). All file contents are encrypted using AES-256 and stored only in memory. This makes it suitable for educational use, testing, or handling short-term sensitive data.

## Key Features

* Basic file system operations: create, read, write, delete, truncate
* AES-256 encryption with CFB mode
* Per-file 256-bit encryption keys
* Purely in-memory (no disk storage)

## System Requirements

* **OS**: Linux with FUSE support
* **Python**: 3.8 or later

## Installation

### Linux Packages

```bash
sudo apt-get install fuse libfuse-dev
```

### Python Dependencies

```bash
pip install fusepy cryptography
```

## Usage

### Mount the file system

```bash
mkdir /tmp/memfs
sudo python fuse_in_memory.py /tmp/memfs
```

### Basic example (in Python)

```python
from fuse_in_memory import InMemoryFileSystem

fs = InMemoryFileSystem()
fs.create('/secret.txt', 0o644)
fs.set_key('/secret.txt', b'12345678901234567890123456789012')  # 32-byte key
fs.write('/secret.txt', b'hello world', 0, None)
print(fs.read('/secret.txt', 11, 0, None))  # Output: b'hello world'
```

## Testing and Benchmark

### Functional Demo (manual)

To manually test functionality, view printed output, and run a built-in benchmark:

````bash
python tests/demo_fuse_in_memory.py <mount_filepath>
````

This script uses `print()` to demonstrate encryption, key validation, directory handling, etc.

### Unit Tests with Coverage

To run automated unit tests and measure coverage:

```bash
pytest --cov=fuse_in_memory --cov-report=term-missing tests/test_fuse_in_memory.py
```

This will:

* Execute all Pytest-based unit tests
* Report code coverage and highlight untested lines

## Notes

* Each file must have its own 32-byte (256-bit) encryption key
* Read/write operations are blocked without a key
* Data is volatile and lost when the program exits
