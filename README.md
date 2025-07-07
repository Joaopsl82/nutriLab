# nutriLab
Plataforma de gerenciamento de dieta para nutricionistas.

# Clonando o projeto
1. git clone https://github.com/Joaopsl82/nutriLab.git para clonar o projeto

# Instalando ambiente virtual
<strong> 1. Caso esteja usando Linux </strong> <br>
  a. `python3 -m venv venv` para criar o ambiente virtual <br>
  b. `source venv/bin/activate` para ativar o ambiente virtual

<strong> 2. Caso esteja usando Windows </strong> <br> 
  a. `python -m venv venv` <br>
  b. `venv/Scripts/Activate`
  
<strong> 3. Caso algum comando retorne um erro de permissão execute o código abaixo e tente novamente </strong><br>
  a. `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

# Instalando as Bibliotecas
  a. `pip install django` <br>
  b. `pip install pillow`

# Para rodar o servidor
  a. `python3 manage.py runserver` para caso esteja rodando no Linux <br>
  b. `python manage.py runserver` para caso esteja rodando no Windows

# Criando e fazendo migrações do banco de dados
  a. `python manage.py makemigrations` <br>
  b. `python manage.py migrate`
  <br><br>
  Se estiver no Linux é só digitar python3 e copiar o restante do código

# Visualizando o projeto
  Para visualizar o projeto após iniciar o servidor entre no link: `127.0.0.1:8000/auth/logar`
