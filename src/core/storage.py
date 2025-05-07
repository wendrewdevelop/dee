import os
import uuid
import secrets
import re
import time
import msgpack
import hashlib
import mimetypes
import numpy as np
import psycopg2 
import paramiko
import zipfile
import sqlite3
from optmizations.numba_utils import fast_checksum


class Repo:
    BRANCH_REGEX = re.compile(r"^[A-Za-z0-9._-]+$")

    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.repo_dir = os.path.join(self.path, ".dee")
        self.objects_dir = os.path.join(self.repo_dir, "objects")
        self.refs_dir = os.path.join(self.repo_dir, "refs")
        self.staging_dir = os.path.join(self.repo_dir, "staging")
        self.index_file = os.path.join(self.repo_dir, "index.msgpack")
        self.head_file = os.path.join(self.repo_dir, "HEAD")
        self.state_file = os.path.join(self.repo_dir, "state.msgpack")
        self.heads_dir = os.path.join(self.refs_dir, "heads")
        self.hooks_dir = os.path.join(self.repo_dir, "hooks")
        self.token_file = os.path.join(self.repo_dir, "token")

        self.ignored_paths = {
            ".venv", "venv", ".vscode", ".env", "env", "__pycache__", ".git", ".dee"
        }

    def _has_remote_link(self):
        """Verifica se já existe um link com servidor remoto"""
        return os.path.exists(os.path.join(self.repo_dir, "remote_link"))

    def _store_repo_id_locally(self, repo_id):
        """Armazena o ID do repositório no diretório .dee"""
        with open(os.path.join(self.repo_dir, "remote_link"), "w") as f:
            f.write(str(repo_id))

    def _get_stored_repo_id(self):
        """Recupera o ID do repositório armazenado localmente"""
        path = os.path.join(self.repo_dir, "remote_link")
        if os.path.exists(path):
            with open(path, "r") as f:
                return f.read().strip()
        return None

    def is_initialized(self):
        return os.path.exists(self.repo_dir) and os.path.isdir(self.repo_dir)

    def _validate_branch_name(self, branch_name):
        if not self.BRANCH_REGEX.match(branch_name):
            raise ValueError(f"Invalid branch name: '{branch_name}'")

    def _run_hook(self, hook_name, *args):
        script = os.path.join(self.hooks_dir, hook_name)
        if os.path.isfile(script) and os.access(script, os.X_OK):
            subprocess.run([script] + list(args), cwd=self.path)

    def has_changes(self):
        if not os.path.exists(self.state_file):
            return False
        with open(self.state_file, "rb") as f:
            state = msgpack.unpackb(f.read(), strict_map_key=False)
        return state.get("has_changes", False)

    def send_zip_to_remote(self, zip_path, remote_path, host, username, password):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=host, username=username, password=password)
        sftp = ssh.open_sftp()
        sftp.put(zip_path, remote_path)
        sftp.close()
        ssh.close()

    def zip_commit_files(self, commit_hash, zip_path):
        commit_path = os.path.join(self.objects_dir, commit_hash)
        with open(commit_path, "rb") as f:
            commit_data = msgpack.unpackb(f.read(), strict_map_key=False)
        files = commit_data.get("files", {})
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for rel_path, meta in files.items():
                staged_file = os.path.join(self.staging_dir, meta["hash"])
                if os.path.exists(staged_file):
                    zipf.write(staged_file, arcname=rel_path)

    def insert_zip_into_db(self, 
                        zip_path, 
                        repo_link=None, 
                        head=None,
                        branch="main"):
        with open(zip_path, 'rb') as f:
            zip_data = f.read()

        try:
            conn = psycopg2.connect(
                host="192.168.3.59",   
                database="server",     
                user="postgres",    
                password="postgres"   
            )
            cursor = conn.cursor()
            
            # Inserção otimizada
            cursor.execute("""
                INSERT INTO tb_repo_object (repo_id, upload_hash, branch, repo_link_id)
                VALUES (%s, %s, %s, %s)
                RETURNING repo_id
            """, (str(uuid.uuid4()), head, branch, str(repo_link)))

            conn.commit()

        except psycopg2.Error as e:
            print(f"Erro ao inserir dados: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    def init(self):
        os.makedirs(self.objects_dir, exist_ok=True)
        os.makedirs(self.refs_dir, exist_ok=True)
        os.makedirs(self.heads_dir, exist_ok=True)
        os.makedirs(self.staging_dir, exist_ok=True)
        os.makedirs(self.hooks_dir, exist_ok=True)
        with open(self.index_file, "wb") as f:
            f.write(msgpack.packb({}))
        with open(self.head_file, "w") as f:
            f.write("")
        with open(self.state_file, "wb") as f:
            f.write(msgpack.packb({"has_changes": False}))
        with open(os.path.join(self.heads_dir, "main"), "w") as f:
            f.write("")
        with open(self.head_file, "w") as f:
            f.write("ref: refs/heads/main")
        with open(self.token_file, "w") as f:
            f.write(secrets.token_hex(32))
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
        branch = self.get_current_branch()
        if branch:
            branch_path = os.path.join(self.heads_dir, branch)
            with open(branch_path, "w") as f:
                f.write(commit_hash)
        else:
            with open(self.head_file, "w") as f:
                f.write(commit_hash)
        with open(self.state_file, "wb") as f:
            f.write(msgpack.packb({"has_changes": False}))
        print(f"✅ Commit criado: {commit_hash}")

    def push(self, repo_id=None):
        conn = psycopg2.connect(
            dbname="server",
            user="postgres",
            password="postgres",
            host="192.168.3.59",
            port="5432"
        )
        
        # Verifica se é o primeiro push e se o repo_id foi fornecido
        is_first_push = not self._has_remote_link()
        if is_first_push and not repo_id:
            print("❗️ ID do repositório obrigatório no primeiro push. Use: dee push <repo_id>")
            return
        
        # Tenta obter o ID armazenado localmente para pushes subsequentes
        stored_repo_id = self._get_stored_repo_id()
        if not repo_id and stored_repo_id:
            repo_id = stored_repo_id

        # Validação do repo_id
        try:
            uuid.UUID(str(repo_id))
        except ValueError:
            print("❗️ ID do repositório inválido")
            return

        # Restante do código original com adaptações
        with open(self.head_file, "r") as f:
            head = f.read().strip()

        zip_path = os.path.join(f"{head}.zip")
        self.zip_commit_files(head, zip_path)

        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM tb_repo WHERE repo_id = %s", (str(repo_id),))
            repo_instance = cursor.fetchone()
            
            if not repo_instance:
                print("❗️ Repositório não encontrado no servidor")
                return
                
            repo_link_id = repo_instance[0]
            if is_first_push:
                self._store_repo_id_locally(repo_id)  # Armazena localmente

        self.insert_zip_into_db(
            zip_path, 
            repo_link=repo_link_id,
            head=head,
            branch=self.get_current_branch() or "main"
        )

        # Envio para servidor remoto (mantido igual)
        remote_path = f"/home/servidor/repos/{head}.zip"
        self.send_zip_to_remote(
            zip_path, 
            remote_path, 
            host='192.168.3.59', 
            username='servidor', 
            password='0110'
        )

        os.remove(zip_path)
        print(f"📤 Commit '{head}' vinculado ao repositório {repo_id}")

    def get_head_commit(self):
        content = open(self.head_file).read().strip()
        if content.startswith("ref:"):
            ref = content.split(" ",1)[1]
            return open(os.path.join(self.repo_dir, ref)).read().strip()
        return content

    def create_branch(self, branch_name, start_point=None):
        heads = os.path.join(self.refs_dir, "heads")
        os.makedirs(heads, exist_ok=True)
        start = start_point or self.get_head_commit()
        ref_path = os.path.join(heads, branch_name)
        with open(ref_path, "w") as f:
            f.write(start)
        print(f"✅ Branch '{branch_name}' criada em {start}")

    def list_branches(self):
        heads = os.path.join(self.refs_dir, "heads")
        return os.listdir(heads)

    def checkout(self, branch_name):
        self._validate_branch_name(branch_name)
        ref = f"refs/heads/{branch_name}"
        ref_path = os.path.join(self.repo_dir, ref)
        if not os.path.exists(ref_path):
            print(f"❗️Branch '{branch_name}' não existe.")
            return
        # run pre-checkout hook
        self._run_hook('pre-checkout', branch_name)
        # Atualiza HEAD
        with open(self.head_file, "w") as f:
            f.write(f"ref: {ref}")
        # Recarrega arquivos do commit (implemente process_tree)
        commit_hash = open(ref_path).read().strip()
        self.process_tree(commit_hash)
        print(f"✅ Agora em branch '{branch_name}'")
        # run post-checkout hook
        self._run_hook('post-checkout', branch_name)

    def merge(self, source_branch, target_branch=None):
        # implementa fast-forward merge básico
        target = target_branch or self.get_current_branch()
        self._validate_branch_name(source_branch)
        self._validate_branch_name(target)
        source_hash = open(os.path.join(self.heads_dir, source_branch)).read().strip()
        target_hash = open(os.path.join(self.heads_dir, target)).read().strip()
        # se target é ancestral de source, fast-forward
        if self.is_ancestor(target_hash, source_hash):
            path = os.path.join(self.heads_dir, target)
            with open(path, 'w') as f:
                f.write(source_hash)
            print(f"✅ Merge fast-forward de {source_branch} em {target}")
        else:
            print("⚠️ Merge não fast-forward: conflito detectado ou merge de três vias necessário.")

    def rebase(self, branch, onto_branch):
        self._validate_branch_name(branch)
        self._validate_branch_name(onto_branch)
        print(f"🔄 Rebase de {branch} em {onto_branch} iniciado")
        # TODO: implementar lógica de replay de commits
        print(f"✅ Rebase concluído (stub)")

    def get_current_branch(self):
        content = open(self.head_file).read().strip()
        if content.startswith("ref:"):
            return content.split('/')[-1]
        return None

    def is_ancestor(self, ancestor, descendant):
        return False

    def retrieve_token(self):
        token = open(self.token_file).read()
        return token

    def clone(self, repo_obj_hash, target_path):
        """Implementação do clone com nome do repositório do banco de dados"""
        conn = None
        ssh = None
        try:
            # 1. Conexão com o banco de dados
            conn = psycopg2.connect(
                host="192.168.3.59",
                database="server",
                user="postgres",
                password="postgres"
            )
            cursor = conn.cursor()

            # 2. Buscar repo_link_id na tb_repo_object
            cursor.execute(
                "SELECT repo_link_id FROM tb_repo_object WHERE upload_hash = %s",
                (repo_obj_hash,)
            )
            result = cursor.fetchone()
            
            if not result:
                raise ValueError("Nenhum repositório encontrado com o hash fornecido")
                
            repo_link_id = result[0]

            # 3. Buscar nome do repositório na tb_repo
            cursor.execute(
                "SELECT repo_name FROM tb_repo WHERE repo_id = %s",
                (repo_link_id,)
            )
            result = cursor.fetchone()
            
            if not result:
                raise ValueError("Registro na tb_repo não encontrado")
                
            repo_name = result[0].strip()
            clone_path = os.path.join(target_path, repo_name)

            # 4. Criar diretório para o clone
            if os.path.exists(clone_path):
                shutil.rmtree(clone_path)
            os.makedirs(clone_path, exist_ok=True)

            # 5. Configurar novo repositório
            self.path = clone_path
            self.init()  # Reutiliza o método init existente

            # 6. Download do arquivo zip
            remote_path = f"/home/servidor/repos/{repo_obj_hash}.zip"
            local_zip = os.path.join(self.repo_dir, f"temp_{repo_obj_hash}.zip")
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                hostname='192.168.3.59',
                username='servidor',
                password='0110'
            )
            
            with ssh.open_sftp() as sftp:
                sftp.get(remote_path, local_zip)

            # 7. Extrair arquivos
            with zipfile.ZipFile(local_zip, 'r') as zip_ref:
                zip_ref.extractall(clone_path)  # Extrai direto para o diretório do repositório

            # 8. Atualizar HEAD e registro remoto
            with open(self.head_file, "w") as f:
                f.write(repo_obj_hash)
                
            self._store_repo_id_locally(repo_link_id)

            return clone_path

        except Exception as error:
            # Limpeza em caso de erro
            if 'clone_path' in locals() and os.path.exists(clone_path):
                shutil.rmtree(clone_path)
            return f'Erro ao clonar o repositório: {str(error)}'
        
        finally:
            # 9. Limpeza final
            if conn:
                conn.close()
            if ssh:
                ssh.close()
            if 'local_zip' in locals() and os.path.exists(local_zip):
                os.remove(local_zip)
