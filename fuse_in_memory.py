import os
import sys
import errno
from fuse import FUSE, FuseOSError, Operations
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import secrets

class InMemoryFileSystem(Operations):
    def __init__(self):
        # Root directory metadata initialization
        self.files = {}
        self.data = {}
        self.keys = {}
        self.files['/'] = {
            'st_mode': (0o755 | 0o040000),
            'st_nlink': 2,
            'st_size': 0
        }
        self.data['/'] = b''

    def encrypt(self, key, plaintext):
        # Random IV ensures unique ciphertext for same plaintext
        iv = secrets.token_bytes(16)
        cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ct = encryptor.update(plaintext) + encryptor.finalize()
        return iv + ct

    def decrypt(self, key, ciphertext):
        # Extract IV from ciphertext before decryption
        if len(ciphertext) == 0:
            return b''
        iv = ciphertext[:16]
        ct = ciphertext[16:]
        cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        return decryptor.update(ct) + decryptor.finalize()

    def getattr(self, path, fh=None):
        if path not in self.files:
            raise FuseOSError(errno.ENOENT)
        return self.files[path]

    def readdir(self, path, fh):
        return ['.', '..'] + [name[1:] for name in self.files if name != '/' and os.path.dirname(name) == path]

    def mkdir(self, path, mode):
        self.files[path] = {
            'st_mode': (mode | 0o040000),
            'st_nlink': 2,
            'st_size': 0
        }
        self.data[path] = b''
        self.files[os.path.dirname(path)]['st_nlink'] += 1

    def rmdir(self, path):
        del self.files[path]
        del self.data[path]
        self.files[os.path.dirname(path)]['st_nlink'] -= 1

    def open(self, path, flags):
        if path not in self.files:
            raise FuseOSError(errno.ENOENT)
        if path not in self.keys:
            raise FuseOSError(errno.EACCES)
        return 0

    def set_key(self, path, key):
        if len(key) != 32:
            raise ValueError("The encryption key must be 32 bytes (256 bits) long.")
        self.keys[path] = key

    def create(self, path, mode, fi=None):
        self.files[path] = {
            'st_mode': (mode | 0o100000),
            'st_nlink': 1,
            'st_size': 0
        }
        self.data[path] = b''
        return 0

    def read(self, path, size, offset, fh):
        if path not in self.keys:
            raise FuseOSError(errno.EACCES)
        decrypted_data = self.decrypt(self.keys[path], self.data[path])
        return decrypted_data[offset:offset+size]

    def write(self, path, data, offset, fh):
        if path not in self.files:
            raise FuseOSError(errno.ENOENT)
        if path not in self.keys:
            raise FuseOSError(errno.EACCES)
        decrypted_data = self.decrypt(self.keys[path], self.data[path])
        new_data = decrypted_data[:offset] + data + decrypted_data[offset + len(data):]
        self.data[path] = self.encrypt(self.keys[path], new_data)
        self.files[path]['st_size'] = len(new_data)
        return len(data)

    def unlink(self, path):
        if path not in self.files:
            raise FuseOSError(errno.ENOENT)
        del self.files[path]
        del self.data[path]
        if path in self.keys:
            del self.keys[path]

    def truncate(self, path, length, fh=None):
        if path not in self.files:
            raise FuseOSError(errno.ENOENT)
        if path not in self.keys:
            raise FuseOSError(errno.EACCES)
        decrypted_data = self.decrypt(self.keys[path], self.data[path])
        new_data = decrypted_data[:length]
        self.data[path] = self.encrypt(self.keys[path], new_data)
        self.files[path]['st_size'] = length

def main(mountpoint):
    # Mount with single-threaded mode to simplify synchronization
    print(f"Mounting filesystem at {mountpoint}")
    FUSE(InMemoryFileSystem(), mountpoint, nothreads=True, foreground=True)
    print(f"Filesystem mounted successfully at {mountpoint}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('usage: %s <mountpoint>' % sys.argv[0])
        sys.exit(1)
    main(sys.argv[1])
