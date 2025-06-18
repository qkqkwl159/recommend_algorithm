import tkinter as tk
from PIL import Image, ImageTk
import cv2
import os
import glob

window = tk.Tk()
window.title("Video Player")
window.geometry("1280x800")


label = tk.Label(window, text="Video Player")
label.grid(row=0, column=0, columnspan=3)

frame = tk.Frame(window, width=1280, height=800)
frame.grid(row=1, column=0, columnspan=3)

label1 = tk.Label(frame)
label1.grid(row=0, column=0, sticky="nsew")

# frame 내부와 window의 column weight를 조정하여 중앙 정렬
window.grid_columnconfigure(0, weight=1)
window.grid_columnconfigure(1, weight=1)
window.grid_columnconfigure(2, weight=1)
frame.grid_rowconfigure(0, weight=1)
frame.grid_columnconfigure(0, weight=1)

# meta 디렉터리의 모든 mp4 파일 리스트를 가져와 정렬
video_files = sorted(glob.glob("output/meta/*.mp4"))
video_idx = 0
cap = None

def play_next_video():
    global cap, video_idx
    if cap is not None:
        cap.release()
    if video_idx >= len(video_files):
        window.destroy()
        return
    cap = cv2.VideoCapture(video_files[video_idx])
    video_idx += 1
    video_play()

def video_play():
    global cap
    ret, frame = cap.read()
    if not ret:
        play_next_video()
        return
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(frame)
    imgtk = ImageTk.PhotoImage(image=img)
    #opencv video to tkinter image
    label1.imgtk = imgtk
    label1.configure(image=imgtk)
    label1.after(10, video_play)

play_next_video()
window.bind('<Escape>', lambda event: window.destroy())
window.mainloop()

