import json
import datetime
from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import declarative_base, relationship as orm_relationship, sessionmaker
from backend.app.config import settings

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Video(Base):
    __tablename__ = "videos"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_name = Column(String, nullable=False)
    fps = Column(Float, default=30.0)
    width = Column(Integer, default=0)
    height = Column(Integer, default=0)
    total_frames = Column(Integer, default=0)
    duration_seconds = Column(Float, default=0.0)
    status = Column(String, default="idle")
    progress_pct = Column(Float, default=0.0)
    current_stage_label = Column(String, default="Idle")
    current_frame = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    has_annotated_video = Column(Boolean, default=False)
    created_at = Column(String, default=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    objects = orm_relationship("TrackedObject", back_populates="video", cascade="all, delete-orphan")
    events = orm_relationship("Event", back_populates="video", cascade="all, delete-orphan")
    relationships = orm_relationship("EventRelationship", back_populates="video", cascade="all, delete-orphan")

class TrackedObject(Base):
    __tablename__ = "objects"

    id = Column(String, primary_key=True, index=True) # e.g. "P01", "truck_1", "machine_1"
    video_id = Column(String, ForeignKey("videos.id"), index=True, nullable=False)
    track_id = Column(Integer, nullable=False)
    class_name = Column(String, nullable=False)
    label = Column(String, nullable=False)
    first_seen = Column(Float, nullable=False)
    last_seen = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)
    confidence = Column(Float, default=1.0)

    video = orm_relationship("Video", back_populates="objects")
    tracks = orm_relationship("ObjectTrack", back_populates="obj", cascade="all, delete-orphan")
    events = orm_relationship("Event", back_populates="obj", cascade="all, delete-orphan")

class ObjectTrack(Base):
    __tablename__ = "object_tracks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(String, ForeignKey("videos.id"), index=True, nullable=False)
    object_id = Column(String, ForeignKey("objects.id"), index=True, nullable=False)
    frame_number = Column(Integer, nullable=False)
    timestamp = Column(Float, nullable=False, index=True)
    bbox_x1 = Column(Float, nullable=False)
    bbox_y1 = Column(Float, nullable=False)
    bbox_x2 = Column(Float, nullable=False)
    bbox_y2 = Column(Float, nullable=False)
    confidence = Column(Float, default=1.0)

    obj = orm_relationship("TrackedObject", back_populates="tracks")

class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True, index=True) # e.g. "E01", "E02"
    video_id = Column(String, ForeignKey("videos.id"), index=True, nullable=False)
    object_id = Column(String, ForeignKey("objects.id"), index=True, nullable=True)
    related_object_id = Column(String, nullable=True)
    event_type = Column(String, nullable=False, index=True)
    start_time = Column(Float, nullable=False, index=True)
    end_time = Column(Float, nullable=False, index=True)
    duration = Column(Float, default=0.0)
    confidence = Column(Float, default=1.0)
    description = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=True)

    video = orm_relationship("Video", back_populates="events")
    obj = orm_relationship("TrackedObject", back_populates="events")

    @property
    def meta(self):
        if self.metadata_json:
            try:
                return json.loads(self.metadata_json)
            except Exception:
                return {}
        return {}

    @meta.setter
    def meta(self, val):
        self.metadata_json = json.dumps(val) if val else None

class EventRelationship(Base):
    __tablename__ = "event_relationships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(String, ForeignKey("videos.id"), index=True, nullable=False)
    source_event_id = Column(String, ForeignKey("events.id"), index=True, nullable=False)
    relationship = Column(String, nullable=False, index=True) # BEFORE, AFTER, IMMEDIATELY_BEFORE, etc.
    target_event_id = Column(String, ForeignKey("events.id"), index=True, nullable=False)
    time_difference = Column(Float, nullable=False) # seconds delta

    video = orm_relationship("Video", back_populates="relationships")

class Question(Base):
    __tablename__ = "questions"

    id = Column(String, primary_key=True, index=True)
    video_id = Column(String, ForeignKey("videos.id"), index=True, nullable=False)
    question_text = Column(Text, nullable=False)
    created_at = Column(String, default=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    answers = orm_relationship("Answer", back_populates="question", cascade="all, delete-orphan")

class Answer(Base):
    __tablename__ = "answers"

    id = Column(String, primary_key=True, index=True)
    question_id = Column(String, ForeignKey("questions.id"), index=True, nullable=False)
    answer_text = Column(Text, nullable=False)
    confidence = Column(Float, default=1.0)
    timestamps_json = Column(Text, nullable=False)
    evidence_json = Column(Text, nullable=False)
    created_at = Column(String, default=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    question = orm_relationship("Question", back_populates="answers")

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
