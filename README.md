# Kino API

API REST da plataforma Kino, responsável pela autenticação do usuário de demonstração, persistência das avaliações em SQLite e integração com a API do The Movie Database (TMDB).

## Instalação e execução

### Pré-requisito

- Docker instalado e em execução.

### Variáveis de ambiente

Crie o arquivo `.env` a partir do exemplo disponibilizado:

```bash
cp .env.example .env
```

Preencha as variáveis:

```env
TMDB_ACCESS_TOKEN=seu_token_de_leitura_do_tmdb
JWT_SECRET_KEY=uma_chave_secreta_longa
```

### Construção da imagem

Na raiz do projeto do backend, execute:

```bash
docker build -t kino-backend .
```

### Inicialização do container

```bash
docker run --name kino-backend \
  --env-file .env \
  -p 8000:8000 \
  -v kino-backend-data:/app/database \
  kino-backend
```

A API estará disponível em `http://localhost:8000` e sua documentação Swagger em `http://localhost:8000/docs`.

O volume `kino-backend-data` preserva o banco SQLite entre diferentes execuções do container.

### Credenciais de demonstração

O usuário de demonstração é criado automaticamente durante a inicialização da aplicação:

```text
Email: demo@example.com
Senha: demo123
```

## Interface

Esta API é utilizada pelo frontend da plataforma Kino. O frontend deve ser executado separadamente.

**Repositório do frontend:** [https://github.com/ricardopontesdantas/mvp-kino-frontend](https://github.com/ricardopontesdantas/mvp-kino-frontend)
