import sys
import csv
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QInputDialog, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
import cv2
from PIL import Image
from PyQt5.QtGui import QPixmap, QImage

class VideoCategorizer(QWidget):
    def __init__(self, video_dir):
        super().__init__()
        self.setWindowTitle("영상 카테고리 입력기 (PyQt5)")
        self.setGeometry(100, 100, 1200, 950)
        self.video_dir = Path(video_dir)
        self.video_files = sorted([f for f in self.video_dir.iterdir() if f.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv']])
        self.video_index = 0
        self.cap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.play_frame)
        self.current_category = None
        #########################################################
        #########################################################
        #########################################################
        # 비디오 정보 저장 파일 경로
        self.csv_path = Path("datainfo/video_db.csv")
        #########################################################
        #########################################################
        #########################################################
        #########################################################
        self.write_header = not self.csv_path.exists()
        # --- 폴더에 없는 파일이 csv에 있으면 자동으로 제거 ---
        if self.csv_path.exists():
            with open(self.csv_path, newline='', encoding='utf-8') as f:
                reader = list(csv.DictReader(f))
            valid_stems = set(f.stem for f in self.video_files)
            filtered = [row for row in reader if row['video_id'] in valid_stems]
            if len(filtered) != len(reader):
                with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=['video_id', 'title', 'category_id', 'file_path'])
                    writer.writeheader()
                    writer.writerows(filtered)
        # 이미 등록된 video_id 목록 불러오기
        self.existing_video_ids = set()
        if self.csv_path.exists():
            with open(self.csv_path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.existing_video_ids.add(row['video_id'])
        # 등록되지 않은 영상만 필터링
        self.video_files = [f for f in self.video_files if f.stem not in self.existing_video_ids]
        # 영상이 하나도 없으면 창을 띄우지 않고 종료
        if not self.video_files:
            print("추가로 분류할 영상이 없습니다. 프로그램을 종료합니다.")
            sys.exit(0)

        # Layouts
        main_layout = QVBoxLayout()
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("font-size: 18pt;")
        self.info_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.info_label)

        self.video_label = QLabel()
        self.video_label.setFixedSize(1000, 700)
        self.video_label.setStyleSheet("background-color: black;")
        self.video_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.video_label, alignment=Qt.AlignCenter)

        self.next_btn = QPushButton("카테고리 입력 및 다음 영상")
        self.next_btn.clicked.connect(self.input_category_and_next)
        main_layout.addWidget(self.next_btn)

        self.setLayout(main_layout)
        self.show_next_video()

    def show_next_video(self):
        if self.cap is not None:
            self.cap.release()
        if self.video_index >= len(self.video_files):
            QMessageBox.information(self, "완료", "모든 영상의 카테고리 입력이 끝났습니다!")
            self.close()
            return
        self.current_file = self.video_files[self.video_index]
        self.info_label.setText(f"{self.current_file.name} ({self.video_index+1}/{len(self.video_files)})")
        self.cap = cv2.VideoCapture(str(self.current_file))
        if not self.cap.isOpened():
            QMessageBox.critical(self, "오류", f"영상을 열 수 없습니다:\n{self.current_file}")
            self.video_index += 1
            self.show_next_video()
            return
        self.timer.start(30)

    def play_frame(self):
        if self.cap is None:
            return
        ret, frame = self.cap.read()
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # 반복 재생
            ret, frame = self.cap.read()
            if not ret:
                return
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)
        qimg = QImage(img.tobytes(), img.width, img.height, img.width * 3, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        self.video_label.setPixmap(pixmap.scaled(self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def input_category_and_next(self):
        self.timer.stop()
        # info/category.csv에서 카테고리 목록 읽기
        category_msg = ""
        try:
            #########################################################
            #########################################################
            # 카테고리 정보 파일 경로
            with open("datainfo/category.csv", newline='', encoding='utf-8') as f:
            #########################################################
            #########################################################
                reader = csv.DictReader(f)
                category_msg = "\n".join([f"{row['category_id']}: {row['category']}" for row in reader])
        except Exception as e:
            category_msg = "(카테고리 정보를 불러올 수 없습니다)"
        msg = f"category_id를 입력하세요 (숫자만):\n\n{category_msg}"
        cat_id, ok = QInputDialog.getInt(self, "카테고리 입력", msg, min=1, max=10)
        if not ok:
            self.timer.start(30)
            return
        self.save_to_csv(cat_id)
        self.video_index += 1
        self.show_next_video()

    def save_to_csv(self, category_id):
        video_id = self.current_file.stem
        title = self.current_file.stem
        file_path = str(self.current_file)
        with open(self.csv_path, mode='a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            if self.write_header:
                writer.writerow(["video_id", "title", "category_id", "file_path"])
                self.write_header = False
            writer.writerow([video_id, title, category_id, file_path])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python make_video_db.py [영상_폴더_경로]")
        sys.exit(1)
    app = QApplication(sys.argv)
    window = VideoCategorizer(sys.argv[1])
    window.show()
    sys.exit(app.exec_()) 