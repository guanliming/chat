import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'chat-app-secret-key-12345'
    
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@localhost:5432/chat_app'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
