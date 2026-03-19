from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Session

# Usando SQLite para rodar sem precisar instalar PostgreSQL.
# Em um ambiente real com PostGIS, a URL seria:
#   postgresql://usuario:senha@localhost:5432/recife_db
# E o campo de coordenadas usaria:
#   from geoalchemy2 import Geography
#   localizacao = Column(Geography(geometry_type="POINT", srid=4326))
# Isso permitiria consultas espaciais como "pontos num raio de 500m".
engine = create_engine("sqlite:///recife_geo.db", echo=False)


class Base(DeclarativeBase):
    pass


class PontoAlagamento(Base):
    __tablename__ = "pontos_alagamento"

    id = Column(Integer, primary_key=True, autoincrement=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    descricao = Column(String, nullable=False)
    criado_em = Column(DateTime(timezone=True), nullable=False)


def criar_tabelas():
    Base.metadata.create_all(bind=engine)


def salvar_ponto_alagamento(lat: float, lon: float, descricao: str) -> dict:
    # Persiste um ponto de alagamento no banco.
    # Em produção com PostGIS, o campo localizacao armazenaria um POINT
    # geográfico que permite consultas como ST_DWithin e ST_Distance.
    with Session(engine) as db:
        try:
            ponto = PontoAlagamento(
                latitude=lat,
                longitude=lon,
                descricao=descricao,
                criado_em=datetime.now(timezone.utc),
            )
            db.add(ponto)
            db.commit()
            db.refresh(ponto)
            return {
                "id": ponto.id,
                "latitude": ponto.latitude,
                "longitude": ponto.longitude,
                "descricao": ponto.descricao,
                "criado_em": ponto.criado_em.isoformat(),
            }
        except Exception:
            db.rollback()
            raise
