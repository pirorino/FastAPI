from asyncio.windows_events import NULL
import os
import hashlib
import pdb
import json
import ast
from fastapi import APIRouter, Depends, HTTPException, UploadFile,File,Form
from typing import List
from starlette.requests import Request

from databases import Database
# from sqlalchemy.sql import text

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from jose import jwt
import logging
from starlette.templating import Jinja2Templates  # new

from utils.dbutils import get_connection
from .models import users
from .models import pointtran
from .models import pointstock

# 2021/12/12 Hirayama added start
from .models import nbtt_conversation_lists
from .models import nbmt_users
# 2021/12/12 Hirayama added end

# 2022/09/25 Hirayama added start
from .models import nbet_surveys
# 2022/09/25 Hirayama added end

from .schemas import UserCreate, UserUpdate, UserSelect, Token
from .schemas import PointTranCreate, PointTranUpdate, PointTranSelect
from .schemas import PointStockCreate, PointStockUpdate, PointStockSelect
from .schemas import CompleteList

# 2021/12/12 Hirayama added start
from .schemas import nbtt_user_statusSelect,nbtt_user_statusCreate,nbtt_conversation_listsSelect,nbtt_conversation_listsCreate
from .schemas import nbmt_usersSelect,nbmt_usersCreate,nbmt_usersUpdate
# 2021/12/12 Hirayama added end

# 2022/09/25 Hirayama added start
from .schemas import nbet_surveysCreate,nbet_surveysSelect
# 2022/09/25 Hirayama added end

import shutil
# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")
jinja_env = templates.env  # Jinja2.Environment : filterやglobalの設定用

Secret_Key = "S08EbmDoqkD7T6yhDMxDaxm27Fadt2s9d"
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 入力したパスワード（平文）をハッシュ化して返します。
# def get_users_insert_dict(user):
#    subroutine = "get_users_insert_dict"
#    print("function :" + subroutine)
#    pwhash=hashlib.sha256(user.password.encode('utf-8')).hexdigest()
#    values=user.dict()
#    values.pop("password")
#    values["hashed_password"]=pwhash
#    return values

def get_users_insert_dict(password:str):
    subroutine = "get_users_insert_dict"
    print("function :" + subroutine)
    pwhash=hashlib.sha256(password.encode('utf-8')).hexdigest()
    # values=user.dict()
    # values.pop("password")
    # values["hashed_password"]=pwhash
    return pwhash

# def test_dict(user):
#     values=user.dict()
#     return values


# async def create_tokens(database: Database,username: str): 20211212 hirayama modified
async def create_tokens(database: Database,email: str):
    """パスワード認証を行い、トークンを生成"""
    try:
        subroutine = "create_tokens"
        print("function :" + subroutine)
        # ペイロード作成
        access_payload = {
            'token_type': 'access_token',
            'exp': datetime.utcnow() + timedelta(minutes=60),
        #    'username': username, 20211212 hirayama modified
            'username': email,
        }
        refresh_payload = {
            'token_type': 'refresh_token',
            'exp': datetime.utcnow() + timedelta(days=30),
        #    'username': username, 20211212 hirayama modified
            'username': email,
        }

        # トークン作成
        access_token = jwt.encode(access_payload, Secret_Key, algorithm='HS256')
        refresh_token = jwt.encode(refresh_payload, Secret_Key, algorithm='HS256')
        print("create token succeeded")
        # DBにリフレッシュトークンを保存
        # print("username:" + username)
        # print("refresh_token:" + refresh_token)
        # query = users.update().where(users.columns.username==username).values(refresh_token=refresh_token)  20211212 hirayama modified   
        query = nbmt_users.update().where(nbmt_users.columns.email==email).values(refresh_token=refresh_token)
        ret = await database.execute(query)
        # ユーザIDも返すように変更
        user = await get_user_info(database, email)
        UserId = user[0]
        print("UserId:" + str(UserId))

        print("access_token:" + access_token)
        print("refresh_token:" + refresh_token)
        return {'access_token': access_token, 'refresh_token': refresh_token, 'userId': str(UserId), 'token_type': 'bearer'}
        # return {'access_token': access_token, 'refresh_token': refresh_token, 'token_type': 'bearer'}
    except Exception as e:
        raise HTTPException(status_code=401, detail=subroutine + ":" + str(e))

async def get_current_user_from_token(database: Database,token: str, token_type: str):
    """tokenからユーザーを取得"""
    # トークンをデコードしてペイロードを取得。有効期限と署名は自動で検証される。
    try:
        subroutine = "get_current_user_from_token"
        print(subroutine)
        payload = jwt.decode(token, Secret_Key, algorithms=['HS256'])

        # トークンタイプが一致することを確認
        if payload['token_type'] != token_type:
            raise HTTPException(status_code=401, detail=f'token type unmatched')

        # DBからユーザーを取得
        # query = users.select().where(users.columns.username==payload['username'])
        query = nbmt_users.select().where(nbmt_users.columns.user_id==payload['user_id'])
        user = await database.fetch_one(query)
        print("token_type:",token_type)

        # リフレッシュトークンの場合、受け取ったものとDBに保存されているものが一致するか確認
        if token_type == 'refresh_token' and user[4] != token:
            print("db:",user[4], '\n', "token:",token)
            raise HTTPException(status_code=401, detail='refresh token unmatched')
        print(user)
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail=subroutine + ":" + str(e))

async def check_token(token: str, token_type: str):
    """tokenをチェック"""
    # トークンをデコードしてペイロードを取得。有効期限と署名は自動で検証される。
    try:
        subroutine = "check_token"
        print("function :" + subroutine)
        print("token :" + token)
        payload = jwt.decode(token, Secret_Key, algorithms=['HS256'])

        # print("user_name get")
        # トークンタイプが一致することを確認
        # user_name = payload.get('username')  20211212 hirayama modified
        # print("user_name:" + user_name) 20211212 hirayama modified
        # if user_name is None: 20211212 hirayama modified

        email = payload.get('username')
        print("email:" + email)
        if email is None:
            raise HTTPException(status_code=401, detail=f'token user unmatched')
        if payload['token_type'] != token_type:
            raise HTTPException(status_code=401, detail=f'token type unmatched')
        # return user_name  20211212 hirayama modified
        return email
    except Exception as e:
        raise HTTPException(status_code=401, detail=subroutine + ":" + str(e))

