import sys
import os
import cv2
import datetime
import numpy as np
import torch
import sqlite3
import ast
import resources.res_rc
from PyQt5 import QtWidgets, uic, QtCore, QtGui
from PyQt5.QtCore import QTimer, QDateTime, QPropertyAnimation
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QGraphicsOpacityEffect, QMessageBox
from facenet_pytorch import MTCNN
from facenet_pytorch import InceptionResnetV1
from PIL import Image

# Paths to UI files
MAIN_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "automated.ui")
LOGIN_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "login.ui")
ADMIN_LOGIN_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "loginPermission.ui")
ADMIN_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "admin.ui")
SUPERADMIN_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "superAdmin.ui")
UNRECOGNIZE_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "unrecognizeModule.ui")


class LoginPermissionDialog(QtWidgets.QDialog):
    """Admin Login for Automated Attendance Logging."""
    def __init__(self):
        super(LoginPermissionDialog, self).__init__()
        uic.loadUi(ADMIN_LOGIN_UI_PATH, self)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.exit_btn.clicked.connect(self.close)
        self.minimize_btn.clicked.connect(self.showMinimized)

        # Connect the login button of this dialog
        self.login_btn.clicked.connect(self.login_action)

    def login_action(self):
        username = self.usernameInput.text().strip()
        password = self.passwordInput.text().strip()

        # Example validation logic (replace with your own validation)
        if not username:
            QMessageBox.warning(self, "Login Error", "Username cannot be empty!")
            return
        if not password:
            QMessageBox.warning(self, "Login Error", "Password cannot be empty!")
            return

        if username == "admin" and password == "1234":
            self.logged_in = True
            QMessageBox.information(self, "Success", "Admin logged in for attendance logging!")
            self.accept()
        else:
            QMessageBox.critical(self, "Login Failed", "Invalid admin credentials!")
class LoginDialog(QtWidgets.QDialog):
    """Dashboard Login Dialog"""
    def __init__(self, super_admin_mode=False):
        super(LoginDialog, self).__init__()

        # Load Login UI
        uic.loadUi(LOGIN_UI_PATH, self)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.exit_btn.clicked.connect(self.close)
        self.minimize_btn.clicked.connect(self.showMinimized)
        self.super_admin_mode = super_admin_mode 
        self.logged_in_role = None  # 'admin' or 'superadmin'

        # Connect login button
        self.login_btn.clicked.connect(self.login_action)

    def login_action(self):
        """Handle login process with error messages"""
        username = self.usernameInput.text().strip()
        password = self.passwordInput.text().strip()

        # Error handling
        if not username:
            QtWidgets.QMessageBox.warning(self, "Login Error", "Username cannot be empty!")
            return
        if not password:
            QtWidgets.QMessageBox.warning(self, "Login Error", "Password cannot be empty!")
            return

        # Simulated authentication (Replace with database check)
        if username == "admin" and password == "1234":
           self.logged_in_role = "admin"
           QtWidgets.QMessageBox.information(self, "Success", "Logged in as Admin!")
           self.accept()
        elif username == "superadmin" and password == "4321":
           self.logged_in_role = "superadmin"
           QtWidgets.QMessageBox.information(self, "Success", "Logged in as Super Admin!")
           self.accept()    
        else:
           QtWidgets.QMessageBox.critical(self, "Login Failed", "Invalid username or password!")

