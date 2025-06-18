import sys
import csv
import random
import time
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QMessageBox, QInputDialog
)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import QUrl, QTimer
import datetime
import subprocess
import cv2
from PIL import Image
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt


user_dir = Path("user")
user_dir.mkdir(exist_ok=True)

#########################################################
#########################################################
#########################################################
# 비디오 정보 저장 파일 경로
video_db_path = Path("datainfo/video_db.csv")
#########################################################
#########################################################
#########################################################
# watch_log_path는 user_id 입력 후 동적으로 할당
watch_log_path = None

# 영상 리스트 불러오기
with open(video_db_path, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    videos = list(reader)

class WatchEmulator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("영상 시청 에뮬레이터 (PyQt5)")
        self.setGeometry(100, 100, 1200, 950)
        self.user_id = ""
        self.current_video = None
        self.start_time = None
        self.ordered_videos = []
        self.video_index = 0

        # 프로그램 시작 시 user_id 먼저 입력
        self.get_user_id_first()
        global watch_log_path
        watch_log_path = user_dir / f"{self.user_id}_watchlog.csv"

        # 추천 카테고리 우선 영상 리스트 정렬
        self.ordered_videos = self.get_ordered_videos()
        self.video_index = 0

        # Layouts
        main_layout = QVBoxLayout()
        # user_id를 상단 타이틀로 표시
        self.user_title = QLabel(f"User: {self.user_id}")
        self.user_title.setStyleSheet("font-size: 24pt; font-weight: bold;")
        self.user_title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.user_title)

        # 영상 정보 (제목)
        self.video_info = QLabel("")
        self.video_info.setStyleSheet("font-size: 18pt;")
        self.video_info.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.video_info)

        # Video player
        self.video_label = QLabel()
        self.video_label.setFixedSize(1000, 700)
        self.video_label.setStyleSheet("background-color: black;")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.cap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.play_frame)
        main_layout.addWidget(self.video_label, alignment=Qt.AlignCenter)

        # 버튼 (다음, 종료)
        btn_layout = QHBoxLayout()
        self.next_btn = QPushButton("다음 영상")
        self.next_btn.clicked.connect(self.next_video)
        self.exit_btn = QPushButton("종료")
        self.exit_btn.clicked.connect(self.exit_app)
        btn_layout.addWidget(self.next_btn)
        btn_layout.addWidget(self.exit_btn)
        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

        self.next_video()  # 시작하자마자 첫 영상 재생

    def get_user_id_first(self):
        while True:
            user_id, ok = QInputDialog.getText(self, "user_id 입력", "user_id를 입력하세요:")
            if ok and user_id.strip():
                self.user_id = user_id.strip()
                break

    def get_ordered_videos(self):
        user_log_path = user_dir / f"{self.user_id}_watchlog.csv"
        # 기본: 랜덤 섞기
        import random
        vids = list(videos)
        random.shuffle(vids)
        # 추천 카테고리 우선 정렬
        if user_log_path.exists():
            try:
                import subprocess
                result = subprocess.run([
                    sys.executable, "recommend_by_watchlog.py", self.user_id
                ], capture_output=True, text=True, check=True)
                # best_category_id 추출
                for line in result.stdout.splitlines():
                    if "category_id:" in line:
                        best_category = line.split("category_id:")[-1].split()[0].strip()
                        break
                else:
                    return vids
                # 추천 카테고리 영상 먼저, 그 외 영상 나중
                best = [v for v in vids if v["category_id"] == best_category]
                rest = [v for v in vids if v["category_id"] != best_category]
                return best + rest
            except Exception:
                return vids
        return vids

    def next_video(self):
        # 현재 영상 시청 기록 저장
        if self.start_time is not None:
            self.log_watch_end()
        # 순서대로 영상 재생, 끝나면 처음부터 반복
        if not self.ordered_videos:
            QMessageBox.critical(self, "오류", "영상 리스트가 비어 있습니다.")
            return
        self.current_video = self.ordered_videos[self.video_index]
        info = f"{self.current_video['title']} (video_id: {self.current_video['video_id']}, category_id: {self.current_video['category_id']})"
        self.video_info.setText(info)
        # user_id 타이틀은 이미 설정되어 있으므로 따로 갱신 필요 없음
        file_path = self.current_video["file_path"]
        if not Path(file_path).exists():
            QMessageBox.critical(self, "오류", f"영상 파일이 존재하지 않습니다:\n{file_path}")
            self.start_time = None
            # 다음 영상으로 자동 진행
            self.video_index = (self.video_index + 1) % len(self.ordered_videos)
            self.next_video()
            return
        # OpenCV VideoCapture로 영상 열기
        if self.cap is not None:
            self.cap.release()
        self.cap = cv2.VideoCapture(file_path)
        if not self.cap.isOpened():
            QMessageBox.critical(self, "오류", f"영상을 열 수 없습니다:\n{file_path}")
            self.start_time = None
            # 다음 영상으로 자동 진행
            self.video_index = (self.video_index + 1) % len(self.ordered_videos)
            self.next_video()
            return
        self.timer.start(30)  # 약 30ms마다 프레임 갱신
        # 시청 시간 측정 시작
        self.start_time = time.time()
        # 다음 인덱스 준비
        self.video_index = (self.video_index + 1) % len(self.ordered_videos)

    def play_frame(self):
        if self.cap is None:
            return
        ret, frame = self.cap.read()
        if not ret:
            # 반복 재생: 영상이 끝나면 처음 프레임부터 다시 재생
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()
            if not ret:
                self.timer.stop()
                self.cap.release()
                self.cap = None
                return
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)
        qimg = QImage(img.tobytes(), img.width, img.height, img.width * 3, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        self.video_label.setPixmap(pixmap.scaled(self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def log_watch_end(self):
        if self.start_time is None:
            return
        end_time = time.time()
        watch_time = int(end_time - self.start_time)
        # 실제 영상 길이(초) 계산
        total_duration = 0
        if self.cap is not None:
            frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            if fps > 0:
                total_duration = int(frame_count / fps)
        if total_duration == 0:
            total_duration = 15  # fallback
        category_id = self.current_video["category_id"]
        # 헤더가 없으면 추가
        write_header = not watch_log_path.exists()
        if write_header:
            with open(watch_log_path, "a", newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["user_id", "video_id", "category_id", "watch_time", "total_duration"])
        # 시청 기록 추가
        with open(watch_log_path, "a", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([self.user_id, self.current_video["video_id"], category_id, watch_time, total_duration])
        self.start_time = None

    def exit_app(self):
        # 종료 시 시청 기록 저장
        if self.start_time is not None:
            self.log_watch_end()
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WatchEmulator()
    window.show()
    sys.exit(app.exec_())