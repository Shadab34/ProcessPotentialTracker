import os
import streamlit.web.bootstrap as bootstrap
import sys
import subprocess

# Check if running in Streamlit Cloud
is_cloud = 'STREAMLIT_SHARING' in os.environ or 'STREAMLIT_SERVER_PORT' in os.environ

# Set environment variables for Streamlit Cloud
os.environ['IS_STREAMLIT_CLOUD'] = 'true'

def main():
    # Print debug info
    print("Starting Streamlit app with entry_point.py")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    
    # Print environment variables for debugging
    print("Environment variables:")
    for key, value in os.environ.items():
        if key.startswith('STREAMLIT') or key == 'PORT' or key == 'IS_STREAMLIT_CLOUD':
            print(f"  {key}={value}")
    
    # Get the port from environment variable or use default
    port = int(os.environ.get('PORT', 8501))
    print(f"Using port: {port}")
    
    # Run the Streamlit app
    app_path = os.path.join(os.path.dirname(__file__), 'app.py')
    
    # Verify app file exists
    if not os.path.exists(app_path):
        print(f"ERROR: App file not found at {app_path}")
        print(f"Directory contents: {os.listdir(os.path.dirname(__file__))}")
        sys.exit(1)
    
    print(f"Running app from: {app_path}")
    
    # Run with proper flags
    args = [
        "--server.port", str(port),
        "--server.address", "0.0.0.0",
        "--server.headless", "true",
        "--server.enableCORS", "false",
        "--server.enableXsrfProtection", "false"
    ]
    
    # Bootstrap Streamlit
    bootstrap.run(app_path, '', args, flag_options={})

if __name__ == "__main__":
    main() 