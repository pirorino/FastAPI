import os
import hashlib
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
from .schemas import UserCreate, UserUpdate, UserSelect, Token
from .schemas import PointTranCreate, PointTranUpdate, PointTranSelect
from .schemas import PointStockCreate, PointStockUpdate, PointStockSelect
from .schemas import CompleteList

import shutil
# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")
jinja_env = templates.env  # Jinja2.Environment : filterやglobalの設定用

Secret_Key = "S08EbmDoqkD7T6yhDMxDaxm27Fadt2s9d"
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 入力したパスワード（平文）をハッシュ化して返します。
def get_users_insert_dict(user):
    pwhash=hashlib.sha256(user.password.encode('utf-8')).hexdigest()
    values=user.dict()
    values.pop("password")
    values["hashed_password"]=pwhash
    return values

def test_dict(user):
    values=user.dict()
    return values


async def create_tokens(database: Database,username: str):
    """パスワード認証を行い、トークンを生成"""
    try:
        subroutine = "create_tokens"
        # ペイロード作成
        access_payload = {
            'token_type': 'access_token',
            'exp': datetime.utcnow() + timedelta(minutes=60),
            'username': username,
        }
        refresh_payload = {
            'token_type': 'refresh_token',
            'exp': datetime.utcnow() + timedelta(days=30),
            'username': username,
        }

        # トークン作成
        access_token = jwt.encode(access_payload, Secret_Key, algorithm='HS256')
        refresh_token = jwt.encode(refresh_payload, Secret_Key, algorithm='HS256')
        print("create token succeeded")
        # DBにリフレッシュトークンを保存
        # print("username:" + username)
        # print("refresh_token:" + refresh_token)
        query = users.update().where(users.columns.username==username).values(refresh_token=refresh_token)    
        ret = await database.execute(query)

        print("access_token:" + access_token)
        print("refresh_token:" + refresh_token)
        return {'access_token': access_token, 'refresh_token': refresh_token, 'token_type': 'bearer'}
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
        query = users.select().where(users.columns.username==payload['username'])
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
        user_name = payload.get('username')
        print("user_name:" + user_name)
        if user_name is None:
            raise HTTPException(status_code=401, detail=f'token user unmatched')
        if payload['token_type'] != token_type:
            raise HTTPException(status_code=401, detail=f'token type unmatched')
        return user_name
    except Exception as e:
        raise HTTPException(status_code=401, detail=subroutine + ":" + str(e))

async def authenticate(database: Database,username: str, password: str):
    # パスワード認証し、userを返します。
    # user = User.get(name=name)
    print("authenticate username:" + username)
    try:
        subroutine = "authenticate"
        query = users.select().where(users.columns.username==username)
        ret = await database.fetch_one(query)
        # print("hashed_password:",ret[3])
        # user = db.query(User).filter(User.email == email).first()
    except Exception as e:
        raise HTTPException(status_code=401, detail=subroutine + ":" + str(e))
    if ret == None:
        print("no user")
        raise HTTPException(status_code=401, detail='no data matched')
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
    if ret[3] != hashed_password:
        print("password unmatch")
        raise HTTPException(status_code=401, detail='password unmatch')
    return ret

# usersを全件検索して「UserSelect」のリストをjsonにして返します。
# @router.get("/users/super/del")
# async def read_users_super_del(delete_user: UserUpdate,token: str = Depends(oauth2_scheme),database: Database = Depends(get_connection)):
#     print("/users/super/del start")
#     user = await get_current_user_from_token(database,token , 'access_token')

# curl -X GET "http://localhost:8000/"

async def check_privilege(database: Database,username: str):
    """userから権限を取得"""
    try:
        subroutine = "check_privilege"
        print(subroutine)

        # DBからユーザーを取得
        query = users.select().where(users.columns.username==username)
        ret = await database.fetch_one(query)
        # [6]はis_superuser
        return ret[6]
    except Exception as e:
        raise HTTPException(status_code=401, detail=subroutine + ":" + str(e))

@router.get('/')
async def get_index(request: Request):
    # 初期画面の表示
    return templates.TemplateResponse('index.html',{'request': request})