# async def authenticate(database: Database,username: str, password: str): 20211212 hirayama modified
async def authenticate(database: Database,email: str, password: str):
    # パスワード認証し、userを返します。
    # user = User.get(name=name)
    # print("authenticate username:" + username)
    print("authenticate user_id:" + str(email))
    try:
        subroutine = "authenticate"
        print("function :" + subroutine)
        # query = users.select().where(users.columns.username==username) 20211212 hirayama modified
        query = nbmt_users.select().where(nbmt_users.columns.email==email)
        ret = await database.fetch_one(query)
        # print("hashed_password:",ret[3])
        # user = db.query(User).filter(User.email == email).first()
    except Exception as e:
        print("authenticate db error" + str(e))
        raise HTTPException(status_code=401, detail=subroutine + ":" + str(e))
    if ret == None:
        print("no user")
        raise HTTPException(status_code=401, detail='no data matched')
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
    # if ret[3] != hashed_password: 20211212 hirayama modified
    if ret[6] != hashed_password:
        print("password unmatch")
        raise HTTPException(status_code=401, detail='password unmatch')
    print("return from authenticate")
    return ret

# usersを全件検索して「UserSelect」のリストをjsonにして返します。
# @router.get("/users/super/del")
# async def read_users_super_del(delete_user: UserUpdate,token: str = Depends(oauth2_scheme),database: Database = Depends(get_connection)):
#     print("/users/super/del start")
#     user = await get_current_user_from_token(database,token , 'access_token')

# curl -X GET "http://localhost:8000/"

# async def check_privilege(database: Database,username: str): 20211212 hirayama modified
async def check_privilege(database: Database,email: str):
    """userから権限を取得"""
    try:
        subroutine = "check_privilege"
        print("function :" + subroutine)

        # DBからユーザーを取得
        # query = users.select().where(users.columns.username==username) 20211212 hirayama modified
        query = nbmt_users.select().where(nbmt_users.columns.email==email)
        ret = await database.fetch_one(query)
        ## [6]はis_superuser 20211212 hirayama modified
        #return ret[6] 20211212 hirayama modified
        # [8]はis_superuser
        return ret[8]
    except Exception as e:
        raise HTTPException(status_code=401, detail=subroutine + ":" + str(e))

async def get_user_info(database: Database,email: str): #20211229 komata modified
    # """emailからuser情報を取得"""
    try:
        subroutine = "get_user_info"
        print("function :" + subroutine)

        # DBからユーザーを取得
        query = nbmt_users.select().where(nbmt_users.columns.email==email)
        query.compile(compile_kwargs={"literal_binds": True})
        ret = await database.fetch_one(query)
        return ret
    except Exception as e:
        raise HTTPException(status_code=401, detail=subroutine + ":" + str(e))

async def set_user_info(database: Database,email: str): #20220121 komata modified
    try:
        subroutine = "set_user_info"
        query = nbmt_users.update().where(nbmt_users.columns.email==email).values(refresh_token=refresh_token)
        ret = await database.execute(query)
    except Exception as e:
        raise HTTPException(status_code=401, detail=subroutine + ":" + str(e))

async def get_max_userID(database: Database):
    # ユーザテーブルから、最大のUserIDを返す
    try:
        subroutine = "get_max_userID"
        print(subroutine)

        # DBから最大ユーザーIDを取得
        query = "select max(user_id) from nbmt_users"
#        query = nbmt_users.select().where(nbmt_users.columns.user_id==payload['user_id'])
        maxUserID = await database.fetch_one(query)
        print("maxUserID:",maxUserID)

        return maxUserID
    except Exception as e:
        raise HTTPException(status_code=401, detail=subroutine + ":" + str(e))

@router.get('/')
async def get_index(request: Request):
    # 初期画面の表示
    subroutine = "index"
    print("function :" + subroutine)
    return templates.TemplateResponse('index.html',{'request': request})

@router.get('/login')
async def login(request: Request):
    subroutine = "login"
    print("function :" + subroutine)
    # login画面の表示
    return templates.TemplateResponse('login.html',{'request': request})

@router.post("/fileupload")
async def fileupload_post_multi(request: Request,files: List[UploadFile] = File(...), access_token: str = Form(...),database: Database = Depends(get_connection)):
    ''' docstring
    アップロードされたファイルを保存する。開発中であり正常動作しない
    '''
    # トークンのチェック
    try:
        user = await check_token(access_token , 'access_token')
        print("user:" + user)
    except Exception as e:
        print("fileupload_post_multi check_token error:" + str(e))
        return {"errorcode": 2,"msg": "token check error"}

    try:
        subroutine = "upload_file"
        # form = await request.form()
        uploadedpath = "./uploads"
        now = datetime.now()

        file_no = 0
        # files = os.listdir(uploadedpath)
        # for formdata in form:

        # transaction = await database.transaction()
        # await transaction.start()
        for file in files:
            file_no = file_no + 1
            filename = user + "_" + str(file_no).zfill(4) + "_" + file.filename 
            path = os.path.join(uploadedpath, filename)
            fout = open(path, 'wb')
            while 1:
                chunk = await file.read(100000)
                if not chunk: break
                fout.write (chunk)
            fout.close()

            entry_data = {
                "username": user,
                "filename": filename,
                "update_datetime": now.strftime('%Y%m%d%H%M%S'),
                "path": path,
                "is_deleted": False
            }

            query = "INSERT INTO userpicture (username,filename,update_datetime,path,is_deleted) values ('%s','%s',TO_TIMESTAMP('%s', 'YYYYMMDDHH24MISS'),'%s',%s ) \
               ON CONFLICT  ON CONSTRAINT userpicture_pkey DO UPDATE SET filename = '%s',path = '%s'" \
                % (entry_data["username"],entry_data["filename"],entry_data["update_datetime"],entry_data["path"],entry_data["is_deleted"],entry_data["filename"],entry_data["path"])
            
            print("db exec:" + query)
            result = await database.execute(query)
            print (result)
        # await transaction.commit()
        return {"status":"OK"}    
    except Exception as e:
        raise HTTPException(status_code=401, detail=subroutine + ":" + str(e))

