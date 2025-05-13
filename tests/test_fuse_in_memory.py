import runpy
from unittest import mock
import sys
import fuse_in_memory
import errno
import os
import time
import base64
import secrets
import pytest
from fuse_in_memory import InMemoryFileSystem
from fuse import FuseOSError


def generate_random_key():
    key = os.urandom(32)
    encoded_key = base64.b64encode(key).decode('utf-8')
    return key, encoded_key


@pytest.fixture
def fs():
    return InMemoryFileSystem()


def test_encryption_decryption(fs, tmp_path):
    mountpoint = str(tmp_path)

    key, encoded_key = generate_random_key()
    print(f"Generated Base64 Encoded Key: {encoded_key}")

    fs.set_key("/testfile", key)
    fs.create("/testfile", 0o644)
    fs.open("/testfile", os.O_RDWR)
    fs.write("/testfile", b"Hello, world!", 0, None)

    encrypted_data = fs.data["/testfile"]
    assert isinstance(encrypted_data, bytes)

    data = fs.read("/testfile", 13, 0, None)
    assert data == b"Hello, world!"

    fs.truncate("/testfile", 5)
    data = fs.read("/testfile", 5, 0, None)
    assert data == b"Hello"

    fs.unlink("/testfile")
    with pytest.raises(FuseOSError):
        fs.getattr("/testfile")


def test_key_validation(fs, tmp_path):
    mountpoint = str(tmp_path)

    key1, _ = generate_random_key()
    key2, _ = generate_random_key()

    fs.set_key("/file1", key1)
    fs.set_key("/file2", key2)
    fs.create("/file1", 0o644)
    fs.create("/file2", 0o644)
    fs.open("/file1", os.O_RDWR)
    fs.open("/file2", os.O_RDWR)

    fs.write("/file1", b"Data for file1", 0, None)
    fs.write("/file2", b"Data for file2", 0, None)

    data1 = fs.read("/file1", 14, 0, None)
    assert data1 == b"Data for file1"

    data2 = fs.read("/file2", 14, 0, None)
    assert data2 == b"Data for file2"

    wrong_key = generate_random_key()[0]
    decrypted_wrong = fs.decrypt(wrong_key, fs.data["/file1"])
    assert decrypted_wrong != b"Data for file1"

    fs.set_key("/ok", os.urandom(32))
    fs.create("/ok", 0o644)
    assert fs.open("/ok", os.O_RDWR) == 0

    fs.unlink("/file1")
    fs.unlink("/file2")
    with pytest.raises(FuseOSError):
        fs.getattr("/file1")
    with pytest.raises(FuseOSError):
        fs.getattr("/file2")


def test_open_without_key(fs):
    fs.create("/nokey", 0o644)
    with pytest.raises(FuseOSError) as e:
        fs.open("/nokey", os.O_RDWR)
    assert e.value.errno == errno.EACCES


def test_set_key_invalid_length(fs):
    with pytest.raises(ValueError):
        fs.set_key("/badkey", b"short")


def test_decrypt_empty(fs):
    key, _ = generate_random_key()
    fs.set_key("/empty", key)
    fs.create("/empty", 0o644)
    fs.open("/empty", os.O_RDWR)
    fs.write("/empty", b"non-empty", 0, None)
    fs.truncate("/empty", 0)
    data = fs.read("/empty", 10, 0, None)
    assert data == b""  # ensures truncated data is empty


def test_write_path_not_exist(fs):
    with pytest.raises(FuseOSError) as e:
        fs.write("/noexist", b"data", 0, None)
    assert e.value.errno == errno.ENOENT


def test_write_no_key(fs):
    fs.create("/nokey", 0o644)
    with pytest.raises(FuseOSError) as e:
        fs.write("/nokey", b"data", 0, None)
    assert e.value.errno == errno.EACCES


def test_truncate_path_not_exist(fs):
    with pytest.raises(FuseOSError) as e:
        fs.truncate("/missing", 10)
    assert e.value.errno == errno.ENOENT


def test_truncate_no_key(fs):
    fs.create("/nokey_trunc", 0o644)
    with pytest.raises(FuseOSError) as e:
        fs.truncate("/nokey_trunc", 5)
    assert e.value.errno == errno.EACCES


def test_unlink_not_exist(fs):
    with pytest.raises(FuseOSError) as e:
        fs.unlink("/noexist")
    assert e.value.errno == errno.ENOENT


def test_directory_creation_deletion(fs, tmp_path):
    mountpoint = str(tmp_path)

    fs.mkdir("/testdir", 0o755)
    attrs = fs.getattr("/testdir")
    assert attrs['st_mode'] & 0o040000

    fs.rmdir("/testdir")
    with pytest.raises(FuseOSError):
        fs.getattr("/testdir")


def test_readdir(fs):
    fs.mkdir("/folder", 0o755)
    fs.create("/folder/file1", 0o644)
    entries = fs.readdir("/folder", None)
    assert "file1" in entries


def test_benchmark_io(fs, tmp_path):
    mountpoint = str(tmp_path)

    key, _ = generate_random_key()
    fs.set_key("/benchfile", key)
    fs.create("/benchfile", 0o644)
    fs.open("/benchfile", os.O_RDWR)

    data_size = 1024 * 100  # 100KB
    data = b"A" * data_size

    start = time.time()
    fs.write("/benchfile", data, 0, None)
    write_elapsed = time.time() - start

    start = time.time()
    read_data = fs.read("/benchfile", data_size, 0, None)
    read_elapsed = time.time() - start

    assert read_data == data
    print(f"Write: {write_elapsed:.4f}s, Read: {read_elapsed:.4f}s")

    fs.unlink("/benchfile")


def test_main_called(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["fuse_in_memory.py", "/mnt/fake"])
    with mock.patch("fuse_in_memory.FUSE") as mocked:
        fuse_in_memory.main("/mnt/fake")
        mocked.assert_called_once()


def test_main_usage(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["fuse_in_memory.py"])
    with pytest.raises(SystemExit):
        runpy.run_path("fuse_in_memory.py", run_name="__main__")
    captured = capsys.readouterr()
    assert "usage" in captured.out.lower()


def test_main_success(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["fuse_in_memory.py", "/mnt/fake"])
    with mock.patch("fuse_in_memory.FUSE") as mocked:
        fuse_in_memory.main("/mnt/fake")
        mocked.assert_called_once()
