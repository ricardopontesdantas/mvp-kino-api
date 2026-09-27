import os
import requests
import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, Query, HTTPException, Depends, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models import Review

from auth import (
    CurrentUser,
    authenticate_user,
    create_access_token,
    create_demo_user,
)
from database import SessionLocal, create_tables, get_session
from schemas import *

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    with SessionLocal() as session:
        create_demo_user(session)
    yield

app = FastAPI(title='API de Avaliação de Filmes', lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)

DatabaseSession = Annotated[Session, Depends(get_session)]

load_dotenv(Path(__file__).with_name('.env'))
tmdb_token = os.getenv('TMDB_ACCESS_TOKEN')
TMDB_MAX_PAGE = 500

@app.get(
    '/',
    tags=['Documentação'],
    summary='Documentação OpenAPI Swagger')
def home():
    '''
    Redireciona para a documentação Swagger da API de Avaliação de Filmes
    '''
    return RedirectResponse('/docs')





@app.get(
    '/movies',
    tags=['Filme'],
    summary='Obter lista de filmes para avaliação',
    response_model=MovieListSchema,
    status_code=200,
    responses={
        500: {'model': ErrorSchema},
        502: {'model': ErrorSchema},
        504: {'model': ErrorSchema},
    })
def get_movies(
    current_user: CurrentUser,
    page: Annotated[int, Query(ge=1, le=TMDB_MAX_PAGE)] = 1,
):
    '''
    Faz a busca por todos os filmes cadastrados na API TMDB

    Retorna uma lista de filmes da API TMDB
    '''

    if not tmdb_token:
        raise HTTPException(
            status_code=500,
            detail='TMDB access token is not configured',
        )

    url = 'https://api.themoviedb.org/3/movie/popular'
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {tmdb_token}'
    }
    params = {
        'language': 'pt-BR',
        'page': page
    }
    
    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=10
        )
    
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail='TMDB request timed out',
        )
    
    except requests.exceptions.RequestException:
        raise HTTPException(
            status_code=502,
            detail='Failed to communicate with TMDB',
        )

    if not response.ok:
        raise HTTPException(
            status_code=502,
            detail='TMDB returned an unexpected response',
        )

    try:
        movies = response.json()
        return {
            'page': movies['page'],
            'total_pages': min(movies['total_pages'], TMDB_MAX_PAGE),
            'movies': movies['results']
        }
    
    except (
        requests.exceptions.JSONDecodeError,
        KeyError,
        TypeError
    ):
        raise HTTPException(
            status_code=502,
            detail='TMDB returned an invalid response',
        )

@app.get(
    '/movies/ranking',
    tags=['Avaliação'],
    summary='Obter ranking de filmes mais bem avaliados',
    response_model=RankingListSchema,
    status_code=200)
def get_ranking(session: DatabaseSession, current_user: CurrentUser):
    '''
    Faz a busca pelos 10 filmes mais bem avaliados pelo usuário

    Retorna uma lista de filmes
    '''

    statement = (
        select(Review)
        .where(
            Review.user_id == current_user.user_id,
            Review.rating.is_not(None)
        )
        .order_by(
            Review.rating.desc(),
            Review.review_id.asc()
        )
        .limit(10)
    )

    reviews = session.scalars(statement).all()
    
    return {'movies': reviews}

@app.get(
    '/movies/watched', 
    tags=['Avaliação'],
    summary='Obter lista de filmes assistidos',
    response_model=WatchedListSchema,
    status_code=200)
def get_watched(session: DatabaseSession, current_user: CurrentUser):
    '''
    Faz a busca pelos últimos 20 filmes marcados como assistidos pelo usuário

    Retorna uma lista de filmes
    '''

    statement = (
        select(Review)
        .where(
            Review.user_id == current_user.user_id,
            Review.watched.is_(True)
        )
        .order_by(
            Review.updated_at.desc()
        )
        .limit(20)
    )

    reviews = session.scalars(statement).all()
    
    return {'movies': reviews}

@app.get(
    '/movies/{movie_id}',
    tags=['Filme'],
    summary='Obter filme pelo ID',
    response_model=MovieSchema,
    status_code=200,
    responses={
        404: {'model': ErrorSchema},
        500: {'model': ErrorSchema},
        502: {'model': ErrorSchema},
        504: {'model': ErrorSchema},
    })
def get_movie(movie_id: int, current_user: CurrentUser):
    '''
    Faz a busca de um filme pelo ID

    Retorna o filme
    '''

    if not tmdb_token:
        raise HTTPException(
            status_code=500,
            detail='TMDB access token is not configured',
        )

    url = f'https://api.themoviedb.org/3/movie/{movie_id}'
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {tmdb_token}'
    }
    params = {
        'language': 'pt-BR'
    }
    
    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=10
        )
    
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail='TMDB request timed out',
        )
    
    except requests.exceptions.RequestException:
        raise HTTPException(
            status_code=502,
            detail='Failed to communicate with TMDB',
        )

    if response.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail=f'Movie {movie_id} not found',
        )

    if not response.ok:
        raise HTTPException(
            status_code=502,
            detail='TMDB returned an unexpected response',
        )

    try:
        return response.json()
    
    except requests.exceptions.JSONDecodeError:
        raise HTTPException(
            status_code=502,
            detail='TMDB returned an invalid response',
        )





