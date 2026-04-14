# Teacher Grading Management System

## Overview
A web‑based application that digitises the entire grading workflow – from grade entry by lecturers, through HOD verification, to final approval by the Dean. Built with Django and MySQL.

## Key Features
- **Role‑based dashboards** (Lecturer, HOD, Dean, Student)
- **AI grade validation** – flags unusual grades (class average ±25 points)
- **Multi‑step approval** – Lecturer → HOD → Dean → Student view
- **Automatic letter grade calculation** (A, B+, B, … F)
- **Audit trail** and override reason tracking
- **Responsive frontend** (HTML5, CSS3, JavaScript)

## Technology Stack
- Backend: Django 4.2, Python 3.13
- Database: MySQL (via XAMPP)
- Frontend: HTML5, CSS3, JavaScript (Vanilla)
- Authentication: Django’s auth with custom UserProfile roles

## Setup Instructions
1. Clone the repo:  
   `git clone https://github.com/codebytiya/teacher-grading-system.git`
2. Install dependencies:  
   `pip install -r requirements.txt`
3. Configure MySQL database (create database, update `settings.py`).
4. Run migrations:  
   `python manage.py migrate`
5. Create superuser:  
   `python manage.py createsuperuser`
6. Start server:  
   `python manage.py runserver`

## Project Status
Backend complete (15+ tables with foreign keys). Frontend dashboards under active development.

## Contributors
- Tiyamika Malunga (MA1600) – codebytiya

## License
Academic project – not for commercial use.
