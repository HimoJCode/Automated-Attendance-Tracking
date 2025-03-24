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
ADMIN_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "admin.ui")


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

        # Simulated authentication (Replace with database check)
        if username == "admin" and password == "1234":
            QtWidgets.QMessageBox.information(self, "Success", "Login successful!")
            self.accept()  # Close login window
        else:
            QtWidgets.QMessageBox.critical(self, "Login Failed", "Invalid username or password!")

class AdminDashboard(QtWidgets.QMainWindow):
    """Admin Dashboard UI (After Successful Login)"""
    def __init__(self):
        super(AdminDashboard, self).__init__()

        # Load Admin UI
        uic.loadUi(ADMIN_UI_PATH, self)

        # Debugging: Print available UI elements
        #print("Available UI elements in Admin:", self.__dict__)

        # Set up QTimer to update the time every second
        self.timer_clock = QTimer(self)
        self.timer_clock.timeout.connect(self.update_time)
        self.timer_clock.start(1000)  # Update every 1 second

        # Update time on startup
        self.update_time()

    def update_time(self):
        """Update Date and Time dynamically."""
        current_datetime = QDateTime.currentDateTime()
        current_date = current_datetime.toString("MMMM, dd, yyyy")
        current_time = current_datetime.toString("hh:mm:ss AP")

        # Ensure date_label exists
        if hasattr(self, "date_label"):
            self.date_label.setText(f"{current_date}")
        else:
            print("Error: 'date_label' not found in Admin UI!")

        # Ensure time_label exists
        if hasattr(self, "time_label"):
            self.time_label.setText(f"{current_time}")
        else:
            print("Error: 'time_label' not found in Admin UI!")

class AttendanceApp(QtWidgets.QMainWindow):
    """Main Attendance System UI"""
    def __init__(self):
        super(AttendanceApp, self).__init__()

        # Load the Main UI
        uic.loadUi(MAIN_UI_PATH, self)

        # Debugging: Print available UI elements
        #print("Available UI elements in Main:", self.__dict__)

        # Set up webcam feed
        self.camera = cv2.VideoCapture(0)  # Open default webcam
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # Update every 30ms

        # Connect login button
        if hasattr(self, "loginButton"):
            self.loginButton.clicked.connect(self.show_login)
        else:
            print("Error: 'loginButton' not found in UI!")

    def update_frame(self):
        """Capture frames from the webcam and display in Live Video."""
        ret, frame = self.camera.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
            self.liveVideoLabel.setPixmap(QPixmap.fromImage(q_img))  # Update QLabel with camera feed

    def show_login(self):
        """Show Login Dialog when Login button is clicked"""
        login_dialog = LoginDialog()
        if login_dialog.exec_() == QtWidgets.QDialog.Accepted:
            print("User logged in successfully!")

            # Close the main window and open Admin UI after login
            self.close()
            self.admin_window = AdminDashboard()
            self.admin_window.show()

    def closeEvent(self, event):
        """Stop the camera when closing the application."""
        self.camera.release()
        event.accept()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = AttendanceApp()
    window.show()
    sys.exit(app.exec_())
