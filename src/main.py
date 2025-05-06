from cli.commands import cli, register_commands


def main():
    print("Bem-vindo ao dee!")
    register_commands(cli)
    cli()


if __name__ == "__main__":
    main()
