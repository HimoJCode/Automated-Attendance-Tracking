import sys
import os
import cv2
import datetime
import numpy as np
import torch
import sqlite3
import ast
import shutil
import resources.res_rc
import hashlib
from PyQt5 import QtWidgets, uic, QtCore, QtGui
from PyQt5.QtCore import QTimer, QDateTime, QPropertyAnimation
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QGraphicsOpacityEffect, QMessageBox, QFileDialog, QDialog
from facenet_pytorch import MTCNN
from facenet_pytorch import InceptionResnetV1
from PIL import Image

# Paths to UI files
MAIN_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "automated.ui")
LOGIN_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "login.ui")
ADMIN_LOGIN_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "loginPermission.ui")
ADMIN_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "admin.ui")
SUPERADMIN_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "superAdmin.ui")
UPDATE_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "updateStudent.ui")
ADD_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "addStudent.ui")
ADD_ADMIN_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "addAdmin.ui")
ADD_STAFF_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "addStaff.ui")
UPDATE_STAFF_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "updateStaff.ui")
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

        if not username or not password:
            QtWidgets.QMessageBox.warning(self, "Missing Fields", "Username and password must not be empty.")
            return

        try:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()

            conn = sqlite3.connect("recognition.db")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT admin_id, admin_role 
                FROM Admin 
                WHERE username = ? AND password_hash = ?
            """, (username, hashed_password))
            result = cursor.fetchone()
            conn.close()

            if result:
                self.admin_id, self.logged_in_role = result
                self.logged_in = True  
                self.accept()
            else:
                QtWidgets.QMessageBox.critical(self, "Login Failed", "Invalid username or password!")

        except sqlite3.Error as e:
            QtWidgets.QMessageBox.critical(self, "Database Error", f"An error occurred while connecting to the database:\n{e}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Unexpected Error", f"An unexpected error occurred:\n{e}")

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
        username = self.usernameInput.text().strip()
        password = self.passwordInput.text().strip()

        if not username or not password:
            QtWidgets.QMessageBox.warning(self, "Missing Fields", "Username and password must not be empty.")
            return

        try:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()

            conn = sqlite3.connect("recognition.db")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT admin_id, admin_role 
                FROM Admin 
                WHERE username = ? AND password_hash = ?
            """, (username, hashed_password))
            result = cursor.fetchone()
            conn.close()

            if result:
                self.admin_id, self.logged_in_role = result
                self.logged_in = True 
                self.accept()
            else:
                QtWidgets.QMessageBox.critical(self, "Login Failed", "Invalid username or password!")

        except sqlite3.Error as e:
            QtWidgets.QMessageBox.critical(self, "Database Error", f"An error occurred while connecting to the database:\n{e}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Unexpected Error", f"An unexpected error occurred:\n{e}")

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

        self.toolMenu_btn.clicked.connect(lambda: self.Down_Menu_Num_0())
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
                CASE 
                    WHEN p.first_name = '[Deleted]' THEN 'Deleted Student'
                    ELSE p.first_name || ' ' || p.middle_name || ' ' || p.last_name
                END AS full_name,
                COALESCE(g.grade_level, 'N/A') AS grade,
                COALESCE(s.strand_name, 'N/A') AS strand,
                a.date_in,
                a.time_in
            FROM AttendanceRecords a
            LEFT JOIN Person p ON a.person_id = p.person_id
            LEFT JOIN StudentDetails sd ON sd.person_id = p.person_id
            LEFT JOIN GradeLevel g ON g.grade_level_id = sd.grade_level_id
            LEFT JOIN Strand s ON s.strand_id = sd.strand_id
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
    """Super Admin Dashboard UI (After Successful Login)"""
    def __init__(self, current_admin_id):
        super(SuperAdminDashboard, self).__init__()
        self.current_admin_id = current_admin_id
        uic.loadUi(SUPERADMIN_UI_PATH, self)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.initUI_btn()
        self.init_page_navigation()
        self.setup_timers()
        self.populate_initial_data()
        self.selected_student_row = None
        self.selected_staff_row = None

    def setup_timers(self):
        self.timer_clock = QTimer(self)
        self.timer_clock.timeout.connect(self.update_time)
        self.timer_clock.start(1000)
        self.update_time()
    def initUI_btn(self):
        self.Down_Menu_Num = 0
        self.Side_Menu_Num = 0
        self.burgerMenu_btn.clicked.connect(self.Side_Menu_Num_0)
        self.close_btn.clicked.connect(self.Side_Menu_Num_0)
        self.toolMenu_btn.clicked.connect(self.Down_Menu_Num_0)
        self.logout_btn.clicked.connect(self.logout)
        self.superAdmin_btn.clicked.connect(self.superAdmin)
        self.updateStudent_btn.clicked.connect(self.update_selected_student)
        self.removeStudent_btn.clicked.connect(self.remove_selected_student)
        self.addStudent_btn.clicked.connect(self.open_add_student_dialog)
        self.addAdmin_btn.clicked.connect(self.open_add_admin_dialog)
        self.addStaff_btn.clicked.connect(self.open_add_staff_dialog)
        self.updateStaff_btn.clicked.connect(self.update_selected_staff)
        self.removeStaff_btn.clicked.connect(self.remove_selected_staff)
        self.changePassword_btn.clicked.connect(self.change_password)
        self.removeAdmin_btn.clicked.connect(self.remove_admin)
        self.searchBar.returnPressed.connect(self.search_attendance)
        self.studentList_searchBar.textChanged.connect(self.search_student_list)
        self.staff_searchBar.textChanged.connect(self.search_staff_list)
        self.studentList_table.itemSelectionChanged.connect(self.get_selected_student_row)

    def init_page_navigation(self):
        self.attendanceLogs_btn.clicked.connect(lambda: self.switch_page(0, self.attendanceLogs_btn))
        self.students_btn.clicked.connect(lambda: self.switch_page(1, self.students_btn))
        self.admin_btn.clicked.connect(lambda: self.switch_page(2, self.admin_btn))
        self.staffs_btn.clicked.connect(lambda: self.switch_page(3, self.staffs_btn))

        self.nav_buttons = [
            self.attendanceLogs_btn,
            self.students_btn,
            self.admin_btn,
            self.staffs_btn
        ]
        self.switch_page(0, self.attendanceLogs_btn)  # default selection

    def switch_page(self, index, active_button):
        self.stackedWidget.setCurrentIndex(index)

        # Reset all buttons to default (white border)
        for btn in self.nav_buttons:
            btn.setStyleSheet("""
                QPushButton {
                    color: #ffffff;
                    font: 87 11pt "Segoe UI Black";
                    background-color: #5A5958;
                    border: 2px solid #ffffff;
                }
            """)

        # Set active button to black border
        active_button.setStyleSheet("""
            QPushButton {
                color: #ffffff;
                font: 87 11pt "Segoe UI Black";
                background-color: #5A5958;
                border: 2px solid #000000;
            }
        """)


    def populate_initial_data(self):
        self.setup_strand_filter()
        self.setup_grade_filter()
        self.setup_department_filter()
        self.strandFilter.setCurrentText("Select All")
        self.gradeFilter.setCurrentText("Select All")
        self.departmentFilter.setCurrentText("Select All") 
        self.populate_studentList_data()
        self.populate_attendance_data()
        self.populate_admin_table()
        self.populate_staff_table()
        
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

    def Side_Menu_Num_0(self):
        if self.Side_Menu_Num == 0:
            self.animation1 = QtCore.QPropertyAnimation(self.leftMenu, b"maximumWidth")
            self.animation1.setDuration(500)
            self.animation1.setStartValue(0)
            self.animation1.setEndValue(221)
            self.animation1.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
            self.animation1.start()

            self.animation2 = QtCore.QPropertyAnimation(self.leftMenu, b"minimumWidth")
            self.animation2.setDuration(500)
            self.animation2.setStartValue(0)
            self.animation2.setEndValue(221)
            self.animation2.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
            self.animation2.start()

            self.Side_Menu_Num = 1
        else:
            self.animation1 = QtCore.QPropertyAnimation(self.leftMenu, b"minimumWidth")
            self.animation1.setDuration(500)
            self.animation1.setStartValue(211)
            self.animation1.setEndValue(0)
            self.animation1.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
            self.animation1.start()

            self.animation2 = QtCore.QPropertyAnimation(self.leftMenu, b"maximumWidth")
            self.animation2.setDuration(500)
            self.animation2.setStartValue(211)
            self.animation2.setEndValue(0)
            self.animation2.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
            self.animation2.start()

            self.Side_Menu_Num = 0

    def update_time(self):
        now = QDateTime.currentDateTime()
        if hasattr(self, "date_label"):
            self.date_label.setText(now.toString("MMMM dd, yyyy"))
        if hasattr(self, "time_label"):
            self.time_label.setText(now.toString("hh:mm:ss AP"))

    def populate_studentList_data(self):
        selected_strand = self.strandFilter.currentText()
        selected_grade = self.gradeFilter.currentText()

        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()

        base_query = """
            SELECT
                p.person_id,
                p.first_name || ' ' || p.middle_name || ' ' || p.last_name AS full_name,
                g.grade_level,
                s.strand_name,
                p.gender
            FROM Person p
            JOIN StudentDetails sd ON p.person_id = sd.person_id
            JOIN Strand s ON sd.strand_id = s.strand_id
            JOIN GradeLevel g ON sd.grade_level_id = g.grade_level_id
        """

        filters = []
        params = []

        if selected_strand != "Select All":
            filters.append("s.strand_name = ?")
            params.append(selected_strand)

        if selected_grade != "Select All":
            filters.append("g.grade_level = ?")
            params.append(selected_grade)

        if filters:
            base_query += " WHERE " + " AND ".join(filters)

        cursor.execute(base_query, params)
        data = cursor.fetchall()
        conn.close()

        self.student_list_data = data

        table = self.studentList_table
        table.setRowCount(len(data))
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["ID","NAME", "GRADE", "STRAND", "GENDER"])
        table.verticalHeader().setVisible(True)

        for row_index, row_data in enumerate(data):
            for col_index, col_data in enumerate(row_data):
                item = QtWidgets.QTableWidgetItem(str(col_data))
                item.setForeground(QtGui.QColor("black"))
                item.setTextAlignment(QtCore.Qt.AlignLeft)
                table.setItem(row_index, col_index, item)

            header_item = QtWidgets.QTableWidgetItem(str(row_index + 1))
            header_item.setTextAlignment(QtCore.Qt.AlignCenter)
            table.setVerticalHeaderItem(row_index, header_item)
            table.setRowHeight(row_index, 30)

         # Adjust columns to fit neatly
        table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

        # Set a fixed width for each column
        table.setColumnWidth(0, 10)   # ID
        table.setColumnWidth(1, 270)  # NAME
        table.setColumnWidth(2, 130)  # GRADE
        table.setColumnWidth(3, 160)  # STRAND
        table.setColumnWidth(4, 160)  # Gender

        table.setColumnHidden(0, True)# Hide the ID column

        # Set a fixed height for each row
        table.verticalHeader().setDefaultSectionSize(30)
    def populate_staff_table(self):
        selected_department = self.departmentFilter.currentText()

        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()

        base_query = """
            SELECT sd.staff_id, p.first_name || ' ' || p.middle_name || ' ' || p.last_name,
                p.gender, d.department_name
            FROM StaffDetails sd
            JOIN Person p ON sd.person_id = p.person_id
            JOIN Department d ON sd.department_id = d.department_id
        """
        params = []
        if selected_department != "Select All":
            base_query += " WHERE d.department_name = ?"
            params.append(selected_department)

        cursor.execute(base_query, params)
        rows = cursor.fetchall()
        conn.close()

        self.staff_list_data = rows
        self.display_staff_table(rows)

        table = self.staffTable
        table.setRowCount(len(rows))
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["ID", "Name", "Gender", "Department"])
        table.verticalHeader().setVisible(True)

        for row_index, row_data in enumerate(rows):
            for col_index, col_data in enumerate(row_data):
                item = QtWidgets.QTableWidgetItem(str(col_data))
                item.setTextAlignment(QtCore.Qt.AlignLeft)
                item.setForeground(QtGui.QColor("black"))
                table.setItem(row_index, col_index, item)

            header_item = QtWidgets.QTableWidgetItem(str(row_index + 1))
            header_item.setTextAlignment(QtCore.Qt.AlignCenter)
            table.setVerticalHeaderItem(row_index, header_item)
            table.setRowHeight(row_index, 30)
        
          # Adjust columns to fit neatly
        table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

        # Set a fixed width for each column
        table.setColumnWidth(0, 80)   # ID
        table.setColumnWidth(1, 270)  # NAME
        table.setColumnWidth(2, 130)  # GENDER
        table.setColumnWidth(3, 160)  # DEPARTMENT

        table.setColumnHidden(0, True)# Hide the ID column

        # Set a fixed height for each row
        table.verticalHeader().setDefaultSectionSize(30)

    def display_staff_table(self, data):
        table = self.staffTable
        table.setRowCount(len(data))
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["ID", "Name", "Gender", "Department"])

        for row_index, row_data in enumerate(data):
            for col_index, col_data in enumerate(row_data):
                item = QtWidgets.QTableWidgetItem(str(col_data))
                item.setTextAlignment(QtCore.Qt.AlignLeft)
                item.setForeground(QtGui.QColor("black"))
                table.setItem(row_index, col_index, item)

            header_item = QtWidgets.QTableWidgetItem(str(row_index + 1))
            header_item.setTextAlignment(QtCore.Qt.AlignCenter)
            table.setVerticalHeaderItem(row_index, header_item)
            table.setRowHeight(row_index, 30)

        table.setColumnHidden(0, True)
        table.setColumnWidth(0, 80)
        table.setColumnWidth(1, 270)
        table.setColumnWidth(2, 130)
        table.setColumnWidth(3, 160)
        table.verticalHeader().setDefaultSectionSize(30)
        table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

        for row_index in range(len(data)):
            header_item = QtWidgets.QTableWidgetItem(str(row_index + 1))
            header_item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.staffTable.setVerticalHeaderItem(row_index, header_item)


    def search_staff_list(self):
        search_text = self.staff_searchBar.text().strip().lower()
        searched_data = []

        for row in self.staff_list_data:
            full_name = str(row[1]).lower()

            if search_text in full_name:
                searched_data.append(row)

        self.display_staff_table(searched_data)

        if hasattr(self, "noStaffLabel"):
            self.noStaffLabel.setVisible(len(searched_data) == 0)
            if len(searched_data) == 0:
                self.noStaffLabel.setText("🔍 No matching staff found.")


    def search_student_list(self):
        search_text = self.studentList_searchBar.text().strip().lower()
        searched_data = []

        for row in self.student_list_data:
            name = str(row[1]).lower()
            if search_text in name:
                searched_data.append(row)

        self.display_student_data(searched_data)

        # Show "no data" message if nothing is found
        if hasattr(self, "studentNoDataLabel"):
            self.studentNoDataLabel.setVisible(len(searched_data) == 0)
            if len(searched_data) == 0:
                self.studentNoDataLabel.setText("🔍 No matching student found.")

    def setup_strand_filter(self):
        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()
        cursor.execute("SELECT strand_name FROM Strand ORDER BY strand_name ASC")
        strands = [row[0] for row in cursor.fetchall()]
        conn.close()


        self.strandFilter.clear()
        self.strandFilter.addItem("Select Strand")  # Simulated placeholder
        self.strandFilter.setItemData(0, 0, QtCore.Qt.UserRole - 1)

        self.strandFilter.addItem("Select All")
        self.strandFilter.addItems(strands)
        self.strandFilter.currentIndexChanged.connect(self.populate_studentList_data)

    def setup_grade_filter(self):
        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()
        cursor.execute("SELECT grade_level FROM GradeLevel ORDER BY grade_level ASC")
        grades = [str(row[0]) for row in cursor.fetchall()]
        conn.close()

        self.gradeFilter.clear()
        self.gradeFilter.addItem("Select Grade") 
        self.gradeFilter.setItemData(0, 0, QtCore.Qt.UserRole - 1)

        self.gradeFilter.addItem("Select All")
        self.gradeFilter.addItems(grades)
        self.gradeFilter.currentIndexChanged.connect(self.populate_studentList_data)

    def setup_department_filter(self):
        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()
        cursor.execute("SELECT department_name FROM Department ORDER BY department_name ASC")
        departments = [row[0] for row in cursor.fetchall()]
        conn.close()

        self.departmentFilter.clear()
        self.departmentFilter.addItem("Select Department")  # Simulated placeholder
        self.departmentFilter.setItemData(0, 0, QtCore.Qt.UserRole - 1)

        self.departmentFilter.addItem("Select All")
        self.departmentFilter.addItems(departments)
        self.departmentFilter.currentIndexChanged.connect(self.populate_staff_table)
        self.departmentFilter.setCurrentText("Select All")

    def display_student_data(self, data):
        table = self.studentList_table
        table.setRowCount(len(data))
        table.setColumnCount(5)  # ID, NAME, GRADE, STRAND, GENDER
        table.setHorizontalHeaderLabels(["ID", "NAME", "GRADE", "STRAND", "GENDER"])

        for row_index, row_data in enumerate(data):
            for col_index, col_data in enumerate(row_data):
                item = QtWidgets.QTableWidgetItem(str(col_data))
                item.setForeground(QtGui.QColor("black"))
                item.setTextAlignment(QtCore.Qt.AlignLeft)
                table.setItem(row_index, col_index, item)

            header_item = QtWidgets.QTableWidgetItem(str(row_index + 1))
            header_item.setTextAlignment(QtCore.Qt.AlignCenter)
            table.setVerticalHeaderItem(row_index, header_item)

        # Hides the person_id column
        table.setColumnHidden(0, True)

        table.setColumnWidth(0, 0)

    def open_add_student_dialog(self):
        dialog = AddStudentDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            data = dialog.get_student_data()

            if not all([data["first_name"], data["last_name"], data["image_folder"], data["profile_image"]]):
                QMessageBox.warning(self, "Missing Info", "All fields including images must be provided.")
                return

            conn = sqlite3.connect("recognition.db")
            cursor = conn.cursor()

            # 1. Insert person record first with temporary profile path
            cursor.execute("""
                INSERT INTO Person (first_name, middle_name, last_name, gender, profile_image_url)
                VALUES (?, ?, ?, ?, ?)
            """, (
                data["first_name"], data["middle_name"], data["last_name"], data["gender"],
                "temp"  
            ))
            person_id = cursor.lastrowid

            # 2. Get IDs
            cursor.execute("SELECT strand_id FROM Strand WHERE strand_name = ?", (data["strand"],))
            strand_id = cursor.fetchone()[0]

            cursor.execute("SELECT grade_level_id FROM GradeLevel WHERE grade_level = ?", (data["grade"],))
            grade_id = cursor.fetchone()[0]

            cursor.execute("INSERT INTO StudentDetails (person_id, strand_id, grade_level_id) VALUES (?, ?, ?)",
                        (person_id, strand_id, grade_id))
            conn.commit()

            # 3. Save images
            student_folder = " ".join(part for part in [data['first_name'], data['middle_name'], data['last_name']] if part.strip())
            face_folder = os.path.join("images", student_folder)
            os.makedirs(face_folder, exist_ok=True)


            # Copy profile image
            profile_dst = os.path.join(face_folder, "profile.jpg")
            if not os.path.samefile(os.path.dirname(data["profile_image"]), face_folder):
                shutil.copy(data["profile_image"], profile_dst)
            else:
                # Rename if already in same folder
                src = data["profile_image"]
                profile_dst = os.path.join(face_folder, "profile.jpg")
                if src != profile_dst:
                    os.rename(src, profile_dst)

            # ✅ Update correct profile_image_url path
            cursor.execute("UPDATE Person SET profile_image_url = ? WHERE person_id = ?", (profile_dst, person_id))

            # Add to FaceImages table
            cursor.execute("INSERT INTO FaceImages (person_id, image_path) VALUES (?, ?)", (person_id, profile_dst))

            # 4. Copy all other images from folder
            for file in os.listdir(data["image_folder"]):
                src = os.path.join(data["image_folder"], file)
                if os.path.isfile(src):
                    # Don’t re-copy the profile image if it's the same
                    if os.path.samefile(src, data["profile_image"]):
                        continue

                    dst = os.path.join(face_folder, file)
                    shutil.copy(src, dst)
                    cursor.execute("INSERT INTO FaceImages (person_id, image_path) VALUES (?, ?)", (person_id, dst))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Added", "Student successfully added.")
            self.populate_studentList_data()

            # Trigger embedding generation
            self.generate_embeddings_from_face_images("recognition.db")

    def open_add_staff_dialog(self):
        dialog = AddStaffDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            data = dialog.get_staff_data()

            if not all([data["first_name"], data["last_name"], data["profile_image"]]):
                QMessageBox.warning(self, "Missing Info", "Name and profile image are required.")
                return

            conn = sqlite3.connect("recognition.db")
            cursor = conn.cursor()

            # Insert Person
            cursor.execute("""
                INSERT INTO Person (first_name, middle_name, last_name, gender, profile_image_url)
                VALUES (?, ?, ?, ?, ?)
            """, (data["first_name"], data["middle_name"], data["last_name"], data["gender"], "temp"))
            person_id = cursor.lastrowid

            # Department
            cursor.execute("SELECT department_id FROM Department WHERE department_name = ?", (data["department"],))
            department_id = cursor.fetchone()[0]

            cursor.execute("INSERT INTO StaffDetails (person_id, department_id) VALUES (?, ?)", (person_id, department_id))

            # Save images
            folder_name = " ".join(part for part in [data['first_name'], data['middle_name'], data['last_name']] if part.strip())
            folder_path = os.path.join("images/staff", folder_name)
            os.makedirs(folder_path, exist_ok=True)


            profile_dst = os.path.join(folder_path, "profile.jpg")
            shutil.copy(data["profile_image"], profile_dst)

            cursor.execute("UPDATE Person SET profile_image_url = ? WHERE person_id = ?", (profile_dst, person_id))
            cursor.execute("INSERT INTO FaceImages (person_id, image_path) VALUES (?, ?)", (person_id, profile_dst))

            # Copy other images
            if data["image_folder"]:
                for file in os.listdir(data["image_folder"]):
                    src = os.path.join(data["image_folder"], file)
                    if os.path.isfile(src):
                        if os.path.samefile(src, data["profile_image"]):
                            continue
                        dst = os.path.join(folder_path, file)
                        shutil.copy(src, dst)
                        cursor.execute("INSERT INTO FaceImages (person_id, image_path) VALUES (?, ?)", (person_id, dst))

            conn.commit()
            conn.close()

            self.populate_staff_table()
            QMessageBox.information(self, "Added", "Staff added successfully.")

            self.generate_embeddings_from_face_images("recognition.db")



    def generate_embeddings_from_face_images(self, db_path="recognition.db"):
        print("🔄 Embedding generation started...")
        embedder = InceptionResnetV1(pretrained='vggface2').eval()

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT person_id FROM FaceEmbeddings")
        embedded_ids = {row[0] for row in cursor.fetchall()}

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
                img = cv2.resize(img, (160, 160))
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype('float32') / 255.0
                img = (img - 0.5) / 0.5
                img = np.transpose(img, (2, 0, 1))
                img_tensor = torch.tensor(img).unsqueeze(0).float()

                with torch.no_grad():
                    emb = embedder(img_tensor)[0].numpy()
                emb = emb / np.linalg.norm(emb)

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

    def get_selected_student_row(self):
        selected_items = self.studentList_table.selectedItems()
        if selected_items:
            self.selected_student_row = selected_items[0].row()
        else:
            self.selected_student_row = None

    def update_selected_student(self):
        if self.selected_student_row is None:
            QMessageBox.warning(self, "No Selection", "Please select a student to update.")
            return

        person_id_item = self.studentList_table.item(self.selected_student_row, 0)
        name = self.studentList_table.item(self.selected_student_row, 1).text()
        grade = self.studentList_table.item(self.selected_student_row, 2).text()
        strand = self.studentList_table.item(self.selected_student_row, 3).text()
        gender = self.studentList_table.item(self.selected_student_row, 4).text()

        person_id = person_id_item.text()

        # Split name
        name_parts = name.split()
        first_name = name_parts[0]
        middle_name = name_parts[1] if len(name_parts) > 2 else ""
        last_name = " ".join(name_parts[2:]) if len(name_parts) > 2 else name_parts[-1]

        dialog = UpdateStudentDialog(first_name, middle_name, last_name, grade, strand, gender)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            data = dialog.get_updated_data()

            # Check if there are any actual changes
            if (
                data["first_name"] == first_name and
                data["middle_name"] == middle_name and
                data["last_name"] == last_name and
                data["gender"] == gender and
                data["grade"] == grade and
                data["strand"] == strand
            ):
                QMessageBox.information(self, "No Changes", "No update was made.")
                return

            # --- DATABASE UPDATE ---
            conn = sqlite3.connect("recognition.db")
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE Person SET
                    first_name = ?,
                    middle_name = ?,
                    last_name = ?,
                    gender = ?
                WHERE person_id = ?
            """, (data["first_name"], data["middle_name"], data["last_name"], data["gender"], person_id))

            cursor.execute("SELECT grade_level_id FROM GradeLevel WHERE grade_level = ?", (data["grade"],))
            grade_row = cursor.fetchone()
            grade_id = grade_row[0] if grade_row else None

            cursor.execute("SELECT strand_id FROM Strand WHERE strand_name = ?", (data["strand"],))
            strand_row = cursor.fetchone()
            strand_id = strand_row[0] if strand_row else None

            cursor.execute("""
                UPDATE StudentDetails SET
                    grade_level_id = ?,
                    strand_id = ?
                WHERE person_id = ?
            """, (grade_id, strand_id, person_id))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Updated", "Student information updated successfully.")
            self.populate_studentList_data()


    def update_selected_staff(self):
        selected_row = self.staffTable.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "No Selection", "Select a staff to update.")
            return

        staff_id_item = self.staffTable.item(selected_row, 0)
        full_name = self.staffTable.item(selected_row, 1).text()
        gender = self.staffTable.item(selected_row, 2).text()
        department = self.staffTable.item(selected_row, 3).text()

        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()
        cursor.execute("SELECT person_id FROM StaffDetails WHERE staff_id = ?", (staff_id_item.text(),))
        person_id = cursor.fetchone()[0]

        name_parts = full_name.split()
        first = name_parts[0]
        middle = name_parts[1] if len(name_parts) > 2 else ""
        last = " ".join(name_parts[2:]) if len(name_parts) > 2 else name_parts[-1]

        dialog = UpdateStaffDialog(first, middle, last, gender, department)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            updated = dialog.get_updated_data()

            # Check for changes
            if (
                updated["first_name"] == first and
                updated["middle_name"] == middle and
                updated["last_name"] == last and
                updated["gender"] == gender and
                updated["department"] == department
            ):
                conn.close()
                QMessageBox.information(self, "No Changes", "No update was made.")
                return

            # Update
            cursor.execute("""
                UPDATE Person SET first_name=?, middle_name=?, last_name=?, gender=? WHERE person_id=?
            """, (updated["first_name"], updated["middle_name"], updated["last_name"], updated["gender"], person_id))

            cursor.execute("SELECT department_id FROM Department WHERE department_name = ?", (updated["department"],))
            department_id = cursor.fetchone()[0]

            cursor.execute("UPDATE StaffDetails SET department_id = ? WHERE person_id = ?", (department_id, person_id))
            conn.commit()
            conn.close()

            self.populate_staff_table()
            QMessageBox.information(self, "Updated", "Staff info updated.")

    def remove_selected_student(self):
        if self.selected_student_row is None:
            QMessageBox.warning(self, "No Selection", "Please select a student first.")
            return

        person_id_item = self.studentList_table.item(self.selected_student_row, 0)
        full_name_item = self.studentList_table.item(self.selected_student_row, 1)

        if not person_id_item:
            QMessageBox.critical(self, "Error", "Unable to retrieve student ID.")
            return

        person_id = person_id_item.text()
        full_name = full_name_item.text()

        confirm = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Are you sure you want to delete '{full_name}'?\nThis will delete all related face data, but keep attendance logs.",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm != QMessageBox.Yes:
            return

        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()

        # Delete from FaceEmbeddings
        cursor.execute("DELETE FROM FaceEmbeddings WHERE person_id = ?", (person_id,))

        # Get FaceImages paths
        cursor.execute("SELECT image_path FROM FaceImages WHERE person_id = ?", (person_id,))
        image_paths = [row[0] for row in cursor.fetchall()]

        # Delete from FaceImages
        cursor.execute("DELETE FROM FaceImages WHERE person_id = ?", (person_id,))

        # Delete from StudentDetails
        cursor.execute("DELETE FROM StudentDetails WHERE person_id = ?", (person_id,))

        # Update Person table — keep entry but clear name/profile info (so logs remain intact)
        cursor.execute("""
            UPDATE Person
            SET first_name = '[Deleted]', middle_name = '', last_name = '',
                gender = '', profile_image_url = ''
            WHERE person_id = ?
        """, (person_id,))

        conn.commit()
        conn.close()

        # Delete student folder if exists
        if image_paths:
            student_folder = os.path.dirname(image_paths[0])
            try:
                if os.path.exists(student_folder):
                    shutil.rmtree(student_folder)
            except Exception as e:
                print(f"⚠️ Failed to delete folder {student_folder}: {e}")

        QMessageBox.information(self, "Removed", f"'{full_name}' removed. Attendance logs kept.")
        self.populate_studentList_data()
        self.selected_student_row = None

    def remove_selected_staff(self):
        selected_row = self.staffTable.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a staff member to remove.")
            return

        staff_id = self.staffTable.item(selected_row, 0).text()
        full_name = self.staffTable.item(selected_row, 1).text()

        confirm = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Are you sure you want to delete '{full_name}'?\nThis will delete all face data and keep attendance logs.",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm != QMessageBox.Yes:
            return

        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()

        # Get person_id
        cursor.execute("SELECT person_id FROM StaffDetails WHERE staff_id = ?", (staff_id,))
        result = cursor.fetchone()
        if not result:
            QMessageBox.critical(self, "Error", "Could not find associated person.")
            return
        person_id = result[0]

        # Delete from embeddings
        cursor.execute("DELETE FROM FaceEmbeddings WHERE person_id = ?", (person_id,))
        
        # Get image paths and delete them
        cursor.execute("SELECT image_path FROM FaceImages WHERE person_id = ?", (person_id,))
        image_paths = [row[0] for row in cursor.fetchall()]
        cursor.execute("DELETE FROM FaceImages WHERE person_id = ?", (person_id,))
        
        # Delete staff details
        cursor.execute("DELETE FROM StaffDetails WHERE person_id = ?", (person_id,))
        
        # Anonymize the person
        cursor.execute("""
            UPDATE Person
            SET first_name = '[Deleted]', middle_name = '', last_name = '', gender = '', profile_image_url = ''
            WHERE person_id = ?
        """, (person_id,))
        
        conn.commit()
        conn.close()

        # Remove folder
        if image_paths:
            folder = os.path.dirname(image_paths[0])
            if os.path.exists(folder):
                shutil.rmtree(folder, ignore_errors=True)

        self.populate_staff_table()
        QMessageBox.information(self, "Removed", f"'{full_name}' removed.")



    def populate_attendance_data(self):
        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN p.first_name = '[Deleted]' THEN 'Deleted Student'
                    ELSE COALESCE(p.first_name || ' ' || p.middle_name || ' ' || p.last_name, 'Deleted Student')
                END AS full_name,
                COALESCE(g.grade_level, 'N/A'),
                COALESCE(s.strand_name, 'N/A'),
                a.date_in,
                a.time_in
            FROM AttendanceRecords a
            LEFT JOIN Person p ON a.person_id = p.person_id
            LEFT JOIN StudentDetails sd ON sd.person_id = a.person_id
            LEFT JOIN GradeLevel g ON g.grade_level_id = sd.grade_level_id
            LEFT JOIN Strand s ON s.strand_id = sd.strand_id
            ORDER BY a.attendance_id DESC
        """)
        data = cursor.fetchall()
        conn.close()

        #Store in memory so it can be searched later
        self.attendance_data = data

        table = self.attendanceTableWidget
        table.setRowCount(len(data))
        table.setHorizontalHeaderLabels(["NAME", "GRADE", "STRAND", "DATE", "TIME"])
        table.verticalHeader().setVisible(True)

        for row_index, row_data in enumerate(data):
            for col_index, col_data in enumerate(row_data):
                item = QtWidgets.QTableWidgetItem(str(col_data))
                item.setForeground(QtGui.QColor("black"))
                item.setTextAlignment(QtCore.Qt.AlignLeft)
                table.setItem(row_index, col_index, item)

            header_item = QtWidgets.QTableWidgetItem(str(row_index + 1))
            header_item.setTextAlignment(QtCore.Qt.AlignCenter)
            table.setVerticalHeaderItem(row_index, header_item)

        # Set a fixed width for each column
        table.setColumnWidth(0, 320)  # NAME
        table.setColumnWidth(1, 170)  # GRADE
        table.setColumnWidth(2, 180)  # STRAND
        table.setColumnWidth(3, 280)  # DATE
        table.setColumnWidth(4, 150)  # TIME

        # Set a fixed height for each row
        table.verticalHeader().setDefaultSectionSize(50)
        table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

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

        for row in self.attendance_data:
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

    def populate_admin_table(self):
        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT a.admin_id, a.username, a.admin_role, COALESCE(c.username, 'Super Admin') AS created_by
            FROM Admin a
            LEFT JOIN Admin c ON a.created_by_admin_id = c.admin_id
            WHERE a.admin_role = 'admin'
        """)
        rows = cursor.fetchall()
        conn.close()

        table = self.adminTable
        table.setRowCount(len(rows))
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Username", "Password", "Role", "Created By"])
        table.verticalHeader().setVisible(True)
        self.admin_ids = []

        for row_index, (admin_id, username, role, created_by) in enumerate(rows):
            self.admin_ids.append(admin_id)

            values = [username, "••••••", role, created_by]
            for col_index, value in enumerate(values):
                item = QtWidgets.QTableWidgetItem(value)
                item.setTextAlignment(QtCore.Qt.AlignLeft)
                item.setForeground(QtGui.QColor("black"))
                table.setItem(row_index, col_index, item)

        # Consistent Column Widths (adjust these as needed)
        table.setColumnWidth(0, 200)  #USERNAME
        table.setColumnWidth(1, 155)  #PASSWORD
        table.setColumnWidth(2, 145)  #ROLE
        table.setColumnWidth(3, 130)  #CREATED BY

        # Styling
        table.verticalHeader().setDefaultSectionSize(40)
        table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)


    def open_add_admin_dialog(self):
        dialog = AddAdminDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.populate_admin_table()

    def change_password(self):
        selected_row = self.adminTable.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Warning", "Please select an admin.")
            return

        username_item = self.adminTable.item(selected_row, 0)
        username = username_item.text() if username_item else "selected admin"

        new_pass, ok = QtWidgets.QInputDialog.getText(
            self, "Change Password", f"Enter new password for '{username}':", QtWidgets.QLineEdit.Password
        )
        if not ok or not new_pass.strip():
            return

        admin_id = self.admin_ids[selected_row]
        password_hash = hashlib.sha256(new_pass.encode()).hexdigest()

        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE Admin SET password_hash = ? WHERE admin_id = ?", (password_hash, admin_id))
        conn.commit()
        conn.close()

        QMessageBox.information(self, "Success", f"Password for '{username}' changed successfully.")


    def remove_admin(self):
        selected_row = self.adminTable.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Warning", "Please select an admin to remove.")
            return

        username_item = self.adminTable.item(selected_row, 0)
        username = username_item.text() if username_item else "this admin"

        confirm = QMessageBox.question(
            self,
            "Confirm",
            f"Are you sure you want to delete '{username}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        admin_id = self.admin_ids[selected_row]

        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Admin WHERE admin_id = ?", (admin_id,))
        conn.commit()
        conn.close()

        self.populate_admin_table()
        QMessageBox.information(self, "Removed", f"Admin '{username}' removed successfully.")

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
        self.setGraphicsEffect(None)
        QMessageBox.information(self, "Logout", "You have been logged out.")
        self.close()
        self.attendance_window = AttendanceApp()
        self.attendance_window.show()

    def superAdmin(self):
        login_dialog = LoginDialog(super_admin_mode=True)
        if login_dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.super_admin_window = SuperAdminDashboard(self.current_admin_id)
            self.super_admin_window.show()

class AddStudentDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(AddStudentDialog, self).__init__(parent)
        uic.loadUi(ADD_UI_PATH, self)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        # Animations
        self.effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)
        self.animation = QPropertyAnimation(self.effect, b"opacity")
        self.animation.setDuration(500)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.start()

        # Button connections
        self.imagesUpload_btn.clicked.connect(self.select_image_folder)
        self.profileImageUpload_btn.clicked.connect(self.select_profile_image)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.image_folder = ""
        self.profile_image_path = ""

        self.genderComboBox.addItems(["Male", "Female"])
        self.load_comboboxes()

    def select_image_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder with Student Images")
        if folder:
            self.image_folder = folder
            self.imagesUpload_btn.setText("Selected")

    def select_profile_image(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Profile Image", "", "Images (*.png *.jpg *.jpeg)")
        if file:
            self.profile_image_path = file
            self.profileImageUpload_btn.setText("Selected")

    def load_comboboxes(self):
        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()

        cursor.execute("SELECT strand_name FROM Strand ORDER BY strand_name")
        self.strandComboBox.addItems([row[0] for row in cursor.fetchall()])

        cursor.execute("SELECT grade_level FROM GradeLevel ORDER BY grade_level")
        self.gradeComboBox.addItems([str(row[0]) for row in cursor.fetchall()])

        conn.close()

    def get_student_data(self):
        return {
            "first_name": self.firstNameLineEdit.text().strip(),
            "middle_name": self.middleNameLineEdit.text().strip(),
            "last_name": self.lastNameLineEdit.text().strip(),
            "gender": self.genderComboBox.currentText(),
            "strand": self.strandComboBox.currentText(),
            "grade": self.gradeComboBox.currentText(),
            "image_folder": self.image_folder,
            "profile_image": self.profile_image_path
        }

class AddStaffDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(AddStaffDialog, self).__init__(parent)
        uic.loadUi(ADD_STAFF_UI_PATH, self)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        self.effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)
        self.animation = QPropertyAnimation(self.effect, b"opacity")
        self.animation.setDuration(500)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.start()

        self.image_folder = ""
        self.profile_image_path = ""

        self.genderComboBox.addItems(["Male", "Female"])
        self.load_comboboxes()

        self.imagesUpload_btn.clicked.connect(self.select_image_folder)
        self.profileImageUpload_btn.clicked.connect(self.select_profile_image)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def select_image_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder with Staff Images")
        if folder:
            self.image_folder = folder
            self.imagesUpload_btn.setText("Selected")

    def select_profile_image(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Profile Image", "", "Images (*.png *.jpg *.jpeg)")
        if file:
            self.profile_image_path = file
            self.profileImageUpload_btn.setText("Selected")

    def load_comboboxes(self):
        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()
        cursor.execute("SELECT department_name FROM Department ORDER BY department_name")
        self.departmentComboBox.addItems([row[0] for row in cursor.fetchall()])
        conn.close()

    def get_staff_data(self):
        return {
            "first_name": self.firstNameLineEdit.text().strip(),
            "middle_name": self.middleNameLineEdit.text().strip(),
            "last_name": self.lastNameLineEdit.text().strip(),
            "gender": self.genderComboBox.currentText(),
            "department": self.departmentComboBox.currentText(),
            "image_folder": self.image_folder,
            "profile_image": self.profile_image_path
        }


class UpdateStudentDialog(QtWidgets.QDialog):
    def __init__(self, first_name, middle_name, last_name, grade, strand, gender):
        super(UpdateStudentDialog, self).__init__()
        uic.loadUi(UPDATE_UI_PATH, self)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        self.effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)

        self.animation = QPropertyAnimation(self.effect, b"opacity")
        self.animation.setDuration(500)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.start()

        self.populate_grade_combobox(grade)
        self.populate_strand_combobox(strand)
        
        self.genderComboBox.addItems(["Male", "Female"])
        self.genderComboBox.setCurrentText(gender)

        self.firstNameLineEdit.setText(first_name)
        self.middleNameLineEdit.setText(middle_name)
        self.lastNameLineEdit.setText(last_name)

        self.original_data = {
            "first_name": first_name.strip(),
            "middle_name": middle_name.strip(),
            "last_name": last_name.strip(),
            "grade": grade.strip(),
            "strand": strand.strip(),
            "gender": gender.strip()
        }

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
    def get_updated_data(self):
        return {
            "first_name": self.firstNameLineEdit.text().strip(),
            "middle_name": self.middleNameLineEdit.text().strip(),
            "last_name": self.lastNameLineEdit.text().strip(),
            "grade": self.gradeComboBox.currentText(),
            "strand": self.strandComboBox.currentText(),
            "gender": self.genderComboBox.currentText()
        }

    def populate_grade_combobox(self, current_value):
        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()
        cursor.execute("SELECT grade_level FROM GradeLevel ORDER BY grade_level ASC")
        grades = [str(row[0]) for row in cursor.fetchall()]
        conn.close()

        self.gradeComboBox.addItems(grades)
        self.gradeComboBox.setCurrentText(current_value)

    def populate_strand_combobox(self, current_value):
        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()
        cursor.execute("SELECT strand_name FROM Strand ORDER BY strand_name ASC")
        strands = [row[0] for row in cursor.fetchall()]
        conn.close()

        self.strandComboBox.addItems(strands)
        self.strandComboBox.setCurrentText(current_value)

    def fade_and_close(self, result):
        self.animation = QPropertyAnimation(self.effect, b"opacity")
        self.animation.setDuration(300)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.finished.connect(lambda: self.done(result))
        self.animation.start()

    def accept(self):
        updated_data = self.get_updated_data()
        if updated_data == self.original_data:
            QMessageBox.information(self, "No Changes", "No update was made.")
            return  # Don't close the dialog
        self.fade_and_close(QtWidgets.QDialog.Accepted)

    def reject(self):
        self.fade_and_close(QtWidgets.QDialog.Rejected)

class UpdateStaffDialog(QtWidgets.QDialog):
    def __init__(self, first_name, middle_name, last_name, gender, department):
        super(UpdateStaffDialog, self).__init__()
        uic.loadUi(UPDATE_STAFF_UI_PATH, self)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)

        self.firstNameLineEdit.setText(first_name)
        self.middleNameLineEdit.setText(middle_name)
        self.lastNameLineEdit.setText(last_name)
        self.genderComboBox.addItems(["Male", "Female"])
        self.genderComboBox.setCurrentText(gender)

        self.load_departments()
        self.departmentComboBox.setCurrentText(department)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def load_departments(self):
        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()
        cursor.execute("SELECT department_name FROM Department ORDER BY department_name")
        self.departmentComboBox.addItems([row[0] for row in cursor.fetchall()])
        conn.close()

    def get_updated_data(self):
        return {
            "first_name": self.firstNameLineEdit.text().strip(),
            "middle_name": self.middleNameLineEdit.text().strip(),
            "last_name": self.lastNameLineEdit.text().strip(),
            "gender": self.genderComboBox.currentText(),
            "department": self.departmentComboBox.currentText()
        }

class AddAdminDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, creator_admin_id=None):
        super(AddAdminDialog, self).__init__(parent)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.setModal(True)
        self.creator_admin_id = creator_admin_id

        uic.loadUi(ADD_ADMIN_UI_PATH, self)

        self.effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)
        self.animation = QPropertyAnimation(self.effect, b"opacity")
        self.animation.setDuration(400)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.start()

        self.buttonBox.accepted.connect(self.validate_and_submit)
        self.buttonBox.rejected.connect(self.reject)

        self.role = "admin"  

    def validate_and_submit(self):
        username = self.usernameLineEdit.text().strip()
        password = self.passwordLineEdit.text()
        confirm = self.confirmPasswordLineEdit.text()
        role = self.role

        if not username or not password or not confirm:
            QMessageBox.warning(self, "Missing Fields", "Please complete all fields.")
            return
        if password != confirm:
            QMessageBox.warning(self, "Mismatch", "Passwords do not match.")
            return
        if len(password) < 5:
            QMessageBox.warning(self, "Weak Password", "Password must be at least 5 characters.")
            return

        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM Admin WHERE username = ?", (username,))
        if cursor.fetchone():
            QMessageBox.warning(self, "Exists", "Username already exists.")
            conn.close()
            return

        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        cursor.execute("""
            INSERT INTO Admin (username, password_hash, admin_role, created_by_admin_id)
            VALUES (?, ?, ?, ?)
        """, (username, password_hash, role, self.creator_admin_id))

        conn.commit()
        conn.close()

        QMessageBox.information(self, "Success", f"Admin '{username}' added.")
        self.accept()

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
        self.dialog_shown = False

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
            self.camera.release()  

            dialog = UnrecognizeModule(parent=self, frame=self.last_frame)
            dialog.exec_()

            # Delay restart slightly
            QTimer.singleShot(300, self.restart_main_camera)

            self.dialog_shown = False
            self.unrecognized_detected = False
            self.unrecognized_timer.stop()

    def restart_main_camera(self):
        self.camera = cv2.VideoCapture(0)  # Re-initialize safely
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
                CASE 
                    WHEN p.first_name = '[Deleted]' THEN 'Deleted Student'
                    ELSE p.first_name || ' ' || p.middle_name || ' ' || p.last_name
                END AS full_name,
                COALESCE(g.grade_level, 'N/A') AS grade,
                COALESCE(s.strand_name, 'N/A') AS strand,
                a.date_in,
                a.time_in
            FROM AttendanceRecords a
            LEFT JOIN Person p ON a.person_id = p.person_id
            LEFT JOIN StudentDetails sd ON sd.person_id = p.person_id
            LEFT JOIN GradeLevel g ON g.grade_level_id = sd.grade_level_id
            LEFT JOIN Strand s ON s.strand_id = sd.strand_id
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

            if login_dialog.logged_in_role == "super_admin":
                self.super_admin_window = SuperAdminDashboard(current_admin_id=login_dialog.admin_id)
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
