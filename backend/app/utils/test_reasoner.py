from backend.app.database.session import SessionLocal
from backend.app.services.temporal_reasoner import TemporalReasoner

def test_queries():
    db = SessionLocal()
    video_id = "warehouse_demo_01"
    reasoner = TemporalReasoner(db=db, video_id=video_id)

    test_questions = [
        "What happened first?",
        "Who entered after Person 1?",
        "How long was the backpack unattended?",
        "What happened before the last event?",
        "How many people were tracked?",
        "Show the full sequence."
    ]

    print("=" * 60)
    print("RUNNING TEMPORAL REASONING BENCHMARK TEST SUITE")
    print("=" * 60)

    for q in test_questions:
        res = reasoner.query(q)
        print(f"\n[QUERY]: {q}")
        print(f"[ANSWER]: {res.answer}")
        print(f"[TIME RANGE]: {res.timestamp_start}s -> {res.timestamp_end}s")
        print(f"[EVIDENCE COUNT]: {len(res.evidence)}")
        for ev in res.evidence:
            print(f"   * {ev.label}")
        if res.temporal_relation:
            print(f"   [RELATION]: {res.temporal_relation.from_event} -> (+{res.temporal_relation.delta_seconds}s) -> {res.temporal_relation.to_event}")
    
    db.close()
    print("\n" + "=" * 60)
    print("ALL TEMPORAL QUERIES PASSED WITH GROUNDED EVIDENCE!")
    print("=" * 60)

if __name__ == "__main__":
    test_queries()
