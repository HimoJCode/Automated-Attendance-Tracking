
-- Lookup Tables
CREATE TABLE Strand (
    strand_id INTEGER PRIMARY KEY AUTOINCREMENT,
    strand_name TEXT NOT NULL,
    description TEXT
);

CREATE TABLE GradeLevel (
    grade_level_id INTEGER PRIMARY KEY AUTOINCREMENT,
    grade_level TEXT NOT NULL,
    description TEXT
);

CREATE TABLE Department (
    department_id INTEGER PRIMARY KEY AUTOINCREMENT,
    department_name TEXT NOT NULL,
    description TEXT
);

-- Person Table
CREATE TABLE Person (
    person_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    middle_name TEXT,
    gender TEXT,
    profile_image_url TEXT
);

-- Student Details
CREATE TABLE StudentDetails (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER UNIQUE NOT NULL,
    strand_id INTEGER,
    grade_level_id INTEGER,
    FOREIGN KEY (person_id) REFERENCES Person(person_id) ON DELETE CASCADE,
    FOREIGN KEY (strand_id) REFERENCES Strand(strand_id),
    FOREIGN KEY (grade_level_id) REFERENCES GradeLevel(grade_level_id)
);

-- Staff Details
CREATE TABLE StaffDetails (
    staff_id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER UNIQUE NOT NULL,
    department_id INTEGER,
    FOREIGN KEY (person_id) REFERENCES Person(person_id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES Department(department_id)
);

-- Admin Table
CREATE TABLE Admin (
    admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    admin_role TEXT NOT NULL CHECK (admin_role IN ('admin', 'super_admin')),
    person_id INTEGER,
    created_by_admin_id INTEGER,
    FOREIGN KEY (person_id) REFERENCES Person(person_id),
    FOREIGN KEY (created_by_admin_id) REFERENCES Admin(admin_id)
);

-- Face Images Table
CREATE TABLE FaceImages (
    image_id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER NOT NULL,
    image_path TEXT NOT NULL,
    uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (person_id) REFERENCES Person(person_id) ON DELETE CASCADE
);

-- Face Embeddings Table (JSON string for embeddings)
CREATE TABLE FaceEmbeddings (
    embedding_id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER NOT NULL,
    embedding_vector TEXT NOT NULL,
    FOREIGN KEY (person_id) REFERENCES Person(person_id) ON DELETE CASCADE
);

-- Attendance Table
CREATE TABLE AttendanceRecords (
    attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER NOT NULL,
    date_in TEXT,
    time_in TEXT,
    FOREIGN KEY (person_id) REFERENCES Person(person_id) ON DELETE CASCADE
);