class AdminDashboard(QtWidgets.QMainWindow):
    """Admin Dashboard UI (After Successful Login)"""
    def __init__(self):
        super(AdminDashboard, self).__init__()

        # Load Admin UI
        uic.loadUi(ADMIN_UI_PATH, self)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        # Set up QTimer to update the time every second
        self.timer_clock = QTimer(self)
        self.timer_clock.timeout.connect(self.update_time)
        self.timer_clock.start(1000)  # Update every 1 second

        # Update time on startup
        self.update_time()

        self.Down_Menu_Num = 0

        self.toolButtonMenu.clicked.connect(lambda: self.Down_Menu_Num_0())
        self.logout_btn.clicked.connect(self.logout)
        self.superAdmin_btn.clicked.connect(self.superAdmin)

        self.searchBar.returnPressed.connect(self.search_attendance)

        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()

        self.populate_attendance_data()

    def Down_Menu_Num_0(self):
        if self.Down_Menu_Num == 0:
            self.animation1 = QtCore.QPropertyAnimation(self.frame_1, b"minimumHeight")
            self.animation1.setDuration(500)
            self.animation1.setStartValue(51)
            self.animation1.setEndValue(121)
            self.animation1.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
            self.animation1.start()

            self.animation2 = QtCore.QPropertyAnimation(self.frame_1, b"maximumHeight")
            self.animation2.setDuration(500)
            self.animation2.setStartValue(51)
            self.animation2.setEndValue(121)
            self.animation2.setEasingCurve(QtCore.QEasingCurve.InOutQuart)

            self.animation2.start()
            self.Down_Menu_Num = 1

        else:
            self.animation1 = QtCore.QPropertyAnimation(self.frame_1, b"maximumHeight")
            self.animation1.setDuration(500)
            self.animation1.setStartValue(121)
            self.animation1.setEndValue(51)
            self.animation1.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
            self.animation1.start()

            self.animation2 = QtCore.QPropertyAnimation(self.frame_1, b"minimumHeight")
            self.animation2.setDuration(500)
            self.animation2.setStartValue(121)
            self.animation2.setEndValue(51)
            self.animation2.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
            self.animation2.start()

            self.Down_Menu_Num = 0
    def update_time(self):
        """Update Date and Time dynamically."""
        current_datetime = QDateTime.currentDateTime()
        current_date = current_datetime.toString("MMMM dd, yyyy")
        current_time = current_datetime.toString("hh:mm:ss AP")

        # Ensure date_label exists
        if hasattr(self, "date_label"):
            self.date_label.setText(f"{current_date}")
        # Ensure time_label exists
        if hasattr(self, "time_label"):
            self.time_label.setText(f"{current_time}")
    
    def populate_attendance_data(self):
        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                p.first_name || ' ' || p.middle_name || ' ' || p.last_name AS full_name,
                g.grade_level,
                s.strand_name,
                a.date_in,
                a.time_in
            FROM AttendanceRecords a
            JOIN Person p ON a.person_id = p.person_id
            JOIN StudentDetails sd ON sd.person_id = p.person_id
            JOIN GradeLevel g ON g.grade_level_id = sd.grade_level_id
            JOIN Strand s ON s.strand_id = sd.strand_id
            ORDER BY a.attendance_id DESC
        """)
        data = cursor.fetchall()
        conn.close()

        #Store in memory so it can be searched later
        self.all_data = data

        table = self.attendanceTableWidget
        table.setRowCount(len(data))
        table.setHorizontalHeaderLabels(["NAME", "GRADE", "STRAND", "DATE", "TIME"])

        for row_index, row_data in enumerate(data):
            for col_index, col_data in enumerate(row_data):
                item = QtWidgets.QTableWidgetItem(str(col_data))
                item.setForeground(QtGui.QColor("black"))
                item.setTextAlignment(QtCore.Qt.AlignLeft)
                table.setItem(row_index, col_index, item)

            header_item = QtWidgets.QTableWidgetItem(str(row_index + 1))
            header_item.setTextAlignment(QtCore.Qt.AlignCenter)
            table.setVerticalHeaderItem(row_index, header_item)
        
         # Adjust columns to fit neatly
        table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

        # Set a fixed width for each column
        table.setColumnWidth(0, 320)  # NAME
        table.setColumnWidth(1, 180)  # GRADE
        table.setColumnWidth(2, 180)  # STRAND
        table.setColumnWidth(3, 280)  # DATE
        table.setColumnWidth(4, 150)  # TIME

        # Set a fixed height for each row
        table.verticalHeader().setDefaultSectionSize(50)
        for row_index in range(len(data)):
            self.attendanceTableWidget.setVerticalHeaderItem(
                row_index, QtWidgets.QTableWidgetItem(str(row_index + 1))
            )

    def refresh_table(self, data):
        table = self.table = self.attendanceTableWidget
        table.setRowCount(0)  # Clear existing rows
        table.setHorizontalHeaderLabels(["NAME", "GRADE", "STRAND", "DATE", "TIME"])
        table.setRowCount(len(data))
        table.setHorizontalHeaderLabels(["NAME", "GRADE", "STRAND", "DATE", "TIME"])

        for row_index, row_data in enumerate(data):
            for col_index, col_data in enumerate(row_data):
                item = QtWidgets.QTableWidgetItem(str(col_data))
                item.setForeground(QtGui.QColor("black"))
                item.setTextAlignment(QtCore.Qt.AlignLeft)
                table.setItem(row_index, col_index, item)

        # Adjust columns to fit neatly
        table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

        # Set a fixed width for each column
        table.setColumnWidth(0, 320)  # NAME
        table.setColumnWidth(1, 190)  # GRADE
        table.setColumnWidth(2, 180)  # STRAND
        table.setColumnWidth(3, 280)  # DATE
        table.setColumnWidth(4, 150)  # TIME

        # Set a fixed height for each row
        table.verticalHeader().setDefaultSectionSize(50)
        for row_index in range(len(data)):
            self.attendanceTableWidget.setVerticalHeaderItem(
                row_index, QtWidgets.QTableWidgetItem(str(row_index + 1))
            )
    def search_attendance(self):
        search_text = self.searchBar.text().strip().lower()
        filtered_data = []

        for row in self.all_data:
            name = str(row[0]).lower()
            grade = str(row[1]).lower()
            strand = str(row[2]).lower()
            date = str(row[3]).lower()

            # Check if search text matches any of the fields directly
            if (search_text in name or
                search_text in grade or
                search_text in strand or
                search_text in date or
                search_text in self.extract_month_name(date).lower()):
                filtered_data.append(row)

        self.refresh_table(filtered_data)
        self.noDataLabel.setVisible(len(filtered_data) == 0)
        if len(filtered_data) == 0:
            self.noDataLabel.setText("🔍 No matching records found.")
            self.noDataLabel.setVisible(True)
            self.attendanceTableWidget.setVisible(False)
        else:
            self.noDataLabel.setVisible(False)
            self.attendanceTableWidget.setVisible(True)

    def extract_month_name(self, date_str):
        try:
            dt = datetime.datetime.strptime(date_str, '%B %d, %Y')
            return dt.strftime('%B')
        except:
            return ''

    def logout(self):
        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            "Logout Confirmation",
            "Are you sure you want to logout?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            # Start fade-out animation before logging out
            self.start_fade_out()
    
    def start_fade_out(self):
        # Set up the opacity effect
        self.effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)
    
        # Create the animation to fade out
        self.animation = QPropertyAnimation(self.effect, b"opacity")
        self.animation.setDuration(800)  # Duration in milliseconds (adjust as needed)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.finished.connect(self.finish_logout)
        self.animation.start()

    def finish_logout(self):
        # Optionally, reset the opacity back to 1 for future use
        self.setGraphicsEffect(None)

         # Show a logout message
        QMessageBox.information(self, "Logout", "You have been logged out.")

         # Close the current Admin Dashboard window
        self.close()

        # Open the AttendanceApp window (automated.ui)
        self.attendance_window = AttendanceApp()
        self.attendance_window.show()

    def superAdmin(self):
        # Open login dialog as a popup
        login_dialog = LoginDialog(super_admin_mode=True)
        if login_dialog.exec_() == QtWidgets.QDialog.Accepted:

             # If login is successful, open Super Admin window
            self.super_admin_window = SuperAdminDashboard()
            self.super_admin_window.show()


class SuperAdminDashboard(QtWidgets.QMainWindow):
    def __init__(self):
        super(SuperAdminDashboard, self).__init__()
        uic.loadUi(SUPERADMIN_UI_PATH, self)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        
        # Set up QTimer to update the time every second
        self.timer_clock = QTimer(self)
        self.timer_clock.timeout.connect(self.update_time)
        self.timer_clock.start(1000)  # Update every 1 second

        # Update time on startup
        self.update_time()

        self.Down_Menu_Num = 0

        self.toolButtonMenu.clicked.connect(lambda: self.Down_Menu_Num_0())
        self.logout_btn.clicked.connect(self.logout)
        self.superAdmin_btn.clicked.connect(self.superAdmin)

    def Down_Menu_Num_0(self):
        if self.Down_Menu_Num == 0:
            self.animation1 = QtCore.QPropertyAnimation(self.frame_1, b"minimumHeight")
            self.animation1.setDuration(500)
            self.animation1.setStartValue(51)
            self.animation1.setEndValue(121)
            self.animation1.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
            self.animation1.start()

            self.animation2 = QtCore.QPropertyAnimation(self.frame_1, b"maximumHeight")
            self.animation2.setDuration(500)
            self.animation2.setStartValue(51)
            self.animation2.setEndValue(121)
            self.animation2.setEasingCurve(QtCore.QEasingCurve.InOutQuart)

            self.animation2.start()
            self.Down_Menu_Num = 1

        else:
            self.animation1 = QtCore.QPropertyAnimation(self.frame_1, b"maximumHeight")
            self.animation1.setDuration(500)
            self.animation1.setStartValue(121)
            self.animation1.setEndValue(51)
            self.animation1.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
            self.animation1.start()

            self.animation2 = QtCore.QPropertyAnimation(self.frame_1, b"minimumHeight")
            self.animation2.setDuration(500)
            self.animation2.setStartValue(121)
            self.animation2.setEndValue(51)
            self.animation2.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
            self.animation2.start()

            self.Down_Menu_Num = 0
    def update_time(self):
        """Update Date and Time dynamically."""
        current_datetime = QDateTime.currentDateTime()
        current_date = current_datetime.toString("MMMM dd, yyyy")
        current_time = current_datetime.toString("hh:mm:ss AP")

        if hasattr(self, "date_label"):
            self.date_label.setText(f"{current_date}")
        if hasattr(self, "time_label"):
            self.time_label.setText(f"{current_time}")

    def logout(self):
        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            "Logout Confirmation",
            "Are you sure you want to logout?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            # Start fade-out animation before logging out
            self.start_fade_out()

    def start_fade_out(self):
        # Set up the opacity effect
        self.effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)

        # Create the animation to fade out
        self.animation = QPropertyAnimation(self.effect, b"opacity")
        self.animation.setDuration(800)  # Duration in milliseconds (adjust as needed)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.finished.connect(self.finish_logout)
        self.animation.start()

    def finish_logout(self):
        #Reset the opacity back to 1 for future use
        self.setGraphicsEffect(None)

         # Show a logout message
        QMessageBox.information(self, "Logout", "You have been logged out.")

         # Close the current Admin Dashboard window
        self.close()

        # Open the AttendanceApp window (automated.ui)
        self.attendance_window = AttendanceApp()
        self.attendance_window.show()

    def superAdmin(self):
        # Open login dialog as a popup
        login_dialog = LoginDialog(super_admin_mode=True)
        if login_dialog.exec_() == QtWidgets.QDialog.Accepted:

             # If login is successful, open Super Admin window
            self.super_admin_window = SuperAdminDashboard()
            self.super_admin_window.show()

from facenet_pytorch import MTCNN

class UnrecognizeModule(QtWidgets.QDialog):
    def __init__(self, parent=None, frame=None):
        super(UnrecognizeModule, self).__init__(parent)

        uic.loadUi(UNRECOGNIZE_UI_PATH, self)
        self.setModal(True)
        self.setWindowTitle("Unrecognized Person")
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)

        # UI Elements
        self.scan_face_label = self.findChild(QtWidgets.QLabel, "scanFace")
        self.reminder_text = self.findChild(QtWidgets.QLabel, "importantReminder")
        self.reminder_head = self.findChild(QtWidgets.QLabel, "importantReminderHead")
        self.startScan_btn = self.findChild(QtWidgets.QPushButton, "startScan_btn")
        self.cancelScan_btn = self.findChild(QtWidgets.QPushButton, "cancelScan_btn")

        # Detector
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.detector = MTCNN(keep_all=False, device=self.device)

        # Camera and Timer
        self.camera = cv2.VideoCapture(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

        # Connect buttons
        if self.startScan_btn:
            self.startScan_btn.clicked.connect(self.start_camera)
        if self.cancelScan_btn:
            self.cancelScan_btn.clicked.connect(self.reject)

        if frame is not None and frame.size > 0:
            self.display_frame(frame)

    def start_camera(self):
        if self.reminder_text:
            self.reminder_text.hide()
        if self.reminder_head:
            self.reminder_head.hide()
        self.timer.start(30)

    def update_frame(self):
        ret, frame = self.camera.read()
        if not ret:
            return

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_pil = Image.fromarray(rgb_frame)

        # Detect faces
        boxes, _ = self.detector.detect(image_pil)

        if boxes is not None:
            for box in boxes:
                x1, y1, x2, y2 = map(int, box)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

        self.display_frame(frame)

    def display_frame(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        q_img = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img).scaled(
            self.scan_face_label.width(), self.scan_face_label.height(), QtCore.Qt.KeepAspectRatio)
        self.scan_face_label.setPixmap(pixmap)

    def closeEvent(self, event):
        try:
            if hasattr(self, "timer") and self.timer.isActive():
                self.timer.stop()
            if hasattr(self, "camera") and self.camera.isOpened():
                self.camera.release()
        except Exception as e:
            print("Error releasing camera in UnrecognizeModule:", e)
        event.accept()

    def register_person(self):
        first_name = self.findChild(QtWidgets.QLineEdit, "firstNameInput").text().strip()
        middle_name = self.findChild(QtWidgets.QLineEdit, "middleNameInput").text().strip()
        last_name = self.findChild(QtWidgets.QLineEdit, "lastNameInput").text().strip()
        role = self.findChild(QtWidgets.QComboBox, "roleComboBox").currentText()
        strand = self.findChild(QtWidgets.QComboBox, "strandComboBox").currentText()
        grade = self.findChild(QtWidgets.QComboBox, "gradeComboBox").currentText()

        if not all([first_name, last_name]):
            QtWidgets.QMessageBox.warning(self, "Input Error", "First and Last name are required!")
            return

        # Save to database
        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()

        cursor.execute("INSERT INTO Person (first_name, middle_name, last_name, role) VALUES (?, ?, ?, ?)",
                       (first_name, middle_name, last_name, role))
        person_id = cursor.lastrowid

        if role.lower() == "student":
            cursor.execute("""
                INSERT INTO StudentDetails (person_id, grade_level_id, strand_id)
                VALUES (
                    ?, 
                    (SELECT grade_level_id FROM GradeLevel WHERE grade_level = ?),
                    (SELECT strand_id FROM Strand WHERE strand_name = ?)
                )
            """, (person_id, grade, strand))

        conn.commit()
        conn.close()

        QtWidgets.QMessageBox.information(self, "Success", f"{first_name} {last_name} registered successfully.")
        self.accept()

class AttendanceApp(QtWidgets.QMainWindow):
    """Main Attendance System UI"""
    def __init__(self):
        super(AttendanceApp, self).__init__()

        # Load the Main UI
        uic.loadUi(MAIN_UI_PATH, self)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.exit_btn.clicked.connect(self.close)
        self.minimize_btn.clicked.connect(self.showMinimized)

        # Set up webcam feed
        self.camera = cv2.VideoCapture(0)  # Open default webcam
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # Update every 30ms

         # Initialize MTCNN face detector using the device
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.detector = MTCNN(keep_all=True, device=self.device)

        # Load FaceNet
        self.embedder = InceptionResnetV1(pretrained='vggface2').eval()

        self.generate_embeddings_from_face_images("recognition.db")
        # Load known embeddings
        self.known_embeddings, self.known_ids = self.load_embeddings_from_db()

        # Keep track of recognized people
        self.recognized_ids = set()
        self.dialog_shown = False  # 🚨 Add this line here

        self.dialog_shown = False
        self.unrecognized_detected = False
        self.unrecognized_timer = QTimer(self)
        self.unrecognized_timer.setInterval(5000)  # 5 seconds
        self.unrecognized_timer.setSingleShot(True)
        self.unrecognized_timer.timeout.connect(self.handle_unrecognized_timeout)

        self.populate_attendance_data()

        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT a.person_id, a.date_in, a.time_in
            FROM AttendanceRecords a
            ORDER BY a.attendance_id DESC
            LIMIT 1
        """)
        latest = cursor.fetchone()
        conn.close()

        if latest:
            person_id, date_in, time_in = latest

            self.show_profile(person_id, date_in, time_in)

        # Connect login button
        if hasattr(self, "login_btn"):
            self.login_btn.clicked.connect(self.show_login)
        else:
            print("Error: 'loginButton' not found in UI!")

        self.dialog_shown = False

    def update_frame(self):
        ret, frame = self.camera.read()
        if not ret:
            return
        
        self.last_frame = frame.copy()

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_pil = Image.fromarray(rgb_frame)
        boxes, probs = self.detector.detect(image_pil)

        if boxes is not None:
            for i, (box, prob) in enumerate(zip(boxes, probs)):
                if prob < 0.95:
                    continue

                x1, y1, x2, y2 = map(int, box)

                # Preprocess and embed
                face_tensor = self.preprocess_face_for_embedding(frame, box)
                with torch.no_grad():
                    embedding = self.embedder(face_tensor)[0].numpy()
                embedding = embedding / np.linalg.norm(embedding)

                # Match to known
                distances = [np.linalg.norm(embedding - known) for known in self.known_embeddings]
                if distances:
                    min_dist = min(distances)
                    best_index = distances.index(min_dist)

                    if min_dist < 0.7:  # ✅ Recognized
                        person_id = self.known_ids[best_index]
                        if person_id not in self.recognized_ids:
                            self.recognized_ids.add(person_id)
                            if self.mark_attendance(person_id):
                                self.show_profile(person_id)

                        # Reset unrecognized state
                        self.unrecognized_timer.stop()
                        self.unrecognized_detected = False

                        # Draw green box and label
                        full_name = self.get_person_name(person_id)
                        cv2.putText(frame, full_name, (x1, y1 - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                    else:  # 🚨 Unrecognized person
                        # Draw red box and label
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        label = "Unrecognized Person"
                        font_scale = 0.6
                        thickness = 2
                        font = cv2.FONT_HERSHEY_SIMPLEX
                        text_x = x1
                        text_y = max(20, y1 - 10)
                        cv2.putText(frame, label, (text_x + 2, text_y + 2), font, font_scale, (0, 0, 0), thickness + 2, cv2.LINE_AA)
                        cv2.putText(frame, label, (text_x, text_y), font, font_scale, (0, 0, 255), thickness, cv2.LINE_AA)

                        if not self.unrecognized_detected:
                            self.unrecognized_detected = True
                            self.unrecognized_timer.start()

        # Display frame in UI
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channel = frame_rgb.shape
        bytes_per_line = 3 * width
        q_img = QImage(frame_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
        self.liveVideoLabel.setPixmap(QPixmap.fromImage(q_img))

    def handle_unrecognized_timeout(self):
        if self.unrecognized_detected and not self.dialog_shown:
            self.dialog_shown = True

            self.timer.stop()
            self.camera.release()  # ✅ Also release main camera

            dialog = UnrecognizeModule(parent=self, frame=self.last_frame)
            dialog.exec_()

            # Delay restart slightly
            QTimer.singleShot(300, self.restart_main_camera)

            self.dialog_shown = False
            self.unrecognized_detected = False
            self.unrecognized_timer.stop()

    def restart_main_camera(self):
        self.camera = cv2.VideoCapture(0)  # ✅ Re-initialize safely
        self.timer.start(30)



    def show_unrecognize_person_dialog(self):
        dialog = UnrecognizeModule()
        dialog.exec_()

        # Reset flags after dialog is closed
        self.dialog_shown = False
        self.unrecognized_detected = False
        self.unrecognized_timer.stop()


    def get_person_name(self, person_id):
        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()
        cursor.execute("SELECT first_name || ' ' || middle_name || ' ' || last_name FROM Person WHERE person_id = ?", (person_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else "Unknown"

    def populate_attendance_data(self):
        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()
        cursor.execute("""
                 SELECT 
                    p.first_name || ' ' || p.middle_name || ' ' || p.last_name AS full_name,
                    g.grade_level,
                    s.strand_name,
                    a.date_in,
                    a.time_in
                FROM AttendanceRecords a
                JOIN Person p ON a.person_id = p.person_id
                JOIN StudentDetails sd ON sd.person_id = p.person_id
                JOIN GradeLevel g ON g.grade_level_id = sd.grade_level_id
                JOIN Strand s ON s.strand_id = sd.strand_id
                ORDER BY a.attendance_id DESC
            """)
        data = cursor.fetchall()
        conn.close()

        table = self.attendanceTableWidget
        table.setRowCount(len(data))
        table.setHorizontalHeaderLabels(["NAME", "GRADE", "STRAND", "DATE", "TIME"])

        for row_index, row_data in enumerate(data):
            for col_index, col_data in enumerate(row_data):
                item = QtWidgets.QTableWidgetItem(str(col_data))
                item.setForeground(QtGui.QColor("black"))
                item.setTextAlignment(QtCore.Qt.AlignLeft)
                table.setItem(row_index, col_index, item)

            header_item = QtWidgets.QTableWidgetItem(str(row_index + 1))
            header_item.setTextAlignment(QtCore.Qt.AlignCenter)
            table.setVerticalHeaderItem(row_index, header_item)

        # Adjust columns to fit neatly
        table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

        # Set a fixed width for each column
        table.setColumnWidth(0, 163)  # NAME
        table.setColumnWidth(1, 110)   # GRADE
        table.setColumnWidth(2, 95)  # STRAND
        table.setColumnWidth(3, 140)  # DATE
        table.setColumnWidth(4, 70)   # TIME

        # Set a fixed height for each row
        table.verticalHeader().setDefaultSectionSize(30)
        for row_index in range(len(data)):
            self.attendanceTableWidget.setVerticalHeaderItem(
                row_index, QtWidgets.QTableWidgetItem(str(row_index + 1))
            )

    def preprocess_face_for_embedding(self, frame, box):
        x1, y1, x2, y2 = [int(v) for v in box]
        margin = int(min(x2 - x1, y2 - y1) * 0.1)
        x1, y1 = max(0, x1 - margin), max(0, y1 - margin)
        x2, y2 = min(frame.shape[1], x2 + margin), min(frame.shape[0], y2 + margin)

        face = frame[y1:y2, x1:x2]
        face = cv2.resize(face, (160, 160))
        face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB).astype('float32') / 255.0
        face = (face - 0.5) / 0.5
        return torch.tensor(np.transpose(face, (2, 0, 1))).unsqueeze(0).float()


    def generate_embeddings_from_face_images(self, db_path="recognition.db"):
        print("🔄 Embedding generation started...")
        embedder = InceptionResnetV1(pretrained='vggface2').eval()

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Skip people who already have embeddings
        cursor.execute("SELECT DISTINCT person_id FROM FaceEmbeddings")
        embedded_ids = {row[0] for row in cursor.fetchall()}

        # Get unembedded image paths
        cursor.execute("""
            SELECT person_id, image_path FROM FaceImages
            WHERE person_id NOT IN (
                SELECT DISTINCT person_id FROM FaceEmbeddings
            )
        """)
        rows = cursor.fetchall()

        inserted = 0
        for person_id, image_path in rows:
            if not os.path.exists(image_path):
                print(f"⚠️ Image not found: {image_path}")
                continue

            img = cv2.imread(image_path)
            if img is None:
                print(f"❌ Failed to load: {image_path}")
                continue

            try:
                # Preprocess image
                img = cv2.resize(img, (160, 160))
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype('float32') / 255.0
                img = (img - 0.5) / 0.5
                img = np.transpose(img, (2, 0, 1))
                img_tensor = torch.tensor(img).unsqueeze(0).float()

                # Generate embedding
                with torch.no_grad():
                    emb = embedder(img_tensor)[0].numpy()
                emb = emb / np.linalg.norm(emb)

                # ✅ Fix: Convert embedding list to string
                cursor.execute("""
                    INSERT INTO FaceEmbeddings (person_id, embedding_vector)
                    VALUES (?, ?)
                """, (person_id, str(emb.tolist())))

                inserted += 1

            except Exception as e:
                print(f"❌ Error processing {image_path}: {e}")

        conn.commit()
        conn.close()
        print(f"✅ {inserted} new embeddings added.")

    def load_embeddings_from_db(self):
        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()
        cursor.execute("SELECT person_id, embedding_vector FROM FaceEmbeddings")
        data = cursor.fetchall()
        conn.close()

        embeddings = []
        person_ids = []
        for person_id, emb_str in data:
            try:
                emb = np.array(ast.literal_eval(emb_str))
                emb = emb / np.linalg.norm(emb)
                embeddings.append(emb)
                person_ids.append(person_id)
            except Exception as e:
                print(f"Error loading embedding for person {person_id}: {e}")
                
        return embeddings, person_ids

    def mark_attendance(self, person_id):
        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()

        now = datetime.datetime.now()
        date_str = now.strftime('%B %#d, %Y')
        time_str = now.strftime('%I:%M %p')

        current_hour = now.hour
        current_period = "morning" if current_hour < 12 else "afternoon"

        # Check logs for the current day
        cursor.execute("""
            SELECT time_in FROM AttendanceRecords
            WHERE person_id = ? AND date_in = ?
        """, (person_id, date_str))
        entries = cursor.fetchall()

        for (logged_time,) in entries:
            logged_hour = datetime.datetime.strptime(logged_time, '%I:%M %p').hour
            logged_period = "morning" if logged_hour < 12 else "afternoon"

            if logged_period == current_period:
                conn.close()
                return  #Already logged in this time

        # Not yet logged this time slot, insert new record
        cursor.execute("""
            INSERT INTO AttendanceRecords (person_id, date_in, time_in)
            VALUES (?, ?, ?)
        """, (person_id, date_str, time_str))

        conn.commit()
        conn.close()
        self.populate_attendance_data()
        return True

    def show_profile(self, person_id, date_in=None, time_in=None):
        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT first_name, middle_name, last_name, profile_image_url
            FROM Person WHERE person_id = ?
        """, (person_id,))
        person = cursor.fetchone()

        if person:
            full_name = f"{person[0]} {person[1]} {person[2]}"
            profile_path = person[3]

            # Get strand and grade
            cursor.execute("""
                SELECT s.strand_name, g.grade_level
                FROM StudentDetails sd
                JOIN Strand s ON s.strand_id = sd.strand_id
                JOIN GradeLevel g ON g.grade_level_id = sd.grade_level_id
                WHERE sd.person_id = ?
            """, (person_id,))
            academic = cursor.fetchone()

            strand = academic[0] if academic else "N/A"
            grade = academic[1] if academic else "N/A"

            # If date/time passed in, use those. Otherwise, use current.
            display_date = date_in if date_in else datetime.datetime.now().strftime('%B %d, %Y')
            display_time = time_in if time_in else datetime.datetime.now().strftime('%I:%M %p')

            self.nameLabel.setText(f"{full_name}")
            self.dateLabel.setText(f"{display_date}")
            self.timeLabel.setText(f"{display_time}")
            self.strandLabel.setText(f"{strand}")
            self.gradeLabel.setText(f"{grade}")

            if os.path.exists(profile_path):
                pixmap = QPixmap(profile_path).scaled(250, 250, QtCore.Qt.KeepAspectRatio)
                self.image.setPixmap(pixmap)
            else:
                self.image.clear()

        conn.close()
    def show_unrecognize_person_dialog(self):
        dialog = UnrecognizeModule(self)
        dialog.exec_()
        self.dialog_shown = False  # Reset so next unknown face can trigger it again

    def show_login(self):
        login_dialog = LoginDialog()
        if login_dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.close()

            if login_dialog.logged_in_role == "superadmin":
                self.super_admin_window = SuperAdminDashboard()
                self.super_admin_window.show()
            elif login_dialog.logged_in_role == "admin":
                self.admin_window = AdminDashboard()
                self.admin_window.show()
            else:
                QtWidgets.QMessageBox.critical(self, "Error", "Unknown role!")

    def closeEvent(self, event):
        """Stop the camera when closing the application."""
        self.camera.release()
        event.accept()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    admin_permission_dialog = LoginPermissionDialog()

    if admin_permission_dialog.exec_() == QtWidgets.QDialog.Accepted and admin_permission_dialog.logged_in:
        window = AttendanceApp()
        window.show()
        sys.exit(app.exec_())
    else:
        sys.exit(0)
