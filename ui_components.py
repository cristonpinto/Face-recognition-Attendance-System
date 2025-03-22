import streamlit as st
from streamlit_lottie import st_lottie
import requests
import json

def load_lottieurl(url):
    """
    Load animation from Lottie URL
    """
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

def setup_page_style():
    """
    Set up an enhanced, compact, and user-friendly page style with modern CSS.
    """
    st.markdown("""
    <style>
        /* Main styling */
        .main {
            background: linear-gradient(to bottom, #f8fafc, #eff6ff);
            font-family: 'Inter', sans-serif;
            max-width: 1000px; /* Reduced max-width for compactness */
            margin: 0 auto;
            padding: 1.5rem;
            line-height: 1.5;
            border-radius: 20px;
        }
        
        /* Card styling */
        .css-1r6slb0, .css-12oz5g7 {
            background: white;
            border-radius: 12px;
            padding: 20px; /* Reduced padding for compactness */
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.06);
            margin-bottom: 16px; /* Reduced margin */
            border: 1px solid #e5e7eb;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        
        .css-1r6slb0:hover, .css-12oz5g7:hover {
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
            transform: translateY(-3px);
        }
        
        /* Header styling */
        h1 {
            color: #1e3a8a;
            font-weight: 700;
            font-size: 2.2rem; /* Slightly smaller for compactness */
            margin-bottom: 1rem;
            letter-spacing: -0.3px;
        }
        
        h2 {
            color: #2563eb;
            font-weight: 600;
            font-size: 1.6rem;
            margin: 1.5rem 0 0.8rem;
        }
        
        h3 {
            color: #3b82f6;
            font-weight: 600;
            font-size: 1.2rem;
            margin: 1rem 0 0.5rem;
        }
        
        /* Button styling */
        .stButton>button {
            background: linear-gradient(135deg, #4f46e5, #7c3aed);
            color: white;
            border-radius: 10px;
            border: none;
            padding: 10px 24px; /* Slightly smaller padding */
            font-weight: 600;
            font-size: 0.95rem;
            transition: all 0.3s ease;
            width: 100%;
            max-width: 250px; /* Reduced max-width */
            cursor: pointer;
        }
        
        .stButton>button:hover {
            background: linear-gradient(135deg, #3b82f6, #1e40af);
            box-shadow: 0 6px 12px rgba(59, 130, 246, 0.3);
            transform: translateY(-2px);
        }
        
        /* Checkbox styling */
        .stCheckbox>div>div>div {
            background-color: #4f46e5 !important;
            border-radius: 4px;
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            background: linear-gradient(180deg, #1e40af, #3b82f6);
            padding: 1.5rem 1rem; /* Reduced padding */
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        
        .css-1d391kg .sidebar-content {
            background: transparent;
        }
        
        .css-1d391kg div[data-testid="stSidebarNav"] li div a {
            color: white;
            font-weight: 500;
            padding: 0.6rem 1rem;
            border-radius: 6px;
            transition: all 0.2s ease;
        }
        
        .css-1d391kg div[data-testid="stSidebarNav"] li div a:hover {
            background: rgba(255, 255, 255, 0.15);
            transform: scale(1.02);
        }
        
        /* Hide default elements */
        #MainMenu, footer {
            visibility: hidden;
        }
        
        /* Header banner */
        .header-banner {
            background: linear-gradient(135deg, #1e40af, #4f46e5);
            color: white;
            padding: 3rem; /* Reduced padding */
            border-radius: 12px;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
            position: relative;
            overflow: hidden;
        }
        
        .header-banner::before {
            content: "";
            position: absolute;
            top: 0;
            right: 0;
            bottom: 0;
            left: 0;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 70%);
            opacity: 0.3;
        }
        
        .header-text {
            margin-left: 16px;
            font-size: 2rem; /* Slightly smaller */
            font-weight: 700;
            letter-spacing: -0.4px;
            z-index: 1;
        }
        
        /* Success message */
        .success-msg {
            background: #dcfce7;
            color: #166534;
            padding: 12px 16px; /* More compact */
            border-radius: 10px;
            border-left: 5px solid #166534;
            margin: 1rem auto; /* Centered with reduced margin */
            max-width: 600px; /* Fixed width for better control */
            display: flex;
            align-items: center;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
            animation: slideIn 0.3s ease;
        }
        
        .success-msg::before {
            content: "✓";
            font-size: 1.2rem;
            margin-right: 10px;
            font-weight: bold;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        /* Camera frame */
        .camera-frame {
            border-radius: 12px;
            overflow: hidden;
            border: 3px solid #4f46e5;
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
            margin: 1rem 0; /* Reduced margin */
            transition: border-color 0.3s ease;
        }
        
        .camera-frame:hover {
            border-color: #7c3aed;
        }
        
        /* Table styling */
        .dataframe {
            border-collapse: separate;
            border-spacing: 0;
            width: 100%;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.06);
            margin: 1rem 0;
        }
        
        .dataframe th {
            background: linear-gradient(135deg, #1e40af, #4f46e5);
            color: white;
            padding: 12px 14px; /* More compact */
            font-weight: 600;
            font-size: 0.95rem;
        }
        
        .dataframe td {
            padding: 10px 14px;
            border-bottom: 1px solid #e5e7eb;
            font-size: 0.9rem;
        }
        
        .dataframe tr:nth-child(even) {
            background: #f9fafb;
        }
        
        .dataframe tr:hover {
            background: #dbeafe;
            transition: background 0.2s ease;
        }
        
        /* Spacing and layout */
        .block-container {
            padding: 1.5rem 0; /* Reduced padding */
            max-width: 1000px;
        }
        
        /* Input fields */
        .stTextInput > div > div > input {
            border-radius: 6px;
            border: 1px solid #d1d5db;
            padding: 10px; /* More compact */
            font-size: 0.95rem;
            transition: all 0.2s ease;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #4f46e5;
            box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2);
        }
        
        /* Divider */
        hr {
            margin: 1.5rem 0; /* Reduced margin */
            border: 0;
            height: 1px;
            background: linear-gradient(to right, transparent, #d1d5db 50%, transparent);
        }
        
        /* Info container */
        .info-container {
            background: #eff6ff;
            border-radius: 10px;
            padding: 16px; /* More compact */
            margin: 1rem 0;
            border-left: 5px solid #3b82f6;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
        }
        
        /* Responsive layout */
        @media (max-width: 768px) {
            .main {
                padding: 1rem;
            }
            .header-banner {
                padding: 1.2rem;
                flex-direction: column;
                text-align: center;
            }
            .header-text {
                margin: 10px 0 0;
                font-size: 1.6rem;
            }
            .stButton>button {
                max-width: 100%;
            }
            .success-msg {
                max-width: 90%;
            }
        }
    </style>
    """, unsafe_allow_html=True)


