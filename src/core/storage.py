import os
import time
import msgpack
import hashlib
import mimetypes
import numpy as np
from optmizations.numba_utils import fast_checksum


class Repo:
    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.repo_dir = os.path.join(self.path, ".dee")
        self.objects_dir = os.path.join(self.repo_dir, "objects")
        self.refs_dir = os.path.join(self.repo_dir, "refs")
        self.staging_dir = os.path.join(self.repo_dir, "staging")
        self.index_file = os.path.join(self.repo_dir, "index.msgpack")
        self.head_file = os.path.join(self.repo_dir, "HEAD")
        self.state_file = os.path.join(self.repo_dir, "state.msgpack")

        self.ignored_paths = {
            ".venv", "venv", ".vscode", ".env", "env", "__pycache__", ".git", ".dee"
        }

    def is_initialized(self):
        return os.path.exists(self.repo_dir) and os.path.isdir(self.repo_dir)

    def has_changes(self):
        if not os.path.exists(self.state_file):
            return False
        with open(self.state_file, "rb") as f:
            state = msgpack.unpackb(f.read(), strict_map_key=False)
        return state.get("has_changes", False)

    def init(self):
        os.makedirs(self.objects_dir, exist_ok=True)
        os.makedirs(self.refs_dir, exist_ok=True)
        os.makedirs(self.staging_dir, exist_ok=True)
        with open(self.index_file, "wb") as f:
            f.write(msgpack.packb({}))
        with open(self.head_file, "w") as f:
            f.write("")
        with open(self.state_file, "wb") as f:
            f.write(msgpack.packb({"has_changes": False}))
        print(f"✅ Repositório inicializado em {self.repo_dir}")

    def _should_ignore(self, path):
        return any(ignored in path.split(os.sep) for ignored in self.ignored_paths)

    def add(self, files):
        if not os.path.exists(self.repo_dir):
            print("❗️Repositório não inicializado. Execute 'dee init'")
            return
        if not files:
            files = ["."]
        index = {}
        if os.path.exists(self.index_file):
            with open(self.index_file, "rb") as f:
                content = f.read()
                if content:
                    index = msgpack.unpackb(content, strict_map_key=False)
        added_any = False
        for file in files:
            abs_path = os.path.join(self.path, file)
            for root, dirs, filenames in os.walk(abs_path):
                dirs[:] = [d for d in dirs if not self._should_ignore(os.path.join(root, d))]
                for fname in filenames:
                    full_path = os.path.join(root, fname)
                    if self._should_ignore(full_path):
                        continue
                    rel_path = os.path.relpath(full_path, self.path)
                    with open(full_path, "rb") as f:
                        content = f.read()
                    np_content = np.frombuffer(content, dtype=np.uint8)
                    checksum = fast_checksum(np_content)
                    file_hash = hashlib.sha1(content).hexdigest()
                    with open(os.path.join(self.staging_dir, file_hash), "wb") as f:
                        f.write(content)
                    file_stat = os.stat(full_path)
                    index[rel_path] = {
                        "hash": file_hash,
                        "timestamp": time.time(),
                        "size": file_stat.st_size,
                        "type": mimetypes.guess_type(full_path)[0] or "unknown",
                        "mode": oct(file_stat.st_mode & 0o777),
                        "original_name": os.path.basename(full_path),
                        "abs_path": full_path,
                        "checksum": checksum
                    }
                    print(f"📥 Adicionado ao staging: {rel_path}")
                    added_any = True
        with open(self.index_file, "wb") as f:
            f.write(msgpack.packb(index))
        if added_any:
            with open(self.state_file, "wb") as f:
                f.write(msgpack.packb({"has_changes": True}))
        else:
            print("✅ Nenhum arquivo novo ou alterado para adicionar.")

    def commit(self, message):
        if not os.path.exists(self.repo_dir):
            print("❗️Repositório não inicializado.")
            return
        with open(self.state_file, "rb") as f:
            state = msgpack.unpackb(f.read(), strict_map_key=False)
        if not state.get("has_changes", False):
            print("⚠️ Nenhuma alteração para commit.")
            return
        with open(self.index_file, "rb") as f:
            index = msgpack.unpackb(f.read(), strict_map_key=False)
        timestamp = time.time()
        commit_data = {
            "timestamp": timestamp,
            "message": message,
            "files": index
        }
        serialized = msgpack.packb(commit_data)
        commit_hash = hashlib.sha1(serialized).hexdigest()
        with open(os.path.join(self.objects_dir, commit_hash), "wb") as f:
            f.write(serialized)
        with open(self.head_file, "w") as f:
            f.write(commit_hash)
        with open(self.state_file, "wb") as f:
            f.write(msgpack.packb({"has_changes": False}))
        print(f"✅ Commit criado: {commit_hash}")

    def push(self):
        if not os.path.exists(self.head_file):
            print("❗️Nenhum commit encontrado. Faça um commit primeiro.")
            return
        with open(self.head_file, "r") as f:
            head = f.read().strip()
        if not head:
            print("❗️Nenhum commit encontrado.")
        else:
            print(f"📤 Commit '{head}' aplicado ao HEAD.")