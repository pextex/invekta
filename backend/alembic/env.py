from alembic import context
from app.db import Base, engine
from app import models  # register metadata

if context.is_offline_mode():
    # Export the exact existing migration chain without connecting to any database.
    context.configure(url=engine.url, target_metadata=Base.metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()
