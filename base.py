from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column,String,Boolean,Integer, DateTime

Base = declarative_base()

class User(Base):

    __tablename__ = 'users'

    id = Column(Integer, primary_key= True)
    is_followed = Column(Boolean,default = False)
    follow_backs = Column(Boolean,default = False)
    stale = Column(Boolean,default = False)
    followed_on = Column(DateTime)
    is_special= Column(Boolean)
    # stri = Column(String)

class Post(Base):

    __tablename__ = 'posts'

    id = Column(String, primary_key = True)
    title = Column(String)
    link = Column(String,nullable = False)
    url = Column(String, nullable = False)
    posted = Column(Boolean,nullable = False, default = False)
    added = Column(DateTime,nullable = False)