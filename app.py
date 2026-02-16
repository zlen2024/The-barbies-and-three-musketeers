from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# 1. Authentication Route [cite: 49, 130]
@app.route('/')
@app.route('/login')
def login():
    # Renders the login interface [cite: 71]
    return render_template('login.html')

# 2. Main Dashboard Route [cite: 53, 133]
@app.route('/dashboard')
def dashboard():
    # Renders data visualization and product selection [cite: 75, 124]
    return render_template('dashboard.html')

# 3. Intelligent Forecasting & Reasoning Route [cite: 50, 54]
@app.route('/forecast/<sku_id>')
def forecast(sku_id):
    # This page will display the AI reasoning and "Smart Why" [cite: 123, 139]
    # It communicates with the Intelligence Layer (MCP Server) [cite: 94, 96]
    return render_template('forecasting.html', sku_id=sku_id)

# 4. Purchase Request (PR) Generation Route [cite: 51, 134]
@app.route('/generate-pr', methods=['GET', 'POST'])
def generate_pr():
    # Logic to format approved forecast into a PDF/Doc [cite: 51, 134]
    # Redirects or renders a success/download page [cite: 63]
    return render_template('pr_generator.html')

if __name__ == '__main__':
    app.run(debug=True)
