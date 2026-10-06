import json
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import os

DATABASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "database"))
os.makedirs(DATABASE_DIR, exist_ok=True)
DB_PATH = os.path.join(DATABASE_DIR, "temporallens.db")

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class VideoModel(Base):
    __tablename__ = "videos"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_name = Column(String, nullable=False)
    fps = Column(Float, default=0.0)
    width = Column(Integer, default=0)
    height = Column(Integer, default=0)
    total_frames = Column(Integer, default=0)
    duration_seconds = Column(Float, default=0.0)
    status = Column(String, default="idle")
    progress_pct = Column(Float, default=0.0)
    current_stage_label = Column(String, default="Idle")
    current_frame = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(String, nullable=False)
    has_annotated_video = Column(Boolean, default=False)

    events = relationship("EventModel", back_populates="video", cascade="all, delete-orphan")
    entities = relationship("EntityModel", back_populates="video", cascade="all, delete-orphan")

class EventModel(Base):
    __tablename__ = "events"

    event_id = Column(String, primary_key=True, index=True)
    video_id = Column(String, ForeignKey("videos.id"), index=True, nullable=False)
    type = Column(String, nullable=False, index=True)
    entity_id = Column(String, nullable=False, index=True)
    related_entity_id = Column(String, nullable=True)
    start_time = Column(Float, nullable=False, index=True)
    end_time = Column(Float, nullable=False)
    frame_start = Column(Integer, nullable=False)
    frame_end = Column(Integer, nullable=False)
    confidence = Column(Float, default=1.0)
    description = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=True)

    video = relationship("VideoModel", back_populates="events")

    @property
    def event_metadata(self):
        if self.metadata_json:
            try:
                return json.loads(self.metadata_json)
            except Exception:
                return {}
        return {}

    @event_metadata.setter
    def event_metadata(self, value):
        self.metadata_json = json.dumps(value) if value else None

class EntityModel(Base):
    __tablename__ = "entities"

    entity_id = Column(String, primary_key=True, index=True)
    video_id = Column(String, ForeignKey("videos.id"), index=True, nullable=False)
    track_id = Column(Integer, nullable=False)
    class_name = Column(String, nullable=False)
    first_seen = Column(Float, nullable=False)
    last_seen = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)
    confidence = Column(Float, default=1.0)
    event_count = Column(Integer, default=0)
    trajectory_json = Column(Text, nullable=True)

    video = relationship("VideoModel", back_populates="entities")

    @property
    def trajectory(self):
        if self.trajectory_json:
            try:
                return json.loads(self.trajectory_json)
            except Exception:
                return []
        return []

    @trajectory.setter
    def trajectory(self, value):
        self.trajectory_json = json.dumps(value) if value else None

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
