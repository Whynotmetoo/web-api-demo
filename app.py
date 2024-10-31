from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
import MySQLdb.cursors

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
    
    # 创建数据库
    cursor.execute("CREATE DATABASE IF NOT EXISTS inventory_db")
    
    # 切换到新创建的数据库
    cursor.execute("USE inventory_db")
    
    # 创建表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            quantity INT DEFAULT 0,
            price DECIMAL(10, 2) DEFAULT 0.00
        )
    """)
    
    cursor.close()

# create schema and table in the initialization session
with app.app_context():
    create_database_and_table()

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    session['username'] = username
    # if username in users and users[username] == password:
    #     session['username'] = username
    return redirect(url_for('index'))
    # return 'Login fail'

# Route to display inventory
@app.route('/main')
def index():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    return render_template('index.html', products=products)

# Route to add a new product
@app.route('/add', methods=['POST'])
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
def delete_product(id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM products WHERE id = %s", (id,))
    mysql.connection.commit()
    flash("Product deleted successfully")
    return redirect(url_for('index'))

# Route to update product details
@app.route('/update/<int:id>', methods=['POST'])
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
    app.run(debug=True)
