import streamlit as st
import requests
import time
import io
import base64
from auth import login_user, is_admin, save_login_email

st.set_page_config(page_title="Script Checker", layout="centered")
st.title("🎬 Hoichoi Script Checker")

# Define functions first
def send_request(webhook_url, files=None, data=None, json_data=None, raw_data=None, headers=None):
    """Send request to webhook with different methods"""
    try:
        if files and data:
            # Method 1: Multipart form data
            response = requests.post(
                webhook_url,
                files=files,
                data=data,
                timeout=120
            )
        elif json_data:
            # Method 2: JSON data
            response = requests.post(
                webhook_url,
                json=json_data,
                headers={'Content-Type': 'application/json'},
                timeout=120
            )
        elif raw_data and headers:
            # Method 3: Raw binary data
            response = requests.post(
                webhook_url,
                data=raw_data,
                headers=headers,
                timeout=120
            )
        else:
            st.error("Invalid request configuration")
            return False

        if response.status_code == 200:
            try:
                result = response.json()
                status = result.get("status", "Unknown")
                message = result.get("message", "")
                document_url = result.get("document_url", "")
                document_id = result.get("document_id", "")

                st.success("✅ Script submitted successfully!")
                
                # Make Google Doc link VERY prominent
                if document_url:
                    st.markdown("---")
                    st.markdown("### 📄 Your Script Review Document")
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(90deg, #4CAF50, #45a049);
                        padding: 20px;
                        border-radius: 10px;
                        text-align: center;
                        margin: 20px 0;
                    ">
                        <h2 style="color: white; margin: 0;">
                            <a href="{document_url}" target="_blank" style="
                                color: white;
                                text-decoration: none;
                                font-size: 24px;
                                font-weight: bold;
                            ">
                                🚀 Open Google Doc →
                            </a>
                        </h2>
                        <p style="color: #e8f5e8; margin: 10px 0 0 0; font-size: 14px;">
                            Click to view your script analysis and feedback
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown("---")

                # Show basic info in a clean way
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"**Script:** {json_data.get('project_title') if json_data else data.get('project_title') if data else 'Unknown'}")
                with col2:
                    st.info(f"**Status:** {status}")
                
                if message:
                    st.success(f"📝 {message}")

                return True

            except ValueError as json_error:
                st.success("✅ Script submitted successfully!")
                st.info("Processing in background...")
                return True
                
        else:
            st.error(f"❌ Submission failed. Please try again or contact support.")
            
            # Only show debug info if advanced options are enabled
            if st.session_state.get('show_debug', False):
                st.text("Debug Info:")
                st.code(f"Status: {response.status_code}\nResponse: {response.text[:200]}...")
            
            return False

    except requests.exceptions.Timeout:
        st.error("❌ Request timed out. The file might be too large or the server is slow.")
        return False
    except requests.exceptions.ConnectionError:
        st.error("❌ Connection error. Please check your internet connection.")
        return False
    except Exception as e:
        st.error("❌ Failed to submit the script. Please try again.")
        if st.session_state.get('show_debug', False):
            st.exception(e)
        return False

def test_webhook_connection(webhook_url):
    """Test basic webhook connectivity"""
    st.write("🔍 **Testing Webhook Connection...**")
    
    try:
        # Test with minimal data
        test_data = {"test": "connection", "timestamp": str(time.time())}
        test_response = requests.post(webhook_url, json=test_data, timeout=10)
        
        st.write(f"**Test Results:**")
        st.write(f"- Status: {test_response.status_code}")
        st.write(f"- Response: {test_response.text[:200]}...")
        
    except Exception as e:
        st.error(f"Connection test failed: {e}")

def generate_test_payload(script_title, uploaded_file):
    """Generate test payloads for debugging"""
    st.write("🔍 **Generated Test Payloads:**")
    
    if uploaded_file:
        file_content = uploaded_file.getvalue()
        file_base64 = base64.b64encode(file_content).decode('utf-8')
        
        st.code(f"""
# Multipart Form Data Structure:
files = {{
    "script_file": ("{uploaded_file.name}", {len(file_content)} bytes, "{uploaded_file.type}")
}}
data = {{
    "project_title": "{script_title}",
    "environment": "test",
    "filename": "{uploaded_file.name}"
}}
        """)


# --- Login Section ---
if "email" not in st.session_state:
    st.subheader("🔐 Login with your Hoichoi Email")
    email = st.text_input("Email", "")

    if st.button("Login"):
        if login_user(email):
            st.session_state.email = email
            save_login_email(email)
            st.success("Logged in successfully!")
            st.rerun()
        else:
            st.error("Only @hoichoi.tv emails are allowed to login.")
