import json
import ssl
from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from .config import get_settings


class Base(DeclarativeBase):
    pass


url = make_url(get_settings().database_url)
if url.get_backend_name() == "mysql" and url.drivername == "mysql":
    url = url.set(drivername="mysql+pymysql")

engine_options: dict[str, object] = {"pool_pre_ping": True}
if url.get_backend_name() == "mysql":
    engine_options["pool_recycle"] = 1800
    ssl_option = url.query.get("ssl")
    if ssl_option is not None:
        if not isinstance(ssl_option, str):
            raise ValueError("Managed MySQL SSL policy has an unsupported URL shape.")
        tls_policy = json.loads(ssl_option)
        if tls_policy != {"rejectUnauthorized": True}:
            raise ValueError("Managed MySQL requires verified TLS.")
        engine_options["connect_args"] = {"ssl": ssl.create_default_context()}
        url = url.difference_update_query(["ssl"])
engine = create_engine(url, **engine_options)

if engine.dialect.name == "mysql":
    @event.listens_for(engine, "connect")
    def set_mysql_session_timezone(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("SET time_zone = '+00:00'")
        finally:
            cursor.close()


SessionLocal = sessionmaker(engine, expire_on_commit=False)


def get_db():
    with SessionLocal() as session:
        yield session
