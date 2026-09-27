from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

class ReviewCreateSchema(BaseModel):
    '''
    Define como deve ser a entrada para criação de uma avaliação
    '''

    tmdb_movie_id: int = Field(examples=[640146])
    tmdb_movie_title: str = Field(examples=['Ant-Man and the Wasp: Quantumania'])
    watched: bool = Field(examples=[True])
    rating: int | None = Field(default=None, ge=0, le=10, examples=[4])
    comment: str | None = Field(default=None, examples=['Bad movie!'])

class ReviewUpdateSchema(BaseModel):
    '''
    Define como deve ser a entrada para atualização de uma avaliação
    '''

    watched: bool = Field(examples=[True])
    rating: int | None = Field(default=None, ge=0, le=10, examples=[1])
    comment: str | None = Field(default=None, examples=['The worst movie!!!'])

class ReviewSchema(BaseModel):
    '''
    Define como uma avaliação deve ser representada
    '''
    
    review_id: int = Field(examples=[1])
    tmdb_movie_id: int = Field(examples=[640146])
    tmdb_movie_title: str = Field(examples=['Ant-Man and the Wasp: Quantumania'])
    watched: bool = Field(examples=[True])
    rating: int | None = Field(default=None, ge=0, le=10, examples=[4])
    comment: str | None = Field(default=None, examples=['Bad movie!'])

class RankingListSchema(BaseModel):
    '''
    Define como uma lista de filmes deve ser representada no ranking
    '''

    movies: List[ReviewSchema]

class WatchedListSchema(BaseModel):
    '''
    Define como uma lista de filmes deve ser representada na lista de assistidos
    '''

    movies: List[ReviewSchema]
