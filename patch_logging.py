import re

with open('app.py', 'r') as f:
    content = f.read()

# Add logging imports
import_insert = """import os
import logging
import traceback
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, current_app"""
content = re.sub(r'import os\nfrom datetime import datetime, timedelta\nfrom flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory', import_insert, content)

# Add logging setup after app initialization
logging_setup = """
# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configure Flask to serve React build files"""
content = content.replace("# Configure Flask to serve React build files", logging_setup)

# Add before_request and errorhandler
hooks_setup = """
@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({'error': 'Unauthorized'}), 401

@app.before_request
def log_request_info():
    if request.path.startswith('/api/'):
        user_info = "Anonymous"
        if current_user.is_authenticated:
            user_info = f"User: {current_user.username} (Role: {current_user.role}, ID: {current_user.id})"
        logger.info(f"Incoming Request: {request.method} {request.path} | {user_info}")

@app.errorhandler(Exception)
def handle_exception(e):
    # Log the full stack trace
    logger.error(f"Unhandled Exception: {str(e)}\n{traceback.format_exc()}")
    # Return JSON for API routes
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'message': 'An internal server error occurred', 'error': str(e)}), 500
    # Otherwise render a generic error or just return string
    return "Internal Server Error", 500

# API: Client Logs
@app.route('/api/client-logs', methods=['POST'])
def api_client_logs():
    data = request.json or {}
    level = data.get('level', 'error').lower()
    message = data.get('message', 'Unknown client error')
    stack = data.get('stack', '')
    user_info = "Anonymous"
    if current_user.is_authenticated:
        user_info = f"User: {current_user.username} (Role: {current_user.role}, ID: {current_user.id})"

    log_msg = f"Client Log [{level.upper()}] - {user_info}: {message}"
    if stack:
        log_msg += f"\\nStack: {stack}"

    if level == 'error':
        logger.error(log_msg)
    elif level == 'warn':
        logger.warning(log_msg)
    else:
        logger.info(log_msg)

    return jsonify({'success': True})
"""
content = content.replace("""@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({'error': 'Unauthorized'}), 401""", hooks_setup)

with open('app.py', 'w') as f:
    f.write(content)
