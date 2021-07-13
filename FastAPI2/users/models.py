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
metadata.create_all(bind=engine)