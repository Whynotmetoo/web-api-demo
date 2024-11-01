from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import bcrypt

app = Flask(__name__)
app.secret_key = 'inventory_secret_key'

# MySQL configurations
app.config['MYSQL_HOST'] = 'inventory-db.mysql.database.azure.com'
app.config['MYSQL_USER'] = 'inventory_user'
app.config['MYSQL_PASSWORD'] = 'management_key'
app.config['MYSQL_DB'] = 'inventory_db'

mysql = MySQL(app)

def create_database_and_table():
    cursor = mysql.connection.cursor()
    
    cursor.execute("CREATE DATABASE IF NOT EXISTS inventory_db")
    
    cursor.execute("USE inventory_db")
    
    #create products table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            quantity INT DEFAULT 0,
            price DECIMAL(10, 2) DEFAULT 0.00
        )
    """)
    
    #create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL
        )
    """)
    
    cursor.close()

with app.app_context():
    create_database_and_table()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not username or not password:
            flash("Username and password cannot be empty", "error")
            return redirect(url_for('login'))
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            session['username'] = username
            return redirect(url_for('index'))
        else:
            flash("Invalid username or password", "error")
            return redirect(url_for('login'))
    return render_template('login.html')

# sign up page and request
@app.route('/signup', methods=['GET', 'POST'])
def to_signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not username or not password:
            flash("Username and password cannot be empty", "error")
            return redirect(url_for('to_signup'))
        
        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
            mysql.connection.commit()
            flash("Sign up successful, please log in", "success")
            return redirect(url_for('login'))
        except Exception as e:
            flash("Username already exists", "error")
            return redirect(url_for('to_signup'))
    return render_template('signup.html')

# Route to display inventory
@app.route('/main')
@login_required
def index():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    return render_template('index.html', products=products)

# Route to add a new product
@app.route('/add', methods=['POST'])
@login_required
def add_product():
    name = request.form['name']
    description = request.form['description']
    quantity = request.form['quantity']
    price = request.form['price']
    
    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO products (name, description, quantity, price) VALUES (%s, %s, %s, %s)", 
                   (name, description, quantity, price))
    mysql.connection.commit()
    flash("Product added successfully")
    return redirect(url_for('index'))

# Route to delete a product
@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_product(id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM products WHERE id = %s", (id,))
    mysql.connection.commit()
    flash("Product deleted successfully")
    return redirect(url_for('index'))

# Route to update product details
@app.route('/update/<int:id>', methods=['POST'])
@login_required
def update_product(id):
    name = request.form['name']
    description = request.form['description']
    quantity = request.form['quantity']
    price = request.form['price']
    
    cursor = mysql.connection.cursor()
    cursor.execute("""
        UPDATE products 
        SET name = %s, description = %s, quantity = %s, price = %s 
        WHERE id = %s
        """, (name, description, quantity, price, id))
    mysql.connection.commit()
    flash("Product updated successfully")
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=False)
