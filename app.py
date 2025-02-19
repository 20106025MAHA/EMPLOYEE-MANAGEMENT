from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'employee_management'
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except Error as e:
        print(f"Database connection error: {e}")
        return None

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        
        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500

        try:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO employees (name, email, password, role) VALUES (%s, %s, %s, %s)',
                           (name, email, password, role))
            conn.commit()
        except Error as e:
            return jsonify({"error": f"Database error: {e}"}), 500
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT * FROM employees WHERE email = %s AND password = %s', (email, password))
            employee = cursor.fetchone()
        except Error as e:
            return jsonify({"error": f"Database error: {e}"}), 500
        finally:
            cursor.close()
            conn.close()

        if employee:
            session['employee_id'] = employee['id']
            session['role'] = employee['role']
            return redirect(url_for('admin' if employee['role'] == 'admin' else 'profile'))
        else:
            return jsonify({"error": "Invalid credentials"}), 401
    return render_template('login.html')

@app.route('/profile')
def profile():
    if 'employee_id' in session:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT * FROM employees WHERE id = %s', (session['employee_id'],))
            employee = cursor.fetchone()
        except Error as e:
            return jsonify({"error": f"Database error: {e}"}), 500
        finally:
            cursor.close()
            conn.close()
        
        return render_template('profile.html', employee=employee)
    return redirect(url_for('login'))

@app.route('/admin')
def admin():
    if 'employee_id' in session and session['role'] == 'admin':
        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT * FROM employees')
            employees = cursor.fetchall()
        except Error as e:
            return jsonify({"error": f"Database error: {e}"}), 500
        finally:
            cursor.close()
            conn.close()
        
        return render_template('admin.html', employees=employees)
    return redirect(url_for('login'))

@app.route('/admin/update/<int:employee_id>', methods=['GET', 'POST'])
def update_employee(employee_id):
    if 'employee_id' in session and session['role'] == 'admin':
        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        
        if request.method == 'POST':
            name = request.form.get('name')
            email = request.form.get('email')
            role = request.form.get('role')
            
            try:
                cursor = conn.cursor()
                cursor.execute('UPDATE employees SET name = %s, email = %s, role = %s WHERE id = %s',
                               (name, email, role, employee_id))
                conn.commit()
            except Error as e:
                return jsonify({"error": f"Database error: {e}"}), 500
            finally:
                cursor.close()
                conn.close()
            
            return redirect(url_for('admin'))
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT * FROM employees WHERE id = %s', (employee_id,))
            employee = cursor.fetchone()
        except Error as e:
            return jsonify({"error": f"Database error: {e}"}), 500
        finally:
            cursor.close()
            conn.close()
        
        return render_template('update_employee.html', employee=employee)
    return redirect(url_for('login'))

@app.route('/admin/delete/<int:employee_id>', methods=['POST'])
def delete_employee(employee_id):
    if 'employee_id' in session and session['role'] == 'admin':
        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM employees WHERE id = %s', (employee_id,))
            conn.commit()
        except Error as e:
            return jsonify({"error": f"Database error: {e}"}), 500
        finally:
            cursor.close()
            conn.close()
        
        return redirect(url_for('admin'))
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('employee_id', None)
    session.pop('role', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
