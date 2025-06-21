import os
from textwrap import dedent
import os
from flask import Flask, render_template, request, redirect, session, send_file
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'kharcha_secret'

DATA_FILE = 'data/expenses.csv'
USER_FILE = 'data/users.csv'

os.makedirs('data', exist_ok=True)
if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=['Date', 'Amount', 'Reason', 'Category', 'User']).to_csv(DATA_FILE, index=False)
if not os.path.exists(USER_FILE):
    pd.DataFrame(columns=['username', 'password_hash', 'salary']).to_csv(USER_FILE, index=False)

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
        users = pd.read_csv(USER_FILE)
        if username in users['username'].values:
            return "Username already exists"
        new_user = pd.DataFrame([{
            'username': username,
            'password_hash': generate_password_hash(password),
            'salary': salary
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
    for cat in ['Need', 'Want', 'Saving']:
        summary.setdefault(cat, 0)

    # Daily trend graph
    daily = user_expenses.groupby('Date')['Amount'].sum().reset_index()
    fig1 = go.Figure([go.Scatter(x=daily['Date'], y=daily['Amount'], mode='lines+markers', name='Spending')])
    fig1.update_layout(title='Daily Spending Trend', xaxis_title='Date', yaxis_title='Amount (₹)', height=300)
    graph1 = pio.to_html(fig1, full_html=False)

    # 50-30-20 graph
    users = pd.read_csv(USER_FILE)
    salary = float(users[users['username'] == user]['salary'].values[0])
    totals = {
        'Need': summary.get('Need', 0),
        'Want': summary.get('Want', 0),
        'Saving': summary.get('Saving', 0)
    }
    ideal = {
        'Need': salary * 0.5,
        'Want': salary * 0.3,
        'Saving': salary * 0.2
    }
    df = pd.DataFrame({'Category': ['Need', 'Want', 'Saving']})
    df['Actual'] = df['Category'].map(totals)
    df['Ideal'] = df['Category'].map(ideal)

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=df['Category'], y=df['Actual'], name='Actual', marker_color='blue'))
    fig2.add_trace(go.Bar(x=df['Category'], y=df['Ideal'], name='Ideal (50-30-20)', marker_color='green'))
    fig2.update_layout(title='50-30-20 Budget Comparison', barmode='group', height=300)
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

@app.route('/favicon.ico')
def favicon():
    return redirect('/static/favicon.ico')


if __name__ == '__main__':
    app.run(debug=True)