# WEB library
import streamlit.components.v1 as components
import streamlit as st
import os
import cv2

# Import our custom modules
from ui_components import setup_page_style, create_home_page, create_know_more_page
from page_handlers import handle_mark_attendance, handle_register, handle_attendance_sheet, handle_student_statistics

# Setup page style
setup_page_style()

# Create frame window for video
FRAME_WINDOW = st.image([])

# Setup sidebar menu
menu = ["HOME", "MARK ATTENDANCE", "REGISTER", "ATTENDANCE SHEET", "STUDENT STATISTICS", "KNOW MORE"]
choice = st.sidebar.selectbox("Menu", menu)

# Setup columns for layout
col1, col2, col3 = st.columns(3)

# Setup data variables
path = 'Register_Data'
images = []
class_names = []

# Handle page navigation
if choice == 'MARK ATTENDANCE':
    handle_mark_attendance(col1, path, images, class_names, FRAME_WINDOW)
elif choice == 'REGISTER':
    handle_register()  # Remove col2 argument
elif choice == 'ATTENDANCE SHEET':
    handle_attendance_sheet(col2)
elif choice == 'STUDENT STATISTICS':
    handle_student_statistics()  # No column parameter
elif choice == 'HOME':
    create_home_page(col1)
elif choice == "KNOW MORE":
    create_know_more_page()