@router.get('/login')
async def login(request: Request):
    print("login called")
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
    user = await check_token(access_token , 'access_token')
    print("user:" + user)
    # ユーザの権限チェック
    is_superuser = await check_privilege(database,user)
    page_file = pagename + '.html'
    
    print("load /templates/" + page_file)
    if pagename == 'toppage':
        print('this is toppage')
        if is_superuser == True:
        # superuserの場合、管理者用画面を表示
            page_file = pagename + '_admin.html'
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
            query = "select row_number() over() as number,* from pointtran where from_user_name = '%s' or to_user_name = '%s'"  % (user,user)
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
        query = "select point,version from pointstock where username = '%s' "  % (user)
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
  
    return templates.TemplateResponse(page_file,{'request': request})

    # curl -X GET "http://localhost:8000/pages/test/" -H  "accept: application/json" -H  "Authorization: Bearer {eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzX3Rva2VuIiwiZXhwIjoxNjE1OTAxNzE4LCJ1c2VybmFtZSI6InBpcm9yaW5vIn0.YtqZEfBQ3WaoImnIXw6sMZfNtZpUS3KAYJi5nuvDmE0}}"

@router.get('/static/js/js_auth')
async def get_js_auth(request: Request):
    # js_auth.jsは静的ファイルだが、jinja2テンプレートファイルとして配置したので/static/js/以下にない
    return templates.TemplateResponse('js_auth.js',{'request': request})

@router.get("/users/super", response_model=List[UserSelect])
async def users_findall(token: str = Depends(oauth2_scheme),database: Database = Depends(get_connection)):
    # superuserの場合、usersを全件検索して「UserSelect」のリストをjsonにして返します。
    try:
        subroutine = "users_findall"
        users = await get_current_user_from_token(database,token , 'access_token')
        query = users.select()
        return await database.fetch_all(query)
    except Exception as e:
        raise HTTPException(status_code=401, detail=subroutine + ":" + str(e))
# curl -X GET "http://localhost:8000/users/super" -H  "accept: application/json" -H  "Content-Type: application/x-www-form-urlencoded" -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzX3Rva2VuIiwiZXhwIjoxNjE0MDY1MTY0LCJ1c2VybmFtZSI6InBpcm9yaW5vIn0.kKFsEqorI_LO16vIbrxPe8C1jsGq9B2rJghVSfaARtE"

@router.get("/users/find", response_model=UserSelect)
async def users_findone(id: int, database: Database = Depends(get_connection)):
    # usersをidで検索して「UserSelect」をjsonにして返します。
    try:
        subroutine = "users_findone"
        query = users.select().where(users.columns.id==id)
        return await database.fetch_one(query)
    except Exception as e:
        raise HTTPException(status_code=401, detail=subroutine + ":" + str(e))
# http://localhost:8000/users/find?id=1

@router.post("/users/create", response_model=UserSelect)
async def users_create(user: UserCreate, database: Database = Depends(get_connection)):
    # usersを新規登録します。curlから実行
    # validatorは省略
    try:
        subroutine = "users_create"

        # usersを作成
        query = users.insert()
        values = get_users_insert_dict(user)
        ret = await database.execute(query, values)

        # pointstockを作成
        now = datetime.now()

        entry_data = {
            "username": user.username,
            "update_datetime": now.strftime('%Y%m%d%H%M%S'),
            "point": 100,
            "version": "1",
            "is_deleted": False
        }
        query = "INSERT INTO pointstock \
            (username,update_datetime, point,version,is_deleted) \
                values \
            ('%s',TO_TIMESTAMP('%s', 'YYYYMMDDHH24MISS'),%s,'%s',%s)" \
            % (entry_data["username"],entry_data["update_datetime"],entry_data["point"],entry_data["version"],entry_data["is_deleted"])
        print("db exec:" + query)
        ret = await database.execute(query)
        return {**user.dict()}
    except Exception as e:
        raise HTTPException(status_code=401, detail=subroutine + ":" + str(e))
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
        print("/autocomplete-tousername start")
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
        print("/token start")
        user = await authenticate(db, form.username, form.password)
        # print("user:",user[1])
        token = await create_tokens(db, user[1])
        print("generated token:",token)
        return token
    except Exception as e:
        raise HTTPException(status_code=401, detail=subroutine + ":" + str(e))
# curl -X POST "http://localhost:8000/token" -H  "accept: application/json" -H  "Content-Type: application/x-www-form-urlencoded" -d "username=pirorino&password=password"

@router.get("/users/me/")
async def read_users_me(token: str = Depends(oauth2_scheme),database: Database = Depends(get_connection)):
    # アクセストークンを受け取ってカレントユーザを返却します。画面なし、未使用
    try:
        subroutine = "read_users_me"
        print("/users/me/ start")
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
        print("/users/super/del start")
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
