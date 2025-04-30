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
import random

from PyQt5 import QtWidgets, uic, QtCore, QtGui
from PyQt5.QtCore import QTimer, QDateTime, QPropertyAnimation, Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QGraphicsOpacityEffect, QMessageBox, QFileDialog, QDialog
from facenet_pytorch import MTCNN
from facenet_pytorch import InceptionResnetV1
from PIL import Image
from PyQt5.QtPrintSupport import QPrinter, QPrintPreviewDialog, QPrintDialog
from PyQt5.QtGui import QTextDocument, QTextCursor
from PIL import ImageEnhance, ImageOps

# Paths to UI files
STARTAPP_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "startApp.ui")
MAIN_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "automated.ui")
LOGIN_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "login.ui")
ADMIN_LOGIN_UI_PATH = os.path.join(
    os.path.dirname(__file__), "ui", "loginPermission.ui"
)
ADMIN_LOGIN_UI_PATH = os.path.join(
    os.path.dirname(__file__), "ui", "loginPermission.ui"
)
ADMIN_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "admin.ui")
SUPERADMIN_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "superAdmin.ui")
UPDATE_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "updateStudent.ui")
ADD_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "addStudent.ui")
ADD_ADMIN_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "addAdmin.ui")
ADD_STAFF_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "addStaff.ui")
UPDATE_STAFF_UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "updateStaff.ui")
CHANGE_CREDENTIAL_UI_PATH = os.path.join(
    os.path.dirname(__file__), "ui", "changeCredentials.ui"
)
UNRECOGNIZE_UI_PATH = os.path.join(
    os.path.dirname(__file__), "ui", "unrecognizeModule.ui"
)


class StartScreen(QtWidgets.QDialog):
    def __init__(self):
        super(StartScreen, self).__init__()
        uic.loadUi(STARTAPP_UI_PATH, self)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)

        # Connect buttons
        self.attendanceLogin_btn.clicked.connect(self.open_attendance_login)
        self.loginAdmin_btn.clicked.connect(self.open_admin_login)
        self.minimize_btn.clicked.connect(self.showMinimized)
        self.exit_btn.clicked.connect(self.confirm_exit)

        # Center StartScreen on screen
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def open_attendance_login(self):
        dialog = LoginPermissionDialog()
        if dialog.exec_() == QtWidgets.QDialog.Accepted and dialog.logged_in:
            self.attendance_app = AttendanceApp()
            self.attendance_app.show()
            self.close()

    def open_admin_login(self):
        dialog = LoginDialog()
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            role = dialog.logged_in_role
            if role == "admin":
                self.admin_dashboard = AdminDashboard()
                self.admin_dashboard.show()
            elif role == "super_admin":
                self.superadmin_dashboard = SuperAdminDashboard(
                    current_admin_id=dialog.admin_id, return_to_start=True
                )
                self.superadmin_dashboard.show()
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Unknown Role", f"Logged in as unknown role: {role}"
                )
            self.close()

    def fade_in(self):
        self.effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)

        self.animation = QPropertyAnimation(self.effect, b"opacity")
        self.animation.setDuration(800)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.start()

    def confirm_exit(self):
        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm Exit",
            "Are you sure you want to exit?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        if reply == QtWidgets.QMessageBox.Yes:
            self.close()

        # For dragging the window

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()


class LoginPermissionDialog(QtWidgets.QDialog):
    """Admin Login for Automated Attendance Logging."""

    def __init__(self):
        super(LoginPermissionDialog, self).__init__()
        uic.loadUi(ADMIN_LOGIN_UI_PATH, self)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.exit_btn.clicked.connect(self.close)

        self.login_btn.clicked.connect(self.login_action)

        # Center StartScreen on screen
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def login_action(self):
        username = self.usernameInput.text().strip()
        password = self.passwordInput.text().strip()

        if not username or not password:
            QtWidgets.QMessageBox.warning(
                self, "Missing Fields", "Username and password must not be empty."
            )
            return

        try:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()

            conn = sqlite3.connect("recognition.db")
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT admin_id, admin_role 
                FROM Admin 
                WHERE username = ? AND password_hash = ?
            """,
                (username, hashed_password),
            )
            result = cursor.fetchone()
            conn.close()

            if result:
                self.admin_id, self.logged_in_role = result
                self.logged_in = True
                self.accept()
            else:
                QtWidgets.QMessageBox.critical(
                    self, "Login Failed", "Invalid username or password!"
                )

        except sqlite3.Error as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Database Error",
                f"An error occurred while connecting to the database:\n{e}",
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Unexpected Error", f"An unexpected error occurred:\n{e}"
            )

        # For dragging the window

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()


class LoginDialog(QtWidgets.QDialog):
    """Dashboard Login Dialog"""

    def __init__(self, super_admin_mode=False):
        super(LoginDialog, self).__init__()

        # Load Login UI
        uic.loadUi(LOGIN_UI_PATH, self)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.exit_btn.clicked.connect(self.close)
        self.super_admin_mode = super_admin_mode
        self.logged_in_role = None  # 'admin' or 'superadmin'

        # Connect login button
        self.login_btn.clicked.connect(self.login_action)

        # Center StartScreen on screen
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def login_action(self):
        username = self.usernameInput.text().strip()
        password = self.passwordInput.text().strip()

        if not username or not password:
            QtWidgets.QMessageBox.warning(
                self, "Missing Fields", "Username and password must not be empty."
            )
            return

        try:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()

            conn = sqlite3.connect("recognition.db")
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT admin_id, admin_role 
                FROM Admin 
                WHERE username = ? AND password_hash = ?
            """,
                (username, hashed_password),
            )
            result = cursor.fetchone()
            conn.close()

            if result:
                self.admin_id = result[0]
                self.logged_in_role = result[
                    1
                ]  # Correctly set to 'admin' or 'super_admin'
                self.logged_in = True
                self.accept()

            else:
                QtWidgets.QMessageBox.critical(
                    self, "Login Failed", "Invalid username or password!"
                )

        except sqlite3.Error as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Database Error",
                f"An error occurred while connecting to the database:\n{e}",
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Unexpected Error", f"An unexpected error occurred:\n{e}"
            )

        # For dragging the window

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()


class SuperAdminPasswordDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(SuperAdminPasswordDialog, self).__init__(parent)
        self.setWindowTitle("Super Admin Verification")
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)

        layout = QtWidgets.QVBoxLayout()

        self.label = QtWidgets.QLabel("Enter Password:")
        layout.addWidget(self.label)

        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        layout.addWidget(self.password_input)

        self.buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        self.setLayout(layout)

        # Center StartScreen on screen
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def get_password(self):
        return self.password_input.text().strip()

        # For dragging the window

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()


def verify_superadmin_password(parent):
    dialog = SuperAdminPasswordDialog(parent)
    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        password = dialog.get_password()
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()
        cursor.execute(
            """
                SELECT admin_id FROM Admin WHERE password_hash = ? AND admin_role = 'super_admin'
            """,
            (hashed_password,),
        )
        result = cursor.fetchone()
        conn.close()

        if result:
            return True

    QMessageBox.warning(parent, "Permission Denied", "Incorrect password.")
    return False


