import os
from flask import Flask, render_template, request, redirect, session, send_file
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'kharcha_secret'

DATA_FILE = 'data/expenses.csv'
USER_FILE = 'data/users.csv'

os.makedirs('data', exist_ok=True)
if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=['Date', 'Amount', 'Reason', 'Category', 'User']).to_csv(DATA_FILE, index=False)
if not os.path.exists(USER_FILE):
    pd.DataFrame(columns=['username', 'password_hash', 'salary', 'rule']).to_csv(USER_FILE, index=False)

# Rule definitions
RULES = {
    "50-30-20": {"Need": 0.5, "Want": 0.3, "Saving": 0.2},
    "60-20-20": {"Need": 0.6, "Want": 0.2, "Saving": 0.2},
    "70-20-10": {"Need": 0.7, "Want": 0.0, "Saving": 0.2, "Giving": 0.1}
}

@app.route('/')
def home():
    if 'user' in session:
        return redirect('/dashboard')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        salary = float(request.form['salary'])
        rule = request.form['rule']
        users = pd.read_csv(USER_FILE)
        if username in users['username'].values:
            return "Username already exists"
        new_user = pd.DataFrame([{
            'username': username,
            'password_hash': generate_password_hash(password),
            'salary': salary,
            'rule': rule
        }])
        new_user.to_csv(USER_FILE, mode='a', header=not os.path.exists(USER_FILE), index=False)
        return redirect('/')
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    users = pd.read_csv(USER_FILE)
    user_row = users[users['username'] == username]
    if not user_row.empty and check_password_hash(user_row.iloc[0]['password_hash'], password):
        session['user'] = username
        return redirect('/dashboard')
    return "Invalid credentials"

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')

    user = session['user']
    expenses = pd.read_csv(DATA_FILE)
    user_expenses = expenses[expenses['User'] == user]

    summary = user_expenses.groupby('Category')['Amount'].sum().to_dict()
    for cat in ['Need', 'Want', 'Saving', 'Giving']:
        summary.setdefault(cat, 0)

    # Load user profile
    users = pd.read_csv(USER_FILE)
    user_row = users[users['username'] == user].iloc[0]
    salary = float(user_row['salary'])
    rule = user_row['rule']
    rule_split = RULES.get(rule, RULES['50-30-20'])

    # Daily trend graph
    daily = user_expenses.groupby('Date')['Amount'].sum().reset_index()
    fig1 = go.Figure([go.Scatter(x=daily['Date'], y=daily['Amount'], mode='lines+markers', name='Spending')])
    fig1.update_layout(title='Daily Spending Trend', xaxis_title='Date', yaxis_title='Amount (₹)', height=300)
    graph1 = pio.to_html(fig1, full_html=False)

    # Budget rule comparison graph
    categories = list(rule_split.keys())
    actual = [summary.get(cat, 0) for cat in categories]
    ideal = [salary * pct for pct in rule_split.values()]

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=categories, y=actual, name='Actual', marker_color='blue'))
    fig2.add_trace(go.Bar(x=categories, y=ideal, name=f'Ideal ({rule})', marker_color='green'))
    fig2.update_layout(title='Budget Comparison', barmode='group', height=300)
    graph2 = pio.to_html(fig2, full_html=False)

    return render_template('index.html', summary=summary, data=user_expenses[::-1], graph_html1=graph1, graph_html2=graph2)

@app.route('/add', methods=['POST'])
def add():
    if 'user' not in session:
        return redirect('/')
    new_data = pd.DataFrame([{
        'Date': request.form['date'],
        'Amount': float(request.form['amount']),
        'Reason': request.form['reason'],
        'Category': request.form['category'],
        'User': session['user']
    }])
    new_data.to_csv(DATA_FILE, mode='a', header=False, index=False)
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

@app.route('/download')
def download():
    if 'user' not in session:
        return redirect('/')
    df = pd.read_csv(DATA_FILE)
    user_df = df[df['User'] == session['user']]
    download_path = f"data/{session['user']}_expenses.csv"
    user_df.to_csv(download_path, index=False)
    return send_file(download_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)