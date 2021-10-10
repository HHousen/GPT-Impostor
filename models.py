import sqlalchemy as db
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

association_table = db.Table(
    "association",
    Base.metadata,
    db.Column("guild_id", db.ForeignKey("guilds.id")),
    db.Column("user_id", db.ForeignKey("users.id")),
)


class Guild(Base):
    __tablename__ = "guilds"
    id = db.Column(db.Integer(), primary_key=True, unique=True, nullable=False)
    ping_mode_users = relationship("User", secondary=association_table)


class User(Base):
    __tablename__ = "users"
    id = db.Column(db.Integer(), primary_key=True, unique=True, nullable=False)
    name = db.Column(db.String(), nullable=False)