@router.post('/pages/{pagename}')
async def post_pagename(request: Request,pagename: str,access_token: str,param: str = "",database: Database = Depends(get_connection)):
    # 汎用ページ表示処理
    print("/pages/" + pagename + " loaded")

    # トークンのチェック
    # user = await check_token(access_token , 'access_token')  20211212 hirayama modified
    email = await check_token(access_token , 'access_token')
    # print("user:" + user)  20211212 hirayama modified
    print("email:" + email)
    user = await get_user_info(database, email) #20211229 komata modified
    print("user:" + str(user[0]))
    # ユーザの権限チェック
    # is_superuser = await check_privilege(database,user)  20211212 hirayama modified
    is_superuser = await check_privilege(database,email)
    page_file = pagename + '.html'
    
    print("load /templates/" + page_file)
    if pagename == 'toppage':
        print('this is toppage')
        if is_superuser == True:
        # superuserの場合、管理者用画面を表示
            page_file = pagename + '_admin.html'
    elif pagename == 'profile':  #20211229 komata modified
        print('profile')
    elif pagename == 'hobby':  #20211229 komata modified
        print('hobby')
    elif pagename == 'nbcmain':
        print('nbcmain page')
        # page_file = pagename + '.html'
    # 2022/9/18 modified start
    elif pagename == 'jitsi_api':
        # jitsi会話画面
        now = datetime.now()
        print('this is jitsi_api')
        conversation_code = param.split(':')[0]
        user_id = param.split(':')[1]
        if user_id == "":
            user_id = 0
        query = "select username_sei,username_mei from nbmt_users where user_id ='%s'"  % (user_id)
        print(query)
        result = await database.fetch_all(query)
        result_length = len(result)
        if result_length == 0:
            fullname = "anonymous"
        else:
            fullname = result[0][0] + " " + result[0][1] 
        print("conversation_code:" + conversation_code + " fullname:" + fullname)

        # 受け側の場合はreservation_talking_category の更新 2022/11/12 added
        query = nbtt_conversation_lists.update().where(nbtt_conversation_lists.columns.conversation_code==conversation_code).where(nbtt_conversation_lists.columns.to_user_id==int(user_id)).values( \
        reservation_talking_category="talking", \
        update_timestamp=now, \
        update_user_id=int(user_id) \
        )
        print("query jitsi_api - ConversationListUpdate:" + str(query))
        resultset = await database.execute(query)
        # 受け側の場合はreservation_talking_category の更新 2022/11/12 added end

        return templates.TemplateResponse(page_file,{'request': request,'chatroomName': conversation_code,'fullname': fullname,'userid': user_id})
    # 2022/9/18 modified end
    elif pagename == 'pointtranlist':
        # ポイントトランザクションの一覧処理
        print('this is pointtranlist')
        prevbtn = 0
        nextbtn = 0
        if is_superuser == True:
            # superuserの場合、全データを表示
            query = "select row_number() over() as number,* from pointtran"
        else:
            # superuserでない場合、元または先がログインユーザのデータを表示
            # query = "select row_number() over() as number,* from pointtran where from_user_name = '%s' or to_user_name = '%s'"  % (user,user) 20211212 hirayama modified
            query = "select row_number() over() as number,* from pointtran where from_user_name = '%s' or to_user_name = '%s'"  % (email,email)
        if param != "":
            # parameterが設定されている（現在表示NOがある）場合、param以降のデータを表示する
            maxcount = int(param)
            query = query + " limit 31 offset %s" % (maxcount)
        else:
            # parameterが設定されていない（現在表示NOがない、初期状態）場合、1行目以降のデータを表示する
            query = query + " limit 31 offset 0"
        print(query)
        # SELECT * FROM sample LIMIT 4 OFFSET 2;
        result = await database.fetch_all(query)
        result_length = len(result)
        if result_length == 0:
            # empty =["","empty","","","",""]
            # result.append(empty)
            # print(str(result[0][0]))
            print("prevbtn:" + str(prevbtn))
            print("nextbtn:" + str(nextbtn))
        else:
            print(result[0])
            if result[0][0] != 1:
                # 先頭が1行目ではない場合、前画面表示ができるという事
                prevbtn = result[0][0]
            if result_length == 31:
                # 結果が31行取得できたなら、次画面表示ができるという事
                nextbtn = 30
                del result[-1]
        return templates.TemplateResponse(page_file,{'request': request,'pointtran': result,'prevbtn': prevbtn,'nextbtn': nextbtn})
    elif pagename == 'sendpointtran':
        # ポイント送信登録処理、現在の所持ポイント数を表示する為fetchする
        print('this is sendpointtran')
        pointstock = 0
        # query = "select point,version from pointstock where username = '%s' "  % (user)  20211212 hirayama modified
        query = "select point,version from pointstock where username = '%s' "  % (email)
        resultstock = await database.fetch_one(query)
        pointstock = resultstock["point"]
        version = resultstock["version"]
        print(pointstock)
        print(version)
        return templates.TemplateResponse(page_file,{'request': request,'pointstock': pointstock,'version': version})
    elif pagename == 'userlist':
        # 単純なユーザ一覧
        query = users.select()
        print('this is userlist')
        return templates.TemplateResponse(page_file,{'request': request,'user': await database.fetch_all(query)})
    elif pagename == 'picture':
        # 画像表示、開発中
        print('this is picture test')
        return templates.TemplateResponse(page_file,{'request': request})
    else:
        print('Sorry, we are out of ' + pagename + '.')
    print("call newpage")
    return templates.TemplateResponse(page_file,{'request': request,'user': user})  #20211229 komata modified

    # curl -X GET "http://localhost:8000/pages/test/" -H  "accept: application/json" -H  "Authorization: Bearer {eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzX3Rva2VuIiwiZXhwIjoxNjE1OTAxNzE4LCJ1c2VybmFtZSI6InBpcm9yaW5vIn0.YtqZEfBQ3WaoImnIXw6sMZfNtZpUS3KAYJi5nuvDmE0}}"

@router.get('/static/js/js_auth')
async def get_js_auth(request: Request):
    # js_auth.jsは静的ファイルだが、jinja2テンプレートファイルとして配置したので/static/js/以下にない
    return templates.TemplateResponse('js_auth.js',{'request': request})

# @router.get("/users/super", response_model=List[UserSelect]) 20211212 hirayama comment out
# async def users_findall(token: str = Depends(oauth2_scheme),database: Database = Depends(get_connection)):
#     # superuserの場合、usersを全件検索して「UserSelect」のリストをjsonにして返します。
#     try:
#         subroutine = "users_findall"
#         users = await get_current_user_from_token(database,token , 'access_token')
#         query = users.select()
#         return await database.fetch_all(query)
#     except Exception as e:
#         raise HTTPException(status_code=401, detail=subroutine + ":" + str(e))
# curl -X GET "http://localhost:8000/users/super" -H  "accept: application/json" -H  "Content-Type: application/x-www-form-urlencoded" -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzX3Rva2VuIiwiZXhwIjoxNjE0MDY1MTY0LCJ1c2VybmFtZSI6InBpcm9yaW5vIn0.kKFsEqorI_LO16vIbrxPe8C1jsGq9B2rJghVSfaARtE"

