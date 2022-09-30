from pydantic import BaseModel
import datetime

from sqlalchemy.sql.sqltypes import Integer, SmallInteger

# insert用のrequest model。id(自動採番)は入力不要のため定義しない。
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    is_active: bool
    is_superuser: bool

# update用のrequest model
class UserUpdate(BaseModel):
    id : int
    username: str
    email: str
    password: str
    is_active: bool
    is_superuser: bool

# select用のrequest model。selectでは、パスワード不要のため定義しない。
class UserSelect(BaseModel):
    username: str
    email: str
    is_active: bool
    is_superuser: bool

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

# Point Transaction
class PointTranCreate(BaseModel):
    from_user_name: str
    to_user_name: str
    entry_date: str
    point: int
    comment: str
    is_deleted: bool

# update用のrequest model
class PointTranUpdate(BaseModel):
    from_user_name: str
    to_user_name: str
    entry_date: str
    point: int
    comment: str
    is_deleted: bool

# select用のrequest model。selectでは、パスワード不要のため定義しない。
class PointTranSelect(BaseModel):
    from_user_name: str
    to_user_name: str
    entry_date: str
    point: int
    comment: str
    is_deleted: bool

class CompleteList(BaseModel):
    candidate: str

# Point Stock
class PointStockCreate(BaseModel):
    username: str
    update_datetime: str
    point: int
    version: str
    is_deleted: bool

# update用のrequest model
class PointStockUpdate(BaseModel):
    username: str
    update_datetime: str
    point: int
    version: str
    is_deleted: bool

# select用のrequest model
class PointStockSelect(BaseModel):
    username: str
    update_datetime: str
    point: int
    version: str
    is_deleted: bool

# ----- 2021/11/24 added
class nbtt_user_statusSelect(BaseModel):
    user_id: int
    st_status_id: int
    conversational_timestamp: str
    expire_timestamp: str
    regist_timestamp: str
    regist_user_id: str
    update_timestamp: str
    update_user_id: str

class nbtt_user_statusCreate(BaseModel):
    user_id: int
    st_status_id: int
    conversational_timestamp: str
    expire_timestamp: str
    regist_timestamp: str
    regist_user_id: str
    update_timestamp: str
    update_user_id: str

class nbtt_conversation_listsSelect(BaseModel):
    conversation_code: str
    user_id: int
    to_user_id: int # 2022/2/22 added
    start_timestamp: str
    scheduled_end_timestamp: str
    reservation_talking_category: str
    is_deleted: bool
    regist_timestamp: str
    regist_user_id: str
    update_timestamp: str
    update_user_id: str

class nbtt_conversation_listsCreate(BaseModel):
    conversation_code: str
    user_id: int
    to_user_id: int # 2022/2/22 added
    start_timestamp: str
    scheduled_end_timestamp: str
    reservation_talking_category: str
    is_deleted: bool
    regist_timestamp: str
    regist_user_id: int
    update_timestamp: str
    update_user_id: int

# ----- 2021/12/05 update
class nbmt_usersCreate(BaseModel):
    user_id: int
    username_sei: str
    username_mei: str
    username_sei_kana: str
    username_mei_kana: str
    email: str
    hashed_password: str
    refresh_token: str
    is_superuser: bool
    image_id : int
    IMS_join_year : int
    birthplace: str
    free_comment: str
    regist_timestamp: str
    regist_user_id: int
    update_timestamp: str
    update_user_id: int

# update用のrequest model
class nbmt_usersUpdate(BaseModel):
    user_id: int
    username_sei: str
    username_mei: str
    username_sei_kana: str
    username_mei_kana: str
    email: str
    hashed_password: str
    refresh_token: str
    is_superuser: bool
    image_id : int
    IMS_join_year : int
    birthplace: str
    free_comment: str
    regist_timestamp: str
    regist_user_id: int
    update_timestamp: str
    update_user_id: int

# select用のrequest model
class nbmt_usersSelect(BaseModel):
    user_id: int
    username_sei: str
    username_mei: str
    username_sei_kana: str
    username_mei_kana: str
    email: str
    hashed_password: str
    refresh_token: str
    is_superuser: bool
    image_id : int
    IMS_join_year : int
    birthplace: str
    free_comment: str
    regist_timestamp: str
    regist_user_id: int
    update_timestamp: str
    update_user_id: int

# 20220925 hirayama added start 
class nbet_surveysCreate(BaseModel):
    user_id: int
    to_user_id: int
    conversation_code: str
    talktime_length: int
    comment: str
    is_deleted: bool
    regist_timestamp: str
    regist_user_id: int
    update_timestamp: str
    update_user_id: int

class nbet_surveysSelect(BaseModel):
    user_id: int
    to_user_id: int
    conversation_code: str
    talktime_length: int
    comment: str
    is_deleted: bool
    regist_timestamp: str
    regist_user_id: int
    update_timestamp: str
    update_user_id: int
# 20220925 hirayama added end
