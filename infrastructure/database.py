import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Buscamos a URL de conexão das variáveis de ambiente (configuradas no Docker)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://v360_user:v360_password@db:5432/v360_db")

# 2. Criamos o "Motor" (Engine). Ele é quem efetivamente gerencia a comunicação com o PostgreSQL
engine = create_engine(DATABASE_URL)

# 3. Criamos uma fábrica de sessões. Cada vez que a API receber uma requisição, abrimos uma sessão para consultar ou salvar dados
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. A classe Base, que servirá de "molde" para criarmos as nossas tabelas no próximo passo
Base = declarative_base()

# 5. Uma função utilitária para injetarmos o banco de dados de forma segura nas rotas da API
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()