# @router.get("/users/find", response_model=UserSelect) 20211212 hirayama comment out
# async def users_findone(id: int, database: Database = Depends(get_connection)):
#     # usersをidで検索して「UserSelect」をjsonにして返します。
#     try:
#         subroutine = "users_findone"
#         query = users.select().where(users.columns.id==id)
#         return await database.fetch_one(query)
#     except Exception as e:
#         raise HTTPException(status_code=401, detail=subroutine + ":" + str(e))
# http://localhost:8000/users/find?id=1

#@router.post("/users/create", response_model=UserSelect) 20211212 hirayama comment out
# async def users_create(user: UserCreate, database: Database = Depends(get_connection)):
#     # usersを新規登録します。curlから実行
#     # validatorは省略
#     try:
#         subroutine = "users_create"
# 
#         # usersを作成
#         query = users.insert()
#         values = get_users_insert_dict(user)
#         ret = await database.execute(query, values)
# 
#         # pointstockを作成
#         now = datetime.now()
# 
#         entry_data = {
#             "username": user.username,
#             "update_datetime": now.strftime('%Y%m%d%H%M%S'),
#             "point": 100,
#             "version": "1",
#             "is_deleted": False
#         }
#         query = "INSERT INTO pointstock \
#             (username,update_datetime, point,version,is_deleted) \
#                 values \
#             ('%s',TO_TIMESTAMP('%s', 'YYYYMMDDHH24MISS'),%s,'%s',%s)" \
#             % (entry_data["username"],entry_data["update_datetime"],entry_data["point"],entry_data["version"],entry_data["is_deleted"])
#         print("db exec:" + query)
#         ret = await database.execute(query)
#         return {**user.dict()}
#     except Exception as e:
#         raise HTTPException(status_code=401, detail=subroutine + ":" + str(e))
# curl -X POST "http://localhost:8000/users/create" -H  "accept: application/json" -H  "Content-Type: application/x-www-form-urlencoded" -d @create_user.json
# curl -X POST "http://localhost:8000/users/create" -H  "accept: application/json" -H  "Content-Type: application/x-www-form-urlencoded" -d @create_user2.json

@router.post("/pt/create")
async def ptCreate(pt: PointTranCreate,access_token: str,database: Database = Depends(get_connection)):
    # ポイントを送信する。トークンをチェック、送り先ユーザチェック、所有ポイントチェック、トラン作成、所有ポイント更新
    # トークンチェック
    try:
        ptvalues = pt.dict()
        subroutine = "PointTranCreate"
        print(subroutine + ":try check_token:" + access_token )
        ct = await check_token(access_token , 'access_token')
    except Exception as e:
        print("ptcreate check_token error:" + str(e))
        return {"errorcode": 2,"msg": "token check error"}
        # raise HTTPException(status_code=401, detail=subroutine + ":" + str(e))

    # SQL(receivercheck)実行
    try:
        query = "select count(*) from users where username ='%s'" % (ptvalues["to_user_name"])
        print("db exec:" + query)
        result = await database.execute(query)
        if result == 0:
            print("count:" + str(result))
            return {"errorcode": 1,"msg": "送り先ユーザが存在しません"}
    except Exception as e:
        print("ptcreate check error:" + str(e))
        return {"errorcode": 1,"msg": "その他のSQL(check)エラー"}

    # SQL(stockcheck)実行
    try:
        query = "select * from pointstock where username ='%s'" % (ptvalues["from_user_name"])
        print("db exec:" + query)
        result1 = await database.fetch_one(query)
        print(dict(result1))

        if result1["point"] < ptvalues["point"]: # 登録ポイントよりpointstockテーブルの値が小さい場合
            print("count:" + str(result1))
            return {"errorcode": 1,"msg": "ポイントが足りません"}
        before_point = result1["point"]
        before_version = int(result1["version"])
        after_version = before_version + 1
    except Exception as e:
        print("ptcreate stockcheck error:" + str(e))
        return {"errorcode": 1,"msg": "その他のSQL(stockcheck)エラー"}

    # SQL(pointstockのupdate 及び pointtranのinsert)実行
    nowdate = datetime.now()
    # 以下、transactionはローカルpostgresでは動作していたがコンテナに移動してから動作しなくなった。バグ
    # transactionを有効にするとエラーにはならないが書き込みがcommitされない
    # transaction = await database.transaction()
    try:
        # await transaction.start()
        query = "UPDATE pointstock SET update_datetime = '%s',point = %s, version = '%s', is_deleted = %s \
            where username = '%s' and version = '%s'" \
            % (nowdate,before_point - ptvalues["point"],str(after_version),ptvalues["is_deleted"],ptvalues["from_user_name"],str(before_version))
        print("db exec:" + query)
        result = await database.execute(query)
        # updateがエラーになったらバージョン違いの可能性が高い
        
        query = "INSERT INTO pointtran \
            (create_date,from_user_name, to_user_name, entry_date, point, comment, is_deleted) \
                values \
            ('%s','%s','%s', TO_TIMESTAMP('%s', 'YYYYMMDDHH24MISS'),%s,'%s',%s)" \
            % (nowdate,ptvalues["from_user_name"],ptvalues["to_user_name"],ptvalues["entry_date"],ptvalues["point"],ptvalues["comment"],ptvalues["is_deleted"])
        print("db exec:" + query)
        result = await database.execute(query)
        # await transaction.commit()

        return {"errorcode": 0,"msg": "登録しました","newstock": before_point - ptvalues["point"]}
    except Exception as e:
        # await transaction.rollback()
        print("ptcreate insert error:" + str(e))
        return {"errorcode": 1,"msg": "登録に失敗しました。再度実行してください。"}
        # raise HTTPException(status_code=401, detail=subroutine + ":" + str(e))

# curl -X POST "http://localhost:8000/pt/create?access_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzX3Rva2VuIiwiZXhwIjoxNjE2MDg1NTAzLCJ1c2VybmFtZSI6InBpcm9yaW5vIn0.Y3pAEMaZfOcxVdMEB7FzHumj8PREHVT5H2OrEAsrJMA","refresh_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaF90b2tlbiIsImV4cCI6MTYyMzg1NzkwMywidXNlcm5hbWUiOiJwaXJvcmlubyJ9.vXNNbWxLzJEx0QKXMqeHPYCjTFO9JfEKJ803HYRbyKc" -H  "accept: application/json" -H  "Content-Type: application/x-www-form-urlencoded" -d @create_pt.json

