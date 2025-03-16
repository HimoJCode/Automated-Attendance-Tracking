import sys
import os
import cv2
import datetime
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QTimer, QDateTime
from PyQt5.QtGui import QImage, QPixmap

# Paths to UI files
MAIN_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "automated.ui")
LOGIN_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "login.ui")

class LoginDialog(QtWidgets.QDialog):
    """Login Window Class"""
    def __init__(self):
        super(LoginDialog, self).__init__()
        
        # Load Login UI
        uic.loadUi(LOGIN_UI_PATH, self)

        # Connect login button
        self.loginButton.clicked.connect(self.login_action)

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

        # Simulated authentication (Replace this with database check)
        if username == "admin" and password == "1234":
            QtWidgets.QMessageBox.information(self, "Success", "Login successful!")
            self.accept()  # Close login window
        else:
            QtWidgets.QMessageBox.critical(self, "Login Failed", "Invalid username or password!")

class AttendanceApp(QtWidgets.QMainWindow):
    """Main Attendance System UI"""
    def __init__(self):
        super(AttendanceApp, self).__init__()

        # Load the Main UI
        uic.loadUi(MAIN_UI_PATH, self)

        # Set up webcam feed
        self.camera = cv2.VideoCapture(0)  # Open default webcam
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # Update every 30ms

        # Start real-time clock
        self.timer_clock = QTimer(self)
        #self.timer_clock.timeout.connect(self.update_time)
        self.timer_clock.start(1000)  # Update every second

        # Connect buttons
        self.loginButton.clicked.connect(self.show_login)

    def update_frame(self):
        """Capture frames from the webcam and display in Live Video."""
        ret, frame = self.camera.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
            self.liveVideoLabel.setPixmap(QPixmap.fromImage(q_img))  # Update QLabel with camera feed

    """def update_time(self):
    
        current_time = QDateTime.currentDateTime()
        self.dateLabel.setText(current_time.toString("yyyy-MM-dd"))  # Update Date
        self.timeLabel.setText(current_time.toString("hh:mm:ss AP"))  # Update Time"""

    def show_login(self):
        """Show Login Dialog when Login button is clicked"""
        login_dialog = LoginDialog()
        if login_dialog.exec_() == QtWidgets.QDialog.Accepted:
            print("User logged in successfully!")

    def closeEvent(self, event):
        """Stop the camera when closing the application."""
        self.camera.release()
        event.accept()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = AttendanceApp()
    window.show()
    sys.exit(app.exec_())
