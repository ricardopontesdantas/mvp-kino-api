from pydantic import BaseModel, Field

class UserSchema(BaseModel):
    '''
    Define como um usuário será representado
    '''

    name: str = 'John Doe'
    email: str = 'johndoe@example.com'


class LoginSchema(BaseModel):
    '''
    Define os dados necessários para o login
    '''

    email: str = Field(examples=['demo@example.com'])
    password: str = Field(examples=['demo123'])


class TokenSchema(BaseModel):
    '''
    Define a resposta devolvida após um login válido
    '''

    access_token: str
    token_type: str = 'bearer'
