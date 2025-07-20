from datetime import datetime

from flask_login import UserMixin
from geoalchemy2 import Geometry
from sqlalchemy import Column, DateTime, Integer, String, Boolean, ForeignKey, select, exists, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import shape, mapping
from werkzeug.security import check_password_hash

from db_sync import db_session

Base = declarative_base()


class User(UserMixin, Base):
    __tablename__ = "users"
    id = Column(Integer(), primary_key=True)
    username = Column(String(32), nullable=False, unique=True)
    password_hash = Column(String(192), nullable=False)
    is_admin = Column(Boolean(), default=False)
    created_at = Column(DateTime(), default=datetime.utcnow)
    updated_at = Column(DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"{self.id}: {self.username}"

    @classmethod
    def user_exists(cls, username: str) -> bool:
        return db_session.scalar(select(exists().where(cls.username == username)))

    @property
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "is_admin": self.is_admin,
        }

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Network(Base):
    __tablename__ = "networks"
    id = Column(Integer(), primary_key=True)
    name = Column(String(128), nullable=False, unique=True)
    owner_id = Column(Integer(), ForeignKey("users.id"))
    latest_version = Column(Integer(), default=1)
    public = Column(Boolean(), default=False)
    created_at = Column(DateTime(), default=datetime.utcnow)
    updated_at = Column(DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", backref="networks")
    maps = relationship("Map", back_populates="network", cascade="all, delete-orphan")

    def __repr__(self):
        return f"{self.id}: {self.name}"

    @classmethod
    def name_exists(cls, name: str) -> bool:
        return db_session.scalar(select(exists().where(cls.name == name)))

    @property
    def versions(self) -> dict:
        res = db_session.query(Map.id, Map.version).filter(Map.network_id == self.id).order_by("version")
        return {r[1]: r[0] for r in res}

    @property
    def to_dict(self) -> dict:
        return {
            "network_id": self.id,
            "name": self.name,
            "owner_id": self.owner_id,
            "owner": self.owner.username,
            "versions": self.versions,
            "latest_version": self.latest_version,
            "public": self.public,
            "created_at": self.created_at,
        }


class Map(Base):
    __tablename__ = "maps"
    id = Column(Integer(), primary_key=True)
    network_id = Column(Integer(), ForeignKey("networks.id", ondelete="CASCADE"))
    version = Column(Integer(), default=1)
    type = Column(String(32), nullable=True)
    name = Column(String(128), nullable=True)
    crs = Column(JSONB)
    created_at = Column(DateTime(), default=datetime.utcnow)

    network = relationship("Network", back_populates="maps", lazy="joined")
    features = relationship("Feature", back_populates="map", cascade="all, delete-orphan", passive_deletes=True)

    def __repr__(self):
        return f"{self.network.name} ver. {self.version}"

    @property
    def feature_count(self) -> int:
        return db_session.query(func.count(Feature.id)).filter(Feature.map_id == self.id).scalar()

    @property
    def to_dict(self) -> dict:
        return {
            "map_id": self.id,
            "network_id": self.network_id,
            "network": self.network.name,
            "version": self.version,
        }

    @property
    def edges(self) -> list:
        return [{"geometry": mapping(to_shape(feat.geom))} for feat in self.features]

    def add_geodata(self, geojson):
        self.type = geojson.get("type", "")
        self.name = geojson.get("name", "")
        self.crs = geojson.get("crs", {})
        for feature in geojson.get("features", []):
            type = feature.get("type", "")
            props = feature.get("properties", {})
            geom = from_shape(shape(feature.get("geometry", {})), srid=4326)
            self.features.append(Feature(type=type, props=props, geom=geom))


class Feature(Base):
    __tablename__ = "features"
    id = Column(Integer(), primary_key=True)
    map_id = Column(Integer(), ForeignKey("maps.id", ondelete="CASCADE"))
    type = Column(String(32), nullable=True)
    props = Column(JSONB)
    geom = Column(Geometry(geometry_type='GEOMETRY', srid=4326))

    map = relationship("Map", back_populates="features")
