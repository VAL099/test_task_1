"""
Realizare aplicatie care permite inregistrarea unui utilizator, 
dupa inregistrare isi poate genera un token autorizare API. 
In baza acelui token utilizatorul poate face doar 50 requesturi pe zi, 
daca trece limita sa fie afisat un mesaj "Limit out" 
"""

import sqlite3
import threading
import secrets
import redis
from datetime import datetime
from hashlib import sha256
import uvicorn
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import RedirectResponse, Response, JSONResponse
from apscheduler.schedulers.background import BackgroundScheduler
from handlers import DB_Writer
import models
import handlers

thread_local = threading.local()
app = FastAPI()
scheduler = BackgroundScheduler() # for updating 
redis_instance = redis.Redis(host='localhost', port=6379, db=0) # this redis instance is running in Docker

tokens = {} # this is for storing tokens locally

"""SETUP DB, cuz SQLite doesn't support multi-threading"""
def get_db_writer():
    # Check if DB_Writer instance already exists for the current thread
    if not hasattr(thread_local, 'db_writer'):  
        connection_with_db = sqlite3.connect('project_db.db')
        thread_local.db = DB_Writer(connection_with_db)
    return thread_local.db

"""Setting up token refresher"""
@app.on_event("startup")
async def startup_event():
    scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()

@scheduler.scheduled_job("cron", hour=0)  
def daily_routine():
    # if it's stored locally
    tokens = {key: [tokens[key][0], 0] for key in tokens}
    # If it's stored in redis
    # redis_dict = redis_instance.keys()
    # updated_dict = {key.decode(): [value.decode(), 0] for key, value in redis_dict.items()}
    # redis_instance.set('hash_key', updated_dict)
    """ not sure if it's exactly right with redis approach """ 

@app.get('/', include_in_schema=False)
async def home():
    return RedirectResponse(url='/docs')

@app.post('/register')
async def register(reg_model: models.Register):
    try:
        get_db_writer().reg_user(reg_model.username, 
                                 sha256(reg_model.password.encode()).hexdigest())
        return Response(status_code=201)
    except Exception as error:
        raise HTTPException(status_code=406, detail=f'Failed!\n{error}')
    
@app.get('/generate_token')
async def generate_token(user:str = Header()):
    # creating 32bytes token
    if user not in tokens:
        token = secrets.token_urlsafe(32)
        # create a dict {possesor: [token, uses]}
        """This is for REDIS aproach"""
        # redis_instance.set(user, [token, 0])  # for storing tokens in Redis instance
        """If tokens are stored locally aproach"""
        tokens.setdefault(user, [token, 0])
        return JSONResponse(status_code=201, content={'token':token})
    raise HTTPException(status_code=401, detail='You already posses a token!')

@app.get('/{id}/avg')
async def get_product_avg(id:int, user:str = Header(), token:str = Header()):

    # request.cookies.get('user')
    try:
        if user in tokens and tokens[user][0] == token and tokens[user][1] < 10:
            # increment token use count
            tokens[user][1] += 1
            # get requested data
            data = get_db_writer().get_product_mark(id)
            if data == []:
                return Response(status_code = 404)    
            prod_name, prod_mark = handlers.task1(data)
            return JSONResponse(status_code = 200, 
                                content = { "nume":prod_name, "nota_medie":prod_mark })        
        # if day limit achieved!
        if tokens[user][1] == 10:
            raise HTTPException(status_code=401, detail='LIMIT OUT!')
        if tokens[user][0] != token:
            raise HTTPException(status_code=401, detail='Wrong token!')
    except KeyError:
        raise HTTPException(status_code=401, detail='Please, generate an access token first!')

@app.get('/{id}/reviews')
async def get_product_avg(id:int, user:str = Header(), token:str = Header()):

    # request.cookies.get('user')
    try:
        if user in tokens and tokens[user][0] == token and tokens[user][1] < 10:
            # increment token use count
            tokens[user][1] += 1
            # get requested data
            data = get_db_writer().get_product_evals(id)
            if data == []:
                return Response(status_code = 404)   
            prod_name, prod_evaluations = handlers.task2(data)
            
            return JSONResponse(status_code = 200, 
                                content = { "nume":prod_name, "evaluations":prod_evaluations })        
        # if day limit achieved!
        if tokens[user][1] == 10:
            raise HTTPException(status_code=401, detail='LIMIT OUT!')
        if tokens[user][0] != token:
            raise HTTPException(status_code=401, detail='Wrong token!')
    except KeyError:
        raise HTTPException(status_code=401, detail='Please, generate an access token first!')



if __name__ == "__main__": 

    uvicorn.run('app:app', port=4587, reload=True)
