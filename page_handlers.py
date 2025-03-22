import streamlit as st
import pandas as pd
import cv2
import os
import time
import numpy as np
import face_recognition
from PIL import Image
import datetime
from face_recognition_utils import find_encodings, mark_attendance
from ui_components import create_header, format_info_card

from email.mime.text import MIMEText  # Ensure this import is included
import datetime
import smtplib

def eye_aspect_ratio(eye):
    """
    Calculate the eye aspect ratio to detect blinks
    A ratio of ~0.3 or less typically indicates a blink
    """
    # Compute the euclidean distances between the vertical eye landmarks
    A = np.linalg.norm(eye[1] - eye[5])
    B = np.linalg.norm(eye[2] - eye[4])
    
    # Compute the euclidean distance between the horizontal eye landmarks
    C = np.linalg.norm(eye[0] - eye[3])
    
    # Calculate the eye aspect ratio
    ear = (A + B) / (2.0 * C)
    return ear

def handle_mark_attendance(col1, path, images, class_names, frame_window):
    """
    Handle the mark attendance page with enhanced UI, blink detection, and email notification
    """
    import streamlit as st
    import os
    import cv2
    import numpy as np
    import face_recognition
    import time
    import pandas as pd  # Added for CSV handling
    import smtplib
    from email.mime.text import MIMEText
    from scipy.spatial import distance as dist  # For eye_aspect_ratio

   
    """
    Handle the mark attendance page with enhanced UI and blink detection
    """
    create_header()
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e40af, #4f46e5); color: white; padding: 15px; border-radius: 12px; margin-bottom: 20px; text-align: center; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); ">
        <h1>Mark Your Attendance</h1>
        <p style="font-size: 18px; color: white;">Stand in front of the camera and let the system recognize you</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("""
        <div style="background-color: #eff6ff; padding: 20px; border-radius: 10px;">
            <h3 style="color: #1e3a8a; margin-top: 0;">Instructions</h3>
            <ol style="padding-left: 20px;">
                <li>Click the button below to activate camera</li>
                <li>Position your face clearly in the frame</li>
                <li>Blink naturally a few times for verification</li>
                <li>Wait for the green box with your name</li>
                <li>Your attendance will be marked automatically</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='margin-top: 20px;'>", unsafe_allow_html=True)
        run = st.checkbox("ACTIVATE CAMERA", key="activate_camera")
        st.markdown("</div>", unsafe_allow_html=True)
        
        if run:
            st.markdown("""
            <div class="success-msg">
                Camera activated! Please look directly at the camera and blink naturally.
            </div>
            """, unsafe_allow_html=True)
        
        # Status indicator
        status_placeholder = st.empty()
        
        # Attendance results section
        results_container = st.container()
    
    with col2:
        st.markdown('<div class="camera-frame">', unsafe_allow_html=True)
        frame_placeholder = st.empty()
        st.markdown('</div>', unsafe_allow_html=True)
    
    if run:
        # Load images and encode faces
        my_list = os.listdir(path)
        for cl in my_list:
            curl_img = cv2.imread(f'{path}/{cl}')
            images.append(curl_img)
            class_names.append(os.path.splitext(cl)[0])
        
        encode_list_known = find_encodings(images)
        status_placeholder.markdown("""
        <div style="background-color: #dbeafe; padding: 10px; border-radius: 8px; margin-top: 15px;">
            <p style="margin: 0; color: #1e3a8a;"><span style="font-weight: bold;">✓</span> Encodings loaded successfully</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Initialize variables for attendance tracking
        last_recognized = None
        recognition_count = 0
        attendance_marked = False
        recognition_threshold = 5
        
        # Blink detection variables
        blink_counter = 0
        blink_total = 0
        previous_ear = 1.0
        EAR_THRESHOLD = 0.3
        CONSEC_FRAMES_THRESHOLD = 3
        blink_consec_counter = 0
        blink_verified = False
        MIN_BLINKS_REQUIRED = 2
        
        # Start capturing video
        cap = cv2.VideoCapture(0)
        
        while run:
            success, img = cap.read()
            if not success:
                status_placeholder.error("Error: Could not access camera. Please check your camera connection.")
                break
                
            # Resize image for faster processing
            img_s = cv2.resize(img, (0, 0), None, 0.25, 0.25)
            img_s = cv2.cvtColor(img_s, cv2.COLOR_BGR2RGB)
            
            # Detect faces in current frame
            face_cur_frame = face_recognition.face_locations(img_s)
            encode_cur_frame = face_recognition.face_encodings(img_s, face_cur_frame)
            
            # Process each face detected
            for encode_face, face_loc in zip(encode_cur_frame, face_cur_frame):
                matches = face_recognition.compare_faces(encode_list_known, encode_face)
                face_dis = face_recognition.face_distance(encode_list_known, encode_face)
                
                match_index = np.argmin(face_dis)
                confidence = 1 - face_dis[match_index]
                confidence_percent = f"{confidence*100:.1f}%"
                
                # Check if face is recognized
                if matches[match_index] and confidence > 0.6:
                    name = class_names[match_index].upper()
                    
                    # Get facial landmarks for blink detection
                    face_landmarks = face_recognition.face_landmarks(img_s, [face_loc])
                    
                    if face_landmarks:
                        left_eye = np.array(face_landmarks[0]['left_eye'])
                        right_eye = np.array(face_landmarks[0]['right_eye'])
                        
                        left_ear = eye_aspect_ratio(left_eye)
                        right_ear = eye_aspect_ratio(right_eye)
                        ear = (left_ear + right_ear) / 2.0
                        
                        # Draw eye contours
                        scaled_left_eye = left_eye * 4
                        scaled_right_eye = right_eye * 4
                        for eye in [scaled_left_eye, scaled_right_eye]:
                            eye = eye.reshape((-1, 1, 2))
                            cv2.polylines(img, [eye.astype(np.int32)], True, (0, 255, 255), 1)
                        
                        # Check for blink
                        if not blink_verified:
                            if ear < EAR_THRESHOLD:
                                blink_consec_counter += 1
                            else:
                                if blink_consec_counter >= CONSEC_FRAMES_THRESHOLD:
                                    blink_total += 1
                                    cv2.putText(img, f"BLINK DETECTED!", (10, 30),
                                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                                blink_consec_counter = 0
                            
                            if blink_total >= MIN_BLINKS_REQUIRED:
                                blink_verified = True
                        
                        cv2.putText(img, f"EAR: {ear:.2f}", (300, 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                    
                    # Draw bounding box
                    y1, x2, y2, x1 = face_loc
                    y1, x2, y2, x1 = y1*4, x2*4, y2*4, x1*4
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.rectangle(img, (x1, y2-35), (x2, y2), (0, 255, 0), cv2.FILLED)
                    cv2.putText(img, f"{name} ({confidence_percent})", (x1+6, y2-6),
                                cv2.FONT_HERSHEY_COMPLEX, 0.6, (255, 255, 255), 2)
                    
                    # Track consecutive recognitions only if blink verification passed
                    if blink_verified:
                        if last_recognized == name:
                            recognition_count += 1
                        else:
                            recognition_count = 1
                            last_recognized = name
                    
                    # Update status with confidence level and blink info
                    status_text = f"""
                    <div style="background-color: #dcfce7; padding: 10px; border-radius: 8px; margin-top: 15px;">
                        <p style="margin: 0; color: #166534;">
                            <span style="font-weight: bold;">Recognized:</span> {name}<br>
                            <span style="font-weight: bold;">Confidence:</span> {confidence_percent}<br>
                            <span style="font-weight: bold;">Blink Status:</span> {'✓ Verified' if blink_verified else f'Detected {blink_total}/{MIN_BLINKS_REQUIRED} blinks'}<br>
                            <span style="font-weight: bold;">Status:</span> {'✓ Verified' if recognition_count >= recognition_threshold and blink_verified else 'Verifying...'}
                        </p>
                    </div>
                    """
                    status_placeholder.markdown(status_text, unsafe_allow_html=True)
                    
                    # Mark attendance and send email after consistent recognition and blink verification
                    if recognition_count >= recognition_threshold and blink_verified and not attendance_marked:
                        attendance_time = mark_attendance(name)
                        attendance_marked = True
                        
                        # Retrieve email from Attendance_Sheet.csv
                        try:
                            df = pd.read_csv('Attendance_Sheet.csv', on_bad_lines='warn')
                            student_email = df[df['NAME'].str.upper() == name]['EMAIL'].iloc[0] if not df[df['NAME'].str.upper() == name].empty else None
                        except Exception as e:
                            st.error(f"Error reading email from CSV: {str(e)}")
                            student_email = None

                        # Send email if email is found
                        if student_email:
                            try:
                                send_attendance_email(student_email, name, attendance_time)
                                email_status = "A confirmation email has been sent."
                            except Exception as e:
                                email_status = f"Failed to send email: {str(e)}"
                        else:
                            email_status = "Email not found in records."
                        
                        # Display success message with original styling
                        with results_container:
                            st.markdown(f"""
                            <div style="background-color: #dcfce7; padding: 15px; border-radius: 8px; border-left: 5px solid #166534; margin-top: 20px;">
                                <h3 style="color: #166534; margin-top: 0;">Attendance Marked Successfully!</h3>
                                <p><strong>Name:</strong> {name}</p>
                                <p><strong>Time:</strong> {attendance_time}</p>
                                <p><strong>Liveness Detection:</strong> Passed</p>
                                <p><strong>Email Status:</strong> {email_status}</p>
                                <p>Your attendance has been recorded. Thank you!</p>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    y1, x2, y2, x1 = face_loc
                    y1, x2, y2, x1 = y1*4, x2*4, y2*4, x1*4
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.rectangle(img, (x1, y2-35), (x2, y2), (0, 0, 255), cv2.FILLED)
                    cv2.putText(img, "UNKNOWN", (x1+6, y2-6),
                                cv2.FONT_HERSHEY_COMPLEX, 0.6, (255, 255, 255), 2)
                    status_placeholder.warning("Unknown face detected. Please register first or reposition your face.")
                    last_recognized = None
                    recognition_count = 0
            
            # If no faces detected
            if not face_cur_frame:
                status_placeholder.info("No face detected. Please position yourself in front of the camera.")
                last_recognized = None
                recognition_count = 0
            
            # Add blink counter to the frame
            if not blink_verified:
                cv2.putText(img, f"Blinks: {blink_total}/{MIN_BLINKS_REQUIRED}", (10, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                cv2.putText(img, "Blink Verification: PASSED", (10, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Display the image in the Streamlit app
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            frame_placeholder.image(img, channels="RGB", use_container_width=True)
            
            # Check if the checkbox is still checked
            if not st.session_state.activate_camera:
                break
                
            time.sleep(0.1)
        
        # Release camera when done
        cap.release()
    
    # If camera is not active, show placeholder image
    else:
        placeholder_img = np.zeros((480, 640, 3), dtype=np.uint8)
        placeholder_img.fill(240)
        cv2.putText(placeholder_img, "Camera Inactive", (180, 240),
                    cv2.FONT_HERSHEY_COMPLEX, 1, (100, 100, 100), 2)
        frame_placeholder.image(placeholder_img, channels="RGB", use_container_width=True)
        status_placeholder.markdown("""
        <div style="background-color: #f3f4f6; padding: 10px; border-radius: 8px; margin-top: 15px;">
            <p style="margin: 0; color: #4b5563;">Click "ACTIVATE CAMERA" to begin attendance marking</p>
        </div>
        """, unsafe_allow_html=True)

# Helper functions
def eye_aspect_ratio(eye):
    from scipy.spatial import distance as dist
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

def find_encodings(images):
    encode_list = []
    for img in images:
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img_rgb)[0]
        encode_list.append(encode)
    return encode_list

def mark_attendance(name):
    import datetime
    now = datetime.datetime.now()
    dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
    attendance_file = 'Attendance_Sheet.csv'
    if os.path.exists(attendance_file):
        df = pd.read_csv(attendance_file)
        new_entry = pd.DataFrame({
            "NAME": [name],
            "TIME": [dt_string],
            "EMAIL": [df[df['NAME'].str.upper() == name]['EMAIL'].iloc[0] if not df[df['NAME'].str.upper() == name].empty else "N/A"],
            "ID": [df[df['NAME'].str.upper() == name]['ID'].iloc[0] if not df[df['NAME'].str.upper() == name].empty else "N/A"]
        })
        df = pd.concat([df, new_entry], ignore_index=True)
        df.to_csv(attendance_file, index=False)
    else:
        pd.DataFrame({"NAME": [name], "TIME": [dt_string], "EMAIL": ["N/A"], "ID": ["N/A"]}).to_csv(attendance_file, index=False)
    return dt_string

def send_attendance_email(email, name, attendance_time):
    sender_email = "cristonhimasha73@gmail.com"  # Replace with your email
    sender_password = "dylc xare ljvv ssxu"  # Replace with your app-specific password
    subject = "Attendance Confirmation - Class Attendance"
    body = f"""
    Dear {name.split()[0]} {name.split()[-1] if len(name.split()) > 1 else ''},

    Your attendance has been successfully recorded for the class.

    Details:
    - Name: {name}
    - Date and Time: {attendance_time}
    - Status: Present

    Thank you for attending the class! If you have any questions, feel free to reach out.

    Best regards,
    The Attendance System Team
    """
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = email
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)

# Assuming these helper functions are defined elsewhere in your code
def eye_aspect_ratio(eye):
    from scipy.spatial import distance as dist
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

def find_encodings(images):
    encode_list = []
    for img in images:
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img_rgb)[0]
        encode_list.append(encode)
    return encode_list

def mark_attendance(name):
    import datetime
    now = datetime.datetime.now()
    dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
    attendance_file = 'Attendance_Sheet.csv'
    if os.path.exists(attendance_file):
        df = pd.read_csv(attendance_file)
        new_entry = pd.DataFrame({"NAME": [name], "TIME": [dt_string], "EMAIL": [df[df['NAME'].str.upper() == name]['EMAIL'].iloc[0] if not df[df['NAME'].str.upper() == name].empty else "N/A"], "ID": [df[df['NAME'].str.upper() == name]['ID'].iloc[0] if not df[df['NAME'].str.upper() == name].empty else "N/A"]})
        df = pd.concat([df, new_entry], ignore_index=True)
        df.to_csv(attendance_file, index=False)
    else:
        pd.DataFrame({"NAME": [name], "TIME": [dt_string], "EMAIL": ["N/A"], "ID": ["N/A"]}).to_csv(attendance_file, index=False)
    return dt_string

def handle_register():
    import streamlit as st
    import os
    import datetime
    import pandas as pd
    from streamlit_lottie import st_lottie
    import requests
    import time
    import numpy as np
    import cv2
    from streamlit_extras.add_vertical_space import add_vertical_space
    from streamlit_extras.stylable_container import stylable_container
    from streamlit_extras.switch_page_button import switch_page
    from streamlit_extras.colored_header import colored_header
    from streamlit_card import card
    import json

    # Load animated icons
    def load_lottie_url(url):
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    
    # Lottie animations
    lottie_camera = load_lottie_url("https://assets5.lottiefiles.com/packages/lf20_bzgbs8vz.json")
    lottie_success = load_lottie_url("https://assets7.lottiefiles.com/packages/lf20_jbrw3hcz.json")
    lottie_loading = load_lottie_url("https://assets3.lottiefiles.com/packages/lf20_usmfx6bp.json")

    # CSS
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    :root {
        --primary-color: #6366f1;
        --primary-light: #818cf8;
        --primary-dark: #4f46e5;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --error-color: #ef4444;
        --text-primary: #1f2937;
        --text-secondary: #4b5563;
        --bg-light: #f9fafb;
        --card-bg: rgba(255, 255, 255, 0.95);
        --border-radius: 12px;
    }
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #e0f2fe 0%, #dbeafe 50%, #ede9fe 100%);
    }
    
    .card-container {
        background: var(--card-bg);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: var(--border-radius);
        padding: 30px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.5);
        transition: all 0.3s ease;
        margin-top: 20px;
    }
    
    .card-container:hover {
        box-shadow: 0 15px 40px rgba(0, 0, 0, 0.15);
        transform: translateY(-2px);
    }
    
    .header-text {
        color: var(--text-primary);
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.5rem;
        background: linear-gradient(90deg, #4f46e5, #7c3aed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .subheader {
        color: var(--text-secondary);
        font-size: 1.1rem;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .section-title {
        color: var(--primary-dark);
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 1rem;
        position: relative;
        padding-bottom: 8px;
    }
    
    .section-title:after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 40px;
        height: 3px;
        background: linear-gradient(90deg, var(--primary-color), var(--primary-light));
        border-radius: 3px;
    }
    
    .input-label {
        font-weight: 500;
        color: var(--text-primary);
        margin-bottom: 5px;
    }
    
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 1px solid #e5e7eb;
        padding: 12px 16px;
        transition: all 0.2s;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
    }
    
    /* Camera frame styling */
    .camera-container {
        border: 2px dashed #d1d5db;
        border-radius: var(--border-radius);
        padding: 15px;
        background-color: rgba(249, 250, 251, 0.7);
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .camera-container:hover {
        border-color: var(--primary-color);
        background-color: rgba(249, 250, 251, 0.9);
    }
    
    /* Button styling */
    .custom-btn {
        background: linear-gradient(45deg, var(--primary-dark), var(--primary-color));
        color: white;
        padding: 10px 20px;
        border-radius: 30px;
        border: none;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        cursor: pointer;
        transition: all 0.3s ease;
        width: 100%;
        margin-top: 10px;
    }
    
    .custom-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(79, 70, 229, 0.4);
    }
    
    .custom-btn.secondary {
        background: white;
        color: var(--primary-dark);
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    
    .custom-btn.secondary:hover {
        border-color: var(--primary-color);
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
    }
    
    /* Success message */
    .success-msg {
        background-color: rgba(220, 252, 231, 0.9);
        padding: 20px;
        border-radius: var(--border-radius);
        border-left: 5px solid var(--success-color);
        margin-top: 20px;
        animation: slideIn 0.5s ease forwards;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Captured photos grid */
    .photo-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
        gap: 10px;
        margin-top: 15px;
    }
    
    .photo-item {
        border-radius: 8px;
        overflow: hidden;
        border: 3px solid white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
        position: relative;
    }
    
    .photo-item:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }
    
    .photo-counter {
        position: absolute;
        bottom: 5px;
        right: 5px;
        background: rgba(0, 0, 0, 0.6);
        color: white;
        border-radius: 10px;
        padding: 2px 8px;
        font-size: 0.7rem;
        font-weight: 600;
    }
    
    /* Tips section */
    .tips-card {
        border-radius: var(--border-radius);
        overflow: hidden;
        transition: all 0.3s ease;
    }
    
    .tips-header {
        padding: 15px;
        font-weight: 600;
        color: white;
    }
    
    .tips-content {
        padding: 15px;
        background: white;
    }
    
    .tips-list {
        margin: 0;
        padding-left: 20px;
    }
    
    .tips-list li {
        margin-bottom: 5px;
    }
    
    .do-header {
        background: var(--success-color);
    }
    
    .dont-header {
        background: var(--error-color);
    }
    
    /* Progress indicator */
    .progress-container {
        display: flex;
        justify-content: space-between;
        margin: 20px 0;
        position: relative;
        padding: 0 10px;
    }
    
    .progress-step {
        display: flex;
        flex-direction: column;
        align-items: center;
        position: relative;
        z-index: 2;
    }
    
    .step-number {
        width: 35px;
        height: 35px;
        border-radius: 50%;
        background: #e5e7eb;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        color: var(--text-secondary);
        position: relative;
        z-index: 2;
        transition: all 0.3s ease;
    }
    
    .step-label {
        margin-top: 8px;
        font-size: 0.85rem;
        color: var(--text-secondary);
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .progress-step.active .step-number {
        background: var(--primary-color);
        color: white;
        box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.2);
    }
    
    .progress-step.active .step-label {
        color: var(--primary-color);
        font-weight: 500;
    }
    
    .progress-step.completed .step-number {
        background: var(--success-color);
        color: white;
    }
    
    .progress-step.completed .step-label {
        color: var(--success-color);
    }
    
    .progress-line {
        position: absolute;
        top: 17px;
        height: 2px;
        background: #e5e7eb;
        left: 0;
        right: 0;
        z-index: 1;
    }
    
    .progress-line-fill {
        position: absolute;
        top: 17px;
        height: 2px;
        background: var(--success-color);
        left: 0;
        z-index: 1;
        transition: width 0.5s ease;
    }
    
    /* Tooltip */
    .tooltip {
        position: relative;
        display: inline-block;
    }
    
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 200px;
        background-color: #333;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 5px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        transform: translateX(-50%);
        opacity: 0;
        transition: opacity 0.3s;
    }
    
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    
    /* Loading spinner */
    .loading-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 30px;
    }
    
    .loading-text {
        margin-top: 15px;
        color: var(--primary-dark);
        font-weight: 500;
    }
    
    /* Badge */
    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    
    .badge.green {
        background-color: rgba(16, 185, 129, 0.1);
        color: var(--success-color);
    }
    
    .badge.blue {
        background-color: rgba(59, 130, 246, 0.1);
        color: #3b82f6;
    }
    
    .badge.amber {
        background-color: rgba(245, 158, 11, 0.1);
        color: var(--warning-color);
    }
    
    /* Review table styling */
    .review-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
    }
    
    .review-table tr {
        border-bottom: 1px solid #f3f4f6;
    }
    
    .review-table tr:last-child {
        border-bottom: none;
    }
    
    .review-table td {
        padding: 12px 8px;
        vertical-align: top;
    }
    
    .review-table td:first-child {
        width: 35%;
        color: var(--text-secondary);
        font-weight: 500;
    }
    
    .review-table td:last-child {
        color: var(--text-primary);
    }
    
    /* Photo thumbnail grid */
    .photo-thumbnails {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
        margin-top: 8px;
    }
    
    .photo-thumbnail {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.2s ease;
        position: relative;
        aspect-ratio: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        background: white;
    }
    
    .photo-thumbnail:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    .photo-thumbnail img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    
    /* Confetti animation for successful registration */
    @keyframes confetti-fall {
        0% { transform: translateY(-100vh) rotate(0deg); }
        100% { transform: translateY(100vh) rotate(720deg); }
    }
    
    .confetti {
        position: fixed;
        z-index: 999;
        width: 10px;
        height: 10px;
        pointer-events: none;
        animation: confetti-fall linear forwards;
    }
    
    /* Button container */
    .button-container {
        display: flex;
        gap: 15px;
        margin-top: 25px;
    }
    
    /* Success card styling */
    .success-card {
        background: linear-gradient(145deg, #ffffff, #f9fafb);
        border-radius: var(--border-radius);
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
        padding: 30px;
        position: relative;
        overflow: hidden;
        animation: fadeIn 0.6s ease-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .success-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 5px;
        background: linear-gradient(90deg, var(--success-color), #3b82f6);
    }
    
    .success-details {
        display: grid;
        grid-template-columns: 120px 1fr;
        gap: 8px;
        margin-top: 15px;
    }
    
    .success-details-label {
        color: var(--text-secondary);
        font-weight: 500;
    }
    
    .success-details-value {
        color: var(--text-primary);
    }
    
    /* Stacked photos visual */
    .stacked-photos {
        position: relative;
        width: 150px;
        height: 150px;
        margin: 0 auto;
    }
    
    .stacked-photo {
        position: absolute;
        width: 130px;
        height: 130px;
        border-radius: 10px;
        background: white;
        border: 5px solid white;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        transition: all 0.3s ease;
    }
    
    .stacked-photo:nth-child(1) {
        transform: rotate(-10deg);
        z-index: 1;
    }
    
    .stacked-photo:nth-child(2) {
        transform: rotate(5deg);
        z-index: 2;
    }
    
    .stacked-photo:nth-child(3) {
        transform: rotate(-5deg);
        z-index: 3;
    }
    
    .stacked-photo img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    
    /* Button styling */
    .btn {
        padding: 10px 20px;
        border-radius: 30px;
        font-weight: 500;
        transition: all 0.3s ease;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
    }
    
    .btn-primary {
        background: linear-gradient(45deg, var(--primary-dark), var(--primary-color));
        color: white;
        border: none;
        box-shadow: 0 4px 10px rgba(99, 102, 241, 0.3);
    }
    
    .btn-primary:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(99, 102, 241, 0.4);
    }
    
    .btn-secondary {
        background: white;
        color: var(--primary-dark);
        border: 1px solid #e5e7eb;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
    }
    
    .btn-secondary:hover {
        background: #f9fafb;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.08);
    }
    
    /* Hide the default Streamlit button styling */
    div.stButton > button {
        height: auto;
    }
    
    div.stButton > button:hover {
        color: inherit;
        border-color: inherit;
    }
    
    /* Custom Streamlit button styling */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(45deg, var(--primary-dark), var(--primary-color));
        color: white;
        border: none;
        font-weight: 600;
        padding: 10px 20px;
        border-radius: 30px;
        transition: all 0.3s ease;
    }
    
    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(99, 102, 241, 0.4);
    }
    
    div.stButton > button[kind="secondary"] {
        background: white;
        color: var(--primary-dark);
        border: 1px solid #e5e7eb;
        font-weight: 500;
        padding: 10px 20px;
        border-radius: 30px;
        transition: all 0.3s ease;
    }
    
    div.stButton > button[kind="secondary"]:hover {
        border-color: var(--primary-color);
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.08);
    }
    
    /* Fix column layout */
    .columns-container {
        display: flex;
        gap: 20px;
    }
    
    .column {
        flex: 1;
    }
    </style>
    """, unsafe_allow_html=True)

    # Page Header
    st.markdown('<h1 class="header-text">Smart Attendance System</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subheader">Register your profile with multiple photos for enhanced recognition</p>', unsafe_allow_html=True)

    # Initialize session state variables
    if 'captured_images' not in st.session_state:
        st.session_state.captured_images = []
    if 'registration_step' not in st.session_state:
        st.session_state.registration_step = 1
    if 'registration_complete' not in st.session_state:
        st.session_state.registration_complete = False
    if 'processing' not in st.session_state:
        st.session_state.processing = False

    # Progress tracker
    if not st.session_state.registration_complete:
        # Calculate progress width for animation
        progress_width = "0%"
        if st.session_state.registration_step == 2:
            progress_width = "50%"
        elif st.session_state.registration_step == 3:
            progress_width = "100%"
        
        st.markdown(f"""
        <div class="progress-container">
            <div class="progress-line"></div>
            <div class="progress-line-fill" style="width: {progress_width};"></div>
            
            <div class="progress-step {'active' if st.session_state.registration_step == 1 else 'completed' if st.session_state.registration_step > 1 else ''}">
                <div class="step-number">{'' if st.session_state.registration_step > 1 else '1'}</div>
                <div class="step-label">Personal Details</div>
            </div>
            
            <div class="progress-step {'active' if st.session_state.registration_step == 2 else 'completed' if st.session_state.registration_step > 2 else ''}">
                <div class="step-number">{'' if st.session_state.registration_step > 2 else '2'}</div>
                <div class="step-label">Photo Capture</div>
            </div>
            
            <div class="progress-step {'active' if st.session_state.registration_step == 3 else ''}">
                <div class="step-number">3</div>
                <div class="step-label">Confirmation</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Main container
    st.markdown('<div class="card-container">', unsafe_allow_html=True)

    if st.session_state.registration_complete:
        # Display confetti effect for successful registration
        colors = ["#4f46e5", "#818cf8", "#10b981", "#3b82f6", "#f59e0b"]
        st.markdown("""
        <script>
        function createConfetti() {
            const confettiContainer = document.createElement('div');
            confettiContainer.style.position = 'fixed';
            confettiContainer.style.top = '0';
            confettiContainer.style.left = '0';
            confettiContainer.style.width = '100%';
            confettiContainer.style.height = '100%';
            confettiContainer.style.pointerEvents = 'none';
            confettiContainer.style.zIndex = '9999';
            document.body.appendChild(confettiContainer);
            
            const colors = ["#4f46e5", "#818cf8", "#10b981", "#3b82f6", "#f59e0b"];
            
            for (let i = 0; i < 100; i++) {
                setTimeout(() => {
                    const confetti = document.createElement('div');
                    confetti.className = 'confetti';
                    confetti.style.left = Math.random() * 100 + '%';
                    confetti.style.background = colors[Math.floor(Math.random() * colors.length)];
                    confetti.style.width = Math.random() * 10 + 5 + 'px';
                    confetti.style.height = Math.random() * 10 + 5 + 'px';
                    confetti.style.opacity = Math.random() + 0.5;
                    confetti.style.animationDuration = Math.random() * 3 + 2 + 's';
                    
                    confettiContainer.appendChild(confetti);
                    
                    setTimeout(() => {
                        confetti.remove();
                    }, 5000);
                }, i * 50);
            }
            
            setTimeout(() => {
                confettiContainer.remove();
            }, 6000);
        }
        
        // Run after page load
        document.addEventListener('DOMContentLoaded', createConfetti);
        
        // For Streamlit hot-reloading, run immediately too
        createConfetti();
        </script>
        """, unsafe_allow_html=True)
        
        # Show success screen
        st.markdown("""
        <div class="success-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h2 style="margin-top: 0; color: var(--success-color); display: flex; align-items: center; gap: 10px;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                            <polyline points="22 4 12 14.01 9 11.01"></polyline>
                        </svg>
                        Registration Complete!
                    </h2>
                    <p style="color: var(--text-secondary); margin-bottom: 20px;">
                        Your profile has been successfully registered in our system.
                    </p>
                </div>
        """, unsafe_allow_html=True)
        
        # Display Lottie animation
        st_lottie(lottie_success, height=150, key="success_animation")
        
        st.markdown("""
            </div>
            
            <div class="success-details">
                <div class="success-details-label">Full Name:</div>
                <div class="success-details-value">{}</div>
                
                <div class="success-details-label">ID/Employee:</div>
                <div class="success-details-value">{}</div>
                
                <div class="success-details-label">Email:</div>
                <div class="success-details-value">{}</div>
                
                <div class="success-details-label">Photos:</div>
                <div class="success-details-value">{} photos registered</div>
                
                <div class="success-details-label">Registered on:</div>
                <div class="success-details-value">{}</div>
                
                <div class="success-details-label">Status:</div>
                <div class="success-details-value">
                    <span class="badge green">Active</span>
                    <span class="badge blue" style="margin-left: 5px;">Email Sent</span>
                </div>
            </div>
            
            <div class="button-container">
                <button onclick="resetRegistration()" class="btn btn-secondary">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 5px;">
                        <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 9"></path>
                        <path d="M3 3v6h6"></path>
                    </svg>
                    Register Another Person
                </button>
                
                <button onclick="goToDashboard()" class="btn btn-primary">
                    Go to Dashboard
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-left: 5px;">
                        <polyline points="9 18 15 12 9 6"></polyline>
                    </svg>
                </button>
            </div>
            
            <script>
            function resetRegistration() {
                window.streamlitRegistry?.setComponentValue("register_another", true);
            }
            
            function goToDashboard() {
                window.streamlitRegistry?.setComponentValue("go_dashboard", true);
            }
            </script>
        </div>
        """.format(
            f"{st.session_state.user_first_name} {st.session_state.user_last_name}",
            st.session_state.user_id if hasattr(st.session_state, 'user_id') and st.session_state.user_id else "Not provided",
            st.session_state.user_email,
            len(st.session_state.captured_images),
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ), unsafe_allow_html=True)
        
        # Options for the user after registration
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("Register Another Person", key="register_another", use_container_width=True):
                st.session_state.captured_images = []
                st.session_state.registration_step = 1
                st.session_state.registration_complete = False
                st.rerun()
        
        with col_btn2:
            if st.button("Go to Dashboard", key="go_dashboard", use_container_width=True):
                # Logic for navigating to dashboard
                st.info("Redirecting to dashboard...")
                # switch_page("dashboard")
            
    elif st.session_state.processing:
        # Loading state with animation
        st.markdown("""
        <div class="loading-container">
            <div style="width: 200px; height: 200px;">
        """, unsafe_allow_html=True)
        st_lottie(lottie_loading, height=200, key="loading_animation")
        st.markdown("""
            </div>
            <p class="loading-text">Processing your registration...</p>
            <p style="color: var(--text-secondary); text-align: center; max-width: 400px; margin: 0 auto;">
                We're saving your photos and creating your profile. This will only take a moment.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Simulate processing time (in a real app, this would be actual processing)
        time.sleep(2)
        st.session_state.processing = False
        st.session_state.registration_complete = True
        st.rerun()
            
    elif st.session_state.registration_step == 1:
        # Step 1: Personal Details
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown('<h3 class="section-title">Personal Information</h3>', unsafe_allow_html=True)
            user_first_name = st.text_input("First Name", key="reg_first_name", placeholder="John")
            user_last_name = st.text_input("Last Name", key="reg_last_name", placeholder="Doe")
            user_id = st.text_input("ID/Employee Number (Optional)", key="reg_id", placeholder="EMP123")
            user_email = st.text_input("Email Address", key="reg_email", placeholder="john.doe@example.com")
            
            # Store in session state
            if user_first_name:
                st.session_state.user_first_name = user_first_name
            if user_last_name:
                st.session_state.user_last_name = user_last_name
            if user_id:
                st.session_state.user_id = user_id
            if user_email:
                st.session_state.user_email = user_email
        
        with col2:
            st.markdown("""
                <div style="height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 20px;">
                """, unsafe_allow_html=True)
            if lottie_camera is not None:
                st_lottie(lottie_camera, height=200, key="camera_animation")
            else:
                st.image("https://img.icons8.com/fluent/96/000000/camera.png", width=100, caption="Camera Animation Unavailable")
            st.markdown("""
                <h4 style="text-align: center; margin-top: 15px; color: var(--primary-dark);">Why Register with Photos?</h4>
                <p style="text-align: center; color: var(--text-secondary); margin-bottom: 0;">
                    Multiple photos enhance our AI recognition system's accuracy,
                    ensuring seamless attendance tracking and access control.
                </p>
                </div>
                """, unsafe_allow_html=True)
        
        # Next button
        if st.button("Continue to Photo Capture →", key="step1_next", use_container_width=True):
            if user_first_name and user_last_name and user_email:
                st.session_state.registration_step = 2
                st.rerun()
            else:
                st.warning("Please fill in all required fields (First Name, Last Name, and Email).")
            
    elif st.session_state.registration_step == 2:
        # Step 2: Photo Capture
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.markdown('<h3 class="section-title">Capture Your Photos</h3>', unsafe_allow_html=True)
            
            # Camera input with styling
            st.markdown('<div class="camera-container">', unsafe_allow_html=True)
            camera_image = st.camera_input("", key="webcam_input")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Capture button
            col_btn1, col_btn2 = st.columns([2, 1])
            with col_btn1:
                if st.button("Capture Photo", key="capture_btn", use_container_width=True):
                    if camera_image is not None:
                        st.session_state.captured_images.append(camera_image)
                        st.success(f"Photo {len(st.session_state.captured_images)} captured successfully!")
                    else:
                        st.warning("Please position yourself in the camera frame first.")
            
            with col_btn2:
                if st.button("Clear All", key="clear_photos", use_container_width=True):
                    st.session_state.captured_images = []
                    st.rerun()
        
        with col2:
            st.markdown('<h3 class="section-title">Capture Guidelines</h3>', unsafe_allow_html=True)
            
            with stylable_container(
                key="tips_container",
                css_styles="""
                {
                    border-radius: 10px;
                    background-color: white;
                    padding: 15px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                    height: 100%;
                }
                """
            ):
                st.markdown("""
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <div style="background-color: rgba(16, 185, 129, 0.1); width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 10px;">
                        <span style="color: #10b981; font-weight: bold;">✓</span>
                    </div>
                    <div>
                        <p style="margin: 0; font-weight: 500; color: var(--text-primary);">Tips for Best Results:</p>
                    </div>
                </div>
                <ul style="margin-top: 10px; padding-left: 20px; color: var(--text-secondary);">
                    <li>Take 3-5 photos for best accuracy</li>
                    <li>Ensure good, even lighting on your face</li>
                    <li>Look directly at the camera</li>
                    <li>Try slight angle variations</li>
                    <li>Keep a neutral expression</li>
                </ul>
                
                <div style="display: flex; align-items: center; margin: 15px 0 10px;">
                    <div style="background-color: rgba(239, 68, 68, 0.1); width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 10px;">
                        <span style="color: #ef4444; font-weight: bold;">✗</span>
                    </div>
                    <div>
                        <p style="margin: 0; font-weight: 500; color: var(--text-primary);">Avoid:</p>
                    </div>
                </div>
                <ul style="margin-top: 10px; padding-left: 20px; color: var(--text-secondary);">
                    <li>Blurry images</li>
                    <li>Side profiles only</li>
                    <li>Face obstructions (hats, large glasses)</li>
                    <li>Poor lighting conditions</li>
                </ul>
                """, unsafe_allow_html=True)
        
        # Display captured photos
        if st.session_state.captured_images:
            st.markdown('<h3 class="section-title">Captured Photos</h3>', unsafe_allow_html=True)
            
            cols = st.columns(5)
            for i, img in enumerate(st.session_state.captured_images):
                with cols[i % 5]:
                    st.image(img, width=120)
                    st.markdown(f"""
                    <div style="text-align: center; margin-top: -5px;">
                        <span class="badge blue">Photo {i+1}</span>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Navigation buttons
            col_back, col_space, col_next = st.columns([1, 2, 1])
            
            with col_back:
                if st.button("← Back", key="step2_back", use_container_width=True):
                    st.session_state.registration_step = 1
                    st.rerun()
            
            with col_next:
                if st.button("Continue →", key="step2_next", use_container_width=True):
                    if len(st.session_state.captured_images) >= 3:
                        st.session_state.registration_step = 3
                        st.rerun()
                    else:
                        st.warning("Please capture at least 3 photos before continuing.")
        else:
            st.info("No photos captured yet. Take at least 3 photos to continue.")
            
            # Back button only
            if st.button("← Back to Personal Details", key="step2_back_only", use_container_width=True):
                st.session_state.registration_step = 1
                st.rerun()
            
    elif st.session_state.registration_step == 3:
        # Step 3: Review and Confirm
        st.markdown('<h3 class="section-title">Review Your Information</h3>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("""
            <div style="background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
                <h4 style="color: var(--primary-dark); margin-top: 0; font-size: 1.1rem; font-weight: 600; margin-bottom: 15px;">Personal Details</h4>
                <table class="review-table">
                    <tr>
                        <td>Full Name</td>
                        <td><strong>{full_name}</strong></td>
                    </tr>
                    <tr>
                        <td>ID/Employee</td>
                        <td>{user_id}</td>
                    </tr>
                    <tr>
                        <td>Email</td>
                        <td>{email}</td>
                    </tr>
                    <tr>
                        <td>Photos</td>
                        <td><strong>{photo_count}</strong> captured</td>
                    </tr>
                    <tr>
                        <td>Registration Date</td>
                        <td>{reg_date}</td>
                    </tr>
                </table>
            </div>
            """.format(
                full_name=f"{st.session_state.user_first_name} {st.session_state.user_last_name}",
                user_id=st.session_state.user_id if hasattr(st.session_state, 'user_id') and st.session_state.user_id else "Not provided",
                email=st.session_state.user_email,
                photo_count=len(st.session_state.captured_images),
                reg_date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ), unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            <div style="background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
                <h4 style="color: var(--primary-dark); margin-top: 0; font-size: 1.1rem; font-weight: 600; margin-bottom: 15px;">Captured Photos</h4>
                <div class="photo-thumbnails">
            """, unsafe_allow_html=True)
            
            # Generate photo thumbnails directly in HTML
            photo_html = ""
            for i, img in enumerate(st.session_state.captured_images[:6]):  # Show up to 6 photos
                placeholder_img = f"https://via.placeholder.com/100?text=Photo+{i+1}"
                photo_html += f"""
                <div class="photo-thumbnail">
                    <img src="{placeholder_img}" alt="Photo {i+1}">
                </div>
                """
            
            st.markdown(photo_html, unsafe_allow_html=True)
            
            if len(st.session_state.captured_images) > 6:
                st.markdown(f"""
                <div style="text-align: center; color: var(--text-secondary); font-style: italic; margin-top: 10px;">
                    +{len(st.session_state.captured_images) - 6} more photos
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div></div>", unsafe_allow_html=True)
            
            # Show sample thumbnails since we can't directly render the captured images in HTML
            with st.container():
                st.subheader("Photo Preview")
                gallery_cols = st.columns(3)
                for i, img in enumerate(st.session_state.captured_images[:6]):
                    with gallery_cols[i % 3]:
                        st.image(img, width=100, caption=f"Photo {i+1}")
        
        # Privacy notice and terms
        st.markdown("""
        <div style="background-color: rgba(59, 130, 246, 0.05); border-radius: 8px; padding: 15px; margin-top: 20px;">
            <div style="display: flex; align-items: flex-start; gap: 10px;">
                <div>
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="12" y1="16" x2="12" y2="12"></line>
                        <line x1="12" y1="8" x2="12.01" y2="8"></line>
                    </svg>
                </div>
                <div>
                    <p style="margin: 0; color: var(--text-secondary); font-size: 0.9rem;">
                        By confirming your registration, you agree to our <a href="#" style="color: #3b82f6; text-decoration: none; font-weight: 500;">Privacy Policy</a> and 
                        <a href="#" style="color: #3b82f6; text-decoration: none; font-weight: 500;">Terms of Service</a>. Your photos will be used only for attendance recognition purposes 
                        and stored securely. You can request deletion of your data at any time.
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation and submission buttons
        col_back, col_space, col_submit = st.columns([1, 1, 2])
        
        with col_back:
            if st.button("← Back", key="step3_back", use_container_width=True):
                st.session_state.registration_step = 2
                st.rerun()

        with col_submit:
            if st.button("Confirm & Register", key="step3_submit", use_container_width=True):
                # Validate and process registration
                if hasattr(st.session_state, 'user_first_name') and hasattr(st.session_state, 'user_last_name') and \
                   hasattr(st.session_state, 'user_email') and st.session_state.captured_images:
                    # Set processing state
                    st.session_state.processing = True
                    
                    # Save photos to Register_Data folder
                    register_path = 'Register_Data'
                    if not os.path.exists(register_path):
                        os.makedirs(register_path)
                    
                    user_id = st.session_state.user_id if hasattr(st.session_state, 'user_id') and st.session_state.user_id else f"{st.session_state.user_first_name}_{st.session_state.user_last_name}"
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    photo_count = 0
                    
                    for i, img in enumerate(st.session_state.captured_images):
                        # Convert BytesIO image to OpenCV format
                        img_bytes = img.getvalue()
                        nparr = np.frombuffer(img_bytes, np.uint8)
                        cv_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                        
                        # Save photo
                        photo_filename = f"{user_id}_{timestamp}_{i+1}.jpg"
                        photo_path = os.path.join(register_path, photo_filename)
                        cv2.imwrite(photo_path, cv_img)
                        photo_count += 1
                    
                    # Save student details to CSV
                    details = {
                        'First Name': st.session_state.user_first_name,
                        'Last Name': st.session_state.user_last_name,
                        'ID': st.session_state.user_id if hasattr(st.session_state, 'user_id') else 'N/A',
                        'Email': st.session_state.user_email,
                        'Photo Count': photo_count,
                        'Registration Date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    df = pd.DataFrame([details])
                    csv_path = 'student_details.csv'
                    if os.path.exists(csv_path):
                        df.to_csv(csv_path, mode='a', header=False, index=False)
                    else:
                        df.to_csv(csv_path, mode='w', header=True, index=False)
                    
                    # Trigger processing animation and move to success state
                    st.session_state.processing = True
                    st.rerun()
                else:
                    st.error("Registration data incomplete. Please go back and fill all required fields.")

    st.markdown('</div>', unsafe_allow_html=True)  # Close card-container

    # Confetti animation on successful registration
    if st.session_state.registration_complete:
        st.markdown("""
        <div class="confetti-container">
            <div class="confetti" style="left: 10%; background: #4f46e5;"></div>
            <div class="confetti" style="left: 20%; background: #10b981; animation-delay: 0.2s;"></div>
            <div class="confetti" style="left: 30%; background: #f59e0b; animation-delay: 0.4s;"></div>
            <div class="confetti" style="left: 40%; background: #ef4444; animation-delay: 0.6s;"></div>
            <div class="confetti" style="left: 50%; background: #6366f1; animation-delay: 0.8s;"></div>
            <div class="confetti" style="left: 60%; background: #4f46e5;"></div>
            <div class="confetti" style="left: 70%; background: #10b981; animation-delay: 0.2s;"></div>
            <div class="confetti" style="left: 80%; background: #f59e0b; animation-delay: 0.4s;"></div>
            <div class="confetti" style="left: 90%; background: #ef4444; animation-delay: 0.6s;"></div>
        </div>
        """, unsafe_allow_html=True)
def send_registration_email(email, first_name, last_name, user_id, photo_count):
    """
    Send a confirmation email to the user after successful registration
    """
    sender_email = "cristonhimasha73@gmail.com"  # Replace with your email
    sender_password = "hzhs pqtd fsnc xsws"    # Replace with your app-specific password
    subject = "Registration Confirmation - Facial Recognition System"
    body = f"""
    Dear {first_name} {last_name},

    Congratulations! Your registration in our Facial Recognition Attendance System is complete.

    Registration Details:
    - Name: {first_name} {last_name}
    - ID: {user_id if user_id else "Not provided"}
    - Photos Registered: {photo_count}
    - Registration Date: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    You can now use the 'Mark Attendance' feature with your registered face.

    For any issues, please contact support@example.com.

    Best regards,
    The Attendance System Team
    """
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = email
    
    with smtplib.SMTP('smtp.gmail.com', 587) as server:  # Example for Gmail
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
def handle_attendance_sheet(col2):
    import streamlit as st
    import os
    import pandas as pd
    import datetime

    # CSS unchanged
    st.markdown("""
    <style>
        .main-header { background: linear-gradient(135deg, #1e40af, #4f46e5); color: white; padding: 15px; border-radius: 12px; margin-bottom: 20px; text-align: center; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); }
        .stat-card { background: white; border-radius: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05); padding: 15px; text-align: center; transition: transform 0.2s, box-shadow 0.2s; }
        .stat-card:hover { transform: translateY(-3px); box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1); }
        .stat-value { font-size: 24px; font-weight: bold; color: #4f46e5; margin: 8px 0; }
        .stat-label { color: #6b7280; font-size: 13px; }
        .filter-container { background: #f9fafb; padding: 15px; border-radius: 10px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05); }
        .section-title { color: #1e40af; margin-bottom: 12px; font-size: 18px; font-weight: 600; display: flex; align-items: center; }
        .section-title::before { content: ""; width: 3px; height: 20px; background: #4f46e5; margin-right: 8px; border-radius: 2px; }
        .empty-state { background: #f9fafb; border: 1px dashed #d1d5db; border-radius: 10px; padding: 30px; text-align: center; margin: 20px 0; }
        .table-container { border-radius: 10px; overflow: hidden; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05); margin-bottom: 15px; }
        .info-box { background: #eff6ff; border-left: 4px solid #4f46e5; padding: 12px; border-radius: 4px; margin-top: 15px; }
        .export-button { background: #4f46e5; color: white; border-radius: 6px; padding: 8px 12px; font-weight: 500; transition: background 0.3s; }
        .export-button:hover { background: #3b82f6; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-header"><h1>📊 Attendance Dashboard</h1><p>View, analyze, and export attendance records</p></div>', unsafe_allow_html=True)

    if not os.path.exists('Attendance_Sheet.csv'):
        st.markdown("""
        <div class="empty-state">
            <img src="https://img.icons8.com/fluent/96/000000/attendance.png">
            <h2 style="margin-top: 20px; color: #4f46e5;">No Attendance Records Yet</h2>
            <p style="margin: 15px 0; color: #6b7280;">Start by registering or marking attendance</p>
            <a href="#" style="text-decoration: none;"><div style="background: #4f46e5; color: white; padding: 10px 20px; border-radius: 6px; display: inline-block;">Go to Register/Mark Attendance</div></a>
        </div>
        """, unsafe_allow_html=True)
        return

    # Load data with error handling
    try:
        df = pd.read_csv('Attendance_Sheet.csv', on_bad_lines='warn')  # Skip bad lines and warn
        if df.empty:
            st.warning("Attendance sheet is empty or unreadable.")
            return
    except Exception as e:
        st.error(f"Error reading Attendance_Sheet.csv: {str(e)}. Please check the file format.")
        return

    # Ensure all expected columns exist
    expected_columns = ["NAME", "TIME", "EMAIL", "ID"]
    for col in expected_columns:
        if col not in df.columns:
            df[col] = "N/A"
    filtered_df = df.copy()

    # Add DATE column
    if 'DATE' not in df.columns:
        df['DATE'] = pd.to_datetime(df['TIME'], errors='coerce').dt.date
        filtered_df['DATE'] = df['DATE']

    # Statistics
    total_records = len(df)
    unique_students = df['NAME'].nunique()
    days_recorded = df['DATE'].nunique()
    latest_time = pd.to_datetime(df['TIME'], errors='coerce').max().strftime("%d %b, %H:%M") if not df['TIME'].isna().all() else "N/A"

    st.markdown('<div class="section-title">Quick Statistics</div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="stat-card"><div class="stat-label">TOTAL RECORDS</div><div class="stat-value">{total_records}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="stat-card"><div class="stat-label">UNIQUE STUDENTS</div><div class="stat-value">{unique_students}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="stat-card"><div class="stat-label">DAYS RECORDED</div><div class="stat-value">{days_recorded}</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="stat-card"><div class="stat-label">LATEST RECORD</div><div class="stat-value" style="font-size: 20px;">{latest_time}</div></div>', unsafe_allow_html=True)

    # Filter section
    st.markdown('<div class="section-title">Filter & Sort</div>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="filter-container">', unsafe_allow_html=True)
        if 'filters_applied' not in st.session_state:
            st.session_state.filters_applied = False

        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([1, 1, 1, 1])
        with filter_col1:
            dates = filtered_df['DATE'].dropna().unique()
            selected_date = st.selectbox("📅 Date", ["All Dates"] + sorted(dates, reverse=True))
            if selected_date != "All Dates":
                filtered_df = filtered_df[filtered_df['DATE'] == selected_date]
                st.session_state.filters_applied = True
        with filter_col2:
            names = sorted(filtered_df['NAME'].dropna().unique())
            selected_name = st.selectbox("👤 Student Name", ["All Students"] + names)
            if selected_name != "All Students":
                filtered_df = filtered_df[filtered_df['NAME'] == selected_name]
                st.session_state.filters_applied = True
        with filter_col3:
            emails = sorted(filtered_df['EMAIL'].dropna().unique()) if 'EMAIL' in filtered_df.columns else ["All Emails"]
            selected_email = st.selectbox("✉️ Email", ["All Emails"] + emails)
            if selected_email != "All Emails" and 'EMAIL' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['EMAIL'] == selected_email]
                st.session_state.filters_applied = True
        with filter_col4:
            sort_options = {"Latest First": ("TIME", False), "Earliest First": ("TIME", True), "Name (A-Z)": ("NAME", True), "Name (Z-A)": ("NAME", False)}
            selected_sort = st.selectbox("🔄 Sort By", list(sort_options.keys()))
            sort_column, sort_ascending = sort_options[selected_sort]
            filtered_df = filtered_df.sort_values(by=sort_column, ascending=sort_ascending, na_position='last')

        reset_col1, reset_col2 = st.columns([1, 5])
        with reset_col1:
            if st.button("Reset Filters") and st.session_state.filters_applied:
                st.session_state.filters_applied = False
                st.success("Filters reset! Please refresh the page.")
        st.markdown('</div>', unsafe_allow_html=True)

    # Records display
    st.markdown('<div class="section-title">Attendance Records</div>', unsafe_allow_html=True)
    if filtered_df.empty:
        st.info("No records match your current filters.")
    else:
        display_df = filtered_df.copy()
        display_df['Time'] = pd.to_datetime(display_df['TIME'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M')
        columns_to_show = ['NAME', 'DATE', 'Time', 'EMAIL'] if 'EMAIL' in display_df.columns else ['NAME', 'DATE', 'Time']
        if 'ID' in display_df.columns:
            columns_to_show.append('ID')
        clean_df = display_df[columns_to_show].rename(columns={'NAME': 'Student Name', 'DATE': 'Date', 'EMAIL': 'Email', 'ID': 'ID'})

        st.markdown('<div class="table-container">', unsafe_allow_html=True)
        st.dataframe(clean_df, use_container_width=True, height=min(400, len(clean_df) * 35 + 38))
        st.markdown('</div>', unsafe_allow_html=True)

        export_col1, export_col2 = st.columns([1, 5])
        with export_col1:
            if st.button("Export Data", key="export_button"):
                csv = clean_df.to_csv(index=False)
                st.download_button(label="Download CSV", data=csv, file_name=f"attendance_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv", mime="text/csv")

    # Insights section
    if len(df) > 5 and df['DATE'].nunique() > 1:
        st.markdown('<div class="section-title">Attendance Insights</div>', unsafe_allow_html=True)
        insight_col1, insight_col2 = st.columns([1, 1])
        with insight_col1:
            daily_attendance = df.groupby('DATE').size().reset_index(name='count')
            daily_attendance['DATE'] = pd.to_datetime(daily_attendance['DATE'], errors='coerce')
            daily_attendance = daily_attendance.sort_values('DATE')
            st.subheader("Daily Attendance")
            st.line_chart(daily_attendance.set_index('DATE'))
        with insight_col2:
            top_students = df['NAME'].value_counts().head(5)
            st.subheader("Most Frequent Attendees")
            st.bar_chart(top_students)

    with st.expander("ℹ️ About This Dashboard"):
        st.markdown("""
        This dashboard displays attendance records including student names, dates, times, and emails. Features include:
        - **Filter** by date, name, or email
        - **Sort** records by various criteria
        - **Export** data as CSV
        - View **insights** on attendance trends
        Data is stored in 'Attendance_Sheet.csv'. For advanced use, consider a database backend.
        """)
def mark_attendance(name):
    import datetime
    import pandas as pd
    import os
    
    now = datetime.datetime.now()
    date_string = now.strftime("%Y-%m-%d")
    time_string = now.strftime("%H:%M:%S")
    attendance_file = 'Attendance_Sheet.csv'
    
    # Normalize name (remove numbers and underscores)
    normalized_name = ''.join(c for c in name if not c.isdigit()).replace("_", " ").strip()
    
    if os.path.exists(attendance_file):
        df = pd.read_csv(attendance_file)
        # Ensure columns exist
        for col in ["NAME", "DATE", "TIME", "EMAIL", "ID"]:
            if col not in df.columns:
                df[col] = "N/A"
        email = df[df['NAME'].str.upper() == normalized_name.upper()]['EMAIL'].iloc[0] if not df[df['NAME'].str.upper() == normalized_name.upper()].empty else "N/A"
        id_val = df[df['NAME'].str.upper() == normalized_name.upper()]['ID'].iloc[0] if not df[df['NAME'].str.upper() == normalized_name.upper()].empty else "N/A"
        new_entry = pd.DataFrame({
            "NAME": [normalized_name],
            "DATE": [date_string],
            "TIME": [time_string],
            "EMAIL": [email],
            "ID": [id_val]
        })
        df = pd.concat([df, new_entry], ignore_index=True)
        df.to_csv(attendance_file, index=False)
    else:
        pd.DataFrame({
            "NAME": [normalized_name],
            "DATE": [date_string],
            "TIME": [time_string],
            "EMAIL": ["N/A"],
            "ID": ["N/A"]
        }).to_csv(attendance_file, index=False)
    return f"{date_string} {time_string}"
def handle_student_statistics():
    """
    Display student attendance statistics with improved layout and responsive design
    """
    import streamlit as st
    import pandas as pd
    import os
    import datetime
    from dateutil.relativedelta import relativedelta
    import plotly.express as px

    # Full-width layout styling
    st.markdown("""
    <style>
    .statistics-header { 
        background: linear-gradient(135deg, #1e40af, #4f46e5); 
        color: white; 
        padding: 20px 30px; 
        border-radius: 15px; 
        margin-bottom: 25px; 
        text-align: center; 
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.15); 
    }
    .statistics-header h1 {
        color: white !important;
        margin-bottom: 10px;
        font-size: 2.4rem;
    }
    .statistics-header p {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.2rem;
    }
    .stat-card { 
        background: white; 
        border-radius: 12px; 
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.05); 
        padding: 20px; 
        text-align: center; 
        transition: transform 0.3s, box-shadow 0.3s; 
        height: 100%;
    }
    .stat-card:hover { 
        transform: translateY(-5px); 
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1); 
    }
    .stat-value { 
        font-size: 32px; 
        font-weight: 700; 
        color: #4f46e5; 
        margin: 10px 0; 
        line-height: 1;
    }
    .stat-label { 
        color: #6b7280; 
        font-size: 16px; 
        font-weight: 500;
    }
    .section-title { 
        color: #1e40af; 
        font-size: 24px; 
        font-weight: 600; 
        margin: 30px 0 20px; 
        border-bottom: 3px solid #4f46e5; 
        padding-bottom: 10px; 
        width: fit-content;
    }
    .summary-box { 
        background: linear-gradient(to right, #eff6ff, #f8fafc); 
        padding: 25px; 
        border-radius: 12px; 
        border-left: 6px solid #1e3a8a; 
        margin-bottom: 25px; 
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.05);
    }
    .decision-good { 
        color: #166534; 
        font-weight: 600; 
        background: rgba(22, 101, 52, 0.1);
        padding: 6px 12px;
        border-radius: 20px;
        display: inline-block;
    }
    .decision-risk { 
        color: #b91c1c; 
        font-weight: 600; 
        background: rgba(185, 28, 28, 0.1);
        padding: 6px 12px;
        border-radius: 20px;
        display: inline-block;
    }
    .data-table {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
        margin: 20px 0;
    }
    .data-table th {
        background: linear-gradient(135deg, #1e40af, #4f46e5);
        color: white;
        padding: 12px 15px;
    }
    .data-table td {
        padding: 10px 15px;
    }
    .chart-container {
        background: white;
        border-radius: 12px;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.05);
        padding: 20px;
        margin: 20px 0;
    }
    .export-button {
        background: linear-gradient(135deg, #4f46e5, #7c3aed);
        color: white;
        border-radius: 10px;
        border: none;
        padding: 12px 25px;
        font-weight: 600;
        text-align: center;
        transition: all 0.3s ease;
        margin-top: 20px;
        cursor: pointer;
    }
    .export-button:hover {
        background: linear-gradient(135deg, #3b82f6, #1e40af);
        box-shadow: 0 6px 15px rgba(59, 130, 246, 0.3);
    }
    </style>
    """, unsafe_allow_html=True)

    # Full-width header
    st.markdown('<div class="statistics-header"><h1>📊 Student Attendance Dashboard</h1><p>Comprehensive statistics and eligibility tracking</p></div>', unsafe_allow_html=True)

    if not os.path.exists('Attendance_Sheet.csv'):
        st.warning("No attendance data found. Please mark attendance first.")
        return

    # Load and clean data
    try:
        df = pd.read_csv('Attendance_Sheet.csv', on_bad_lines='warn')
        df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
        df = df.dropna(subset=['DATE'])
        df['Month'] = df['DATE'].dt.to_period('M')
        df['Semester'] = df['DATE'].apply(lambda x: f"{x.year}-S{(x.month-1)//6 + 1}")
    except Exception as e:
        st.error(f"Error loading attendance data: {str(e)}")
        return

    # Student selection with search
    col_selection, col_summary = st.columns([1, 2])
    with col_selection:
        st.markdown('<div class="section-title">Select Student</div>', unsafe_allow_html=True)
        students = sorted(df['NAME'].unique())
        search_term = st.text_input("Search for student", "")
        if search_term:
            filtered_students = [s for s in students if search_term.lower() in s.lower()]
            students = filtered_students if filtered_students else students
            if not filtered_students:
                st.info(f"No students found matching '{search_term}'")
        selected_student = st.selectbox("Choose a student", students)

    # Filter data for selected student
    student_df = df[df['NAME'] == selected_student]
    if student_df.empty:
        st.info(f"No attendance records found for {selected_student}.")
        return

    # Calculate statistics
    total_days = len(df['DATE'].dt.date.unique())
    attended_days = len(student_df['DATE'].dt.date.unique())
    attendance_percentage = (attended_days / total_days) * 100 if total_days > 0 else 0

    # Attendance decision (75% threshold)
    if attendance_percentage >= 75:
        status = "Satisfactory"
        status_color = "#166534"
        decision = "Eligible for full credits"
        decision_class = "decision-good"
    else:
        status = "At Risk"
        status_color = "#b91c1c"
        decision = "Needs improvement - Academic warning"
        decision_class = "decision-risk"

    # Quick stats
    st.markdown('<div class="section-title">Attendance Overview</div>', unsafe_allow_html=True)
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    with col_stat1:
        st.markdown(f'''
        <div class="stat-card">
            <div class="stat-label">Days Attended</div>
            <div class="stat-value">{attended_days}</div>
            <div style="font-size: 14px; color: #64748b; margin-top: 5px;">out of {total_days} days</div>
        </div>
        ''', unsafe_allow_html=True)
    with col_stat2:
        st.markdown(f'''
        <div class="stat-card">
            <div class="stat-label">Attendance Rate</div>
            <div class="stat-value">{attendance_percentage:.1f}%</div>
            <div style="font-size: 14px; color: #64748b; margin-top: 5px;">required: 75%</div>
        </div>
        ''', unsafe_allow_html=True)
    with col_stat3:
        st.markdown(f'''
        <div class="stat-card">
            <div class="stat-label">Status</div>
            <div class="stat-value" style="color: {status_color};">{status}</div>
            <div style="font-size: 14px; color: #64748b; margin-top: 5px;">as of {datetime.datetime.now().strftime('%b %d, %Y')}</div>
        </div>
        ''', unsafe_allow_html=True)

    # Summary section
    st.markdown('<div class="section-title">Student Profile & Eligibility</div>', unsafe_allow_html=True)
    col_profile, col_decision = st.columns([3, 2])
    with col_profile:
        email = student_df['EMAIL'].iloc[0] if pd.notna(student_df['EMAIL'].iloc[0]) and student_df['EMAIL'].iloc[0] != "N/A" else "Not registered"
        id_val = student_df['ID'].iloc[0] if pd.notna(student_df['ID'].iloc[0]) and student_df['ID'].iloc[0] != "N/A" else "Not registered"
        st.markdown(f"""
        <div class="summary-box">
            <h3 style="color: #1e3a8a; margin-top: 0;">Student Information</h3>
            <div style="display: grid; grid-template-columns: 120px 1fr; gap: 10px; margin-top: 15px;">
                <div style="font-weight: 600; color: #475569;">Name:</div>
                <div>{selected_student}</div>
                <div style="font-weight: 600; color: #475569;">Email:</div>
                <div>{email}</div>
                <div style="font-weight: 600; color: #475569;">Student ID:</div>
                <div>{id_val}</div>
                <div style="font-weight: 600; color: #475569;">First Attendance:</div>
                <div>{student_df['DATE'].min().strftime('%b %d, %Y') if not student_df.empty else 'N/A'}</div>
                <div style="font-weight: 600; color: #475569;">Latest Attendance:</div>
                <div>{student_df['DATE'].max().strftime('%b %d, %Y') if not student_df.empty else 'N/A'}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_decision:
        st.markdown(f"""
        <div class="summary-box" style="height: 100%;">
            <h3 style="color: {status_color}; margin-top: 0;">{status} Attendance</h3>
            <div style="text-align: center; margin: 20px 0;">
                <div style="font-size: 48px; font-weight: 700; color: {status_color};">{attendance_percentage:.1f}%</div>
                <div style="margin-top: 5px; color: #64748b;">Attendance Rate</div>
            </div>
            <div style="text-align: center; margin-top: 15px;">
                <div class="{decision_class}" style="width: 100%;">{decision}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Monthly attendance analysis
    st.markdown('<div class="section-title">Monthly Attendance Analysis</div>', unsafe_allow_html=True)
    monthly_counts = student_df.groupby('Month').size().reset_index(name='Days Attended')
    monthly_counts['Month'] = monthly_counts['Month'].astype(str)
    monthly_total = df.groupby('Month')['DATE'].apply(lambda x: len(x.dt.date.unique())).reset_index(name='Total Days')
    monthly_total['Month'] = monthly_total['Month'].astype(str)
    monthly_data = monthly_counts.merge(monthly_total, on='Month', how='outer').fillna(0)
    monthly_data['Percentage'] = (monthly_data['Days Attended'] / monthly_data['Total Days'] * 100).fillna(0)
    
    col_table, col_chart = st.columns([1, 2])
    with col_table:
        st.markdown('<div class="data-table">', unsafe_allow_html=True)
        st.dataframe(monthly_data.style.format({'Percentage': '{:.1f}%'}))
        st.markdown('</div>', unsafe_allow_html=True)
    with col_chart:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        fig_monthly = px.line(monthly_data, x='Month', y=['Days Attended', 'Total Days'], 
                              title=f"Monthly Attendance Trend for {selected_student}",
                              labels={'value': 'Days', 'variable': 'Type'},
                              template='plotly_white',
                              color_discrete_map={'Days Attended': '#4f46e5', 'Total Days': '#d97706'})
        fig_monthly.add_scatter(x=monthly_data['Month'], y=monthly_data['Percentage'], mode='lines+markers',
                                name='Percentage', yaxis="y2", line=dict(color='#10b981', width=2, dash='dot'),
                                marker=dict(size=8))
        # Corrected
        fig_monthly.update_layout(
    yaxis2=dict(
        title=dict(
            text='Percentage (%)',
            font=dict(color='#10b981')  # Nested under title
        ),
        tickfont=dict(color='#10b981'),
        anchor="x",
        overlaying="y",
        side="right",
        range=[0, 100]
    ),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    margin=dict(l=20, r=40, t=60, b=20)
)
        fig_monthly.add_shape(type="line", x0=monthly_data['Month'].iloc[0], y0=75, x1=monthly_data['Month'].iloc[-1], y1=75,
                              line=dict(color="#ef4444", width=2, dash="dash"), yref="y2")
        fig_monthly.add_annotation(x=monthly_data['Month'].iloc[-1], y=75, text="Attendance Threshold (75%)",
                                   showarrow=False, yshift=10, bgcolor="rgba(255, 255, 255, 0.8)", bordercolor="#ef4444",
                                   borderwidth=1, borderpad=4, yref="y2")
        st.plotly_chart(fig_monthly, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Semester performance
    st.markdown('<div class="section-title">Semester Performance</div>', unsafe_allow_html=True)
    semester_counts = student_df.groupby('Semester').size().reset_index(name='Days Attended')
    semester_total = df.groupby('Semester')['DATE'].apply(lambda x: len(x.dt.date.unique())).reset_index(name='Total Days')
    semester_data = semester_counts.merge(semester_total, on='Semester', how='outer').fillna(0)
    semester_data['Percentage'] = (semester_data['Days Attended'] / semester_data['Total Days'] * 100).fillna(0)
    semester_data['Status'] = semester_data['Percentage'].apply(lambda x: 'Eligible' if x >= 75 else 'At Risk')
    
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    fig_semester = px.bar(semester_data, x='Semester', y=['Days Attended', 'Total Days'],
                          title=f"Semester Attendance Comparison for {selected_student}",
                          barmode='group', labels={'value': 'Days', 'variable': 'Type'},
                          template='plotly_white', color_discrete_map={'Days Attended': '#4f46e5', 'Total Days': '#d97706'})
    fig_semester.add_scatter(x=semester_data['Semester'], y=semester_data['Percentage'], mode='lines+markers+text',
                             name='Percentage', yaxis="y2", text=semester_data['Percentage'].apply(lambda x: f"{x:.1f}%"),
                             textposition="top center", line=dict(color='#10b981', width=3), marker=dict(size=10, symbol='diamond'))
    for i, row in semester_data.iterrows():
        color = '#166534' if row['Status'] == 'Eligible' else '#b91c1c'
        fig_semester.add_annotation(x=row['Semester'], y=row['Percentage'], text=row['Status'], showarrow=False, yshift=-20,
                                    font=dict(color=color, size=12), bgcolor="rgba(255, 255, 255, 0.8)", bordercolor=color,
                                    borderwidth=1, borderpad=3, yref="y2")
    # Corrected
        fig_semester.update_layout(
    yaxis2=dict(
        title=dict(
            text='Percentage (%)',
            font=dict(color='#10b981')  # Nested under title
        ),
        tickfont=dict(color='#10b981'),
        anchor="x",
        overlaying="y",
        side="right",
        range=[0, 100]
    ),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    margin=dict(l=20, r=40, t=60, b=40)
)
    fig_semester.add_shape(type="line", x0=semester_data['Semester'].iloc[0], y0=75, x1=semester_data['Semester'].iloc[-1], y1=75,
                           line=dict(color="#ef4444", width=2, dash="dash"), yref="y2")
    st.plotly_chart(fig_semester, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Attendance patterns
    st.markdown('<div class="section-title">Attendance Patterns</div>', unsafe_allow_html=True)
    if not student_df.empty:
        student_df['Weekday'] = student_df['DATE'].dt.day_name()
        weekday_counts = student_df.groupby('Weekday').size().reset_index(name='Count')
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekday_counts['Weekday'] = pd.Categorical(weekday_counts['Weekday'], categories=weekday_order, ordered=True)
        weekday_counts = weekday_counts.sort_values('Weekday')
        
        col_pattern1, col_pattern2 = st.columns(2)
        with col_pattern1:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            fig_weekday = px.bar(weekday_counts, x='Weekday', y='Count', title="Attendance by Day of Week",
                                 labels={'Count': 'Number of Days', 'Weekday': 'Day'},
                                 color='Count', color_continuous_scale=px.colors.sequential.Blues, template='plotly_white')
            fig_weekday.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig_weekday, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with col_pattern2:
            if 'TIME' in student_df.columns:
                try:
                    student_df['Hour'] = pd.to_datetime(student_df['TIME'], format='%H:%M:%S', errors='coerce').dt.hour
                    hour_counts = student_df.groupby('Hour').size().reset_index(name='Count')
                    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                    fig_time = px.line(hour_counts, x='Hour', y='Count', title="Attendance by Time of Day",
                                       labels={'Count': 'Number of Days', 'Hour': 'Hour of Day'},
                                       markers=True, template='plotly_white')
                    fig_time.update_traces(line_color='#4f46e5')
                    st.plotly_chart(fig_time, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.info(f"Time pattern analysis not available: {str(e)}")
            else:
                st.info("Time data not available for pattern analysis.")

    # Export options
    st.markdown('<div class="section-title">Export Options</div>', unsafe_allow_html=True)
    col_export1, col_export2 = st.columns(2)
    with col_export1:
        if st.button("Download Student Statistics CSV", key="export_csv"):
            csv = student_df.to_csv(index=False)
            filename = f"{selected_student.replace(' ', '_')}_attendance_{datetime.datetime.now().strftime('%Y%m%d')}.csv"
            st.download_button(label="⬇️ Click to Download CSV", data=csv, file_name=filename, mime="text/csv",
                               key="download_csv", help="Download detailed attendance records for this student")
    with col_export2:
        if st.button("Generate Summary Report", key="summary_report"):
            summary_md = f"""# Attendance Summary for {selected_student}
            
## Overview
- **Student:** {selected_student}
- **Email:** {email}
- **ID:** {id_val}
- **Attendance Rate:** {attendance_percentage:.1f}%
- **Status:** {status}
- **Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}

## Attendance Details
- **Days Attended:** {attended_days} out of {total_days}
- **First Attendance:** {student_df['DATE'].min().strftime('%b %d, %Y') if not student_df.empty else 'N/A'}
- **Latest Attendance:** {student_df['DATE'].max().strftime('%b %d, %Y') if not student_df.empty else 'N/A'}
- **Eligibility Decision:** {decision}

## Monthly Breakdown
"""
            for _, row in monthly_data.iterrows():
                summary_md += f"- **{row['Month']}:** {row['Days Attended']:.0f} days ({row['Percentage']:.1f}%)\n"
            filename = f"{selected_student.replace(' ', '_')}_summary_{datetime.datetime.now().strftime('%Y%m%d')}.md"
            st.download_button(label="⬇️ Download Summary Report", data=summary_md, file_name=filename, mime="text/markdown",
                               key="download_summary", help="Download a readable summary report")