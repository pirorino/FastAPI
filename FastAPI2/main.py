import os
from fastapi import FastAPI, Request, Response
from db import database
from users.router import router as userrouter
from starlette.requests import Request

from fastapi.middleware.cors import CORSMiddleware
import datetime
####################
import time
import datetime
import sys
import json
from logging import getLogger, StreamHandler, DEBUG
from typing import Callable
from fastapi.routing import APIRoute
from pydantic import BaseModel

#################### for cluster execution
# AWS
# HOSTNAME = os.environ['HOSTNAME']
# EXPOSEPORT = "80"
# local
HOSTNAME = "localhost"
EXPOSEPORT = "8000"

print ("waitinghost is " + HOSTNAME)
print ("exposeport is " + EXPOSEPORT)
####################
logger = getLogger(__name__)
handler = StreamHandler(sys.stdout)
handler.setLevel(DEBUG)
logger.addHandler(handler)
logger.setLevel(DEBUG)

class LoggingContextRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            """
            時間計測
            """
            before = time.time()
            response: Response = await original_route_handler(request)
            duration = round(time.time() - before, 4)

            record = {}
            time_local = datetime.datetime.fromtimestamp(before)
            record["time_local"] = time_local.strftime("%Y/%m/%d %H:%M:%S%Z")
            if await request.body():
                record["request_body"] = (await request.body()).decode("utf-8")
            record["request_headers"] = {
                k.decode("utf-8"): v.decode("utf-8") for (k, v) in request.headers.raw
            }
            record["remote_addr"] = request.client.host
            record["request_uri"] = request.url.path
            record["request_method"] = request.method
            record["request_time"] = str(duration)
            record["status"] = response.status_code
            record["response_body"] = response.body.decode("utf-8")
            record["response_headers"] = {
                k.decode("utf-8"): v.decode("utf-8") for (k, v) in response.headers.raw
            }
            logger.info(json.dumps(record))
            return response

        return custom_route_handler

####################
app = FastAPI()
app.router.route_class = LoggingContextRoute

# CORS definition
origins = [
    "http://" + HOSTNAME + ".tiangolo.com",
    "https://" + HOSTNAME + ".tiangolo.com",
    "http://" + HOSTNAME,
    "http://" + HOSTNAME + ":" + EXPOSEPORT
]

# allow_credentials - オリジン間リクエストでCookieをサポートする必要があることを示します。デフォルトは False です。
# expose_headers - ブラウザからアクセスできるようにするレスポンスヘッダーを示します。デフォルトは [] です。
# max_age - ブラウザがCORSレスポンスをキャッシュする最大時間を秒単位で設定します。デフォルトは 600 です。

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#@app.add_api_route('/', index)
#@app.add_api_route('/admin', admin)  # new


# uvicorn main:app --reload
# pip install asyncpg
# pip install psycopg2
# pip install jinja2

# 起動時にDatabaseに接続する。
@app.on_event("startup")
async def startup():
    await database.connect()

# 終了時にDatabaseを切断する。
@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# users routerを登録する。
app.include_router(userrouter)

# middleware state.connectionにdatabaseオブジェクトをセットする。
@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    request.state.connection = database
    response = await call_next(request)
    return response
