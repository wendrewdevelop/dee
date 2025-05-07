import os
import shutil
import json
import time
import hashlib
import click
import requests
import subprocess
from core.storage import Repo


VERSION = "0.1.13"

def check_for_updates():
    if os.getenv("DEE_DISABLE_UPDATE_CHECK"):
        return

    try:
        resp = requests.get(
            "https://api.github.com/repos/wendrewdevelop/dee/releases/latest",
            timeout=2
        )
        resp.raise_for_status()
        latest_tag = resp.json().get("tag_name", "")
        latest = latest_tag.lstrip("v")

        if latest and latest != VERSION:
            print(
                f"\n🆕 Uma nova versão do dee está disponível: {latest}\n"
                "  Atualize com:\n"
                "    curl -sL https://github.com/wendrewdevelop/dee/"
                "releases/latest/download/install.sh | bash\n"
            )
    except Exception:
        # Se falhar, segue sem avisar
        pass


@click.group()
@click.pass_context
def cli(ctx):
    check_for_updates()
    ctx.ensure_object(dict)


@cli.command()
@click.argument("path", default=".")
@click.pass_context
def init(ctx, path):
    repo = Repo(path)
    if repo.is_initialized():
        click.echo("Repositório já inicializado.")
    else:
        repo.init()
        click.echo(f"Repositório dee inicializado em: {path}")


@cli.command()
@click.argument("message")
@click.pass_context
def commit(ctx, message):
    repo = Repo(".")
    if not repo.is_initialized():
        click.echo("Repositório não inicializado. Execute 'dee init .' primeiro.")
        return
    if not repo.has_changes():
        click.echo("Nenhuma alteração detectada. Faça alterações e adicione arquivos com 'dee add' antes de commitar.")
        return
    commit_id = repo.commit(message)
    click.echo(f"Commit criado: {commit_id}")


@click.command()
@click.argument("files", nargs=-1)
@click.pass_context
def add(ctx, files):
    repo = Repo(".")
    if not repo.is_initialized():
        click.echo("Repositório não inicializado. Execute 'dee init .' primeiro.")
        return
    if not files:
        files = ["."]
    repo.add(files)


@cli.command()
@click.argument('repo_id', required=False)
@click.pass_context
def push(ctx, repo_id=None):
    repo = Repo(".")
    if not repo.is_initialized():
        click.echo("Repositório não inicializado. Execute 'dee init .' primeiro.")
        return
    
    # Verifica se é o primeiro push
    if not repo._has_remote_link() and not repo_id:
        click.echo("ERRO: ID do repositório obrigatório no primeiro push!")
        click.echo("Use: dee push <repo_id>")
        return
    
    repo.push(repo_id)
    click.echo("Alterações aplicadas ao HEAD.")


@cli.command()
@click.argument("branch")
@click.argument("start_point", required=False)
@click.pass_context
def branch(ctx, branch, start_point):
    """Cria um novo branch"""
    repo = Repo('.')
    repo.create_branch(branch, start_point)


@cli.command(name="branches")
@click.pass_context
def branches(ctx):
    """Lista branches existentes"""
    repo = Repo('.')
    for b in repo.list_branches():
        click.echo(b)


@cli.command()
@click.argument("branch")
@click.pass_context
def checkout(ctx, branch):
    """Troca para outro branch"""
    repo = Repo('.')
    repo.checkout(branch)


@cli.command()
@click.argument("source_branch")
@click.argument("target_branch", required=False)
@click.pass_context
def merge(ctx, source_branch, target_branch):
    """Faz merge de source_branch em target_branch (ou atual)"""
    repo = Repo('.')
    repo.merge(source_branch, target_branch)

@cli.command()
@click.argument("branch")
@click.argument("onto_branch")
@click.pass_context
def rebase(ctx, branch, onto_branch):
    """Rebase de um branch em outro"""
    repo = Repo('.')
    repo.rebase(branch, onto_branch)


@cli.command()
@click.pass_context
def token(ctx):
    """obtem o token gerado no momento da inicialização do repositorio"""
    repo = Repo('.')
    token = repo.retrieve_token()
    click.echo(f'\nToken::: {token}\n')
    click.echo("Copie e cole o codigo acima nas configurações da sua conta!\n")


@cli.command()
@click.argument("repo_obj_hash")
@click.argument("target_path", required=False)
@click.pass_context
def clone(ctx, repo_obj_hash, target_path="."):
    """Clona um repositório remoto"""
    try:
        repo = Repo('.')
        cloned_path = repo.clone(
            repo_obj_hash, 
            target_path
        )
        click.echo(f"✅ Repositório clonado em: {cloned_path}")
        
    except Exception as e:
        click.echo(f"❗️ Erro ao clonar: {str(e)}")
        if os.path.exists(target_path):
            shutil.rmtree(target_path)


cli.add_command(add)
cli.add_command(branch)
cli.add_command(branches)
cli.add_command(checkout)
cli.add_command(merge)
cli.add_command(rebase)
cli.add_command(token)
cli.add_command(clone)