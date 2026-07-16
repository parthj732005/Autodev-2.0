from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class GeneratedFile(Base):
    __tablename__ = "generated_files"

    id = Column(Integer, primary_key=True)
    project_name = Column(String, index=True)
    story_id = Column(String, index=True)
    agent_name = Column(String)

    file_path = Column(String)
    language = Column(String)
    content = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
