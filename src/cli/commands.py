import os
import shutil
import json
import time
import hashlib
import click
from core.storage import Repo


@click.group()
@click.pass_context
def cli(ctx):
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
@click.pass_context
def push(ctx):
    repo = Repo(".")
    if not repo.is_initialized():
        click.echo("Repositório não inicializado. Execute 'dee init .' primeiro.")
        return
    repo.push()
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


cli.add_command(add)
cli.add_command(branch)
cli.add_command(branches)
cli.add_command(checkout)
cli.add_command(merge)
cli.add_command(rebase)