@router.post("/autocomplete-tousername")
async def autocomplete_gettousername(complete_str: str,access_token: str,database: Database = Depends(get_connection)):
    # ユーザ名の予測入力機能
    try:
        subroutine = "autocomplete_gettousername"
        print("function :" + subroutine)
        # user = await check_token(access_token , 'access_token')

        query = users.select().where(users.c.username.like(complete_str + '%'))
        results = await database.fetch_all(query=query)
        candidatelist = []
        for result in results:
            print(result[1])
            candidatelist.append(result[1])
        return candidatelist
    except Exception as e:
        raise HTTPException(status_code=401, detail=subroutine + ":" + str(e))
    
    # curl -X POST "http://localhost:8000/autocomplete-tousername?access_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzX3Rva2VuIiwiZXhwIjoxNjE2MDg1NTAzLCJ1c2VybmFtZSI6InBpcm9yaW5vIn0.Y3pAEMaZfOcxVdMEB7FzHumj8PREHVT5H2OrEAsrJMA&complete_str=p" -H  "accept: application/json" -H  "Content-Type: application/x-www-form-urlencoded" -d @complete.json

@router.post("/token")
async def get_token(form: OAuth2PasswordRequestForm = Depends(),db: Database = Depends(get_connection)):
    # トークンを発行します
    try:
        subroutine = "get_token"
        print("function :" + subroutine + ":" + form.username + ":" + form.password)
        user = await authenticate(db, form.username, form.password)
        # print("user:",user[1])
        # token = await create_tokens(db, user[1]) 20211212 hirayama modified
        token = await create_tokens(db, user[5])
        print("generated token:",token)
        return token
    except Exception as e:
        print("get_token_error")
        raise HTTPException(status_code=401, detail=subroutine + ":" + str(e))
# curl -X POST "http://localhost:8000/token" -H  "accept: application/json" -H  "Content-Type: application/x-www-form-urlencoded" -d "username=pirorino&password=password"

@router.get("/users/me/")
async def read_users_me(token: str = Depends(oauth2_scheme),database: Database = Depends(get_connection)):
    # アクセストークンを受け取ってカレントユーザを返却します。画面なし、未使用
    try:
        subroutine = "read_users_me"
        print("function :" + subroutine)
        user = await get_current_user_from_token(database,token , 'access_token')
        """ログイン中のユーザーを取得"""
        print("user:",user)
        # curl -X GET "http://localhost:8000/users/me/" -H  "accept: application/json" -H  "Authorization: Bearer {access_token}}"
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail=subroutine + ":" + str(e))

@router.get("/refresh_token")
async def refresh_token(token: str = Depends(oauth2_scheme) ,database: Database = Depends(get_connection)):
    # リフレッシュトークンでトークンを再取得します。
    try:
        subroutine = "refresh_token"
        print("/refresh_token start")
        user = await get_current_user_from_token(database,token , 'refresh_token')
        print("create_tokens:",user[1])
        # curl -X GET "http://localhost:8000/refresh_token" -H  "accept: application/json" -H  "Authorization: Bearer {refresh_token}}"
        # eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaF90b2tlbiIsImV4cCI6MTYyNDQ0NjEyMywidXNlcm5hbWUiOiJwaXJvcmlubyJ9.0B2gnPj6jACeaRiuGos9KvB9gUIME0vJKOv2xxUsm0U
        return await create_tokens(database, user[1])
    except Exception as e:
        print("refresh_token Exception occured" + str(e))
        raise HTTPException(status_code=401, detail=subroutine + ":" + str(e))

@router.get("/users/super/del")
async def read_users_super_del(delete_user: UserUpdate,token: str = Depends(oauth2_scheme),database: Database = Depends(get_connection)):
    # アクセストークンを受け取りスーパーuserの場合ユーザをidで削除します。画面なし、curlから実行
    try:
        subroutine = "read_users_super_del"
        print("function :" + subroutine)
        user = await get_current_user_from_token(database,token , 'access_token')
        """ログイン中のユーザーを取得"""
        # print("user:",user)
        if user[6] != True:
            raise HTTPException(status_code=401, detail='not superuser')
            # curl -X GET "http://localhost:8000/users/super/del" -H  "accept: application/json" -H  "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzX3Rva2VuIiwiZXhwIjoxNjE0MDY1MTY0LCJ1c2VybmFtZSI6InBpcm9yaW5vIn0.kKFsEqorI_LO16vIbrxPe8C1jsGq9B2rJghVSfaARtE"  -d "{\"id\":2,\"username\":\"delete_test\",\"email\":\"delete_test_pirorino\",\"password\":\"delete\",\"is_active\":true,\"is_superuser\":false}"
        print("superuser operation")
        query = users.delete().where(users.columns.id==delete_user.id)
        print("delete sql:id = " + str(delete_user.id))
        await database.execute(query)
    except Exception as e:
        raise HTTPException(status_code=401, detail=subroutine + ":" + str(e))
    return {"result": "delete success"}

