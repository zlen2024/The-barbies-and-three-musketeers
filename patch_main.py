with open('frontend/src/main.jsx', 'r') as f:
    content = f.read()

import_statement = "import ErrorBoundary from './components/ErrorBoundary.jsx'\n"
content = import_statement + content

# Wrap App in ErrorBoundary
content = content.replace("<App />", "<ErrorBoundary>\n      <App />\n    </ErrorBoundary>")

with open('frontend/src/main.jsx', 'w') as f:
    f.write(content)
