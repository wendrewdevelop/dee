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

curl -LO https://github.com/wendrewdevelop/dee/releases/download/v0.1.0/deevcs.tar.gz
tar -xzf deevcs.tar.gz
cd deevcs
make
sudo make install

``` 

### Instalação via wget
```bash
wget https://github.com/wendrewdevelop/dee/releases/download/v0.1.0/deevcs.tar.gz
tar -xzf deevcs.tar.gz
cd deevcs
make
sudo make install

``` 
