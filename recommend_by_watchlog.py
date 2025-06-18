import csv
import sys
from pathlib import Path
from collections import defaultdict

#########################################################
#########################################################
#########################################################
# 비디오 정보 저장 파일 경로
VIDEO_DB_PATH = Path("datainfo/video_db.csv")
#########################################################
#########################################################
#########################################################

def load_video_db():
    video_info = {}
    with open(VIDEO_DB_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            video_info[row['video_id']] = {
                'title': row['title'],
                'category_id': row['category_id'],
                'file_path': row['file_path']
            }
    return video_info

def load_watch_log(user_id):
    logs = []
    user_watchlog_path = Path(f"user/{user_id}_watchlog.csv")
    if not user_watchlog_path.exists():
        print(f"user/{user_id}_watchlog.csv 파일이 존재하지 않습니다.")
        return logs
    with open(user_watchlog_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            logs.append(row)
    return logs

def load_category_map():
    category_map = {}
    try:
        #########################################################
        #########################################################
        #########################################################
        # 카테고리 정보 파일 경로
        with open('datainfo/category.csv', newline='', encoding='utf-8') as f:
        #########################################################
        #########################################################
        #########################################################
        #########################################################
            reader = csv.DictReader(f)
            for row in reader:
                category_map[row['category_id']] = row['category']
    except Exception as e:
        print(f"category.csv 로드 오류: {e}")
    return category_map

def main(user_id):
    video_db = load_video_db()
    category_map = load_category_map()
    logs = load_watch_log(user_id)
    if not logs:
        print(f"user_id '{user_id}'의 시청 기록이 없습니다.")
        return

    # category_id별 각 영상의 시청비율(시청시간/전체길이) 리스트 생성
    category_ratios = defaultdict(list)
    for log in logs:
        if not log['watch_time'] or not log['total_duration'] or not log['video_id']:
            continue
        video_id = log['video_id']
        if video_id not in video_db:
            continue
        watch_time = int(log['watch_time'])
        total_duration = int(log['total_duration'])
        if total_duration > 0:
            category_id = video_db[video_id]['category_id']
            ratio = watch_time / total_duration
            category_ratios[category_id].append(ratio)

    # 카테고리별 시청비율 평균 계산
    category_ratio_avg = {}
    for cid, ratios in category_ratios.items():
        if ratios:
            category_ratio_avg[cid] = sum(ratios) / len(ratios)
        else:
            category_ratio_avg[cid] = 0

    # 평균 시청비율이 높은 category_id 상위 3개 추출
    top_categories = sorted(category_ratio_avg.items(), key=lambda x: x[1], reverse=True)[:3]
    for rank, (best_category, ratio) in enumerate(top_categories, 1):
        category_name = category_map.get(best_category, best_category)
        print(f"[{rank}] user_id '{user_id}'의 평균 시청비율이 높은 category: {category_name} (평균비율: {ratio:.2f})")
        # 해당 카테고리의 영상별 시청비율 정보 수집
        video_infos = []
        for log in logs:
            if not log['watch_time'] or not log['total_duration'] or not log['video_id']:
                continue
            video_id = log['video_id']
            if video_id not in video_db:
                continue
            if video_db[video_id]['category_id'] != best_category:
                continue
            watch_time = int(log['watch_time'])
            total_duration = int(log['total_duration'])
            if total_duration > 0:
                ratio_v = watch_time / total_duration
                video_infos.append({
                    'title': video_db[video_id]['title'],
                    'watch_time': watch_time,
                    'total_duration': total_duration,
                    'ratio': ratio_v
                })
        # best 시청비율 영상 출력
        if video_infos:
            best_video = max(video_infos, key=lambda x: x['ratio'])
            print(f"  - best 시청비율 영상: '{best_video['title']}' | 시청시간: {best_video['watch_time']}초 / {best_video['total_duration']}초 (비율: {best_video['ratio']:.2f})")
        print(f"\ncategory '{category_name}'의 영상 리스트:")
        for vid, info in video_db.items():
            if info['category_id'] == best_category:
                print(f"- {info['title']} (video_id: {vid}, file_path: {info['file_path']})")
        print()

    # --- 카테고리별 평균 시청비율 그래프 저장 (모든 카테고리 포함) ---
    try:
        import matplotlib.pyplot as plt
        # video_db에서 모든 카테고리 id 추출
        all_categories = set(info['category_id'] for info in video_db.values())
        # 문자열 정렬(숫자형이면 숫자 정렬)
        try:
            all_categories = sorted(all_categories, key=lambda x: int(x))
        except:
            all_categories = sorted(all_categories)
        ratios = [category_ratio_avg.get(cid, 0) for cid in all_categories]
        # x축 라벨을 category명으로 변환
        x_labels = [category_map.get(cid, cid) for cid in all_categories]
        plt.figure(figsize=(8, 5))
        plt.bar(x_labels, ratios, color='skyblue')
        plt.xlabel('Category')
        plt.ylabel('Average Watch Ratio')
        plt.title(f"user_id '{user_id}' average watch ratio")
        plt.ylim(0, 1)
        plt.tight_layout()
        import os
        os.makedirs('output', exist_ok=True)
        plt.savefig('output/category_duration.png')
        plt.close()
        print("카테고리별 평균 시청비율 그래프가 'output/category_duration.png'에 저장되었습니다.")
    except Exception as e:
        print(f"그래프 저장 중 오류 발생: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python recommend_by_watchlog.py [user_id]")
        sys.exit(1)
    user_id = sys.argv[1]
    main(user_id) 