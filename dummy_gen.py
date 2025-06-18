#%%
import os
import random
import subprocess
from pathlib import Path
import csv

# 설정값
num_videos = 20 # 생성할 영상 개수
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)
org_dir = Path("output/org")
meta_dir = Path("output/meta")
org_dir.mkdir(exist_ok=True)
meta_dir.mkdir(exist_ok=True)
category_ids = list(range(1, 11))  # 1 ~ 10 카테고리 ID

# 출력 디렉토리 생성
output_dir.mkdir(exist_ok=True)

video_db_path = Path("output/video_db.csv")
write_header = not video_db_path.exists()

# 영상 생성 루프
for i in range(1, num_videos + 1):
    # 랜덤 카테고리 ID 1개 선택
    selected_id = random.choice(category_ids)

    # 메타데이터 인자 구성
    metadata_args = ["-metadata", f"category_id={selected_id}"]

    # 파일명 설정
    dummy_name = org_dir / f"dummy_{i}.mp4"
    final_name = meta_dir / f"dummy_{i}_with_tags.mp4"

    # 더미 영상 생성 (5초, 파란 배경 + sine tone)
    create_cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=blue:s=360x720:d=15",
        "-f", "lavfi", "-i", "sine=frequency=1000",
        "-shortest",
        "-c:v", "libx264",
        "-c:a", "aac",
        str(dummy_name)
    ]
    subprocess.run(create_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 메타데이터 삽입
    tag_cmd = [
        "ffmpeg", "-y",
        "-i", str(dummy_name),
        *metadata_args,
        "-c", "copy",
        str(final_name)
    ]
    subprocess.run(tag_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 결과 출력
    print(f"[완료] {final_name.name} (카테고리 ID: {selected_id})")

    # CSV에 정보 저장
    video_id = f"dummy_{i}"
    title = f"dummy_{i}"
    category_id = selected_id
    file_path = str(final_name)
    with open(video_db_path, mode='a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        if write_header:
            writer.writerow(["video_id", "title", "category_id", "file_path"])
            write_header = False
        writer.writerow([video_id, title, category_id, file_path])

# %%