else:
    st.success(f"👋 Welcome, {st.session_state.email}")

    # --- Admin Panel ---
    if is_admin(st.session_state.email):
        with st.expander("🛠️ Admin Panel - Login History"):
            try:
                with open("storage.json", "r") as f:
                    import json
                    emails = json.loads(f.read())
                st.write("Users who have logged in:")
                st.table(emails)
            except Exception as e:
                st.error("Couldn't load login data.")
                if st.session_state.get('show_debug', False):
                    st.exception(e)

    # --- Script Upload Section ---
    st.subheader("📤 Upload Script for Review")

    script_title = st.text_input("Script Title", "", help="Enter a descriptive title for your script")
    uploaded_file = st.file_uploader(
        "Upload Script File", 
        type=["pdf", "docx"],
        help="Supported formats: PDF and Word documents"
    )
    
    col1, col2 = st.columns([2, 1])
    with col1:
        environment = st.selectbox("Environment", ["production", "test"], help="Use 'test' for debugging")
    with col2:
        upload_method = st.selectbox(
            "Upload Method",
            ["Standard", "Base64", "Binary"],
            help="Try different methods if upload fails"
        )

    if st.button("🚀 Submit Script", type="primary"):
        if not script_title or not uploaded_file:
            st.warning("⚠️ Please provide a script title and upload your script file.")
        else:
            # Map display names to internal names
            method_map = {
                "Standard": "Method 1: Standard Multipart",
                "Base64": "Method 2: Base64 Encoded", 
                "Binary": "Method 3: Raw Binary"
            }
            upload_method = method_map[upload_method]
            
            webhook_url = {
                "production": "https://hoichoi.app.n8n.cloud/webhook/scriptchecker",
                "test": "https://hoichoi.app.n8n.cloud/webhook-test/scriptchecker"
            }[environment]

            with st.spinner("⏳ Processing your script..."):
                # Reset file pointer to beginning
                uploaded_file.seek(0)
                file_content = uploaded_file.getvalue()
                
                success = False
                
                # Method 1: Standard Multipart (Original)
                if upload_method == "Method 1: Standard Multipart":
                    files = {
                        "script_file": (
                            uploaded_file.name,
                            file_content,
                            uploaded_file.type or "application/octet-stream"
                        )
                    }
                    
                    data = {
                        "project_title": script_title,
                        "environment": environment,
                        "user_email": st.session_state.email,
                        "filename": uploaded_file.name,
                        "file_size": str(len(file_content)),
                        "mime_type": uploaded_file.type or "application/octet-stream"
                    }
                    
                    success = send_request(webhook_url, files=files, data=data)
                
                # Method 2: Base64 Encoded
                elif upload_method == "Method 2: Base64 Encoded":
                    # Encode file as base64
                    file_base64 = base64.b64encode(file_content).decode('utf-8')
                    
                    data = {
                        "project_title": script_title,
                        "environment": environment,
                        "user_email": st.session_state.email,
                        "filename": uploaded_file.name,
                        "file_size": str(len(file_content)),
                        "mime_type": uploaded_file.type or "application/octet-stream",
                        "file_data": file_base64,
                        "encoding": "base64"
                    }
                    
                    success = send_request(webhook_url, json_data=data)
                
                # Method 3: Raw Binary
                elif upload_method == "Method 3: Raw Binary":
                    headers = {
                        'Content-Type': uploaded_file.type or 'application/octet-stream',
                        'X-Project-Title': script_title,
                        'X-Environment': environment,
                        'X-User-Email': st.session_state.email,
                        'X-Filename': uploaded_file.name,
                        'X-File-Size': str(len(file_content))
                    }
                    
                    success = send_request(webhook_url, raw_data=file_content, headers=headers)

    # --- Advanced Debug Section (Collapsed by default) ---
    with st.expander("🔧 Advanced Debug Options"):
        if st.checkbox("Enable Debug Mode"):
            st.session_state.show_debug = True
        else:
            st.session_state.show_debug = False
            
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Test Connection"):
                webhook_url = {
                    "production": "https://hoichoi.app.n8n.cloud/webhook/scriptchecker",
                    "test": "https://hoichoi.app.n8n.cloud/webhook-test/scriptchecker"
                }[environment]
                test_webhook_connection(webhook_url)
        
        with col2:
            if st.button("Generate Payload"):
                if uploaded_file:
                    generate_test_payload(script_title, uploaded_file)
                else:
                    st.warning("Please upload a file first")

    # --- Logout Button ---
    st.markdown("---")
    if st.button("Logout"):
        del st.session_state["email"]
        st.rerun()