# ----------------- 2021/11/24 added
@router.post("/users/ConversationListsCreate", response_model=nbtt_conversation_listsSelect)
async def ConversationListCreate(request: Request,access_token: str,conversation_list: nbtt_conversation_listsCreate, database: Database = Depends(get_connection)):
#async def ConversationListCreate(request: Request,conversation_list: nbtt_conversation_listsCreate, database: Database = Depends(get_connection)):
    # ConversationListを新規登録します。
    try:
        subroutine = "ConversationListCreate"
        print("function :" + subroutine)

        user = await check_token(access_token , 'access_token')
        # 現在時間
        now = datetime.now()
        # print(now.strftime('%Y%m%d%H%M%S'))

        # nbtt_conversation_listを作成
        # values = conversation_list.dict()
        dicts = conversation_list.dict()
        endtime = datetime.strptime(dicts["scheduled_end_timestamp"], '%Y-%m-%d %H:%M:%S')
        conversation_time = datetime.strptime(dicts["scheduled_end_timestamp"], '%Y-%m-%d %H:%M:%S') - datetime.strptime(dicts["start_timestamp"], '%Y-%m-%d %H:%M:%S')
        starttime = now
        scheduled_end_timestamp = now + conversation_time
        # print("starttime and endtime:")
        # print(starttime)
        # print(scheduled_end_timestamp)
        # print("time:")
        # print(starttime.strftime('%Y-%m-%d %H:%M:%S'))
        # print("now:")
        # print(starttime)
        # print(datetime.strptime(starttime.strftime('%Y-%m-%d %H:%M:%S'),'%Y-%m-%d %H:%M:%S'))

        values = {
            "conversation_code": format(dicts["user_id"],'05') + now.strftime('%Y%m%d%H%M%S'),
            "user_id": dicts["user_id"], # 2022/2/22 modified
            "to_user_id": dicts["to_user_id"], # 2022/2/22 modified
        #    "start_timestamp": datetime.strptime(dicts["start_timestamp"], '%Y-%m-%d %H:%M:%S'),
            "start_timestamp": starttime,
        #    "scheduled_end_timestamp": datetime.strptime(dicts["scheduled_end_timestamp"], '%Y-%m-%d %H:%M:%S'),
            "scheduled_end_timestamp": scheduled_end_timestamp,
            "reservation_talking_category": dicts["reservation_talking_category"],
            "is_deleted": False,
        #    "regist_timestamp": now,2022/3/27 modified
            "regist_timestamp": datetime.strptime(starttime.strftime('%Y-%m-%d %H:%M:%S'),'%Y-%m-%d %H:%M:%S'),
            "regist_user_id": dicts["regist_user_id"],
            # "update_timestamp": datetime.strptime(dicts["update_timestamp"], '%Y-%m-%d %H:%M:%S'),
        #    "update_timestamp": now, 2022/3/27 modified
            "update_timestamp": datetime.strptime(starttime.strftime('%Y-%m-%d %H:%M:%S'),'%Y-%m-%d %H:%M:%S'),
            "update_user_id": dicts["update_user_id"]
        }

        # 2022/09/18 既に会話が始まっていたらキャンセル処理
        # 会話相手が既にconversationlistに存在し、通話中状態、かつ終了を過ぎていない場合　は申し込みNG
        query = "SELECT \
            conversation_code,\
            user_id,\
            start_timestamp,\
            scheduled_end_timestamp,\
            reservation_talking_category,\
            is_deleted,\
            regist_timestamp,\
            regist_user_id,\
            update_timestamp,\
            update_user_id \
            FROM nbtt_conversation_lists \
            WHERE (user_id = %s or to_user_id = %s) and reservation_talking_category = 'talking' and scheduled_end_timestamp > '%s' and is_deleted = False " \
            % (values["to_user_id"],values["to_user_id"],now.strftime('%Y-%m-%d %H:%M:%S'))
        print("function :" + subroutine + " query talking check len:" + str(len(query)))
        resultset = await database.fetch_all(query)
        if len(resultset) > 0: # 会話相手がtalking状態
            print("length of resultset :" + str(len(resultset)))
        # if len(resultset) == 0: # 会話相手がtalking状態 debug用
            print("now talking.")
            return_values = {
                "conversation_code": values["conversation_code"],
                "user_id": values["user_id"],
                "to_user_id": values["to_user_id"],
                "start_timestamp": values["start_timestamp"].strftime('%Y-%m-%d %H:%M:%S'),
                "scheduled_end_timestamp": values["scheduled_end_timestamp"].strftime('%Y-%m-%d %H:%M:%S'),
                "reservation_talking_category": "missing",
                "is_deleted": True,
                "regist_timestamp": values["regist_timestamp"].strftime('%Y-%m-%d %H:%M:%S'),
                "regist_user_id": values["regist_user_id"],
                "update_timestamp": values["update_timestamp"].strftime('%Y-%m-%d %H:%M:%S'),
                "update_user_id": values["update_user_id"]
            }
            return {**return_values}
        else:
            print("query talking check no match OK.")
    except Exception as e:
        return {"errorcode": 1,"msg": str(e) + "conversation_list query talking checkでエラーが発生しました。"}
        # 2022/09/18 ここまで
    try:
        print("execute nbtt_conversation_lists.insert query")  
        query = nbtt_conversation_lists.insert() # これはDBの方で、受け取ったパラメータとは別です

        # SQLを組み立てる場合はこんな感じになります
        # query = "INSERT INTO nbtt_conversation_list \
        #     ( conversation_code,user_id,start_timestamp, \
        #         scheduled_end_timestamp,reservation_talking_category,is_deleted, \
        #             regist_timestamp,regist_user_id,update_timestamp,update_user_id) \
        #                 values \
        #     ('%s',%s,TO_TIMESTAMP('%s', 'YYYYMMDDHH24MISS'),\
        #          TO_TIMESTAMP('%s', 'YYYYMMDDHH24MISS'),'%s',%s,\
        #              TO_TIMESTAMP('%s', 'YYYYMMDDHH24MISS'),%s,TO_TIMESTAMP('%s', 'YYYYMMDDHH24MISS'),%s)" \
        #     % (entry_data["conversation_code"],\
        #         entry_data["user_id"],\
        #         entry_data["start_timestamp"],\
        #         entry_data["scheduled_end_timestamp"],\
        #         entry_data["reservation_talking_category"],\
        #         entry_data["is_deleted"],\
        #         entry_data["regist_timestamp"],\
        #         entry_data["regist_user_id"],\
        #         entry_data["update_timestamp"],\
        #         entry_data["update_user_id"])

        print(values)
        ret = await database.execute(query,values)

        # 戻り値は文字列・数値なのでtimestamp項目は文字列フォーマットに変換
        return_values = {
            "conversation_code": values["conversation_code"],
            "user_id": values["user_id"],
            "to_user_id": values["to_user_id"], # 2022/2/22 added
            "start_timestamp": values["start_timestamp"].strftime('%Y-%m-%d %H:%M:%S'),
            "scheduled_end_timestamp": values["scheduled_end_timestamp"].strftime('%Y-%m-%d %H:%M:%S'),
            "reservation_talking_category": values["reservation_talking_category"],
            "is_deleted": values["is_deleted"],
            "regist_timestamp": values["regist_timestamp"].strftime('%Y-%m-%d %H:%M:%S'),
            "regist_user_id": values["regist_user_id"],
            "update_timestamp": values["update_timestamp"].strftime('%Y-%m-%d %H:%M:%S'),
            "update_user_id": values["update_user_id"]
        }
        return {**return_values}
    except Exception as e:
        raise HTTPException(status_code=401, detail=subroutine + ":" + str(e))

