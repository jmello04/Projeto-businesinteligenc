from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Session

from app.core.config import get_settings

settings = get_settings()

# Usando SQLite por padrao (DATABASE_URL configuravel via variavel de ambiente).
# Em um ambiente real com PostGIS, a URL seria:
#   postgresql://usuario:senha@localhost:5432/recife_db
# E o campo de coordenadas usaria:
#   from geoalchemy2 import Geography
#   localizacao = Column(Geography(geometry_type="POINT", srid=4326))
# Isso permitiria consultas espaciais como "pontos num raio de 500m".
engine = create_engine(settings.database_url, echo=False)


class Base(DeclarativeBase):
    pass


class PontoAlagamento(Base):
    """Modelo ORM para pontos de alagamento registrados no sistema."""

    __tablename__ = "pontos_alagamento"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    latitude: float = Column(Float, nullable=False)
    longitude: float = Column(Float, nullable=False)
    descricao: str = Column(String, nullable=False)
    criado_em: datetime = Column(DateTime(timezone=True), nullable=False)


def criar_tabelas() -> None:
    """Cria todas as tabelas definidas nos modelos ORM, se ainda nao existirem.

    Deve ser chamada uma unica vez na inicializacao da aplicacao (lifespan).
    """
    Base.metadata.create_all(bind=engine)


def salvar_ponto_alagamento(lat: float, lon: float, descricao: str) -> dict:
    """Persiste um ponto de alagamento no banco de dados.

    Args:
        lat: Latitude do ponto no sistema WGS-84.
        lon: Longitude do ponto no sistema WGS-84.
        descricao: Descricao textual do ocorrido.

    Returns:
        Dicionario com os campos do registro recem-criado, incluindo id e
        timestamp ISO-8601 em UTC.

    Raises:
        Exception: Qualquer erro de banco de dados apos rollback automatico.

    Note:
        Em producao com PostGIS, o campo localizacao armazenaria um POINT
        geografico que permite consultas como ST_DWithin e ST_Distance.
    """
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
