from pydantic import BaseModel, Field
from typing import List

class MovieSchema(BaseModel):
    '''
    Define como um filme que vem da API do TMDB deve ser representado
    '''

    id: int = Field(examples=[640146])
    overview: str | None = Field(examples=["Super-Hero partners Scott Lang and Hope van Dyne, along with with Hope's parents Janet van Dyne and Hank Pym, and Scott's daughter Cassie Lang, find themselves exploring the Quantum Realm, interacting with strange new creatures and embarking on an adventure that will push them beyond the limits of what they thought possible."])
    poster_path: str | None = Field(examples=['/ngl2FKBlU4fhbdsrtdom9LVLBXw.jpg'])
    release_date: str | None = Field(examples=['2023-02-15'])
    title: str = Field(examples=['Ant-Man and the Wasp: Quantumania'])

class MovieListSchema(BaseModel):
    '''
    Define como uma lista de filmes a serem avaliados deve ser representada
    '''

    page: int = Field(examples=[1])
    total_pages: int = Field(examples=[500])
    movies: List[MovieSchema]
