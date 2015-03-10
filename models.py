from sqlalchemy import (Boolean, Column, Date, DateTime, ForeignKey, Integer,
                        Numeric, Sequence, String, Table, Text, Unicode,
                        UnicodeText, create_engine, func, select, text)
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import (backref, column_property, object_session,
                            relationship, scoped_session, sessionmaker,
                            validates)


class Base:

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()


Base = declarative_base(cls=Base)


class Page(Base):
    key = Column("key", String, primary_key=True)
    ip = Column('ip', postgresql.INET)
    created = Column(DateTime, default=func.now())
    body = Column(UnicodeText)
    url = Column(Unicode)


if __name__ == '__main__':
    uri = 'postgresql+psycopg2://aiopg:passwd@localhost:5433/aiopg'
    en = create_engine(uri)
    Base.metadata.bind = en
    from sqlalchemy.orm import sessionmaker
    session = sessionmaker(bind=en)()
#    pages = session.query(Page).all()
    Base.metadata.drop_all()
    Base.metadata.create_all()
    from ptpdb import set_trace
    set_trace()
