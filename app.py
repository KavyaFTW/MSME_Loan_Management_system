from flask import Flask,render_template, request, redirect, url_for, session, flash
import mysql.connector as ms
import datetime

def get_db_connection():
    try:
        conn = ms.connect(
            host="localhost",
            user="root",
            password="kavya123",
            database="loanify"
        )
        return conn
    except ms.Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

conn = get_db_connection()
if conn:
    print("MySQL Connection Successful")
    conn.close()
else:
    print("MySQL Connection Failed. Please check credentials and database.")

app = Flask(__name__)
app.secret_key = "kavini"

@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/login',methods=['POST'])
def login():
    
    email = request.form['email']
    password = request.form['password']
    role = request.form['role']
    
    
    conn = get_db_connection()
    if not conn:
        flash("Database connection error. Please try again later.")
        return redirect(url_for('login_page'))
    
    cursor = conn.cursor()
    
    query = "SELECT email,aadhar_no,user_type,name,user_id FROM users WHERE email = %s AND Aadhar_No = %s AND user_type = %s"    
    cursor.execute(query, (email, password, role))
    
    user = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if user:
        session['logged_in'] = True
        session['email'] = user[0]
        session['password'] = user[1]
        session['role'] = user[2]
        session['username'] = user[3]
        session['user_id'] = user[4]
        

        if session['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif session['role'] == 'lender':
            return redirect(url_for('user_dashboard'))
        elif session['role'] == 'owner':
            return redirect(url_for('user_dashboard'))

    flash('Invalid email, password, or role.')
    return redirect(url_for('login_page'))



@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('role', None)
    session.pop('email', None)
    session.pop('password', None)
    session.pop('username', None)
    session.pop('user_id', None)

    flash('You have been logged out.')
    return redirect(url_for('login_page'))



@app.route('/admin_dashboard')
def admin_dashboard():
    if 'logged_in' not in session or session.get('role') != 'admin':
        flash('You must be logged in as an admin to see this page.')
        return redirect(url_for('login_page'))
    
    active_loans_count = 0
    total_disbursed = 0
    total_collected = 0

    status_chart_data = {
        'labels': [],
        'data': []
    }
    sector_chart_data = {
        'labels': [],
        'data': []
    }
    
    conn = get_db_connection()
    if not conn:
        flash("Database connection error.")
        return render_template('admin_dashboard.html', 
                               active_loans=active_loans_count, 
                               total_disbursed=total_disbursed, 
                               total_collected=total_collected)

    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(loan_id) FROM Loans WHERE status = 'approved'")
        result = cursor.fetchone()
        if result:
            active_loans_count = result[0]

        cursor.execute("SELECT SUM(amount_requested) FROM Loans WHERE status = 'approved'")
        result = cursor.fetchone()
        if result and result[0] is not None:
            total_disbursed = float(result[0])
            
        cursor.execute("SELECT SUM(amount) FROM EMI_Schedule WHERE status = 'Paid'")
        result = cursor.fetchone()
        if result and result[0] is not None:
            total_collected = float(result[0])
        
        query_status = "SELECT status, COUNT(loan_id) FROM Loans GROUP BY status"
        cursor.execute(query_status)
        status_results = cursor.fetchall()
        
        if status_results:
            labels = []
            data = []
            for row in status_results:
                labels.append(row[0].capitalize())
                data.append(row[1])
            status_chart_data = {'labels': labels, 'data': data}
        
        query_sector = """SELECT M.Sector, COUNT(L.loan_id) FROM Loans L JOIN MSME_Profile M ON L.msme_id = M.msme_id GROUP BY M.Sector ORDER BY COUNT(L.loan_id) DESC LIMIT 7"""
        cursor.execute(query_sector)
        sector_results = cursor.fetchall()
        
        if sector_results:
            labels = []
            data = []
            for row in sector_results:
                labels.append(row[0])
                data.append(row[1])
            sector_chart_data = {'labels': labels, 'data': data}
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error fetching dashboard data: {e}")
        flash("An error occurred while fetching dashboard data.")
    
    return render_template('admin_dashboard.html', 
                           active_loans=active_loans_count, 
                           total_disbursed=total_disbursed, 
                           total_collected=total_collected,
                           status_data=status_chart_data,
                           sector_data=sector_chart_data)


@app.route('/customers')
def customers():
    if 'logged_in' not in session or session.get('role') != 'admin':
        flash('You must be logged in as an admin to see this page.')
        return redirect(url_for('login_page'))

    search_customer_id = request.args.get('customer_id', '')    
    search_owner_name = request.args.get('owner_name', '')
    search_business_name = request.args.get('business_name', '')
    search_email = request.args.get('email', '')
    search_sector = request.args.get('sector', '')


    customer_list = []
    conn = get_db_connection()
    if not conn:
        flash("Database connection error.")
        return render_template('customers.html', 
                               customers=customer_list,
                               search_owner_name=search_owner_name,
                               search_business_name=search_business_name,
                               search_email=search_email,
                               search_sector=search_sector)

    try:
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT 
                U.user_id, 
                U.Name AS owner_name, 
                M.Business_Name, 
                U.Email, 
                U.Phone, 
                M.Sector
            FROM Users U
            LEFT JOIN MSME_Profile M ON U.user_id = M.User_ID
        """
        
        where_clauses = []
        params = []
        
        where_clauses.append("U.User_type = 'owner'")

        if search_customer_id:
            where_clauses.append("U.user_id = %s")
            params.append(f"{search_customer_id}")
        
        if search_owner_name:
            where_clauses.append("U.Name LIKE %s")
            params.append(f"%{search_owner_name}%")
        
        if search_business_name:
            where_clauses.append("M.Business_Name LIKE %s")
            params.append(f"%{search_business_name}%")
            
        if search_email:
            where_clauses.append("U.Email LIKE %s")
            params.append(f"%{search_email}%")
            
        if search_sector:
            where_clauses.append("M.Sector LIKE %s")
            params.append(f"%{search_sector}%")

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
            
        query += " ORDER BY U.user_id"
        cursor.execute(query, tuple(params))
        customer_list = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error fetching customer data: {e}")
        flash(f"An error occurred while fetching customer data: {e}")
    
    return render_template('customers.html', 
                           customers=customer_list,
                           search_customer_id=search_customer_id,
                           search_owner_name=search_owner_name,
                           search_business_name=search_business_name,
                           search_email=search_email,
                           search_sector=search_sector)


@app.route('/loans')
def loans():
    if 'logged_in' not in session:
        flash('You must be logged in to see this page.')
        return redirect(url_for('login_page'))
        
    role = session.get('role')
    user_id = session.get('user_id')
    email = session.get('email')
    
    search_loan_id = request.args.get('loan_id', '')
    search_business_name = request.args.get('business_name', '')
    search_lender_name = request.args.get('lender_name', '')
    search_status = request.args.get('status', '')
    
    loan_list = []
    conn = get_db_connection()
    if not conn:
        flash("Database connection error.")
        return render_template('loans.html', loans=loan_list, 
                               search_loan_id=search_loan_id, 
                               search_business_name=search_business_name,
                               search_lender_name=search_lender_name,
                               search_status=search_status)

    try:
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT 
                L.loan_id, 
                M.Business_Name, 
                Lend.Name AS lender_name, 
                L.amount_requested, 
                L.status, 
                L.date_applied
            FROM Loans L
            JOIN MSME_Profile M ON L.msme_id = M.msme_id
            JOIN Lenders Lend ON L.lender_id = Lend.lender_id
        """
        
        where_clauses = []
        params = []
        
        if role == 'lender':
            cursor.execute("SELECT lender_id FROM Lenders WHERE Email = %s", (email,))
            lender = cursor.fetchone()
            if lender:
                where_clauses.append("L.lender_id = %s")
                params.append(lender['lender_id'])
            else:
                where_clauses.append("1=0") 
                
        elif role == 'owner':
            cursor.execute("SELECT msme_id FROM MSME_Profile WHERE User_ID = %s", (user_id,))
            msme_profiles = cursor.fetchall()
            if msme_profiles:
                msme_ids = [p['msme_id'] for p in msme_profiles]
                query_placeholder = ','.join(['%s'] * len(msme_ids))
                where_clauses.append(f"L.msme_id IN ({query_placeholder})")
                params.extend(msme_ids)
            else:
                where_clauses.append("1=0")

        if search_loan_id:
            where_clauses.append("L.loan_id = %s")
            params.append(f"{search_loan_id}")
        
        if search_business_name:
            where_clauses.append("M.Business_Name LIKE %s")
            params.append(f"%{search_business_name}%")
            
        if search_lender_name:
            where_clauses.append("Lend.Name LIKE %s")
            params.append(f"%{search_lender_name}%")
            
        if search_status:
            where_clauses.append("L.status = %s")
            params.append(search_status)
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
            
        query += " ORDER BY L.date_applied DESC"
        cursor.execute(query, tuple(params))
        loan_list = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error fetching loan data: {e}")
        flash(f"An error occurred while fetching loan data: {e}")
    
    return render_template('loans.html', 
                           loans=loan_list, 
                           search_loan_id=search_loan_id, 
                           search_business_name=search_business_name,
                           search_lender_name=search_lender_name,
                           search_status=search_status)

@app.route('/payments')
def payments():
    if 'logged_in' not in session:
        flash('You must be logged in to see this page.')
        return redirect(url_for('login_page'))
        
    role = session.get('role')
    user_id = session.get('user_id')
    email = session.get('email')
    
    search_emi_id = request.args.get('emi_id', '')
    search_loan_id = request.args.get('loan_id', '')
    search_business_name = request.args.get('business_name', '')
    search_lender_name = request.args.get('lender_name', '')
    search_status = request.args.get('status', '')
    
    payment_list = []
    conn = get_db_connection()
    if not conn:
        flash("Database connection error.")
        return render_template('payments.html', payments=payment_list,
                               search_emi_id=search_emi_id,
                               search_loan_id=search_loan_id,
                               search_business_name=search_business_name,
                               search_status=search_status)

    try:
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT 
                E.emi_id, E.loan_id,
                M.Business_Name, Lend.Name AS lender_name,
                E.amount, E.due_date, E.paid_date, E.status
            FROM EMI_Schedule E
            JOIN Loans L ON E.loan_id = L.loan_id
            JOIN MSME_Profile M ON L.msme_id = M.msme_id
            JOIN Lenders Lend ON L.lender_id = Lend.lender_id
        """
        
        where_clauses = []
        params = []
        
        if role == 'lender':
            cursor.execute("SELECT lender_id FROM Lenders WHERE Email = %s", (email,))
            lender = cursor.fetchone()
            if lender:
                where_clauses.append("L.lender_id = %s")
                params.append(lender['lender_id'])
            else:
                where_clauses.append("1=0") 
                
        elif role == 'owner':
            cursor.execute("SELECT msme_id FROM MSME_Profile WHERE User_ID = %s", (user_id,))
            msme_profiles = cursor.fetchall()
            if msme_profiles:
                msme_ids = [p['msme_id'] for p in msme_profiles]
                query_placeholder = ','.join(['%s'] * len(msme_ids))
                where_clauses.append(f"L.msme_id IN ({query_placeholder})")
                params.extend(msme_ids)
            else:
                where_clauses.append("1=0")

        if search_emi_id:
            where_clauses.append("E.emi_id = %s")
            params.append(f"{search_emi_id}")

        if search_loan_id:
            where_clauses.append("E.loan_id = %s")
            params.append(f"{search_loan_id}")
        
        if search_business_name:
            where_clauses.append("M.Business_Name LIKE %s")
            params.append(f"%{search_business_name}%")
        
        if search_lender_name:
            where_clauses.append("Lend.Name LIKE %s")
            params.append(f"%{search_lender_name}%")

        if search_status:
            where_clauses.append("E.status = %s")
            params.append(search_status)
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
            
        query += " ORDER BY E.due_date DESC"
        cursor.execute(query, tuple(params))
        payment_list = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error fetching payment data: {e}")
        flash(f"An error occurred while fetching payment data: {e}")
    
    return render_template('payments.html', 
                           payments=payment_list,
                           search_emi_id=search_emi_id,
                           search_loan_id=search_loan_id,
                           search_business_name=search_business_name,
                           search_lender_name=search_lender_name,
                           search_status=search_status)


@app.route('/admin_settings')
def admin_settings():
    if 'logged_in' not in session or session.get('role') != 'admin':
        flash('You must be logged in as an admin to see this page.')
        return redirect(url_for('login_page'))
    
    return render_template('admin_settings.html')


@app.route('/user_dashboard')
def user_dashboard():
    if 'logged_in' not in session:
        flash('You must be logged in as a user to see this page.')
        return redirect(url_for('login_page'))
    
    active_loans_count = 0
    total_disbursed = 0
    total_collected = 0
    status_chart_data = {'labels': [], 'data': []}
    
    user_id = session.get('user_id')
    email = session.get('email')
    role = session.get('role')

    conn = get_db_connection()
    if not conn:
        flash("Database connection error.")
        return render_template('user_dashboard.html', 
                                active_loans=active_loans_count, 
                                total_disbursed=total_disbursed, 
                                total_collected=total_collected,
                                status_data=status_chart_data)
    
    try:
        cursor = conn.cursor()
        
        if role == 'owner':
            query1 = "SELECT COUNT(loan_id) FROM Loans WHERE status = 'approved' and msme_id in (select msme_id from MSME_Profile where User_ID = %s)"
            cursor.execute(query1, (user_id,))
            result = cursor.fetchone()
            if result: active_loans_count = result[0]
    
            query2 = "SELECT SUM(amount_requested) FROM Loans WHERE status = 'approved' and msme_id in (select msme_id from MSME_Profile where User_ID = %s)"
            cursor.execute(query2, (user_id,))
            result = cursor.fetchone()
            if result and result[0] is not None: total_disbursed = float(result[0])
            
            query3 = "SELECT SUM(amount) FROM EMI_Schedule WHERE status = 'Paid' and loan_id in (select loan_id from Loans where msme_id in (select msme_id from MSME_Profile where User_ID = %s))"
            cursor.execute(query3, (user_id,))
            result = cursor.fetchone()
            if result and result[0] is not None: total_collected = float(result[0])
            
            query_status = "SELECT status, COUNT(loan_id) FROM Loans where msme_id in (select msme_id from MSME_Profile where User_ID = %s) GROUP BY status"
            cursor.execute(query_status, (user_id,))
            
        elif role == 'lender':
            cursor.execute("SELECT lender_id FROM Lenders WHERE Email = %s", (email,))
            lender = cursor.fetchone()
            lender_id = lender[0] if lender else -1

            query1 = "SELECT COUNT(loan_id) FROM Loans WHERE status = 'approved' AND lender_id = %s"
            cursor.execute(query1, (lender_id,))
            result = cursor.fetchone()
            if result: active_loans_count = result[0]
    
            query2 = "SELECT SUM(amount_requested) FROM Loans WHERE status = 'approved' AND lender_id = %s"
            cursor.execute(query2, (lender_id,))
            result = cursor.fetchone()
            if result and result[0] is not None: total_disbursed = float(result[0])
            
            query3 = "SELECT SUM(amount) FROM EMI_Schedule WHERE status = 'Paid' AND loan_id IN (SELECT loan_id FROM Loans WHERE lender_id = %s)"
            cursor.execute(query3, (lender_id,))
            result = cursor.fetchone()
            if result and result[0] is not None: total_collected = float(result[0])
            
            query_status = "SELECT status, COUNT(loan_id) FROM Loans WHERE lender_id = %s GROUP BY status"
            cursor.execute(query_status, (lender_id,))
        
        else:
            query_status = "SELECT 1, 0 WHERE 1=0" 
            cursor.execute(query_status)

        status_results = cursor.fetchall()
        if status_results:
            labels = []
            data = []
            for row in status_results:
                labels.append(str(row[0]).capitalize())
                data.append(row[1])
            status_chart_data = {'labels': labels, 'data': data}

    except Exception as e:
        print(f"Error fetching dashboard data: {e}")
        flash("An error occurred while fetching dashboard data.")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

    return render_template('user_dashboard.html', 
                            active_loans=active_loans_count, 
                            total_disbursed=total_disbursed, 
                            total_collected=total_collected,
                            status_data=status_chart_data)
    

@app.route('/reports')
def reports():
    if 'logged_in' not in session:
        flash('You must be logged in to see this page.')
        return redirect(url_for('login_page'))

    role = session.get('role')
    user_id = session.get('user_id')
    email = session.get('email')

    conn = get_db_connection()
    if not conn:
        flash("Database connection error.")
        
        return render_template('reports.html', status_data={}, sector_data={}, payments_data={}, disbursements_data={})

    status_data = {'labels': [], 'data': []}
    sector_data = {'labels': [], 'data': []}
    payments_over_time = {'labels': [], 'data': []}
    disbursements_over_time = {'labels': [], 'data': []}

    try:
        cursor = conn.cursor(dictionary=True)

        
        loan_where_conditions = []
        loan_params = []
        payment_where_conditions = []
        payment_params = []

        if role == 'lender':
            cursor.execute("SELECT lender_id FROM Lenders WHERE Email = %s", (email,))
            lender = cursor.fetchone()
            if lender:
                loan_where_conditions.append("L.lender_id = %s")
                loan_params.append(lender['lender_id'])
                payment_where_conditions.append("L.lender_id = %s")
                payment_params.append(lender['lender_id'])
            else:
                loan_where_conditions.append("1=0")
                payment_where_conditions.append("1=0")
        
        elif role == 'owner':
            cursor.execute("SELECT msme_id FROM MSME_Profile WHERE User_ID = %s", (user_id,))
            msme_profiles = cursor.fetchall()
            if msme_profiles:
                msme_ids = [p['msme_id'] for p in msme_profiles]
                query_placeholder = ','.join(['%s'] * len(msme_ids))
                
                loan_where_conditions.append(f"L.msme_id IN ({query_placeholder})")
                loan_params.extend(msme_ids)
                payment_where_conditions.append(f"L.msme_id IN ({query_placeholder})")
                payment_params.extend(msme_ids)
            else:
                loan_where_conditions.append("1=0")
                payment_where_conditions.append("1=0")
        
        def build_where_clause(conditions):
            if not conditions:
                return ""
            return "WHERE " + " AND ".join(conditions)

        query1_where = build_where_clause(loan_where_conditions)
        query1 = f"SELECT status, COUNT(L.loan_id) as count FROM Loans L {query1_where} GROUP BY status"
        cursor.execute(query1, tuple(loan_params))
        status_results = cursor.fetchall()
        if status_results:
            status_data['labels'] = [row['status'] for row in status_results]
            status_data['data'] = [row['count'] for row in status_results]

        query2_where = build_where_clause(loan_where_conditions)
        query2 = f"SELECT M.Sector, COUNT(L.loan_id) as count FROM Loans L LEFT JOIN MSME_Profile M ON L.msme_id = M.msme_id {query2_where} GROUP BY M.Sector"
        cursor.execute(query2, tuple(loan_params))
        sector_results = cursor.fetchall()
        if sector_results:
            sector_data['labels'] = [row['Sector'] if row['Sector'] else 'Unknown' for row in sector_results]
            sector_data['data'] = [row['count'] for row in sector_results]

        payment_conditions_q3 = payment_where_conditions + ["E.status = 'Paid'"]
        query3_where = build_where_clause(payment_conditions_q3)
        if not payment_where_conditions and payment_conditions_q3:
             query3_where = "WHERE " + " AND ".join(payment_conditions_q3)
        
        query3 = f"SELECT DATE_FORMAT(E.paid_date, '%Y-%m') as month, SUM(E.amount) as total FROM EMI_Schedule E LEFT JOIN Loans L ON E.loan_id = L.loan_id {query3_where} GROUP BY month ORDER BY month"
        cursor.execute(query3, tuple(payment_params))
        payment_results = cursor.fetchall()
        if payment_results:
            payments_over_time['labels'] = [row['month'] for row in payment_results]
            payments_over_time['data'] = [float(row['total']) for row in payment_results]
            
        loan_conditions_q4 = loan_where_conditions + ["L.status = 'approved'"]
        query4_where = build_where_clause(loan_conditions_q4)
        
        if not loan_where_conditions and loan_conditions_q4:
            query4_where = "WHERE " + " AND ".join(loan_conditions_q4)

        query4 = f"SELECT DATE_FORMAT(L.date_applied, '%Y-%m') as month, SUM(L.amount_requested) as total FROM Loans L {query4_where} GROUP BY month ORDER BY month"
        cursor.execute(query4, tuple(loan_params))
        disbursement_results = cursor.fetchall()
        if disbursement_results:
            disbursements_over_time['labels'] = [row['month'] for row in disbursement_results]
            disbursements_over_time['data'] = [float(row['total']) for row in disbursement_results]

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error fetching reports data: {e}")
        flash("An error occurred while fetching reports data.")

    return render_template('reports.html',
                           status_data=status_data,
                           sector_data=sector_data,
                           payments_data=payments_over_time,
                           disbursements_data=disbursements_over_time)

@app.route('/add_customer', methods=['GET', 'POST'])
def add_customer():
    if 'logged_in' not in session or session.get('role') != 'admin':
        flash('You do not have permission to access this page.')
        return redirect(url_for('login_page'))
    
    if request.method == 'POST':
        try:
            user_id = request.form['user_id']
            msme_id = request.form['msme_id']
            name = request.form['name']
            email = request.form['email']
            phone = request.form['phone']
            aadhar_no = request.form['aadhar_no']
            
            business_name = request.form['business_name']
            reg_no = request.form['reg_no']
            udyam_no = request.form['udyam_no']
            sector = request.form['sector']
            turnover = request.form['turnover']
            years = request.form['years']
            pan_no = request.form['pan_no']
            address = request.form['address']
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            query_user = """
                INSERT INTO Users (user_id, Name, Email, Phone, User_type, Aadhar_No) 
                VALUES (%s, %s, %s, %s, 'owner', %s)
            """
            cursor.execute(query_user, (user_id, name, email, phone, aadhar_no))
            
            query_msme = """
                INSERT INTO MSME_Profile 
                (msme_id, User_ID, Business_Name, Sector, Annual_Turnover, 
                 Years_Operating, Registration_No, Udyam_No, Business_Address, PAN_No)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query_msme, (
                msme_id, user_id, business_name, sector, turnover, 
                years, reg_no, udyam_no, address, pan_no
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('New customer and business profile created successfully!', 'success')
            return redirect(url_for('customers'))

        except ms.Error as e:
            flash(f'Database error: {e}', 'error')
            return redirect(url_for('add_customer'))
        except Exception as e:
            flash(f'Error creating customer: {e}', 'error')
            return redirect(url_for('add_customer'))

    return render_template('add_customer.html')

@app.route('/apply_loan', methods=['GET', 'POST'])
def apply_loan():
    if 'logged_in' not in session or session.get('role') != 'owner':
        flash('You must be logged in as a business owner to apply.')
        return redirect(url_for('login_page'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        try:
            loan_id = request.form['loan_id']
            msme_id = request.form['msme_id']
            lender_id = request.form['lender_id']
            amount = request.form['amount']
            duration = request.form['duration']
            today = datetime.now().date()
            
            cursor.execute("SELECT * FROM MSME_Profile WHERE msme_id = %s AND User_ID = %s", (msme_id, session['user_id']))
            if not cursor.fetchone():
                flash("You do not have permission to apply for this business.")
                return redirect(url_for('apply_loan'))
                
            query = """
                INSERT INTO Loans (loan_id, msme_id, lender_id, amount_requested, date_applied, status, duration_months)
                VALUES (%s, %s, %s, %s, %s, 'pending', %s)
            """
            cursor.execute(query, (loan_id, msme_id, lender_id, amount, today, duration))
            conn.commit()
            
            cursor.close()
            conn.close()
            flash('Loan application submitted successfully!', 'success')
            return redirect(url_for('loans'))
            
        except Exception as e:
            flash(f"Error submitting application: {e}", 'error')
            return redirect(url_for('apply_loan'))

    cursor.execute("SELECT lender_id, Name, Interest_Rate_Percent FROM Lenders")
    all_lenders = cursor.fetchall()
    
    cursor.execute("SELECT msme_id, Business_Name FROM MSME_Profile WHERE User_ID = %s", (session['user_id'],))
    user_msme_profiles = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('apply_loan.html', lenders=all_lenders, msme_profiles=user_msme_profiles)

@app.route('/add_payment', methods=['GET', 'POST'])
def add_payment():
    if 'logged_in' not in session or session.get('role') not in ('admin', 'lender'):
        flash('You do not have permission to access this page.')
        return redirect(url_for('login_page'))

    if request.method == 'POST':
        try:
            emi_id = request.form['emi_id']
            loan_id = request.form['loan_id']
            installment_no = request.form['installment_no']
            amount = request.form['amount']
            paid_date = request.form['paid_date']
            
            query = """
                INSERT INTO EMI_Schedule 
                (emi_id, loan_id, installment_no, amount, paid_date, status, due_date) 
                VALUES (%s, %s, %s, %s, %s, 'Paid', %s)
            """
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(query, (emi_id, loan_id, installment_no, amount, paid_date, paid_date))
            conn.commit()
            
            cursor.close()
            conn.close()
            
            flash('Payment recorded successfully!', 'success')
            return redirect(url_for('payments'))
            
        except Exception as e:
            flash(f"Error recording payment: {e}", 'error')
            return redirect(url_for('add_payment'))

    return render_template('add_payment.html')