class AdminDashboard(QtWidgets.QMainWindow):
    """Admin Dashboard UI (After Successful Login)"""

    def __init__(self, return_to_start=True):
        super(AdminDashboard, self).__init__()
        self.return_to_start = return_to_start

        # Load Admin UI
        uic.loadUi(ADMIN_UI_PATH, self)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)

        # ✅ Connect "Track Attendance" button
        if hasattr(self, "attendanceLogin_btn"):
            self.attendanceLogin_btn.clicked.connect(self.open_attendance_app)
        else:
            print("❌ attendanceLogin_btn not found in UI")

        # ✅ Set up QTimer to update time every second
        self.timer_clock = QTimer(self)
        self.timer_clock.timeout.connect(self.update_time)
        self.timer_clock.start(1000)

        self.update_time()

        # ✅ Menu and button connections
        self.Down_Menu_Num = 0
        self.toolMenu_btn.clicked.connect(lambda: self.Down_Menu_Num_0())
        self.logout_btn.clicked.connect(self.logout)
        self.searchBar.returnPressed.connect(self.search_attendance)
        self.printAttendance_btn.clicked.connect(
            lambda: self.print_table_widget(self.attendanceTableWidget, "Attendance Records")
        )
        self.exportPDFAttendance_btn.clicked.connect(
            lambda: self.print_table_widget(self.attendanceTableWidget, "Attendance Records", export_to_pdf=True)
        )

        # ✅ Load data into the table
        self.populate_attendance_data()

        # ✅ Center the window
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)

        self.move(qr.topLeft())

    def open_attendance_app(self):
        self.attendance_app = AttendanceApp()
        self.attendance_app.show()
        self.close()

    def Down_Menu_Num_0(self):
        if self.Down_Menu_Num == 0:
            self.animation1 = QtCore.QPropertyAnimation(self.frame_1, b"minimumHeight")
            self.animation1.setDuration(500)
            self.animation1.setStartValue(51)
            self.animation1.setEndValue(141)
            self.animation1.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
            self.animation1.start()

            self.animation2 = QtCore.QPropertyAnimation(self.frame_1, b"maximumHeight")
            self.animation2.setDuration(500)
            self.animation2.setStartValue(51)
            self.animation2.setEndValue(141)
            self.animation2.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
            self.animation2.start()

            self.Down_Menu_Num = 1

        else:
            self.animation1 = QtCore.QPropertyAnimation(self.frame_1, b"maximumHeight")
            self.animation1.setDuration(500)
            self.animation1.setStartValue(141)
            self.animation1.setEndValue(51)
            self.animation1.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
            self.animation1.start()

            self.animation2 = QtCore.QPropertyAnimation(self.frame_1, b"minimumHeight")
            self.animation2.setDuration(500)
            self.animation2.setStartValue(141)
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
        cursor.execute(
            """
            SELECT 
                COALESCE(a.full_name, p.first_name || ' ' || p.middle_name || ' ' || p.last_name) AS full_name,
                COALESCE(a.grade_level, g.grade_level) AS grade,
                COALESCE(a.strand_name, s.strand_name) AS strand,
                COALESCE(a.department_name, d.department_name) AS department,
                a.date_in,
                a.time_in
            FROM AttendanceRecords a
            LEFT JOIN Person p ON a.person_id = p.person_id
            LEFT JOIN StudentDetails sd ON sd.person_id = a.person_id
            LEFT JOIN GradeLevel g ON g.grade_level_id = sd.grade_level_id
            LEFT JOIN Strand s ON s.strand_id = sd.strand_id
            LEFT JOIN StaffDetails st ON st.person_id = a.person_id
            LEFT JOIN Department d ON d.department_id = st.department_id
            ORDER BY a.attendance_id DESC
            """
        )
        data = cursor.fetchall()
        conn.close()

        self.attendance_data = data

        table = self.attendanceTableWidget
        table.setRowCount(len(data))
        table.setHorizontalHeaderLabels(["NAME", "GRADE", "STRAND", "DEPARTMENT", "DATE", "TIME"])
        table.verticalHeader().setVisible(True)

        for row_index, row_data in enumerate(data):
            for col_index, col_data in enumerate(row_data):
                text = "" if col_data is None else str(col_data)
                item = QtWidgets.QTableWidgetItem(text)
                item.setForeground(QtGui.QColor("black"))
                item.setTextAlignment(QtCore.Qt.AlignLeft)
                table.setItem(row_index, col_index, item)

            header_item = QtWidgets.QTableWidgetItem(str(row_index + 1))
            header_item.setTextAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)
            table.setVerticalHeaderItem(row_index, header_item)

        table.verticalHeader().setDefaultSectionSize(50)
        table.verticalHeader().setStyleSheet("""
            QHeaderView::section {
                padding-top: 0px;
                margin: 0px;
                font-size: 14px;
                qproperty-alignment: AlignTop | AlignHCenter;
            }
        """)
        table.setColumnWidth(0, 300)
        table.setColumnWidth(1, 150)
        table.setColumnWidth(2, 160)
        table.setColumnWidth(3, 260)
        table.setColumnWidth(4, 180)
        table.setColumnWidth(5, 130)
        table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

       
    def refresh_table(self, data):
        table = self.attendanceTableWidget
        table.setRowCount(0)  # Clear existing rows
        table.setHorizontalHeaderLabels(
            ["NAME", "GRADE", "STRAND", "DEPARTMENT", "DATE", "TIME"]
        )
        table.setRowCount(len(data))

        for row_index, row_data in enumerate(data):
            for col_index, col_data in enumerate(row_data):
                text = "" if col_data is None else str(col_data)
                item = QtWidgets.QTableWidgetItem(text)
                item.setForeground(QtGui.QColor("black"))
                item.setTextAlignment(QtCore.Qt.AlignLeft)
                table.setItem(row_index, col_index, item)

            header_item = QtWidgets.QTableWidgetItem(str(row_index + 1))
            header_item.setTextAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)
            table.setVerticalHeaderItem(row_index, header_item)

        table.verticalHeader().setDefaultSectionSize(30)
        table.verticalHeader().setStyleSheet(""" 
            QHeaderView::section {
                padding-top: 0px;
                margin: 0px;
                font-size: 14px;
                qproperty-alignment: AlignTop | AlignHCenter;
            }
        """)

        # Adjust columns to fit neatly
        table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

        # Set a fixed width for each column
        table.setColumnWidth(0, 300)  # NAME
        table.setColumnWidth(1, 150)  # GRADE
        table.setColumnWidth(2, 160)  # STRAND
        table.setColumnWidth(3, 290)  # DEPARTMENT
        table.setColumnWidth(4, 180)  # DATE
        table.setColumnWidth(5, 130)  # TIME


    def search_attendance(self):
        search_text = self.searchBar.text().strip().lower()
        filtered_data = []

        for row in self.all_data:
            name = str(row[0] or "").lower()
            grade = str(row[1] or "").lower()
            strand = str(row[2] or "").lower()
            department = str(row[3] or "").lower()
            date = str(row[4] or "").lower()

            if (
                search_text in name
                or search_text in grade
                or search_text in strand
                or search_text in department
                or search_text in date
                or search_text in self.extract_month_name(date).lower()
            ):
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
            dt = datetime.datetime.strptime(date_str, "%B %d, %Y")
            return dt.strftime("%B")
        except:
            return ""
        
    def print_table_widget(self, table_widget, title, export_to_pdf=False):
        printer = QPrinter(QPrinter.HighResolution)

        if export_to_pdf:
            save_path, _ = QFileDialog.getSaveFileName(
                self, "Export to PDF", "", "PDF Files (*.pdf)"
            )
            if not save_path:
                return  # User canceled
            if not save_path.endswith(".pdf"):
                save_path += ".pdf"
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(save_path)
            self.render_document(table_widget, title, printer)
            QtWidgets.QMessageBox.information(
                self, "Exported", f"PDF exported to:\n{save_path}"
            )
        else:
            preview = QPrintPreviewDialog(printer, self)
            preview.setWindowTitle("Print Preview")
            preview.paintRequested.connect(
                lambda p: self.render_document(table_widget, title, p)
            )
            preview.exec_()

    def render_document(self, table_widget, title, printer, include_all_rows=False):
        document = QTextDocument()
        cursor = QTextCursor(document)

        # Centered title block
        title_format = QtGui.QTextBlockFormat()
        title_format.setAlignment(Qt.AlignCenter)

        title_char_format = QtGui.QTextCharFormat()
        title_char_format.setFontPointSize(16)
        title_char_format.setFontWeight(QtGui.QFont.Bold)

        cursor.insertBlock(title_format, title_char_format)
        cursor.insertText(title, title_char_format)
        cursor.insertBlock()

        cols = table_widget.columnCount()

        table_format = QtGui.QTextTableFormat()
        table_format.setBorder(1)
        table_format.setCellPadding(4)
        table_format.setCellSpacing(0)

        column_widths = [1.0 / cols] * cols
        table_format.setColumnWidthConstraints(
            [
                QtGui.QTextLength(QtGui.QTextLength.PercentageLength, w * 100)
                for w in column_widths
            ]
        )

        # Collect visible rows or all rows
        row_indices = (
            range(table_widget.rowCount())
            if include_all_rows
            else [
                i
                for i in range(table_widget.rowCount())
                if not table_widget.isRowHidden(i)
            ]
        )

        # Insert table with header + visible rows
        table = cursor.insertTable(len(row_indices) + 1, cols, table_format)

        # Headers (bold)
        bold_format = QtGui.QTextCharFormat()
        bold_format.setFontWeight(QtGui.QFont.Bold)

        for col in range(cols):
            header = table_widget.horizontalHeaderItem(col)
            text = header.text() if header else f"Col {col}"
            table.cellAt(0, col).firstCursorPosition().insertText(text, bold_format)

        # Insert content
        for r_idx, row in enumerate(row_indices, start=1):
            for col in range(cols):
                item = table_widget.item(row, col)
                text = item.text() if item else ""
                table.cellAt(r_idx, col).firstCursorPosition().insertText(text)

        document.print_(printer)
        # For dragging the window

    def logout(self):
        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            "Logout Confirmation",
            "Are you sure you want to logout?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
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

        if self.return_to_start:
            self.start_screen = StartScreen()
            self.start_screen.show()
            self.start_screen.fade_in()
        else:
            self.attendance_window = AttendanceApp()
            self.attendance_window.show()

        # For dragging the window

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()


