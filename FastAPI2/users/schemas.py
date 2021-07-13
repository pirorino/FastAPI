from pydantic import BaseModel
import datetime

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
