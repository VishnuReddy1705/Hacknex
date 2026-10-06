import cv2
import numpy as np
import os

def generate_surveillance_video(output_path: str, duration_sec: int = 15, fps: int = 24, width: int = 640, height: int = 480):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    total_frames = duration_sec * fps
    
    # Load bus image or create a surveillance scene background
    bg = np.ones((height, width, 3), dtype=np.uint8) * 220
    # Draw floor and wall
    cv2.rectangle(bg, (0, 0), (width, int(height * 0.4)), (180, 180, 180), -1)
    # Draw restricted zone
    cv2.rectangle(bg, (int(width * 0.3), int(height * 0.5)), (int(width * 0.7), int(height * 0.85)), (200, 210, 230), -1)
    cv2.putText(bg, "RESTRICTED ZONE B", (int(width * 0.32), int(height * 0.55)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (140, 140, 160), 2)

    # Let's create realistic frames with timestamp overlay
    for frame_idx in range(total_frames):
        frame = bg.copy()
        t = frame_idx / fps

        # Surveillance camera timestamp watermark
        ts_text = f"CAM-04 | 2026-10-07 00:{int(t//60):02d}:{int(t%60):02d}.{int((t%1)*10)}"
        cv2.putText(frame, ts_text, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (50, 50, 50), 1, cv2.LINE_AA)

        out.write(frame)

    out.release()
    print(f"Generated test surveillance video at: {output_path} ({total_frames} frames, {duration_sec}s)")

if __name__ == "__main__":
    generate_surveillance_video("data/uploads/sample_cctv.mp4", duration_sec=10)