class SuperAdminDashboard(QtWidgets.QMainWindow):
    """Super Admin Dashboard UI (After Successful Login)"""

    def __init__(self, current_admin_id, return_to_start=True):
        super(SuperAdminDashboard, self).__init__()
        self.current_admin_id = current_admin_id
        self.return_to_start = return_to_start
        uic.loadUi(SUPERADMIN_UI_PATH, self)

        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.initUI_btn()
        self.init_page_navigation()
        self.setup_timers()
        self.populate_initial_data()
        self.selected_student_row = None
        self.selected_staff_row = None

        # Center StartScreen on screen
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

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
        self.changeCredentials_btn.clicked.connect(self.open_change_credentials_dialog)
        self.logout_btn.clicked.connect(self.logout)
        self.superAdmin_btn.clicked.connect(self.superAdmin)
        self.updateStudent_btn.clicked.connect(self.update_selected_student)
        self.removeStudent_btn.clicked.connect(self.remove_selected_student)
        self.addStudent_btn.clicked.connect(self.open_add_student_dialog)
        self.addAdmin_btn.clicked.connect(self.open_add_admin_dialog)
        self.addStaff_btn.clicked.connect(self.open_add_staff_dialog)
        self.updateStaff_btn.clicked.connect(self.update_selected_staff)
        self.removeStaff_btn.clicked.connect(self.remove_selected_staff)
        self.viewImages_btn.clicked.connect(self.view_selected_images)
        self.viewStaffImages_btn.clicked.connect(self.view_selected_staff_images)
        self.deleteAttendance_btn.clicked.connect(self.delete_all_attendance_records)


        self.printStaff_btn.clicked.connect(
            lambda: self.print_table_widget(self.staffTable, "Staff List")
        )
        self.exportPDFStaff_btn.clicked.connect(
            lambda: self.print_table_widget(self.staffTable, "Staff List", export_to_pdf=True)
        )


        self.printStudent_btn.clicked.connect(
            lambda: self.print_table_widget(self.studentList_table, "Student List")
        )
        self.exportPDFStudent_btn.clicked.connect(
            lambda: self.print_table_widget(
                self.studentList_table, "Student List", export_to_pdf=True
            )
        )
        self.printAttendance_btn.clicked.connect(
            lambda: self.print_table_widget(
                self.attendanceTableWidget, "Attendance Records"
            )
        )
        self.exportPDFAttendance_btn.clicked.connect(
            lambda: self.print_table_widget(
                self.attendanceTableWidget, "Attendance Records", export_to_pdf=True
            )
        )
        self.changePassword_btn.clicked.connect(self.change_password)
        self.removeAdmin_btn.clicked.connect(self.remove_admin)
        self.searchBar.returnPressed.connect(self.search_attendance)
        self.studentList_searchBar.textChanged.connect(self.search_student_list)
        self.staff_searchBar.textChanged.connect(self.search_staff_list)
        self.studentList_table.itemSelectionChanged.connect(
            self.get_selected_student_row
        )

    def init_page_navigation(self):
        self.attendanceLogs_btn.clicked.connect(
            lambda: self.switch_page(0, self.attendanceLogs_btn)
        )
        self.students_btn.clicked.connect(
            lambda: self.switch_page(1, self.students_btn)
        )
        self.admin_btn.clicked.connect(lambda: self.switch_page(2, self.admin_btn))
        self.staffs_btn.clicked.connect(lambda: self.switch_page(3, self.staffs_btn))

        self.nav_buttons = [
            self.attendanceLogs_btn,
            self.students_btn,
            self.admin_btn,
            self.staffs_btn,
        ]
        self.switch_page(0, self.attendanceLogs_btn)  # default selection

    def switch_page(self, index, active_button):
        self.stackedWidget.setCurrentIndex(index)

        default_style = """
            QPushButton {
                color: #ffffff;
                font: 87 11pt "Segoe UI Black";
                background-color: #5A5958;
                border: 2px solid #ffffff;
            }
            QPushButton:hover {
                background-color: #000000;
                border: 2px solid #ffffff;
            }
        """

        active_style = """
            QPushButton {
                color: #ffffff;
                font: 87 11pt "Segoe UI Black";
                background-color: #5A5958;
                border: 2px solid #000000;
            }
            QPushButton:hover {
                background-color: #000000;
                border: 2px solid #ffffff;
            }
        """

        for btn in self.nav_buttons:
            btn.setStyleSheet(default_style)

        active_button.setStyleSheet(active_style)

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
            self.animation1.setEndValue(141)
            self.animation1.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
            self.animation1.start()

            self.animation2 = QtCore.QPropertyAnimation(self.frame_1, b"maximumHeight")
            self.animation2.setDuration(500)
            self.animation2.setStartValue(51)
            self.animation2.setEndValue(141)
            self.animation2.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
            self.animation2.start()

            self.Down_Menu_Num = 1
        else:
            self.animation1 = QtCore.QPropertyAnimation(self.frame_1, b"maximumHeight")
            self.animation1.setDuration(500)
            self.animation1.setStartValue(141)
            self.animation1.setEndValue(51)
            self.animation1.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
            self.animation1.start()

            self.animation2 = QtCore.QPropertyAnimation(self.frame_1, b"minimumHeight")
            self.animation2.setDuration(500)
            self.animation2.setStartValue(141)
            self.animation2.setEndValue(51)
            self.animation2.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
            self.animation2.start()

            self.Down_Menu_Num = 0

    def Side_Menu_Num_0(self):
        if self.Side_Menu_Num == 0:
            self.animation1 = QtCore.QPropertyAnimation(self.leftMenu, b"maximumWidth")
            self.animation1.setDuration(500)
            self.animation1.setStartValue(0)
            self.animation1.setEndValue(250)
            self.animation1.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
            self.animation1.start()

            self.animation2 = QtCore.QPropertyAnimation(self.leftMenu, b"minimumWidth")
            self.animation2.setDuration(500)
            self.animation2.setStartValue(0)
            self.animation2.setEndValue(250)
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

    def augment_and_save_images(self, image_path, save_folder, person_id, cursor):
        def augment_image(image):
            augmented = []
            img_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            for _ in range(8):
                img_aug = img_pil.copy()
                if random.random() > 0.5:
                    img_aug = ImageOps.mirror(img_aug)
                img_aug = ImageEnhance.Brightness(img_aug).enhance(
                    random.uniform(0.8, 1.2)
                )
                img_aug = ImageEnhance.Contrast(img_aug).enhance(
                    random.uniform(0.8, 1.2)
                )
                img_aug = img_aug.rotate(random.uniform(-10, 10))
                augmented.append(cv2.cvtColor(np.array(img_aug), cv2.COLOR_RGB2BGR))
            return augmented

        def detect_and_crop_face(image_np):
            image_pil = Image.fromarray(cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB))
            mtcnn = MTCNN(
                keep_all=False, device="cuda" if torch.cuda.is_available() else "cpu"
            )
            boxes, probs, _ = mtcnn.detect(image_pil, landmarks=True)

            if boxes is None or probs is None:
                return []

            cropped_faces = []
            for i, (box, prob) in enumerate(zip(boxes, probs)):
                if prob < 0.90:
                    continue

                x1, y1, x2, y2 = [int(v) for v in box]
                w, h = x2 - x1, y2 - y1
                margin = int(min(w, h) * 0.1)
                x1m = max(0, x1 - margin)
                y1m = max(0, y1 - margin)
                x2m = min(image_np.shape[1], x2 + margin)
                y2m = min(image_np.shape[0], y2 + margin)
                cropped_face = image_np[y1m:y2m, x1m:x2m]
                resized_face = cv2.resize(cropped_face, (160, 160))
                cropped_faces.append(resized_face)

            return cropped_faces

        original = cv2.imread(image_path)
        if original is None:
            return

        faces = detect_and_crop_face(original)
        if not faces:
            return

        base = os.path.splitext(os.path.basename(image_path))[0]
        for f_idx, face in enumerate(faces):
            filename = f"{base}_crop{f_idx+1}.jpg"
            save_path = os.path.join(save_folder, filename)
            cv2.imwrite(save_path, face)
            cursor.execute(
                "INSERT INTO FaceImages (person_id, image_path) VALUES (?, ?)",
                (person_id, save_path),
            )

            # Now augment this cropped face
            augmented_faces = augment_image(face)
            for i, aug in enumerate(augmented_faces):
                aug_name = f"{base}_crop{f_idx+1}_aug{i+1}.jpg"
                aug_path = os.path.join(save_folder, aug_name)
                cv2.imwrite(aug_path, aug)
                cursor.execute(
                    "INSERT INTO FaceImages (person_id, image_path) VALUES (?, ?)",
                    (person_id, aug_path),
                )

    def view_selected_images(self):
        if self.selected_student_row is None:
            QMessageBox.warning(self, "No Selection", "Please select a student first.")
            return

        person_id_item = self.studentList_table.item(self.selected_student_row, 0)
        if not person_id_item:
            QMessageBox.critical(self, "Error", "Unable to retrieve student ID.")
            return

        person_id = person_id_item.text()

        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()
        cursor.execute("SELECT image_path FROM FaceImages WHERE person_id = ?", (person_id,))
        images = cursor.fetchall()
        conn.close()

        if not images:
            QMessageBox.information(self, "No Images", "No images found for this person.")
            return

        image_paths = [img[0] for img in images]

        viewer = ImageViewerDialog(image_paths)
        viewer.exec_()

    def view_selected_staff_images(self):
        selected_row = self.staffTable.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "No Selection", "Please select a staff member first.")
            return

        staff_id_item = self.staffTable.item(selected_row, 0)
        if not staff_id_item:
            QMessageBox.critical(self, "Error", "Unable to retrieve staff ID.")
            return

        staff_id = int(staff_id_item.text())

        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()

        # Fetch the corresponding person_id
        cursor.execute("SELECT person_id FROM StaffDetails WHERE staff_id = ?", (staff_id,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            QMessageBox.critical(self, "Error", "Unable to retrieve staff person ID.")
            return

        person_id = result[0]

        cursor.execute("SELECT image_path FROM FaceImages WHERE person_id = ?", (person_id,))
        images = cursor.fetchall()
        conn.close()

        if not images:
            QMessageBox.information(self, "No Images", "No images found for this staff.")
            return

        image_paths = [img[0] for img in images]
        viewer = ImageViewerDialog(image_paths)
        viewer.exec_()

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
        table.setHorizontalHeaderLabels(["ID", "NAME", "GRADE", "STRAND", "GENDER"])
        table.verticalHeader().setVisible(True)

        for row_index, row_data in enumerate(data):
            for col_index, col_data in enumerate(row_data):
                item = QtWidgets.QTableWidgetItem(str(col_data))
                item.setForeground(QtGui.QColor("black"))
                item.setTextAlignment(QtCore.Qt.AlignLeft)
                table.setItem(row_index, col_index, item)

            header_item = QtWidgets.QTableWidgetItem(str(row_index + 1))
            header_item.setTextAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)
            table.setVerticalHeaderItem(row_index, header_item)

        table.verticalHeader().setDefaultSectionSize(30)
        table.verticalHeader().setStyleSheet(""" 
            QHeaderView::section {
                padding-top: 0px;
                margin: 0px;
                font-size: 14px;
                qproperty-alignment: AlignTop | AlignHCenter;
            }
        """)

        # Adjust columns to fit neatly
        table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

        # Set a fixed width for each column
        table.setColumnWidth(0, 10)  # ID
        table.setColumnWidth(1, 270)  # NAME
        table.setColumnWidth(2, 130)  # GRADE
        table.setColumnWidth(3, 160)  # STRAND
        table.setColumnWidth(4, 160)  # Gender

        table.setColumnHidden(0, True)  # Hide the ID column

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
            header_item.setTextAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)
            table.setVerticalHeaderItem(row_index, header_item)

        table.verticalHeader().setDefaultSectionSize(30)
        table.verticalHeader().setStyleSheet(""" 
            QHeaderView::section {
                padding-top: 0px;
                margin: 0px;
                font-size: 14px;
                qproperty-alignment: AlignTop | AlignHCenter;
            }
        """)
        # Set a fixed width for each column
        table.setColumnWidth(0, 80)  # ID
        table.setColumnWidth(1, 270)  # NAME
        table.setColumnWidth(2, 170)  # GENDER
        table.setColumnWidth(3, 180)  # DEPARTMENT

        table.setColumnHidden(0, True)  # Hide the ID column

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
            header_item.setTextAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)
            table.setVerticalHeaderItem(row_index, header_item)

        table.verticalHeader().setDefaultSectionSize(30)
        table.verticalHeader().setStyleSheet(""" 
            QHeaderView::section {
                padding-top: 0px;
                margin: 0px;
                font-size: 14px;
                qproperty-alignment: AlignTop | AlignHCenter;
            }
        """)

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
        cursor.execute(
            "SELECT department_name FROM Department ORDER BY department_name ASC"
        )
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

            if not all(
                [
                    data["first_name"],
                    data["last_name"],
                    data["image_folder"],
                    data["profile_image"],
                ]
            ):
                QMessageBox.warning(
                    self,
                    "Missing Info",
                    "All fields including images must be provided.",
                )
                return

            conn = sqlite3.connect("recognition.db")
            cursor = conn.cursor()

            # 1. Insert person record first with temporary profile path
            cursor.execute(
                """
                INSERT INTO Person (first_name, middle_name, last_name, gender, profile_image_url)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    data["first_name"],
                    data["middle_name"],
                    data["last_name"],
                    data["gender"],
                    "temp",
                ),
            )
            person_id = cursor.lastrowid

            # 2. Get IDs
            cursor.execute(
                "SELECT strand_id FROM Strand WHERE strand_name = ?", (data["strand"],)
            )
            strand_id = cursor.fetchone()[0]

            cursor.execute(
                "SELECT grade_level_id FROM GradeLevel WHERE grade_level = ?",
                (data["grade"],),
            )
            grade_id = cursor.fetchone()[0]

            cursor.execute(
                "INSERT INTO StudentDetails (person_id, strand_id, grade_level_id) VALUES (?, ?, ?)",
                (person_id, strand_id, grade_id),
            )
            conn.commit()

            # 3. Save images
            student_folder = " ".join(
                part
                for part in [data["first_name"], data["middle_name"], data["last_name"]]
                if part.strip()
            )
            face_folder = os.path.join("images/student", student_folder)
            os.makedirs(face_folder, exist_ok=True)

            # Copy profile image
            profile_dst = os.path.join(face_folder, "profile.jpg")
            if not os.path.samefile(
                os.path.dirname(data["profile_image"]), face_folder
            ):
                shutil.copy(data["profile_image"], profile_dst)
            else:
                # Rename if already in same folder
                src = data["profile_image"]
                profile_dst = os.path.join(face_folder, "profile.jpg")
                if src != profile_dst:
                    os.rename(src, profile_dst)

            # ✅ Update correct profile_image_url path
            cursor.execute(
                "UPDATE Person SET profile_image_url = ? WHERE person_id = ?",
                (profile_dst, person_id),
            )

            # Add to FaceImages table
            cursor.execute(
                "INSERT INTO FaceImages (person_id, image_path) VALUES (?, ?)",
                (person_id, profile_dst),
            )

            self.augment_and_save_images(profile_dst, face_folder, person_id, cursor)

            # 4. Copy all other images from folder
            for file in os.listdir(data["image_folder"]):
                src = os.path.join(data["image_folder"], file)
                if os.path.isfile(src):
                    # Don’t re-copy the profile image if it's the same
                    if os.path.samefile(src, data["profile_image"]):
                        continue

                    dst = os.path.join(face_folder, file)
                    shutil.copy(src, dst)
                    cursor.execute(
                        "INSERT INTO FaceImages (person_id, image_path) VALUES (?, ?)",
                        (person_id, dst),
                    )

                    self.augment_and_save_images(dst, face_folder, person_id, cursor)

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
                QMessageBox.warning(
                    self, "Missing Info", "Name and profile image are required."
                )
                return

            conn = sqlite3.connect("recognition.db")
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO Person (first_name, middle_name, last_name, gender, profile_image_url)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    data["first_name"],
                    data["middle_name"],
                    data["last_name"],
                    data["gender"],
                    "temp",
                ),
            )
            person_id = cursor.lastrowid

            cursor.execute(
                "SELECT department_id FROM Department WHERE department_name = ?",
                (data["department"],),
            )
            department_id = cursor.fetchone()[0]

            cursor.execute(
                "INSERT INTO StaffDetails (person_id, department_id) VALUES (?, ?)",
                (person_id, department_id),
            )

            folder_name = " ".join(
                part
                for part in [data["first_name"], data["middle_name"], data["last_name"]]
                if part.strip()
            )
            folder_path = os.path.join("images/staff", folder_name)
            os.makedirs(folder_path, exist_ok=True)

            profile_dst = os.path.join(folder_path, "profile.jpg")
            shutil.copy(data["profile_image"], profile_dst)

            cursor.execute(
                "UPDATE Person SET profile_image_url = ? WHERE person_id = ?",
                (profile_dst, person_id),
            )
            cursor.execute(
                "INSERT INTO FaceImages (person_id, image_path) VALUES (?, ?)",
                (person_id, profile_dst),
            )

            self.augment_and_save_images(profile_dst, folder_path, person_id, cursor)

            if data["image_folder"]:
                for file in os.listdir(data["image_folder"]):
                    src = os.path.join(data["image_folder"], file)
                    if os.path.isfile(src):
                        if os.path.samefile(src, data["profile_image"]):
                            continue
                        dst = os.path.join(folder_path, file)
                        shutil.copy(src, dst)
                        cursor.execute(
                            "INSERT INTO FaceImages (person_id, image_path) VALUES (?, ?)",
                            (person_id, dst),
                        )
                        self.augment_and_save_images(
                            dst, folder_path, person_id, cursor
                        )

            conn.commit()
            conn.close()

            self.populate_staff_table()
            QMessageBox.information(self, "Added", "Staff added successfully.")
            self.generate_embeddings_from_face_images("recognition.db")

    def print_table_widget(self, table_widget, title, export_to_pdf=False):
        printer = QPrinter(QPrinter.HighResolution)

        if export_to_pdf:
            save_path, _ = QFileDialog.getSaveFileName(
                self, "Export to PDF", "", "PDF Files (*.pdf)"
            )
            if not save_path:
                return  # User canceled
            if not save_path.endswith(".pdf"):
                save_path += ".pdf"
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(save_path)
            self.render_document(table_widget, title, printer)
            QtWidgets.QMessageBox.information(
                self, "Exported", f"PDF exported to:\n{save_path}"
            )
        else:
            preview = QPrintPreviewDialog(printer, self)
            preview.setWindowTitle("Print Preview")
            preview.paintRequested.connect(
                lambda p: self.render_document(table_widget, title, p)
            )
            preview.exec_()

    def render_document(self, table_widget, title, printer, include_all_rows=False):
        document = QTextDocument()
        cursor = QTextCursor(document)

        # Centered title block
        title_format = QtGui.QTextBlockFormat()
        title_format.setAlignment(Qt.AlignCenter)

        title_char_format = QtGui.QTextCharFormat()
        title_char_format.setFontPointSize(16)
        title_char_format.setFontWeight(QtGui.QFont.Bold)

        cursor.insertBlock(title_format, title_char_format)
        cursor.insertText(title, title_char_format)
        cursor.insertBlock()

        cols = table_widget.columnCount()

        table_format = QtGui.QTextTableFormat()
        table_format.setBorder(1)
        table_format.setCellPadding(4)
        table_format.setCellSpacing(0)

        column_widths = [1.0 / cols] * cols
        table_format.setColumnWidthConstraints(
            [
                QtGui.QTextLength(QtGui.QTextLength.PercentageLength, w * 100)
                for w in column_widths
            ]
        )

        # Collect visible rows or all rows
        row_indices = (
            range(table_widget.rowCount())
            if include_all_rows
            else [
                i
                for i in range(table_widget.rowCount())
                if not table_widget.isRowHidden(i)
            ]
        )

        # Insert table with header + visible rows
        table = cursor.insertTable(len(row_indices) + 1, cols, table_format)

        # Headers (bold)
        bold_format = QtGui.QTextCharFormat()
        bold_format.setFontWeight(QtGui.QFont.Bold)

        for col in range(cols):
            header = table_widget.horizontalHeaderItem(col)
            text = header.text() if header else f"Col {col}"
            table.cellAt(0, col).firstCursorPosition().insertText(text, bold_format)

        # Insert content
        for r_idx, row in enumerate(row_indices, start=1):
            for col in range(cols):
                item = table_widget.item(row, col)
                text = item.text() if item else ""
                table.cellAt(r_idx, col).firstCursorPosition().insertText(text)

        document.print_(printer)
        # For dragging the window

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def delete_all_attendance_records(self):
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete ALL attendance records? This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect("recognition.db")
                cursor = conn.cursor()
                cursor.execute("DELETE FROM AttendanceRecords")
                conn.commit()
                conn.close()

                self.populate_attendance_data()  # refresh the table view
                QMessageBox.information(self, "Success", "All attendance records deleted successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete records: {e}")

    def print_attendance_records(self):
        self.print_table_widget(self.attendanceTableWidget, "Attendance Records")

    def print_attendance_as_pdf(self):
        self.print_table_widget(
            self.attendanceTableWidget, "Attendance Records", export_to_pdf=True
        )


    def generate_embeddings_from_face_images(self, db_path="recognition.db"):
        embedder = InceptionResnetV1(pretrained="vggface2").eval()

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all image paths from FaceImages (not just unembedded ones)
        cursor.execute("DELETE FROM FaceEmbeddings")  # Clear old ones
        cursor.execute("SELECT person_id, image_path FROM FaceImages")
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
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype("float32") / 255.0
                img = (img - 0.5) / 0.5
                img = np.transpose(img, (2, 0, 1))
                img_tensor = torch.tensor(img).unsqueeze(0).float()

                with torch.no_grad():
                    emb = embedder(img_tensor)[0].numpy()
                emb = emb / np.linalg.norm(emb)

                cursor.execute(
                    """
                    INSERT INTO FaceEmbeddings (person_id, embedding_vector)
                    VALUES (?, ?)
                """,
                    (person_id, str(emb.tolist())),
                )
                inserted += 1

            except Exception as e:
                print(f"❌ Error processing {image_path}: {e}")

        conn.commit()
        conn.close()
        print(f"✅ {inserted} embeddings regenerated.")

    def get_selected_student_row(self):
        selected_items = self.studentList_table.selectedItems()
        if selected_items:
            self.selected_student_row = selected_items[0].row()
        else:
            self.selected_student_row = None

    def update_selected_student(self):
        if self.selected_student_row is None:
            QMessageBox.warning(
                self, "No Selection", "Please select a student to update."
            )
            return
        if not verify_superadmin_password(
            self
        ):  # to prompt the superadmin password before performing sensitive actions
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

        dialog = UpdateStudentDialog(
            first_name, middle_name, last_name, grade, strand, gender
        )
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            data = dialog.get_updated_data()

            # Check if there are any actual changes
            if (
                data["first_name"] == first_name
                and data["middle_name"] == middle_name
                and data["last_name"] == last_name
                and data["gender"] == gender
                and data["grade"] == grade
                and data["strand"] == strand
            ):
                QMessageBox.information(self, "No Changes", "No update was made.")
                return

            # --- DATABASE UPDATE ---
            conn = sqlite3.connect("recognition.db")
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE Person SET
                    first_name = ?,
                    middle_name = ?,
                    last_name = ?,
                    gender = ?
                WHERE person_id = ?
            """,
                (
                    data["first_name"],
                    data["middle_name"],
                    data["last_name"],
                    data["gender"],
                    person_id,
                ),
            )

            cursor.execute(
                "SELECT grade_level_id FROM GradeLevel WHERE grade_level = ?",
                (data["grade"],),
            )
            grade_row = cursor.fetchone()
            grade_id = grade_row[0] if grade_row else None

            cursor.execute(
                "SELECT strand_id FROM Strand WHERE strand_name = ?", (data["strand"],)
            )
            strand_row = cursor.fetchone()
            strand_id = strand_row[0] if strand_row else None

            cursor.execute(
                """
                UPDATE StudentDetails SET
                    grade_level_id = ?,
                    strand_id = ?
                WHERE person_id = ?
            """,
                (grade_id, strand_id, person_id),
            )

            conn.commit()
            conn.close()

            QMessageBox.information(
                self, "Updated", "Student information updated successfully."
            )
            self.populate_studentList_data()

    def update_selected_staff(self):
        selected_row = self.staffTable.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "No Selection", "Select a staff to update.")
            return
        if not verify_superadmin_password(self):
            return

        staff_id_item = self.staffTable.item(selected_row, 0)
        full_name = self.staffTable.item(selected_row, 1).text()
        gender = self.staffTable.item(selected_row, 2).text()
        department = self.staffTable.item(selected_row, 3).text()

        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT person_id FROM StaffDetails WHERE staff_id = ?",
            (staff_id_item.text(),),
        )
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
                updated["first_name"] == first
                and updated["middle_name"] == middle
                and updated["last_name"] == last
                and updated["gender"] == gender
                and updated["department"] == department
            ):
                conn.close()
                QMessageBox.information(self, "No Changes", "No update was made.")
                return

            # Update
            cursor.execute(
                """
                UPDATE Person SET first_name=?, middle_name=?, last_name=?, gender=? WHERE person_id=?
            """,
                (
                    updated["first_name"],
                    updated["middle_name"],
                    updated["last_name"],
                    updated["gender"],
                    person_id,
                ),
            )

            cursor.execute(
                "SELECT department_id FROM Department WHERE department_name = ?",
                (updated["department"],),
            )
            department_id = cursor.fetchone()[0]

            cursor.execute(
                "UPDATE StaffDetails SET department_id = ? WHERE person_id = ?",
                (department_id, person_id),
            )
            conn.commit()
            conn.close()

            self.populate_staff_table()
            QMessageBox.information(self, "Updated", "Staff info updated.")

    def remove_selected_student(self):
        if self.selected_student_row is None:
            QMessageBox.warning(self, "No Selection", "Please select a student first.")
            return
        if not verify_superadmin_password(self):
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
            QMessageBox.Yes | QMessageBox.No,
        )

        if confirm != QMessageBox.Yes:
            return

        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()

        # Backup name, grade, and strand to AttendanceRecords
        cursor.execute("""
            SELECT 
                p.first_name || ' ' || IFNULL(p.middle_name, '') || ' ' || p.last_name,
                g.grade_level,
                s.strand_name
            FROM Person p
            LEFT JOIN StudentDetails sd ON sd.person_id = p.person_id
            LEFT JOIN GradeLevel g ON g.grade_level_id = sd.grade_level_id
            LEFT JOIN Strand s ON s.strand_id = sd.strand_id
            WHERE p.person_id = ?
        """, (person_id,))
        result = cursor.fetchone()
        if result:
            full_name_backup, grade_backup, strand_backup = result
            cursor.execute("""
                UPDATE AttendanceRecords
                SET full_name = ?, grade_level = ?, strand_name = ?
                WHERE person_id = ?
            """, (full_name_backup, grade_backup, strand_backup, person_id))

        # Delete from FaceEmbeddings
        cursor.execute("DELETE FROM FaceEmbeddings WHERE person_id = ?", (person_id,))

        # Get and delete FaceImages
        cursor.execute("SELECT image_path FROM FaceImages WHERE person_id = ?", (person_id,))
        image_paths = [row[0] for row in cursor.fetchall()]
        cursor.execute("DELETE FROM FaceImages WHERE person_id = ?", (person_id,))

        # Delete StudentDetails
        cursor.execute("DELETE FROM StudentDetails WHERE person_id = ?", (person_id,))

        # ✅ Now safe to delete Person because attendance data is backed up
        cursor.execute("DELETE FROM Person WHERE person_id = ?", (person_id,))


        conn.commit()
        conn.close()

        # Delete folder if it exists
        if image_paths:
            folder = os.path.dirname(image_paths[0])
            if os.path.exists(folder):
                shutil.rmtree(folder, ignore_errors=True)

        QMessageBox.information(self, "Removed", f"'{full_name}' removed. Attendance logs kept.")
        self.populate_studentList_data()
        self.selected_student_row = None


    def remove_selected_staff(self):
        selected_row = self.staffTable.currentRow()
        if selected_row < 0:
            QMessageBox.warning(
                self, "No Selection", "Please select a staff member to remove."
            )
            return
        if not verify_superadmin_password(self):
            return

        staff_id = self.staffTable.item(selected_row, 0).text()
        full_name = self.staffTable.item(selected_row, 1).text()

        confirm = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Are you sure you want to delete '{full_name}'?\nThis will delete all face data and keep attendance logs.",
            QMessageBox.Yes | QMessageBox.No,
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

        # 🟩 Backup full name and department into AttendanceRecords
        cursor.execute("""
            SELECT 
                p.first_name, p.middle_name, p.last_name,
                d.department_name
            FROM Person p
            LEFT JOIN StaffDetails sd ON sd.person_id = p.person_id
            LEFT JOIN Department d ON d.department_id = sd.department_id
            WHERE p.person_id = ?
        """, (person_id,))
        result = cursor.fetchone()

        if result:
            first_name, middle_name, last_name, department = result
            full_name_final = f"{first_name} {middle_name or ''} {last_name}".strip()

            cursor.execute("""
                UPDATE AttendanceRecords
                SET 
                    full_name = ?,
                    department_name = ?
                WHERE person_id = ?
            """, (full_name_final, department, person_id))

        # 🧹 Clean up
        cursor.execute("DELETE FROM FaceEmbeddings WHERE person_id = ?", (person_id,))
        cursor.execute("SELECT image_path FROM FaceImages WHERE person_id = ?", (person_id,))
        image_paths = [row[0] for row in cursor.fetchall()]
        cursor.execute("DELETE FROM FaceImages WHERE person_id = ?", (person_id,))
        cursor.execute("DELETE FROM StaffDetails WHERE person_id = ?", (person_id,))
        cursor.execute("DELETE FROM Person WHERE person_id = ?", (person_id,))

        conn.commit()
        conn.close()

        # Delete folder
        if image_paths:
            folder = os.path.dirname(image_paths[0])
            if os.path.exists(folder):
                shutil.rmtree(folder, ignore_errors=True)

        self.populate_staff_table()
        QMessageBox.information(self, "Removed", f"'{full_name}' removed.")

    def populate_attendance_data(self):
        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                COALESCE(a.full_name, p.first_name || ' ' || p.middle_name || ' ' || p.last_name) AS full_name,
                COALESCE(a.grade_level, g.grade_level) AS grade,
                COALESCE(a.strand_name, s.strand_name) AS strand,
                COALESCE(a.department_name, d.department_name) AS department,
                a.date_in,
                a.time_in
            FROM AttendanceRecords a
            LEFT JOIN Person p ON a.person_id = p.person_id
            LEFT JOIN StudentDetails sd ON sd.person_id = a.person_id
            LEFT JOIN GradeLevel g ON g.grade_level_id = sd.grade_level_id
            LEFT JOIN Strand s ON s.strand_id = sd.strand_id
            LEFT JOIN StaffDetails st ON st.person_id = a.person_id
            LEFT JOIN Department d ON d.department_id = st.department_id
            ORDER BY a.attendance_id DESC
            """
        )
        data = cursor.fetchall()
        conn.close()

        self.attendance_data = data

        table = self.attendanceTableWidget
        table.setRowCount(len(data))
        table.setHorizontalHeaderLabels(["NAME", "GRADE", "STRAND", "DEPARTMENT", "DATE", "TIME"])
        table.verticalHeader().setVisible(True)

        for row_index, row_data in enumerate(data):
            for col_index, col_data in enumerate(row_data):
                text = "" if col_data is None else str(col_data)
                item = QtWidgets.QTableWidgetItem(text)
                item.setForeground(QtGui.QColor("black"))
                item.setTextAlignment(QtCore.Qt.AlignLeft)
                table.setItem(row_index, col_index, item)

            header_item = QtWidgets.QTableWidgetItem(str(row_index + 1))
            header_item.setTextAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)
            table.setVerticalHeaderItem(row_index, header_item)

        table.verticalHeader().setDefaultSectionSize(50)
        table.verticalHeader().setStyleSheet("""
            QHeaderView::section {
                padding-top: 0px;
                margin: 0px;
                font-size: 14px;
                qproperty-alignment: AlignTop | AlignHCenter;
            }
        """)
        table.setColumnWidth(0, 300)
        table.setColumnWidth(1, 150)
        table.setColumnWidth(2, 160)
        table.setColumnWidth(3, 260)
        table.setColumnWidth(4, 180)
        table.setColumnWidth(5, 130)
        table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

    def refresh_table(self, data):
        table = self.attendanceTableWidget
        table.setRowCount(0)
        table.setRowCount(len(data))
        table.setHorizontalHeaderLabels(
            ["NAME", "GRADE", "STRAND", "DEPARTMENT", "DATE", "TIME"]
        )

        for row_index, row_data in enumerate(data):
            for col_index, col_data in enumerate(row_data):
                text = "" if col_data is None else str(col_data)
                item = QtWidgets.QTableWidgetItem(text)
                item.setForeground(QtGui.QColor("black"))
                item.setTextAlignment(QtCore.Qt.AlignLeft)
                table.setItem(row_index, col_index, item)

            header_item = QtWidgets.QTableWidgetItem(str(row_index + 1))
            header_item.setTextAlignment(QtCore.Qt.AlignCenter)
            table.setVerticalHeaderItem(row_index, header_item)

        # Adjust column widths
        table.setColumnWidth(0, 300)  # NAME
        table.setColumnWidth(1, 150)  # GRADE
        table.setColumnWidth(2, 160)  # STRAND
        table.setColumnWidth(3, 260)  # DEPARTMENT
        table.setColumnWidth(4, 180)  # DATE
        table.setColumnWidth(5, 130)  # TIME

        table.verticalHeader().setDefaultSectionSize(50)
        table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

    def search_attendance(self):
        search_text = self.searchBar.text().strip().lower()
        filtered_data = []

        for row in self.attendance_data:
            name = str(row[0]).lower() if row[0] else ""
            grade = str(row[1]).lower() if row[1] else ""
            strand = str(row[2]).lower() if row[2] else ""
            department = str(row[3]).lower() if row[3] else ""
            date = str(row[4]).lower() if row[4] else ""

            if (
                search_text in name
                or search_text in grade
                or search_text in strand
                or search_text in department
                or search_text in date
                or search_text in self.extract_month_name(date).lower()
            ):
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
            dt = datetime.datetime.strptime(date_str, "%B %d, %Y")
            return dt.strftime("%B")
        except:
            return ""

    def populate_admin_table(self):
        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT a.admin_id, a.username, a.admin_role, COALESCE(c.username, 'Super Admin') AS created_by
            FROM Admin a
            LEFT JOIN Admin c ON a.created_by_admin_id = c.admin_id
            WHERE a.admin_role = 'admin'
        """
        )
        rows = cursor.fetchall()
        conn.close()

        table = self.adminTable
        table.clearContents()  # 🧽 Clear any old content
        table.setRowCount(0)
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Username", "Password", "Role", "Created By"])
        table.verticalHeader().setVisible(True)
        self.admin_ids = []

        table.setRowCount(len(rows))
        table.setVerticalHeaderLabels([str(i + 1) for i in range(len(rows))])

        for row_index, (admin_id, username, role, created_by) in enumerate(rows):
            self.admin_ids.append(admin_id)

            values = [username, "••••••", role, created_by]
            for col_index, value in enumerate(values):
                item = QtWidgets.QTableWidgetItem(value)
                item.setTextAlignment(QtCore.Qt.AlignLeft)
                item.setForeground(QtGui.QColor("black"))
                table.setItem(row_index, col_index, item)
            header_item = QtWidgets.QTableWidgetItem(str(row_index + 1))
            header_item.setTextAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)
            table.setVerticalHeaderItem(row_index, header_item)

        table.verticalHeader().setDefaultSectionSize(30)
        table.verticalHeader().setStyleSheet(""" 
            QHeaderView::section {
                padding-top: 0px;
                margin: 0px;
                font-size: 14px;
                qproperty-alignment: AlignTop | AlignHCenter;
            }
        """)
        # Consistent Column Widths (adjust these as needed)
        table.setColumnWidth(0, 200)  # USERNAME
        table.setColumnWidth(1, 155)  # PASSWORD
        table.setColumnWidth(2, 145)  # ROLE
        table.setColumnWidth(3, 130)  # CREATED BY

        # Styling
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
            self,
            "Change Password",
            f"Enter new password for '{username}':",
            QtWidgets.QLineEdit.Password,
        )
        if not ok or not new_pass.strip():
            return

        admin_id = self.admin_ids[selected_row]
        password_hash = hashlib.sha256(new_pass.encode()).hexdigest()

        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE Admin SET password_hash = ? WHERE admin_id = ?",
            (password_hash, admin_id),
        )
        conn.commit()
        conn.close()

        QMessageBox.information(
            self, "Success", f"Password for '{username}' changed successfully."
        )

    def remove_admin(self):
        selected_row = self.adminTable.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Warning", "Please select an admin to remove.")
            return
        if not verify_superadmin_password(self):
            return

        username_item = self.adminTable.item(selected_row, 0)
        username = username_item.text() if username_item else "this admin"

        confirm = QMessageBox.question(
            self,
            "Confirm",
            f"Are you sure you want to delete '{username}'?",
            QMessageBox.Yes | QMessageBox.No,
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
        QMessageBox.information(
            self, "Removed", f"Admin '{username}' removed successfully."
        )

    def open_change_credentials_dialog(self):
        dialog = ChangeCredentialsDialog(self, current_admin_id=self.current_admin_id)
        dialog.exec_()

    def logout(self):
        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            "Logout Confirmation",
            "Are you sure you want to logout?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
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

        if self.return_to_start:
            self.start_screen = StartScreen()
            self.start_screen.show()
            self.start_screen.fade_in()
        else:
            self.attendance_window = AttendanceApp()
            self.attendance_window.show()

    def superAdmin(self):
        login_dialog = LoginDialog(super_admin_mode=True)
        if login_dialog.exec_() == QtWidgets.QDialog.Accepted:
            role = getattr(login_dialog, "logged_in_role", None)
            if role == "super_admin":
                self.new_window = SuperAdminDashboard(
                    current_admin_id=login_dialog.admin_id
                )
                self.new_window.show()
            elif role == "admin":
                self.new_window = AdminDashboard()
                self.new_window.show()
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Login Failed", "Unknown role or login failure."
                )
            self.close()


class ChangeCredentialsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, current_admin_id=None):
        super(ChangeCredentialsDialog, self).__init__(parent)
        uic.loadUi(CHANGE_CREDENTIAL_UI_PATH, self)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        self.current_admin_id = current_admin_id

        self.load_username()

        self.buttonBox.accepted.connect(self.change_credentials)
        self.buttonBox.rejected.connect(self.reject)

        # Center StartScreen on screen
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def load_username(self):
        """Pre-fill the username field with the currently logged-in admin's username."""
        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT username FROM Admin WHERE admin_id = ?", (self.current_admin_id,)
        )
        result = cursor.fetchone()
        conn.close()

        if result:
            self.usernameLineEdit.setText(result[0])

    def change_credentials(self):
        username = self.usernameLineEdit.text().strip()
        old_pass = self.oldPasswordLineEdit.text()
        new_pass = self.newPasswordLineEdit.text()
        confirm_pass = self.confirmPasswordLineEdit.text()

        if not all([username, old_pass, new_pass, confirm_pass]):
            QMessageBox.warning(self, "Missing Fields", "All fields must be filled.")
            return

        if new_pass != confirm_pass:
            QMessageBox.warning(self, "Mismatch", "New passwords do not match.")
            return

        hashed_old = hashlib.sha256(old_pass.encode()).hexdigest()
        hashed_new = hashlib.sha256(new_pass.encode()).hexdigest()

        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()

        # Get current stored data
        cursor.execute(
            "SELECT username, password_hash FROM Admin WHERE admin_id = ?",
            (self.current_admin_id,),
        )
        current_data = cursor.fetchone()

        if not current_data:
            QMessageBox.critical(self, "Error", "Admin record not found.")
            conn.close()
            return

        current_username, current_password_hash = current_data

        if username != current_username:
            # Check if new username already exists
            cursor.execute(
                "SELECT 1 FROM Admin WHERE username = ? AND admin_id != ?",
                (username, self.current_admin_id),
            )
            if cursor.fetchone():
                QMessageBox.warning(
                    self,
                    "Username Taken",
                    "This username is already in use by another admin.",
                )
                conn.close()
                return

        if current_password_hash != hashed_old:
            QMessageBox.critical(
                self, "Incorrect Password", "The old password is incorrect."
            )
            conn.close()
            return

        if username == current_username and hashed_new == current_password_hash:
            QMessageBox.information(
                self, "No Changes", "No changes were made to your credentials."
            )
            conn.close()
            return

        # ✅ Update username and/or password
        cursor.execute(
            """
            UPDATE Admin SET username = ?, password_hash = ?
            WHERE admin_id = ?
        """,
            (username, hashed_new, self.current_admin_id),
        )
        conn.commit()
        conn.close()

        QMessageBox.information(self, "Success", "Credentials successfully updated.")
        self.accept()


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

        # Center StartScreen on screen
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def select_image_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Folder with Student Images"
        )
        if folder:
            self.image_folder = folder
            self.imagesUpload_btn.setText("Selected")

    def select_profile_image(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Select Profile Image", "", "Images (*.png *.jpg *.jpeg)"
        )
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
            "profile_image": self.profile_image_path,
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

        # Center StartScreen on screen
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def select_image_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Folder with Staff Images"
        )
        if folder:
            self.image_folder = folder
            self.imagesUpload_btn.setText("Selected")

    def select_profile_image(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Select Profile Image", "", "Images (*.png *.jpg *.jpeg)"
        )
        if file:
            self.profile_image_path = file
            self.profileImageUpload_btn.setText("Selected")

    def load_comboboxes(self):
        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT department_name FROM Department ORDER BY department_name"
        )
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
            "profile_image": self.profile_image_path,
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
            "gender": gender.strip(),
        }

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        # Center StartScreen on screen
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def get_updated_data(self):
        return {
            "first_name": self.firstNameLineEdit.text().strip(),
            "middle_name": self.middleNameLineEdit.text().strip(),
            "last_name": self.lastNameLineEdit.text().strip(),
            "grade": self.gradeComboBox.currentText(),
            "strand": self.strandComboBox.currentText(),
            "gender": self.genderComboBox.currentText(),
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

        # Center StartScreen on screen
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def load_departments(self):
        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT department_name FROM Department ORDER BY department_name"
        )
        self.departmentComboBox.addItems([row[0] for row in cursor.fetchall()])
        conn.close()

    def get_updated_data(self):
        return {
            "first_name": self.firstNameLineEdit.text().strip(),
            "middle_name": self.middleNameLineEdit.text().strip(),
            "last_name": self.lastNameLineEdit.text().strip(),
            "gender": self.genderComboBox.currentText(),
            "department": self.departmentComboBox.currentText(),
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

        # Center StartScreen on screen
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

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
            QMessageBox.warning(
                self, "Weak Password", "Password must be at least 5 characters."
            )
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

        cursor.execute(
            """
            INSERT INTO Admin (username, password_hash, admin_role, created_by_admin_id)
            VALUES (?, ?, ?, ?)
        """,
            (username, password_hash, role, self.creator_admin_id),
        )

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

        self.scan_face_label = self.findChild(QtWidgets.QLabel, "scanFace")
        self.cancel_btn = self.findChild(QtWidgets.QPushButton, "cancelButton")
        self.gradeComboBox = self.findChild(QtWidgets.QComboBox, "comboBox_yearLevel")
        self.strandComboBox = self.findChild(QtWidgets.QComboBox, "comboBox_strand")
        self.departmentComboBox = self.findChild(
            QtWidgets.QComboBox, "comboBox_department"
        )
        self.genderComboBox = self.findChild(QtWidgets.QComboBox, "comboBox_gender")

        self.cancel_btn.clicked.connect(self.close)

        # Center StartScreen on screen
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        try:
            conn = sqlite3.connect("recognition.db")
            cursor = conn.cursor()
            cursor.execute("SELECT grade_level FROM GradeLevel")
            self.gradeComboBox.addItems([str(row[0]) for row in cursor.fetchall()])
            cursor.execute("SELECT strand_name FROM Strand")
            self.strandComboBox.addItems([str(row[0]) for row in cursor.fetchall()])
            cursor.execute("SELECT department_name FROM Department")
            self.departmentComboBox.addItems([str(row[0]) for row in cursor.fetchall()])
            self.genderComboBox.addItems(["Select Gender", "Male", "Female", "Other"])
            conn.close()
        except Exception as e:
            print("Error loading dropdowns:", e)

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

       # ✅ Set the correct MTCNN weights directory (for pnet.pt, rnet.pt, onet.pt)
        if getattr(sys, 'frozen', False):
            mtcnn_path = os.path.join(sys._MEIPASS, 'models')  # points to the bundled folder
        else:
            mtcnn_path = os.path.join('models')  # works in development

        # ✅ Initialize MTCNN with explicit weights path
        self.detector = MTCNN(
            keep_all=True,
            device=self.device,
            thresholds=[0.6, 0.7, 0.7],
            margin=14,
            min_face_size=20,
            post_process=True,
            select_largest=False,
            selection_method='probability',
        )

        # Set custom model path if using PyInstaller
        if getattr(sys, 'frozen', False):
            model_path = os.path.join(sys._MEIPASS, 'models', '20180402-114759-vggface2.pt')
        else:
            model_path = os.path.join('models', '20180402-114759-vggface2.pt')

        # Load FaceNet with stripped logits
        self.embedder = InceptionResnetV1(classify=False).eval()
        state_dict = torch.load(model_path, map_location=self.device)
        state_dict = {k: v for k, v in state_dict.items() if not k.startswith('logits.')}
        self.embedder.load_state_dict(state_dict)

        self.camera = cv2.VideoCapture(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

        if frame is not None and frame.size > 0:
            self.display_frame(frame)

        self.radio_student = self.findChild(
            QtWidgets.QRadioButton, "radiobuttonStudent"
        )
        self.radio_staff = self.findChild(QtWidgets.QRadioButton, "radiobuttonStaff")
        self.register_btn = self.findChild(QtWidgets.QPushButton, "registerButton")

        if self.register_btn:
            self.register_btn.clicked.connect(self.register_person)
        if self.radio_student:
            self.radio_student.toggled.connect(self.toggle_role_fields)
        if self.radio_staff:
            self.radio_staff.toggled.connect(self.toggle_role_fields)

        self.gradeComboBox.hide()
        self.strandComboBox.hide()
        self.departmentComboBox.hide()

    def toggle_role_fields(self):
        if self.radio_student.isChecked():
            self.gradeComboBox.show()
            self.strandComboBox.show()
            self.departmentComboBox.hide()
        elif self.radio_staff.isChecked():
            self.gradeComboBox.hide()
            self.strandComboBox.hide()
            self.departmentComboBox.show()

    def update_frame(self):
        ret, frame = self.camera.read()
        if not ret:
            return
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_pil = Image.fromarray(rgb_frame)
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
            self.scan_face_label.width(),
            self.scan_face_label.height(),
            QtCore.Qt.KeepAspectRatio,
        )
        self.scan_face_label.setPixmap(pixmap)

    def register_person(self):
        first_name = (
            self.findChild(QtWidgets.QLineEdit, "firstNameInput").text().strip()
        )
        middle_name = (
            self.findChild(QtWidgets.QLineEdit, "middleNameInput").text().strip()
        )
        last_name = self.findChild(QtWidgets.QLineEdit, "lastNameInput").text().strip()
        gender = self.genderComboBox.currentText()

        if self.radio_student.isChecked():
            role = "Student"
            strand = self.strandComboBox.currentText()
            grade = self.gradeComboBox.currentText()
            folder_base = "images/student"
        else:
            role = "Staff"
            department = self.departmentComboBox.currentText()
            folder_base = "images/staff"

        if not all([first_name, last_name]):
            QtWidgets.QMessageBox.warning(
                self, "Input Error", "First and Last name are required!"
            )
            return

        ret, frame = self.camera.read()
        if not ret:
            QtWidgets.QMessageBox.critical(
                self, "Camera Error", "Failed to capture image."
            )
            return

        faces_info = self.detect_and_crop_face(frame)
        if not faces_info:
            QtWidgets.QMessageBox.warning(
                self, "Face Not Detected", "No face detected."
            )
            return

        face_img, _ = faces_info[0]

        folder_name = " ".join([first_name, middle_name, last_name]).strip()
        folder_path = os.path.join(folder_base, folder_name)
        os.makedirs(folder_path, exist_ok=True)

        profile_path = os.path.join(folder_path, "profile.jpg")
        cv2.imwrite(profile_path, face_img)

        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO Person (first_name, middle_name, last_name, gender, profile_image_url, role)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (first_name, middle_name, last_name, gender, profile_path, role),
        )
        person_id = cursor.lastrowid

        if role == "Student":
            cursor.execute(
                """
                INSERT INTO StudentDetails (person_id, grade_level_id, strand_id)
                VALUES (
                    ?, 
                    (SELECT grade_level_id FROM GradeLevel WHERE grade_level = ?),
                    (SELECT strand_id FROM Strand WHERE strand_name = ?)
                )
            """,
                (person_id, grade, strand),
            )
        else:
            cursor.execute(
                """
                INSERT INTO StaffDetails (person_id, department_id)
                VALUES (
                    ?, 
                    (SELECT department_id FROM Department WHERE department_name = ?)
                )
            """,
                (person_id, department),
            )

        cursor.execute(
            "INSERT INTO FaceImages (person_id, image_path) VALUES (?, ?)",
            (person_id, profile_path),
        )

        # Augment profile + save all
        self.augment_and_save(face_img, folder_path, person_id, cursor)

        conn.commit()
        conn.close()

        # Regenerate embeddings for the new face
        embedder = InceptionResnetV1(pretrained="vggface2").eval()

        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()

        cursor.execute("DELETE FROM FaceEmbeddings WHERE person_id = ?", (person_id,))
        cursor.execute(
            "SELECT image_path FROM FaceImages WHERE person_id = ?", (person_id,)
        )
        images = cursor.fetchall()

        for (img_path,) in images:
            if not os.path.exists(img_path):
                continue
            img = cv2.imread(img_path)
            if img is None:
                continue
            try:
                img = cv2.resize(img, (160, 160))
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype("float32") / 255.0
                img = (img - 0.5) / 0.5
                img = np.transpose(img, (2, 0, 1))
                img_tensor = torch.tensor(img).unsqueeze(0).float()

                with torch.no_grad():
                    emb = embedder(img_tensor)[0].numpy()
                emb = emb / np.linalg.norm(emb)

                cursor.execute(
                    """
                    INSERT INTO FaceEmbeddings (person_id, embedding_vector)
                    VALUES (?, ?)
                """,
                    (person_id, str(emb.tolist())),
                )
            except Exception as e:
                print(f"Embedding failed for {img_path}: {e}")

        conn.commit()
        conn.close()

        QtWidgets.QMessageBox.information(
            self, "Success", f"{first_name} {last_name} registered successfully."
        )
        self.accept()

    def augment_and_save(self, base_image, folder_path, person_id, cursor):
        def augment(img):
            augmented = []
            img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            for i in range(9):
                aug = img_pil.copy()
                if random.random() > 0.5:
                    aug = ImageOps.mirror(aug)
                aug = ImageEnhance.Brightness(aug).enhance(random.uniform(0.8, 1.2))
                aug = ImageEnhance.Contrast(aug).enhance(random.uniform(0.8, 1.2))
                aug = aug.rotate(random.uniform(-10, 10))
                aug_cv = cv2.cvtColor(np.array(aug), cv2.COLOR_RGB2BGR)
                augmented.append(aug_cv)
            return augmented

        augmented_faces = augment(base_image)
        for i, aug_img in enumerate(augmented_faces):
            filename = os.path.join(folder_path, f"augmented_{i+1}.jpg")
            cv2.imwrite(filename, aug_img)
            cursor.execute(
                "INSERT INTO FaceImages (person_id, image_path) VALUES (?, ?)",
                (person_id, filename),
            )

    def detect_and_crop_face(self, image_np):
        image_pil = Image.fromarray(cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB))
        boxes, probs, landmarks = self.detector.detect(image_pil, landmarks=True)

        if boxes is None or probs is None:
            return None

        IMG_SIZE = 160
        MARGIN = 0.2
        faces_info = []

        for i, (box, prob, landmark) in enumerate(zip(boxes, probs, landmarks)):
            if prob < 0.90:
                continue

            x1, y1, x2, y2 = [int(v) for v in box]
            w, h = x2 - x1, y2 - y1

            margin = int(min(w, h) * MARGIN)
            x1m = max(0, x1 - margin)
            y1m = max(0, y1 - margin)
            x2m = min(image_np.shape[1], x2 + margin)
            y2m = min(image_np.shape[0], y2 + margin)

            cropped_face = image_np[y1m:y2m, x1m:x2m]
            resized_face = cv2.resize(cropped_face, (IMG_SIZE, IMG_SIZE))

            faces_info.append((resized_face, (x1, y1, x2, y2)))

        return faces_info

    def preprocess_image(self, img):
        IMG_SIZE = 160
        img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img.astype("float32") / 255.0
        img = (img - 0.5) / 0.5
        img = np.transpose(img, (2, 0, 1))
        return img

    def closeEvent(self, event):
        try:
            if hasattr(self, "timer") and self.timer.isActive():
                self.timer.stop()
            if hasattr(self, "camera") and self.camera.isOpened():
                self.camera.release()
        except Exception as e:
            print("Error releasing camera in UnrecognizeModule:", e)
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            self.setCursor(QtCore.Qt.OpenHandCursor)
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton and hasattr(self, "drag_position"):
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.setCursor(QtCore.Qt.ArrowCursor)