# ----------------- 2021/11/25 added
@router.post("/users/ConversationListsSelect")
async def ConversationListSelect(request: Request,access_token: str,conversation_list: nbtt_conversation_listsSelect, database: Database = Depends(get_connection)):
    # user関連情報の受け渡し方法が決定したら修正
    # 会話相手のデータ検索条件が決定したら修正
    # エラーコード、HTTPエラーの受け渡し方法が決定したら修正

    # 終了予定時間を過ぎていないConversationListを検索します。
    try:
        subroutine = "ConversationListSelect"
        print("function :" + subroutine)
        #user = await check_token(access_token , 'access_token')

        dicts = conversation_list.dict()
        values = {
            "conversation_code": dicts["conversation_code"],
            "user_id": dicts["user_id"],
            "to_user_id": dicts["to_user_id"]
        }
        now = datetime.now()
        print("debug:" + now.strftime('%Y%m%d%H%M%S') + " conversation_code length:" + str(len(dicts["conversation_code"])) + " user_id:" + str(dicts["user_id"]) + " to_user_id:" + str(dicts["to_user_id"]))

        if len(values["conversation_code"]) != 0: # conversation_codeに値がある場合会話コードで検索する
            query = nbtt_conversation_lists.select().where(nbtt_conversation_lists.c.conversation_code == values["conversation_code"]).where(nbtt_conversation_lists.c.scheduled_end_timestamp > now).where(nbtt_conversation_lists.c.is_deleted == False)
            print("function :" + subroutine + " query 1")
        elif len(values["conversation_code"]) == 0 and values["user_id"] != 0 : # conversation_codeに値がなく、user_idが0でない場合、受け取ったuser_idで検索する
            query = nbtt_conversation_lists.select().where(nbtt_conversation_lists.c.user_id == values["user_id"]).where(nbtt_conversation_lists.c.scheduled_end_timestamp > now).where(nbtt_conversation_lists.c.is_deleted == False)
            print("function :" + subroutine + " query 2")
        elif len(values["conversation_code"]) == 0 and values["user_id"] == 0 and values["to_user_id"] != 0 : # conversation_codeに値がなく、user_idが0であり、to_user_idが0でない場合、受け取ったto_useridで検索する
            # 2022/3/27 added start
            # query = nbtt_conversation_lists.select().where(nbtt_conversation_lists.c.to_user_id == values["to_user_id"]).where(nbtt_conversation_lists.c.scheduled_end_timestamp > now).where(nbtt_conversation_lists.c.is_deleted == False)
            # print("★ここに入るはず")
            query = "SELECT \
                    c.conversation_code,\
                    c.user_id,\
                    c.start_timestamp,\
                    c.scheduled_end_timestamp,\
                    c.reservation_talking_category,\
                    c.is_deleted,\
                    c.regist_timestamp,\
                    c.regist_user_id,\
                    c.update_timestamp,\
                    c.update_user_id,\
                    n.username_sei,\
                    n.username_mei\
                    FROM nbtt_conversation_lists c INNER JOIN nbmt_users n on c.to_user_id = n.user_id \
                    WHERE c.scheduled_end_timestamp > '%s' and c.is_deleted = False and c.to_user_id = %s" \
                    % (now.strftime('%Y-%m-%d %H:%M:%S'),values["to_user_id"])
            print("function :" + subroutine + " query 3 len:" + str(len(query)))
            # 2022/3/27 added end
            # 2022/9/25 デバッグ用にそのままにするが、最終的にはreservation_talking_category=proposedを条件に入れる
        else:
            print("nbtt_conversation_lists..conversation_code ='' user_id = 0 to_user_id = 0") # converasation_codeが空で、ユーザIDが0の場合
            query = nbtt_conversation_lists.select()
        # print(subroutine + " query4:" + str(query))
        resultset = await database.fetch_all(query)
        # print("★ここに入るはず②")
        if len(resultset) > 0:
            print("resultset:" + str(resultset[0]["user_id"]))
            print(resultset)
        else:
            print("query no match.")
        return resultset # 正常取得完了
    except Exception as e:
        return {"errorcode": 1,"msg": str(e) + "conversation_listでエラーが発生しました。"}
        # raise HTTPException(status_code=401, detail=subroutine + ":" + str(e))

@router.post("/users/ConversationListsUpdate")
async def ConversationListUpdate(request: Request,access_token: str,conversation_list: nbtt_conversation_listsSelect, database: Database = Depends(get_connection)):
    # user関連情報の受け渡し方法が決定したら修正
    # 会話相手のデータ検索条件が決定したら修正
    # エラーコード、HTTPエラーの受け渡し方法が決定したら修正

    # ConversationListを更新します。
    subroutine = "ConversationListUpdate"
    print("function :" + subroutine)
    user = await check_token(access_token , 'access_token')
    # UserId = user.user_id
    # UserId = 1
    now = datetime.now()
    print(now.strftime('%Y%m%d%H%M%S'))

    dicts = conversation_list.dict()
    values = {
        "conversation_code": dicts["conversation_code"],
        "user_id": dicts["user_id"],
        "reservation_talking_category": dicts["reservation_talking_category"],
        "update_timestamp": dicts["update_timestamp"]
    }

    transaction = await database.transaction()
    try:
        subroutine = "ConversationListUpdate"
        print("function :" + subroutine)
        # user = await check_token(access_token , 'access_token')
        # UserId = user.user_id
        UserId = 1
        now = datetime.now()
        print(now.strftime('%Y%m%d%H%M%S'))

        dicts = conversation_list.dict()
        values = {
            "conversation_code": dicts["conversation_code"],
            "user_id": dicts["user_id"],
            "reservation_talking_category": dicts["reservation_talking_category"]
        }

        query = nbtt_conversation_lists.update().where(nbtt_conversation_lists.columns.conversation_code==values["conversation_code"]).values( \
            reservation_talking_category=values["reservation_talking_category"], \
            update_timestamp=now, \
            update_user_id=UserId \
        )

        print("query ConversationListUpdate:" + str(query))
        print("query param now:" + str(now) +" update_user_id:" + str(UserId) + " conversation_code:" + values["conversation_code"] + " reservation_talking_category:" + values["reservation_talking_category"] )
        resultset = await database.execute(query)
        # 本当はupdate件数をcheckしたいのだが、出す方法がない(ストアドが必要)
        print("nbtt_conversation_lists.update before result")
        await transaction.commit()
        return {"result": "update success"} # 正常更新完了
    except ValueError as v: # update失敗（対象なし）
        print("query:ConversationListUpdate rollbacked")
        await transaction.rollback()
        return {"errorcode": 2,"msg": str(v) + " conversation_listでupdate失敗(対象なし)"}
    except Exception as e: # query失敗（その他のエラー）
        print("query:rollbacked")
        await transaction.rollback()
        print("error occured:" +  str(e))
        return {"errorcode": 1,"msg": str(e) + " conversation_listでエラーが発生しました。"}
        # raise HTTPException(status_code=401, detail=subroutine + ":" + str(e))

