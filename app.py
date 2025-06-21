from flask import Flask, render_template, request, redirect, send_file, session
import pandas as pd
import os
from datetime import datetime
import plotly.express as px
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'supersecret'

DATA_FILE = 'data/expenses.csv'
USER_FILE = 'data/users.csv'

if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=['Date', 'Amount', 'Reason', 'Category', 'User']).to_csv(DATA_FILE, index=False)

if not os.path.exists(USER_FILE):
    pd.DataFrame(columns=['username', 'password_hash', 'salary']).to_csv(USER_FILE, index=False)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = pd.read_csv(USER_FILE)

        user_row = users[users['username'] == username]
        if not user_row.empty and check_password_hash(user_row.iloc[0]['password_hash'], password):
            session['user'] = username
            session['salary'] = user_row.iloc[0]['salary']
            return redirect('/dashboard')
        return "Invalid credentials"
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        salary = float(request.form['salary'])

        users = pd.read_csv(USER_FILE)
        if username in users['username'].values:
            return "Username already exists. Please log in."

        password_hash = generate_password_hash(password)
        new_user = pd.DataFrame([[username, password_hash, salary]], columns=['username', 'password_hash', 'salary'])
        new_user.to_csv(USER_FILE, mode='a', index=False, header=False)
        return redirect('/')
    return render_template('register.html')

@app.route('/dashboard')
def index():
    if 'user' not in session:
        return redirect('/')
    user = session['user']
    df = pd.read_csv(DATA_FILE)
    df_user = df[df['User'] == user]
    summary = df_user.groupby('Category')['Amount'].sum().to_dict()

    df_user['Month'] = pd.to_datetime(df_user['Date']).dt.strftime('%Y-%m')
    monthly_summary = df_user.groupby(['Month', 'Category'])['Amount'].sum().unstack().fillna(0).reset_index()

    fig = px.line(monthly_summary, x='Month', y=monthly_summary.columns[1:], title='Monthly Expenses')
    graph_html = fig.to_html(full_html=False)

    return render_template('index.html', summary=summary, data=df_user.tail(10), graph_html=graph_html)

@app.route('/add', methods=['POST'])
def add():
    if 'user' not in session:
        return redirect('/')
    date = request.form['date']
    amount = float(request.form['amount'])
    reason = request.form['reason']
    category = request.form['category']
    user = session['user']

    if 'rent' in reason.lower():
        category = 'Need'
    elif 'movie' in reason.lower():
        category = 'Want'

    new_data = pd.DataFrame([[date, amount, reason, category, user]],
                            columns=['Date', 'Amount', 'Reason', 'Category', 'User'])
    new_data.to_csv(DATA_FILE, mode='a', index=False, header=False)
    return redirect('/dashboard')

@app.route('/download')
def download():
    return send_file(DATA_FILE, as_attachment=True)

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('salary', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
