# NutriLab

Plataforma web em **Django** para nutricionistas gerirem **pacientes**, **dados clínicos** (peso, medidas laboratoriais, gráfico de evolução), **planos alimentares** (refeições e opções com imagens) e **anotações de consulta**. Interface responsiva (incluindo mobile), com exportação de dados clínicos em CSV e impressão do plano alimentar pelo navegador.

---

## Requisitos

- **Python** 3.10 ou superior (o projeto usa Django 5.2+; em Python 3.14 isso evita problemas conhecidos com o admin).
- **pip** e ambiente virtual recomendado.

---

## Instalação

### 1. Clonar o repositório

```bash
git clone https://github.com/Joaopsl82/nutriLab.git
cd nutriLab
```

(Ajuste o caminho se a pasta do projeto for `nutriLab/nutriLab` conforme a tua cópia local.)

### 2. Ambiente virtual

**Linux / macOS**

```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell)**

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Se o PowerShell bloquear scripts:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### 3. Dependências

Na pasta onde está o ficheiro `manage.py` e `requirements.txt`:

```bash
pip install -r requirements.txt
```

Dependências principais: **Django** na série 5.2 (inferior a 6), **Pillow** (imagens).

### 4. Base de dados

Por omissão usa **SQLite** (`db.sqlite3` na raiz do projeto Django).

```bash
python manage.py migrate
```

### 5. Utilizador administrativo (opcional)

```bash
python manage.py createsuperuser
```

### 6. Servidor de desenvolvimento

```bash
python manage.py runserver
```

Abre no navegador, por exemplo:

- **Login:** [http://127.0.0.1:8000/auth/logar/](http://127.0.0.1:8000/auth/logar/)
- **Cadastro:** [http://127.0.0.1:8000/auth/cadastro/](http://127.0.0.1:8000/auth/cadastro/)
- **Admin Django:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

Ficheiros enviados (fotos de pacientes, imagens das opções do plano) ficam em **`media/`** (servidos em desenvolvimento pela configuração de URLs).

---

## Variáveis de ambiente (opcional)

| Variável | Descrição |
|----------|-----------|
| `DJANGO_SECRET_KEY` | Chave secreta. **Obrigatória em produção** (não uses o valor de desenvolvimento). |
| `DJANGO_DEBUG` | `1`, `true` ou `yes` para debug; caso contrário desativa (adequado a produção). |
| `DJANGO_ALLOWED_HOSTS` | Lista separada por vírgulas, ex.: `meudominio.com,www.meudominio.com`. |
| `DJANGO_EMAIL_HOST_USER` | Identificador de remetente usado no fluxo de e-mail (ver `settings.py`). |

Em desenvolvimento, se não definires nada, o projeto usa valores por omissão do `settings.py`.

---

## Funcionalidades principais

- **Autenticação:** cadastro, login, logout, ativação de conta por token (`/auth/ativar_conta/<token>/`).
- **Pacientes:** CRUD (incluindo foto), **situação** (ativo / pausa / alta), **pesquisa** e filtro por situação.
- **Dados clínicos:** registos com peso, altura, composição e painel laboratorial; tabela ordenada do mais recente ao mais antigo; **gráfico de peso**; **meta de peso** com comparação ao último registo; **anotações de consulta**; **exportação CSV**.
- **Plano alimentar:** refeições (macronutrientes, horário), opções com imagem e descrição; impressão / “guardar como PDF” via impressão do navegador.
- **Segurança:** vistas da plataforma exigem utilizador autenticado; recursos associados a pacientes são restritos ao nutricionista dono do registo.

---

## Testes automatizados

```bash
python manage.py test plataforma
```

---

## Estrutura do projeto (resumo)

```
nutriLab/
├── manage.py
├── requirements.txt
├── nutri_lab/          # settings, urls principais, wsgi
├── autenticacao/       # cadastro, login, ativação
├── plataforma/         # pacientes, dados clínicos, plano alimentar
├── templates/          # base HTML, CSS global (theme)
└── media/              # uploads (criado em runtime)
```

Ficheiros estáticos da app ficam em `templates/static/`; `STATIC_ROOT` aponta para `staticfiles/` para `collectstatic` em produção.

---

## Produção (notas breves)

1. Define `DJANGO_SECRET_KEY`, `DEBUG=0` e `DJANGO_ALLOWED_HOSTS`.
2. Configura um servidor de ficheiros estáticos e **servir `MEDIA`** adequadamente (ou armazenamento objeto).
3. Executa `python manage.py collectstatic`.
4. Usa um servidor WSGI/ASGI (Gunicorn, uvicorn, etc.) e HTTPS.

---

## Licença e autoria

Define a licença no repositório conforme a tua escolha. O histórico de commits e o GitHub do projeto mantêm a autoria.
