import cv2
import numpy as np
from tkinter import *
from tkinter import scrolledtext, messagebox
from PIL import Image, ImageTk
import threading
from datetime import datetime
from playsound import playsound
from plyer import notification
import os
import csv

# Initialize camera and background subtractor
cap = cv2.VideoCapture(0)
fgbg = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=100)

alert_enabled = True
alarm_triggered = False
recording = False
motion_log = []

# -------------------- ALERT HANDLING --------------------
def trigger_alert():
    global alarm_triggered
    if not alarm_triggered:
        alarm_triggered = True
        try:
            threading.Thread(target=playsound, args=("alarm.wav",), daemon=True).start()
        except:
            pass
        
        # Local desktop notification
        notification.notify(
            title="⚠ Motion Detected!",
            message="Check your AI Motion Detector.",
            timeout=5
        )
        
        threading.Timer(5, reset_alarm).start()

def reset_alarm():
    global alarm_triggered
    alarm_triggered = False

# -------------------- SNAPSHOT & LOGGING --------------------
def log_snapshot_to_csv(timestamp, image_path):
    file_exists = os.path.isfile('snapshots_log.csv')
    with open('snapshots_log.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['Timestamp', 'Image_Path'])
        writer.writerow([timestamp, image_path])

def save_snapshot(frame):
    if not os.path.exists("snapshots"):
        os.makedirs("snapshots")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"snapshots/motion_{timestamp}.jpg"
    cv2.imwrite(path, frame)
    log_snapshot_to_csv(timestamp, path)

# -------------------- MOTION DETECTION --------------------
def detect_motion():
    if not recording:
        video_label.after(100, detect_motion)
        return

    ret, frame = cap.read()
    if not ret:
        video_label.after(100, detect_motion)
        return

    frame = cv2.resize(frame, (640, 480))
    fgmask = fgbg.apply(frame)
    _, thresh = cv2.threshold(fgmask, 244, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    motion_detected = False

    for contour in contours:
        if cv2.contourArea(contour) > 1000:
            motion_detected = True
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

    if motion_detected:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not motion_log or motion_log[-1] != timestamp:
            motion_log.append(timestamp)
            log_box.insert(END, f"[{timestamp}] Motion Detected\n")
            log_box.yview(END)
            save_snapshot(frame)
            if alert_enabled:
                trigger_alert()

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(rgb)
    imgtk = ImageTk.PhotoImage(image=img)
    video_label.imgtk = imgtk
    video_label.configure(image=imgtk)
    video_label.after(10, detect_motion)

# -------------------- CONTROL FUNCTIONS --------------------
def toggle_alert():
    global alert_enabled
    alert_enabled = alert_var.get()

def start_detection():
    global recording
    start_screen.pack_forget()
    detection_screen.pack(fill=BOTH, expand=True)
    recording = True
    detect_motion()

def stop_detection():
    global recording
    recording = False

def on_close():
    if messagebox.askokcancel("Exit", "Are you sure you want to exit?"):
        global recording
        recording = False
        cap.release()
        root.destroy()

# -------------------- GUI --------------------
root = Tk()
root.title("AI Motion Detector")
root.configure(bg="white")
root.attributes("-fullscreen", True)
root.bind("<Escape>", lambda event: root.attributes("-fullscreen", False))
title_font = ("Helvetica", 24, "bold")
button_font = ("Arial", 14)
log_font = ("Courier", 12)

# -------------------- START SCREEN --------------------
start_screen = Frame(root, bg="white")
start_screen.pack(fill=BOTH, expand=True)

start_title = Label(start_screen, text="🧠 AI Motion Detector", font=title_font, bg="white", fg="black")
start_title.pack(pady=60)

start_button = Button(start_screen, text="▶ Start Detection", font=button_font, command=start_detection,
                      bg="#28a745", fg="white", width=20, height=2)
start_button.pack(pady=20)

exit_button_start = Button(start_screen, text="❌ Exit", font=button_font, command=on_close,
                           bg="#6c757d", fg="white", width=20, height=2)
exit_button_start.pack(pady=10)

# -------------------- DETECTION SCREEN --------------------
detection_screen = Frame(root, bg="#ffffff")

title_frame = Frame(detection_screen, bg="#007acc", height=60)
title_frame.pack(fill=X)

title_label = Label(title_frame, text="📹 Live Motion Detection", font=title_font, bg="#007acc", fg="white")
title_label.pack(pady=10)

video_frame = Frame(detection_screen, bg="#000000", bd=4, relief=RIDGE)
video_frame.pack(padx=30, pady=15)

video_label = Label(video_frame, bg="#000000")
video_label.pack()

controls_frame = Frame(detection_screen, bg="#ffffff")
controls_frame.pack(pady=10)

start_btn = Button(controls_frame, text="▶ Start", font=button_font, command=start_detection,
                   bg="#28a745", fg="white", width=10)
start_btn.grid(row=0, column=0, padx=10)

stop_btn = Button(controls_frame, text="⏹ Stop", font=button_font, command=stop_detection,
                  bg="#dc3545", fg="white", width=10)
stop_btn.grid(row=0, column=1, padx=10)

exit_btn = Button(controls_frame, text="❌ Exit", font=button_font, command=on_close,
                  bg="#6c757d", fg="white", width=10)
exit_btn.grid(row=0, column=2, padx=10)

alert_var = BooleanVar(value=True)
alert_check = Checkbutton(controls_frame, text="Enable Alerts (Sound + Desktop)", variable=alert_var,
                          command=toggle_alert, bg="#ffffff", font=("Arial", 13))
alert_check.grid(row=0, column=3, padx=10)

log_label = Label(detection_screen, text="📜 Motion Log:", font=("Arial", 16, "bold"), bg="#ffffff")
log_label.pack(pady=(20, 5))

log_box = scrolledtext.ScrolledText(detection_screen, width=120, height=10, font=log_font,
                                    bg="#f8f9fa", fg="#212529", relief=GROOVE, bd=2)
log_box.pack(padx=30, pady=(0, 30))

root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