def create_header():
    """
    Create a modern and professional header for the app.
    """
    st.markdown("""
    <div class="header-banner">
        <img src="https://img.icons8.com/fluent/64/000000/face-id.png" alt="face recognition">
        <div class="header-text">Advanced Face Recognition Attendance System</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Add a brief description below the header
    st.markdown("""
    <p style="font-size: 1.1rem; color: #4b5563; margin-bottom: 2rem; line-height: 1.6;">
        An intelligent system that uses facial recognition technology to accurately track attendance
        and provide real-time insights for educational institutions and organizations.
    </p>
    """, unsafe_allow_html=True)

def create_home_page(col1):
    import streamlit as st
    import requests
    from streamlit_lottie import st_lottie
    
    # Add the load_lottieurl function directly to avoid the import error
    def load_lottieurl(url):
        """
        Loads a Lottie animation from a URL
        """
        try:
            r = requests.get(url)
            if r.status_code != 200:
                return None
            return r.json()
        except Exception:
            return None
    
    # Header section with title and subtitle
    st.markdown("""
    <div class="header-banner">
        <img src="https://img.icons8.com/fluent/64/000000/face-id.png" alt="face recognition">
        <div class="header-text">Advanced facial recognition with liveness detection</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Banner section with animation and key features
    col_animation, col_features = st.columns([1, 1])
    
    with col_animation:
        # Try primary animation
        lottie_face = load_lottieurl("https://assets2.lottiefiles.com/packages/lf20_26ewjiZ.json")
        
        # Fallback options with multiple alternatives
        if lottie_face is None:
            lottie_face = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_xyadoh9h.json")
        if lottie_face is None:
            lottie_face = load_lottieurl("https://assets3.lottiefiles.com/packages/lf20_jtbfg2nb.json")
            
        # Display animation or fallback image
        if lottie_face is not None:
            st_lottie(lottie_face, height=320, key="face_animation")
        else:
            st.image("https://img.icons8.com/fluent/96/000000/face-id.png", width=200)
            st.caption("Animation could not be loaded")
    
    with col_features:
        st.markdown("""
        <div style="background-color: #f8fafc; padding: 25px; border-radius: 12px; height: 100%;">
            <h2 style="color: #1e3a8a; margin-bottom: 20px;">Advanced Features</h2>
            <ul style="list-style-type: none; padding-left: 0;">
                <li style="margin-bottom: 12px; display: flex; align-items: center;">
                    <span style="background-color: #bfdbfe; border-radius: 50%; width: 24px; height: 24px; display: inline-flex; justify-content: center; align-items: center; margin-right: 10px;">✓</span>
                    <span style="font-weight: 500; color: #334155;">Contactless Attendance Tracking</span>
                </li>
                <li style="margin-bottom: 12px; display: flex; align-items: center;">
                    <span style="background-color: #bfdbfe; border-radius: 50%; width: 24px; height: 24px; display: inline-flex; justify-content: center; align-items: center; margin-right: 10px;">✓</span>
                    <span style="font-weight: 500; color: #334155;">Real-time Facial Recognition</span>
                </li>
                <li style="margin-bottom: 12px; display: flex; align-items: center;">
                    <span style="background-color: #bfdbfe; border-radius: 50%; width: 24px; height: 24px; display: inline-flex; justify-content: center; align-items: center; margin-right: 10px;">✓</span>
                    <span style="font-weight: 500; color: #334155;"><b>NEW:</b> Blink Detection</span>
                </li>
                <li style="margin-bottom: 12px; display: flex; align-items: center;">
                    <span style="background-color: #bfdbfe; border-radius: 50%; width: 24px; height: 24px; display: inline-flex; justify-content: center; align-items: center; margin-right: 10px;">✓</span>
                    <span style="font-weight: 500; color: #334155;"><b>NEW:</b> Liveness Detection</span>
                </li>
                <li style="margin-bottom: 12px; display: flex; align-items: center;">
                    <span style="background-color: #bfdbfe; border-radius: 50%; width: 24px; height: 24px; display: inline-flex; justify-content: center; align-items: center; margin-right: 10px;">✓</span>
                    <span style="font-weight: 500; color: #334155;">Comprehensive Attendance Reports</span>
                </li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Separator
    st.markdown("<hr style='margin: 30px 0; border-color: #e2e8f0;'>", unsafe_allow_html=True)
    
    # What's New section
    st.markdown("""
    <div style="text-align: center; margin-bottom: 25px;">
        <h2 style="color: #1e3a8a;">What's New</h2>
    </div>
    """, unsafe_allow_html=True)
    
    new_features_col1, new_features_col2 = st.columns(2)
    
    with new_features_col1:
        st.markdown(format_info_card(
            "Blink Detection", 
            "Our system now verifies user presence through natural blink detection, adding an extra layer of security against photo-based spoofing attempts."
        ), unsafe_allow_html=True)
    
    with new_features_col2:
        st.markdown(format_info_card(
            "Liveness Detection", 
            "Advanced algorithms verify that a real person is present, preventing fraudulent attendance through photos or video recordings."
        ), unsafe_allow_html=True)
    
    # Getting Started section
    st.markdown("""
    <div style="text-align: center; margin: 40px 0 30px 0;">
        <h2 style="color: #1e3a8a;">Getting Started</h2>
        <p style="color: #64748b; margin-bottom: 25px;">Choose an option below or use the sidebar for navigation</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Action cards in three columns
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(to bottom right, #dbeafe, #bfdbfe); padding: 20px; border-radius: 10px; text-align: center; height: 100%; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">
            <img src="https://img.icons8.com/fluent/48/000000/add-user-male.png" style="margin-bottom: 15px;">
            <h3 style="font-size: 18px; color: #1e3a8a;">Register</h3>
            <p style="color: #334155;">Add yourself to the system with facial enrollment</p>
            <div style="background-color: rgba(255, 255, 255, 0.5); border-radius: 5px; padding: 5px; margin-top: 10px; display: inline-block;">
                <span style="color: #2563eb; font-weight: 500;">Quick Setup</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(to bottom right, #e0f2fe, #bfdbfe); padding: 20px; border-radius: 10px; text-align: center; height: 100%; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">
            <img src="https://img.icons8.com/fluent/48/000000/attendance.png" style="margin-bottom: 15px;">
            <h3 style="font-size: 18px; color: #1e3a8a;">Mark Attendance</h3>
            <p style="color: #334155;">Scan your face with liveness verification</p>
            <div style="background-color: rgba(255, 255, 255, 0.5); border-radius: 5px; padding: 5px; margin-top: 10px; display: inline-block;">
                <span style="color: #2563eb; font-weight: 500;">Daily Use</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="background: linear-gradient(to bottom right, #dbeafe, #bfdbfe); padding: 20px; border-radius: 10px; text-align: center; height: 100%; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">
            <img src="https://img.icons8.com/fluent/48/000000/document.png" style="margin-bottom: 15px;">
            <h3 style="font-size: 18px; color: #1e3a8a;">View Reports</h3>
            <p style="color: #334155;">Access detailed attendance analytics</p>
            <div style="background-color: rgba(255, 255, 255, 0.5); border-radius: 5px; padding: 5px; margin-top: 10px; display: inline-block;">
                <span style="color: #2563eb; font-weight: 500;">Management</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # System stats or testimonial section (optional)
    st.markdown("<hr style='margin: 30px 0; border-color: #e2e8f0;'>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background-color: #f1f5f9; padding: 20px; border-radius: 10px; margin-top: 20px; text-align: center;">
        <h3 style="color: #1e3a8a; margin-bottom: 15px;">Why Choose Our System?</h3>
        <div style="display: flex; justify-content: space-around; flex-wrap: wrap;">
            <div style="padding: 10px; min-width: 150px;">
                <h2 style="color: #2563eb; font-size: 2rem; margin-bottom: 5px;">99.7%</h2>
                <p style="color: #64748b;">Recognition Accuracy</p>
            </div>
            <div style="padding: 10px; min-width: 150px;">
                <h2 style="color: #2563eb; font-size: 2rem; margin-bottom: 5px;">0.5s</h2>
                <p style="color: #64748b;">Recognition Speed</p>
            </div>
            <div style="padding: 10px; min-width: 150px;">
                <h2 style="color: #2563eb; font-size: 2rem; margin-bottom: 5px;">100%</h2>
                <p style="color: #64748b;">Contactless Operation</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def format_info_card(title, content):
    """
    Create a styled info card
    """
    return f"""
    <div style="background-color: #f8fafc; padding: 20px; border-radius: 10px; margin-bottom: 15px; border-left: 5px solid #3b82f6; height: 100%; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);">
        <h3 style="color: #1e3a8a; margin-top: 0; font-size: 18px;">{title}</h3>
        <p style="color: #475569;">{content}</p>
    </div>
    """

def create_know_more_page():
    """
    Create an enhanced know more page with styled instructions
    """
    create_header()
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 30px;">
        <h1>How to Use This System</h1>
        <p style="font-size: 18px; color: #4b5563;">Follow these simple steps to get started with our attendance system</p>
    </div>
    """, unsafe_allow_html=True)
    
    instructions = [
        {
            "title": "1. Getting Started",
            "content": "On the HOME page, you'll find a sidebar menu that helps you navigate to other pages. Select the option that matches what you want to do."
        },
        {
            "title": "2. Registration",
            "content": "First, go to the REGISTER page. Upload a clear photo of your face. Make sure to name the file with your name exactly as you want it to appear in the attendance sheet."
        },
        {
            "title": "3. Mark Your Attendance",
            "content": "Navigate to the MARK ATTENDANCE page and click the 'MARK YOUR PRESENCE' button to activate your camera. Wait until the system recognizes your face - you'll see a green box with your name. If you see 'Unknown', you need to register first or upload a clearer image."
        },
        {
            "title": "4. View Attendance Records",
            "content": "Click on the ATTENDANCE SHEET page to view your attendance records. Please don't modify the NAME and TIME fields in the CSV file if you're running the system locally."
        },
        {
            "title": "5. Important Note",
            "content": "This system is currently designed for one-time use per session. To take attendance again, you'll need to clear previous data and store it in another sheet."
        },
        {
            "title": "Coming Soon",
            "content": "We're working on adding check-in/check-out functionality to measure attendance duration, along with a login system to view attendance sheets."
        }
    ]
    
    for instruction in instructions:
        st.markdown(format_info_card(instruction["title"], instruction["content"]), unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background-color: #dcfce7; padding: 20px; border-radius: 8px; text-align: center; margin-top: 30px;">
        <h2 style="color: #166534; margin-top: 0;">Thank you for using our Attendance System!</h2>
        <p>We hope it helps you track attendance efficiently</p>
    </div>
    """, unsafe_allow_html=True)