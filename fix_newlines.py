import re

with open('app.py', 'r') as f:
    content = f.read()

# Fix the specific broken f-string first
content = content.replace('f"Unhandled Exception: {str(e)}\n{traceback.format_exc()}"', 'f"Unhandled Exception: {str(e)}\\n{traceback.format_exc()}"')

with open('app.py', 'w') as f:
    f.write(content)