class AttendanceApp(QtWidgets.QMainWindow):
    """Main Attendance System UI"""

    def __init__(self):
        super(AttendanceApp, self).__init__()

        RECOGNITION_THRESHOLD = 0.7
        DETECTION_THRESHOLD = 0.95

        # Load the Main UI
        uic.loadUi(MAIN_UI_PATH, self)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)

        self.Down_Menu_Num = 0

        self.toolMenu_btn.clicked.connect(lambda: self.Down_Menu_Num_0())
        self.logout_btn.clicked.connect(self.logout)

        # Set up webcam feed
        self.camera = cv2.VideoCapture(0)  # Open default webcam
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # Update every 30ms

        # Initialize MTCNN face detector using the device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # ✅ Set the correct MTCNN weights directory (for pnet.pt, rnet.pt, onet.pt)
        if getattr(sys, 'frozen', False):
            mtcnn_path = os.path.join(sys._MEIPASS, 'models')  # points to the bundled folder
        else:
            mtcnn_path = os.path.join('models')  # works in development

        # ✅ Initialize MTCNN with explicit weights path
        self.detector = MTCNN(
            keep_all=True,
            device=self.device,
            thresholds=[0.6, 0.7, 0.7],
            margin=14,
            min_face_size=20,
            post_process=True,
            select_largest=False,
            selection_method='probability',
        )

        # Set custom model path if using PyInstaller
        if getattr(sys, 'frozen', False):
            model_path = os.path.join(sys._MEIPASS, 'models', '20180402-114759-vggface2.pt')
        else:
            model_path = os.path.join('models', '20180402-114759-vggface2.pt')

        # Load FaceNet with stripped logits
        self.embedder = InceptionResnetV1(classify=False).eval()
        state_dict = torch.load(model_path, map_location=self.device)
        state_dict = {k: v for k, v in state_dict.items() if not k.startswith('logits.')}
        self.embedder.load_state_dict(state_dict)

        self.generate_embeddings_from_face_images("recognition.db")
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

        # Center StartScreen on screen
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT a.person_id, a.date_in, a.time_in
            FROM AttendanceRecords a
            ORDER BY a.attendance_id DESC
            LIMIT 1
        """
        )
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
                distances = [
                    np.linalg.norm(embedding - known) for known in self.known_embeddings
                ]
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
                        cv2.putText(
                            frame,
                            full_name,
                            (x1, y1 - 30),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (0, 255, 0),
                            2,
                        )
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
                        cv2.putText(
                            frame,
                            label,
                            (text_x + 2, text_y + 2),
                            font,
                            font_scale,
                            (0, 0, 0),
                            thickness + 2,
                            cv2.LINE_AA,
                        )
                        cv2.putText(
                            frame,
                            label,
                            (text_x, text_y),
                            font,
                            font_scale,
                            (0, 0, 255),
                            thickness,
                            cv2.LINE_AA,
                        )

                        if not self.unrecognized_detected:
                            self.unrecognized_detected = True
                            self.unrecognized_timer.start()

        # Display frame in UI
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channel = frame_rgb.shape
        bytes_per_line = 3 * width
        q_img = QImage(
            frame_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888
        )
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

            self.known_embeddings, self.known_ids = self.load_embeddings_from_db()
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
        cursor.execute(
            "SELECT first_name || ' ' || middle_name || ' ' || last_name FROM Person WHERE person_id = ?",
            (person_id,),
        )
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else "Unknown"

    def populate_attendance_data(self):
        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COALESCE(a.full_name, p.first_name || ' ' || p.middle_name || ' ' || p.last_name) AS full_name,
                COALESCE(a.grade_level, g.grade_level, '') AS grade,
                COALESCE(a.strand_name, s.strand_name, '') AS strand,
                COALESCE(a.department_name, d.department_name, '') AS department,
                a.date_in,
                a.time_in
            FROM AttendanceRecords a
            LEFT JOIN Person p ON a.person_id = p.person_id
            LEFT JOIN StudentDetails sd ON sd.person_id = p.person_id
            LEFT JOIN GradeLevel g ON g.grade_level_id = sd.grade_level_id
            LEFT JOIN Strand s ON s.strand_id = sd.strand_id
            LEFT JOIN StaffDetails st ON st.person_id = p.person_id
            LEFT JOIN Department d ON d.department_id = st.department_id
            ORDER BY a.attendance_id DESC
        """)
        data = cursor.fetchall()
        conn.close()

        table = self.attendanceTableWidget
        table.setRowCount(len(data))
        table.setHorizontalHeaderLabels(
            ["NAME", "GRADE", "STRAND", "DEPARTMENT", "DATE", "TIME"]
        )

        for row_index, row_data in enumerate(data):
            for col_index, col_data in enumerate(row_data):
                item = QtWidgets.QTableWidgetItem(str(col_data))
                item.setForeground(QtGui.QColor("black"))
                item.setTextAlignment(QtCore.Qt.AlignLeft)
                table.setItem(row_index, col_index, item)

            header_item = QtWidgets.QTableWidgetItem(str(row_index + 1))
            header_item.setTextAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)
            table.setVerticalHeaderItem(row_index, header_item)

        table.verticalHeader().setDefaultSectionSize(30)
        table.verticalHeader().setStyleSheet("""
            QHeaderView::section {
                padding-top: 0px;
                margin: 0px;
                font-size: 14px;
                qproperty-alignment: AlignTop | AlignHCenter;
            }
        """)

        table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

        table.setColumnWidth(0, 180)  # NAME
        table.setColumnWidth(1, 115)  # GRADE
        table.setColumnWidth(2, 90)   # STRAND
        table.setColumnWidth(3, 190)  # DEPARTMENT
        table.setColumnWidth(4, 130)  # DATE
        table.setColumnWidth(5, 100)  # TIME


    def preprocess_face_for_embedding(self, frame, box):
        x1, y1, x2, y2 = [int(v) for v in box]
        margin = int(min(x2 - x1, y2 - y1) * 0.1)
        x1, y1 = max(0, x1 - margin), max(0, y1 - margin)
        x2, y2 = min(frame.shape[1], x2 + margin), min(frame.shape[0], y2 + margin)

        face = frame[y1:y2, x1:x2]
        face = cv2.resize(face, (160, 160))
        face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB).astype("float32") / 255.0
        face = (face - 0.5) / 0.5
        return torch.tensor(np.transpose(face, (2, 0, 1))).unsqueeze(0).float()

    def generate_embeddings_from_face_images(self, db_path="recognition.db"):
        embedder = InceptionResnetV1(pretrained="vggface2").eval()

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Skip people who already have embeddings
        cursor.execute("SELECT DISTINCT person_id FROM FaceEmbeddings")
        embedded_ids = {row[0] for row in cursor.fetchall()}

        # Get unembedded image paths
        cursor.execute(
            """
            SELECT person_id, image_path FROM FaceImages
            WHERE person_id NOT IN (
                SELECT DISTINCT person_id FROM FaceEmbeddings
            )
        """
        )
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
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype("float32") / 255.0
                img = (img - 0.5) / 0.5
                img = np.transpose(img, (2, 0, 1))
                img_tensor = torch.tensor(img).unsqueeze(0).float()

                # Generate embedding
                with torch.no_grad():
                    emb = embedder(img_tensor)[0].numpy()
                emb = emb / np.linalg.norm(emb)

                # ✅ Fix: Convert embedding list to string
                cursor.execute(
                    """
                    INSERT INTO FaceEmbeddings (person_id, embedding_vector)
                    VALUES (?, ?)
                """,
                    (person_id, str(emb.tolist())),
                )

                inserted += 1

            except Exception as e:
                print(f"❌ Error processing {image_path}: {e}")

        conn.commit()
        conn.close()

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
        # ✅ Debug print to verify how many embeddings were loaded
        print(f"✅ Loaded {len(embeddings)} embeddings from database")
        return embeddings, person_ids

    def mark_attendance(self, person_id):
        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()

        now = datetime.datetime.now()
        date_str = now.strftime("%B %#d, %Y")
        time_str = now.strftime("%I:%M %p")

        current_hour = now.hour
        current_period = "morning" if current_hour < 12 else "afternoon"

        # Check logs for the current day
        cursor.execute(
            """
            SELECT time_in FROM AttendanceRecords
            WHERE person_id = ? AND date_in = ?
        """,
            (person_id, date_str),
        )
        entries = cursor.fetchall()

        for (logged_time,) in entries:
            logged_hour = datetime.datetime.strptime(logged_time, "%I:%M %p").hour
            logged_period = "morning" if logged_hour < 12 else "afternoon"

            if logged_period == current_period:
                conn.close()
                return  # Already logged in this time

        # Not yet logged this time slot, insert new record
        cursor.execute(
            """
            INSERT INTO AttendanceRecords (person_id, date_in, time_in)
            VALUES (?, ?, ?)
        """,
            (person_id, date_str, time_str),
        )

        conn.commit()
        conn.close()
        self.populate_attendance_data()
        return True

    def show_profile(self, person_id, date_in=None, time_in=None):
        conn = sqlite3.connect("recognition.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT first_name, middle_name, last_name, profile_image_url
            FROM Person WHERE person_id = ?
        """,
            (person_id,),
        )
        person = cursor.fetchone()

        if person:
            full_name = f"{person[0]} {person[1]} {person[2]}"
            profile_path = person[3]

            # Default values
            strand = "N/A"
            grade = "N/A"
            department = "N/A"

            # Try fetching student details
            cursor.execute(
                """
                SELECT s.strand_name, g.grade_level
                FROM StudentDetails sd
                JOIN Strand s ON s.strand_id = sd.strand_id
                JOIN GradeLevel g ON g.grade_level_id = sd.grade_level_id
                WHERE sd.person_id = ?
            """,
                (person_id,),
            )
            student_info = cursor.fetchone()

            if student_info:
                strand, grade = student_info
            else:
                # Try fetching staff department
                cursor.execute(
                    """
                    SELECT d.department_name
                    FROM StaffDetails st
                    JOIN Department d ON d.department_id = st.department_id
                    WHERE st.person_id = ?
                """,
                    (person_id,),
                )
                staff_info = cursor.fetchone()
                if staff_info:
                    department = staff_info[0]

            # Determine display date and time
            display_date = (
                date_in if date_in else datetime.datetime.now().strftime("%B %d, %Y")
            )
            display_time = (
                time_in if time_in else datetime.datetime.now().strftime("%I:%M %p")
            )

            # Update UI Labels
            self.nameLabel.setText(f"{full_name}")
            self.dateLabel.setText(f"{display_date}")
            self.timeLabel.setText(f"{display_time}")
            self.strandLabel.setText(f"{strand}")
            self.gradeLabel.setText(f"{grade}")
            self.departmentLabel.setText(f"{department}")

            # Load profile image
            if profile_path and os.path.exists(profile_path):
                pixmap = QPixmap(profile_path).scaled(
                    291, 369, QtCore.Qt.KeepAspectRatio
                )
                self.image.setPixmap(pixmap)
            else:
                self.image.clear()

        conn.close()

    def show_unrecognize_person_dialog(self):
        dialog = UnrecognizeModule(self)
        dialog.exec_()
        self.dialog_shown = False  # Reset so next unknown face can trigger it again

    def show_login(self):
        self.admin_window = AdminDashboard(return_to_start=True)
        self.admin_window.show()
        self.close()  # ✅ This closes the AttendanceApp window

    def closeEvent(self, event):
        """Stop the camera when closing the application."""
        self.camera.release()
        event.accept()

    def Down_Menu_Num_0(self):
        if self.Down_Menu_Num == 0:
            self.animation1 = QtCore.QPropertyAnimation(self.frame_1, b"minimumHeight")
            self.animation1.setDuration(500)
            self.animation1.setStartValue(51)
            self.animation1.setEndValue(141)
            self.animation1.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
            self.animation1.start()

            self.animation2 = QtCore.QPropertyAnimation(self.frame_1, b"maximumHeight")
            self.animation2.setDuration(500)
            self.animation2.setStartValue(51)
            self.animation2.setEndValue(141)
            self.animation2.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
            self.animation2.start()

            self.Down_Menu_Num = 1

        else:
            self.animation1 = QtCore.QPropertyAnimation(self.frame_1, b"maximumHeight")
            self.animation1.setDuration(500)
            self.animation1.setStartValue(141)
            self.animation1.setEndValue(51)
            self.animation1.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
            self.animation1.start()

            self.animation2 = QtCore.QPropertyAnimation(self.frame_1, b"minimumHeight")
            self.animation2.setDuration(500)
            self.animation2.setStartValue(141)
            self.animation2.setEndValue(51)
            self.animation2.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
            self.animation2.start()

            self.Down_Menu_Num = 0

    def logout(self):
        reply = QMessageBox.question(
            self,
            "Logout Confirmation",
            "Are you sure you want to logout?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.close()
            self.start_screen = StartScreen()
            self.start_screen.show()

    # For dragging the window
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

class ImageViewerDialog(QtWidgets.QDialog):
    def __init__(self, image_paths):
        super(ImageViewerDialog, self).__init__()
        self.setWindowTitle("View Images")
        self.resize(800, 800)
        layout = QtWidgets.QVBoxLayout(self)

        scroll_area = QtWidgets.QScrollArea()
        scroll_widget = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_widget)

        for path in image_paths:
            if os.path.exists(path):
                pixmap = QPixmap(path).scaledToWidth(400, Qt.SmoothTransformation)
                label = QtWidgets.QLabel()
                label.setPixmap(pixmap)
                label.setAlignment(Qt.AlignCenter)
                scroll_layout.addWidget(label)

        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        self.setLayout(layout)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    start_screen = StartScreen()
    start_screen.fade_in()
    start_screen.show()
    sys.exit(app.exec_())
