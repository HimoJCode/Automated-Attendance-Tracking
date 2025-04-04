import sys
import os
import cv2
import datetime
from PyQt5 import QtWidgets, uic, QtCore, QtGui
from PyQt5.QtCore import QTimer, QDateTime, QPropertyAnimation
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QGraphicsOpacityEffect, QMessageBox
import resources.res_rc

# Paths to UI files
MAIN_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "automated.ui")
LOGIN_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "login.ui")
ADMIN_LOGIN_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "loginPermission.ui")
ADMIN_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "admin.ui")
SUPERADMIN_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "superAdmin.ui")

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
        #image_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "resources/Bg_aci.jpg"))

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
        data = [
            ["Jeramel Himo", "12", "HUMSS", "March 20, 2025", "12:35PM"],
            ["Aubrey Caruz", "12", "STEM", "March 20, 2025", "11:35AM"],
            ["Roland Hontalba", "12", "GAS", "March 20, 2025", "10:32AM"],
            ["Jose Luwenko", "12", "TVET", "March 20, 2025", "09:45AM"],
            ["Joselito Famor", "11", "ABM", "March 20, 2025", "08:20AM"],
            ["Janice Jofell Villamil", "11", "HUMSS", "March 20, 2025", "08:15AM"],
            ["Ezraed Himo", "12", "STEM", "March 20, 2025", "07:35AM"],
            ["Jericho Zandy Arante", "11", "ABM", "November 20, 2025", "06:35AM"],
            ["Arante Aoo", "11", "ABM", "December 20, 2025", "06:35AM"],
            ["Arante Aoo", "11", "ABM", "December 20, 2025", "06:35AM"],
            ["Arante Aoo", "11", "ABM", "December 20, 2025", "06:35AM"],
            ["Arante Aoo", "11", "ABM", "December 20, 2025", "06:35AM"],
            ["Arante Aoo", "11", "ABM", "December 20, 2025", "06:35AM"],
            ["Arante Aoo", "11", "ABM", "December 20, 2025", "06:35AM"],
        ]

        table = self.adminTableWidget
        table.setRowCount(len(data))
        table.setHorizontalHeaderLabels(["NAME", "GRADE", "STRAND", "DATE", "TIME"])

        for row_index, row_data in enumerate(data):
            for col_index, col_data in enumerate(row_data):
                item = QtWidgets.QTableWidgetItem(col_data)
                item.setForeground(QtGui.QColor("white"))
                item.setTextAlignment(QtCore.Qt.AlignLeft)
                table.setItem(row_index, col_index, item)

        # Adjust columns to fit neatly
        table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

        # Set a fixed width for each column
        table.setColumnWidth(0, 320)  # NAME
        table.setColumnWidth(1, 180)   # GRADE
        table.setColumnWidth(2, 160)  # STRAND
        table.setColumnWidth(3, 280)  # DATE
        table.setColumnWidth(4, 130)   # TIME

        # Set a fixed height for each row
        table.verticalHeader().setDefaultSectionSize(50)

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

        # Ensure date_label exists
        if hasattr(self, "date_label"):
            self.date_label.setText(f"{current_date}")
        # Ensure time_label exists
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
        self.camera = cv2.VideoCapture(1)  # Open default webcam
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # Update every 30ms

        self.populate_attendance_data()

        # Connect login button
        if hasattr(self, "login_btn"):
            self.login_btn.clicked.connect(self.show_login)
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

            # (Your face detection logic here)

            self.save_attendance_log(frame)

    def populate_attendance_data(self):
        data = [
            ["Jeramel Himo", "12", "HUMSS", "March 20, 2025", "12:35PM"],
            ["Aubrey Caruz", "12", "STEM", "March 20, 2025", "11:35AM"],
            ["Roland Hontalba", "12", "GAS", "March 20, 2025", "10:32AM"],
            ["Jose Luwenko", "12", "TVET", "March 20, 2025", "09:45AM"],
            ["Joselito Famor", "11", "ABM", "March 20, 2025", "08:20AM"],
            ["Janice Jofell Villamil", "11", "HUMSS", "March 20, 2025", "08:15AM"],
            ["Ezraed Himo", "12", "STEM", "March 20, 2025", "07:35AM"],
            ["Jericho Zandy Arante", "11", "ABM", "November 20, 2025", "06:35AM"],
            ["Arante Aoo", "11", "ABM", "December 20, 2025", "06:35AM"],
            ["Arante Aoo", "11", "ABM", "December 20, 2025", "06:35AM"],
            ["Arante Aoo", "11", "ABM", "December 20, 2025", "06:35AM"],
            ["Arante Aoo", "11", "ABM", "December 20, 2025", "06:35AM"],
            ["Arante Aoo", "11", "ABM", "December 20, 2025", "06:35AM"],
            ["Arante Aoo", "11", "ABM", "December 20, 2025", "06:35AM"],
        ]

        table = self.attendanceTableWidget
        table.setRowCount(len(data))
        table.setHorizontalHeaderLabels(["NAME", "GRADE", "STRAND", "DATE", "TIME"])

        for row_index, row_data in enumerate(data):
            for col_index, col_data in enumerate(row_data):
                item = QtWidgets.QTableWidgetItem(col_data)
                item.setForeground(QtGui.QColor("white"))
                item.setTextAlignment(QtCore.Qt.AlignLeft)
                table.setItem(row_index, col_index, item)

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

    def save_attendance_log(self, frame):
        """Replace this with your logic to save attendance data."""
        print("Attendance log saved at", datetime.datetime.now())

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
