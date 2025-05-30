# DéeVCS  
 *Version Control with Love*  
 
 Uma ferramenta de versionamento feita com carinho, inspirada em Desirée.  
 Combina a eficiência do Git com a leveza do Python e otimizações do Numba ❤️.  
 
 ### Exemplos
 
 ```bash
 # Ordem de execução dos comandos:
 
 dee init .
 dee add .
 dee commit "mensagem..."
 dee push
 ```
 
 ### Atualizar modulo localmente
 
 ```bash
 # precisa ser criado o ambiente virtual do python (virtualenv)
 
 $ pip install --editable .
 ```
 
 ### Instalação via curl
 ```bash
 
 curl -sL https://github.com/wendrewdevelop/dee/releases/latest/download/install.sh | bash
 
 ``` 
 
 ### Passo a passo para instalação
 ```bash
 # 1. Entrar na URL: https://github.com/wendrewdevelop/dee/releases
 # 2. Draft a new release
 # 3. No terminal, dentro do projeto, executar o comando abaixo:
 git git tag -a v1.0.0 -m "Versão 1.0.0"
 git push origin --tags
 # 4. Selecionar a tag
 # 5. Escrever titulo e descrição
 # 6. Compactar o projeto com o comando abaixo:
 tar -czf deevcs.tar.gz deevcs/
 # 7. Anexar arquivo compactado dentro da release
 # 8. Anexar arquivo install.sh dentro da release
 
 ```
 
 ### TO-DO
 - [x] Add token in .dee folder to validade repo;
 - [x] Create cmd to show this token;
 - [x] Add this token on config. account;
 - [ ] Build a hub to tool;
 - [x] fix repo_link_id insert error;
 
 - [ ] Criar página de detalhes da issue;
 - [x] Quando criar o repositorio, instruir o usuário corretamente:
     1. dee init .
     2. dee add .
     3. dee commit "message..."
     4. dee push <repo_id/repo_link> -- Somente no primeiro push
 - [ ] Adicionar linguagens presentes no projeto;