# ----------------- 2021/12/12 added
@router.post("/users/UsersCreate", response_model=nbmt_usersSelect)
async def UsersCreate(users: nbmt_usersCreate, database: Database = Depends(get_connection)):
    # nbmt_usersを新規登録します。
    try:
        subroutine = "UsersCreate"
        print("function :" + subroutine)

        now = datetime.now()
        print(subroutine + now.strftime('%Y%m%d%H%M%S'))

        # user_id は自動インクリメントが必要。

        dicts = users.dict()
        dicts["hashed_password"]=get_users_insert_dict(dicts["hashed_password"])
        values = {
            "user_id": dicts["user_id"],
            "username_sei": dicts["username_sei"],
            "username_mei": dicts["username_mei"],
            "username_sei_kana": dicts["username_sei_kana"],
            "username_mei_kana": dicts["username_mei_kana"],
            "email": dicts["email"],
            "hashed_password": dicts["hashed_password"],
            "refresh_token": dicts["refresh_token"],
            "is_superuser": dicts["is_superuser"],
            "image_id": dicts["image_id"],
            "IMS_join_year": dicts["IMS_join_year"],
            "birthplace": dicts["birthplace"],
            "free_comment": dicts["free_comment"],
            "regist_timestamp": now,
            "regist_user_id": dicts["regist_user_id"],
            "update_timestamp": datetime.strptime(dicts["update_timestamp"], '%Y-%m-%d %H:%M:%S'),
            "update_user_id": dicts["update_user_id"]
        }
        query = nbmt_users.insert() # これはDBの方で、受け取ったパラメータとは別です
        print(subroutine + "query")  

        print(values)
        ret = await database.execute(query,values)

        # 戻り値は文字列・数値なのでtimestamp項目は文字列フォーマットに変換
        return_values = {
            "user_id": values["user_id"],
            "username_sei": values["username_sei"],
            "username_mei": values["username_mei"],
            "username_sei_kana": values["username_sei_kana"],
            "username_mei_kana": values["username_mei_kana"],
            "email": values["email"],
            "hashed_password": values["hashed_password"],
            "refresh_token": values["refresh_token"],
            "is_superuser": values["is_superuser"],
            "image_id": values["image_id"],
            "IMS_join_year": values["IMS_join_year"],
            "birthplace": values["birthplace"],
            "free_comment": values["free_comment"],
            "regist_timestamp": now.strftime('%Y%m%d%H%M%S'),
            "regist_user_id": values["user_id"],
            "update_timestamp": "",
            "update_user_id": NULL
        }
        return {**return_values}
    except Exception as e:
        raise HTTPException(status_code=401, detail=subroutine + ":" + str(e))

# ----------------- 2022/01/29 komata added
@router.post("/users/UsersUpdate", response_model=nbmt_usersSelect)
async def UsersUpdate(request: Request, access_token: str, param: str, database: Database = Depends(get_connection)):
    # nbmt_usersを更新します。
    try:
        subroutine = "UsersUpdate"
        print("function :" + subroutine)
        
        print("param:" + param)
        dic = ast.literal_eval(param)

        email = await check_token(access_token , 'access_token')
        print("email:" + email)

        user = await get_user_info(database, email)

        query = nbmt_users.update().where(nbmt_users.columns.email==email).values( \
           username_sei=dic['username_sei'], \
           username_mei=dic['username_mei'], \
           username_sei_kana=dic['username_sei_kana'], \
           username_mei_kana=dic['username_mei_kana'], \
           email=dic['email'], \
           hashed_password=get_users_insert_dict(dic["password"]), \
           IMS_join_year=int(dic['IMS_join_year']), \
           birthplace=dic['birthplace'], \
           free_comment=dic['free_comment'],
           update_timestamp=datetime.now(),
           update_user_id=user["update_user_id"]
           )
        ret = await database.execute(query)
        user = await get_user_info(database, email)

        return templates.TemplateResponse("profile.html",{'request': request,'user': user})

    except Exception as e:
        raise HTTPException(status_code=401, detail=subroutine + ":" + str(e))

# ----------------- 2022/09/25 hirayama added
@router.post("/users/SurveysCreate", response_model=nbet_surveysSelect)
async def SurveysCreate(surveys: nbet_surveysCreate, database: Database = Depends(get_connection)):
    # nbet_surveyを新規登録します。
    subroutine = "nbet_surveysCreate"
    print("function :" + subroutine)

    now = datetime.now()
    talktimemin = 0

    dicts = surveys.dict()
    values = {
        "respondent_id": dicts["respondent_id"],
        "conversation_code": dicts["conversation_code"],
        "talktime_length": dicts["talktime_length"],
        "comment": dicts["comment"],
        "is_deleted": dicts["is_deleted"],
        "regist_timestamp": now,
        "regist_user_id": dicts["regist_user_id"],
        "update_timestamp": now,
        "update_user_id": dicts["update_user_id"]
    }

    # query 1
    try:
        query = "SELECT *\
        FROM nbtt_conversation_lists\
        WHERE conversation_code = '%s'" \
        % (values["conversation_code"])
        print("function :" + subroutine + " query:" + query)
        query = nbtt_conversation_lists.select()
        resultset = await database.fetch_all(query)
        if len(resultset) > 0:
            # print("resultset:" + str(resultset[0][0]) + ":" + str(resultset[0][2]) + ":" + str(resultset[0][3]) + ":" + str(resultset[0][4]))
            talktime = resultset[0][4] - resultset[0][3]
            # timedelta（時刻の差）にはminがないので計算する。//はあまりを切り捨て
            talktimemin = talktime.seconds // 60
        else:
            print("query1 no match.")
    except Exception as e:
        print(subroutine + " query1 error" + ":" + str(e))

    # query 2
    values["talktime_length"] = talktimemin

    try:
        query = nbet_surveys.insert()
        print(subroutine + "query")  

        print(values)
        ret = await database.execute(query,values)

        # 戻り値は文字列・数値なのでtimestamp項目は文字列フォーマットに変換
        return_values = {
            "respondent_id": values["respondent_id"],
            "conversation_code": values["conversation_code"],
            "talktime_length": values["talktime_length"],
            "comment": values["comment"],
            "is_deleted": values["is_deleted"],
            "regist_timestamp": values["regist_timestamp"].strftime('%Y%m%d%H%M%S'),
            "regist_user_id": values["regist_user_id"],
            "update_timestamp": values["update_timestamp"].strftime('%Y%m%d%H%M%S'),
            "update_user_id": dicts["update_user_id"]
        }
        print(subroutine + ":completed")
        return {**return_values}
    except Exception as e:
        raise HTTPException(status_code=401, detail=subroutine + ":" + str(e))
# ----------------- 2022/09/25 hirayama added end
