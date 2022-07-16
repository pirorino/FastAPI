import sqlalchemy
from db import metadata, engine

users = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, index=True),
    sqlalchemy.Column("username", sqlalchemy.String, index=True),
    sqlalchemy.Column("email", sqlalchemy.String, index=True),
    sqlalchemy.Column("hashed_password", sqlalchemy.String),
    sqlalchemy.Column("refresh_token", sqlalchemy.String),
    sqlalchemy.Column("is_active", sqlalchemy.Boolean(), default=True),
    sqlalchemy.Column("is_superuser", sqlalchemy.Boolean(), default=False)
)

pointtran = sqlalchemy.Table(
    "pointtran",
    metadata,
    sqlalchemy.Column("create_date", sqlalchemy.DateTime, default=False),
    sqlalchemy.Column("from_user_name", sqlalchemy.String, index=True),
    sqlalchemy.Column("to_user_name", sqlalchemy.String, index=True),
    sqlalchemy.Column("entry_date", sqlalchemy.DateTime, index=True),
    sqlalchemy.Column("point", sqlalchemy.String),
    sqlalchemy.Column("comment", sqlalchemy.String),
    sqlalchemy.Column("is_deleted", sqlalchemy.Boolean(), default=False)
)

pointstock = sqlalchemy.Table(
    "pointstock",
    metadata,
    sqlalchemy.Column("username", sqlalchemy.String, primary_key=True,default=False),
    sqlalchemy.Column("update_datetime", sqlalchemy.DateTime),
    sqlalchemy.Column("point", sqlalchemy.Integer),
    sqlalchemy.Column("version", sqlalchemy.String),
    sqlalchemy.Column("is_deleted", sqlalchemy.Boolean(), default=False)
)

userpicture = sqlalchemy.Table(
    "userpicture",
    metadata,
    sqlalchemy.Column("username", sqlalchemy.String, primary_key=True,index=True,default=False),
    # sqlalchemy.Column("username", sqlalchemy.String),
    sqlalchemy.Column("filename", sqlalchemy.String, primary_key=True,index=True,default=False),
    sqlalchemy.Column("update_datetime", sqlalchemy.DateTime),
    sqlalchemy.Column("path", sqlalchemy.String),
    sqlalchemy.Column("is_deleted", sqlalchemy.Boolean(), default=False)
)
nbtt_user_statuses = sqlalchemy.Table(
    "nbtt_user_statuses",
    metadata,
    sqlalchemy.Column("user_id", sqlalchemy.Integer, primary_key=True, index=True),
    sqlalchemy.Column("st_status_id", sqlalchemy.SMALLINT),
    sqlalchemy.Column("conversational_timestamp", sqlalchemy.TIMESTAMP),
    sqlalchemy.Column("expire_timestamp", sqlalchemy.TIMESTAMP),
    sqlalchemy.Column("regist_timestamp", sqlalchemy.TIMESTAMP),
    sqlalchemy.Column("regist_user_id", sqlalchemy.Integer),
    sqlalchemy.Column("update_timestamp", sqlalchemy.TIMESTAMP),
    sqlalchemy.Column("update_user_id", sqlalchemy.Integer)
)
nbtt_conversation_lists = sqlalchemy.Table(
    "nbtt_conversation_lists",
    metadata,
    sqlalchemy.Column("conversation_code", sqlalchemy.String, primary_key=True, index=True), 
    sqlalchemy.Column("user_id", sqlalchemy.Integer, primary_key=True, index=True), 
    sqlalchemy.Column("start_timestamp", sqlalchemy.TIMESTAMP), 
    sqlalchemy.Column("scheduled_end_timestamp", sqlalchemy.TIMESTAMP), 
    sqlalchemy.Column("reservation_talking_category", sqlalchemy.String), 
    sqlalchemy.Column("is_deleted", sqlalchemy.Boolean(), default=False), 
    sqlalchemy.Column("regist_timestamp", sqlalchemy.TIMESTAMP), 
    sqlalchemy.Column("regist_user_id", sqlalchemy.Integer), 
    sqlalchemy.Column("update_timestamp", sqlalchemy.TIMESTAMP), 
    sqlalchemy.Column("update_user_id", sqlalchemy.Integer) 
)
nbmt_users = sqlalchemy.Table(
    "nbmt_users",
    metadata,
    sqlalchemy.Column("user_id", sqlalchemy.Integer, primary_key=True, index=True),
    sqlalchemy.Column("username_sei", sqlalchemy.String(60), nullable=False),
    sqlalchemy.Column("username_mei", sqlalchemy.String(60), nullable=False),
    sqlalchemy.Column("username_sei_kana", sqlalchemy.String(60), nullable=False),
    sqlalchemy.Column("username_mei_kana", sqlalchemy.String(60), nullable=False),
    sqlalchemy.Column("email", sqlalchemy.String(256), unique=True, index=True, nullable=False),
    sqlalchemy.Column("hashed_password", sqlalchemy.String(256), nullable=False),
    sqlalchemy.Column("refresh_token", sqlalchemy.String(512)),
    sqlalchemy.Column("is_superuser", sqlalchemy.Boolean(), default=False),
    sqlalchemy.Column("image_id", sqlalchemy.Integer),
    sqlalchemy.Column("birthplace", sqlalchemy.String(256)),
    sqlalchemy.Column("IMS_join_year", sqlalchemy.SmallInteger),
    sqlalchemy.Column("free_comment", sqlalchemy.String(15)),
    sqlalchemy.Column("regist_timestamp", sqlalchemy.DateTime),
    sqlalchemy.Column("regist_user_id", sqlalchemy.Integer),
    sqlalchemy.Column("update_timestamp", sqlalchemy.DateTime),
    sqlalchemy.Column("update_user_id", sqlalchemy.Integer)
)
metadata.create_all(bind=engine)
