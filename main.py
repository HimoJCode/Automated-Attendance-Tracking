import sys
import os
import cv2
import datetime
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QTimer, QDateTime, QPropertyAnimation
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QGraphicsOpacityEffect, QMessageBox
import resources.res_rc

# Paths to UI files
MAIN_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "automated.ui")
LOGIN_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "login.ui")
ADMIN_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "admin.ui")
SUPERADMIN_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "superAdmin.ui")


class LoginDialog(QtWidgets.QDialog):
    """Login Window Class"""
    def __init__(self, super_admin_mode=False):
        super(LoginDialog, self).__init__()

        # Load Login UI
        uic.loadUi(LOGIN_UI_PATH, self)

        self.super_admin_mode = super_admin_mode 
        self.logged_in_role = None  # 'admin' or 'superadmin'


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

        image_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "resources/Bg_aci.jpg"))


        # Debugging: Print available UI elements
        #print("Available UI elements in Admin:", self.__dict__)

        # Set up QTimer to update the time every second
        self.timer_clock = QTimer(self)
        self.timer_clock.timeout.connect(self.update_time)
        self.timer_clock.start(1000)  # Update every 1 second

        # Update time on startup
        self.update_time()

        menu = QtWidgets.QMenu()

        logout_action = menu.addAction("Logout")
        switch_admin_action = menu.addAction("Change to Super admin")

        # Optional: connect to real functions
        logout_action.triggered.connect(self.logout)
        switch_admin_action.triggered.connect(self.switch_to_super_admin)

        # Attach menu to tool button
        self.toolButtonMenu.setMenu(menu)
        self.toolButtonMenu.setPopupMode(QtWidgets.QToolButton.InstantPopup)

    def update_time(self):
        """Update Date and Time dynamically."""
        current_datetime = QDateTime.currentDateTime()
        current_date = current_datetime.toString("MMMM dd, yyyy")
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
         # Show a logout message (optional)
        QMessageBox.information(self, "Logout", "You have been logged out.")
         # Close the current Admin Dashboard window
        self.close()
        # Open the AttendanceApp window (automated.ui)
        self.attendance_window = AttendanceApp()
        self.attendance_window.show()

    def switch_to_super_admin(self):
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
        self.setWindowTitle("Super Admin Dashboard")

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
    window = AttendanceApp()
    window.show()
    sys.exit(app.exec_())