@app.post(
    '/reviews',
    tags=['Avaliação'],
    summary='Cria uma avaliação',
    response_model=ReviewSchema,
    status_code=201,
    responses={400: {'model': ErrorSchema}, 409: {'model': ErrorSchema}})
def store_review(
    payload: ReviewCreateSchema,
    session: DatabaseSession,
    current_user: CurrentUser,
):
    '''
    Registra uma avaliação em um filme (nota, comentário e/ou status de assistido)

    Retorna a avaliação feita
    '''

    data = payload.model_dump()

    is_empty_review = (
        not data['watched']
        and data['rating'] is None
        and (data['comment'] is None or data['comment'].strip() == '')
    )

    if is_empty_review:
        raise HTTPException(
            status_code=400,
            detail='A review must contain at least one piece of information',
        )
    
    review = Review(user_id=current_user.user_id, **data)
    
    try:
        session.add(review)
        session.commit()
        session.refresh(review)
    
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail='This movie already has a review')

    return review

@app.put(
    '/reviews/{review_id}',
    tags=['Avaliação'],
    summary='Atualizar avaliação pelo ID',
    response_model=ReviewSchema,
    status_code=200,
    responses={
        204: {'description': 'A avaliação ficou vazia e foi removida'},
        404: {'model': ErrorSchema},
    })
def update_review(
    review_id: int,
    payload: ReviewUpdateSchema,
    session: DatabaseSession,
    current_user: CurrentUser,
):
    '''
    Atualiza uma avaliação de um filme (nota, comentário e/ou status de assistido)

    Retorna a avaliação atualizada
    '''

    review = session.scalar(
        select(Review).where(
            Review.review_id == review_id,
            Review.user_id == current_user.user_id,
        )
    )
    
    if review is None:
        raise HTTPException(status_code=404, detail=f'Review {review_id} not found')
    
    data = payload.model_dump()

    is_empty_review = (
        not data['watched']
        and data['rating'] is None
        and (data['comment'] is None or data['comment'].strip() == '')
    )

    if is_empty_review:
        session.delete(review)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    
    allowed_fields = ['watched', 'rating', 'comment']
    
    for field, value in data.items():
        if field in allowed_fields:
            setattr(review, field, value)

    session.commit()
    session.refresh(review)
    
    return review

@app.delete(
    '/reviews/{review_id}',
    tags=['Avaliação'],
    summary='Remove avaliação pelo ID',
    status_code=204,
    responses={404: {'model': ErrorSchema}})
def remove_review(
    review_id: int,
    session: DatabaseSession,
    current_user: CurrentUser,
):
    '''
    Remove uma avaliação de um filme (nota, comentário e status de assistido)

    Retorna uma resposta sem conteúdo
    '''

    review = session.scalar(
        select(Review).where(
            Review.review_id == review_id,
            Review.user_id == current_user.user_id,
        )
    )

    if review is None:
        raise HTTPException(status_code=404, detail=f'Review {review_id} not found')
    
    session.delete(review)
    session.commit()
    return


@app.get(
    '/reviews/movie/{tmdb_movie_id}',
    tags=['Avaliação'],
    summary='Obter avaliação pelo ID do filme no TMDB',
    response_model=ReviewSchema,
    status_code=200,
    responses={404: {'model': ErrorSchema}})
def get_review_by_movie(
    tmdb_movie_id: int,
    session: DatabaseSession,
    current_user: CurrentUser,
):
    '''
    Busca a avaliação do usuário para um filme do TMDB

    Retorna a avaliação encontrada
    '''

    review = session.scalar(
        select(Review).where(
            Review.user_id == current_user.user_id,
            Review.tmdb_movie_id == tmdb_movie_id,
        )
    )

    if review is None:
        raise HTTPException(
            status_code=404,
            detail=f'Review for movie {tmdb_movie_id} not found',
        )

    return review





@app.post(
    '/login',
    tags=['Usuário'],
    summary='Autenticar usuário de demonstração',
    response_model=TokenSchema,
    status_code=200,
    responses={401: {'model': ErrorSchema}})
def login(payload: LoginSchema, session: DatabaseSession):
    user = authenticate_user(payload.email, payload.password, session)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail='Invalid email or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    return {
        'access_token': create_access_token(user),
        'token_type': 'bearer',
    }

@app.post(
    '/logout',
    tags=['Usuário'],
    summary='Encerrar sessão do usuário',
    status_code=status.HTTP_204_NO_CONTENT)
def logout(current_user: CurrentUser):
    return Response(status_code=status.HTTP_204_NO_CONTENT)





@app.get(
    '/health',
    tags=['Sistema'])
def health():
    '''
    Verifica a saúde da API

    Retorna status ok
    '''

    return {'status': 'ok'}
