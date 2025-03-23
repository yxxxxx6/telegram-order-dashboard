# dashboard_server.py
from flask import Flask, request, redirect, url_for, render_template_string, session, jsonify
import json, hashlib, requests

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

BOT_TOKEN = "7647010903:AAGzzofM1Tzx2Ynmn8EWNduF56wSMiEuVL8"
ORDERS_FILE = "orders.json"
USERNAME = "admin"
PASSWORD_HASH = hashlib.sha256("admin123".encode()).hexdigest()

login_page = '''
<!DOCTYPE html>
<html><head><title>Login</title></head>
<body style="font-family:sans-serif;text-align:center;margin-top:80px;">
<h2>Login to Order Dashboard</h2>
<form method="POST">
  <input name="username" placeholder="Username" required><br><br>
  <input name="password" type="password" placeholder="Password" required><br><br>
  <button type="submit">Login</button>
</form>
</body></html>
'''

dashboard_page = '''
<!DOCTYPE html>
<html><head><title>Orders</title></head>
<body style="font-family:sans-serif;padding:20px;">
<h2>Order Dashboard</h2>
<p><a href="/logout">Logout</a></p>
<table border="1" cellpadding="8" cellspacing="0">
<tr><th>ID</th><th>Name</th><th>Items</th><th>Total</th><th>Status</th><th>Actions</th></tr>
{% for order in orders %}
<tr>
<td>{{ order.order_id }}</td>
<td>{{ order.name }}</td>
<td><pre>{{ order.order }}</pre></td>
<td>${{ '%.2f' % order.total }}</td>
<td>{{ order.status }}</td>
<td>
  <form method="POST" action="/update" style="display:inline;">
    <input type="hidden" name="order_id" value="{{ order.order_id }}">
    <button name="action" value="prep">🛠</button>
    <button name="action" value="ready">✅</button>
    <button name="action" value="cancel">❌</button>
  </form>
</td>
</tr>
{% endfor %}
</table>
</body></html>
'''


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        passwd = hashlib.sha256(request.form['password'].encode()).hexdigest()
        if uname == USERNAME and passwd == PASSWORD_HASH:
            session['logged_in'] = True
            return redirect('/dashboard')
    return login_page


@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect('/')
    with open(ORDERS_FILE) as f:
        orders = json.load(f)
    return render_template_string(dashboard_page, orders=orders)


@app.route('/update', methods=['POST'])
def update():
    if not session.get('logged_in'):
        return redirect('/')

    order_id = request.form['order_id']
    action = request.form['action']
    with open(ORDERS_FILE, 'r') as f:
        orders = json.load(f)

    for order in orders:
        if order['order_id'] == order_id:
            if action == 'prep':
                order['status'] = 'Preparing'
                msg = '🛠 Your order is now being prepared.'
            elif action == 'ready':
                order['status'] = 'Ready to Collect'
                msg = '✅ Your order is ready to collect!'
            elif action == 'cancel':
                order['status'] = 'Cancelled'
                msg = '❌ Your order has been cancelled.'
            else:
                msg = None
            if msg:
                requests.get(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    params={
                        'chat_id': order['user_id'],
                        'text': msg
                    })
            break

    with open(ORDERS_FILE, 'w') as f:
        json.dump(orders, f, indent=2)

    return redirect('/dashboard')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/')


if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
