from flask import Flask, request, render_template ,send_file , make_response  , g , jsonify, redirect, Response, send_from_directory, session
# from pymodbus.client import ModbusTcpClient
# from pymodbus import mei_message
import threading
import time
import sqlite3
import json
import re
import base64

app = Flask(__name__)

# 🔐 Add a secret key for session handling
app.secret_key = 'a7c2c2c01871e6842c63e7ed70b7b34972157b482376f87994e392fb3c2ab8b2'  # use a secure random key!


IP="192.168.1.177"
DATABASE = 'DataBase.db'


# class MB():
#   def __init__(self, ip, port=502):
#     self.ip=ip
#     self.port=port
#     self.connect()
#   def connect(self):
#       self.client=ModbusTcpClient(self.ip, port=self.port,timeout=10)
#   def read_reg(self):
#     val=self.client.read_holding_registers(6, 2)
#     return val.registers
#   def write_reg(self, value):
#     self.client.write_register(6, scada_value)
#     return 0
#   def deviceinfo(self):
#     rq = mei_message.ReadDeviceInformationRequest()
#     val=self.client.execute(rq)
#     return(val.information)
#   def close(self):
#     self.client.close()


# modbus = MB(IP)
scada_value = 0 #modbus.read_reg()[0]

def calculate_xp_decrease(current_timer, initial_xp):
    # Calculate the percentage of time that has elapsed
    time_elapsed_percentage = ((30 - current_timer) / 30) * 100
    
    # Decrease the XP by the same percentage
    decreased_xp = initial_xp - (initial_xp * time_elapsed_percentage / 100)
    
    return decreased_xp

timer = 30 * 60  #1800 second which is 30 minute
speed = 1  
shutdown_password = "supersecretshutdownpassword"  # Set your shutdown password here
ex1 = 1000
ex2 = 2000
ex3 = 2000
ex4 = 3000
def update_speed():
    global timer, speed , ex1 ,ex2 , ex3 , ex4
    while timer > 0:
        if timer >= 1200 :
          ex1 =  calculate_xp_decrease(timer/60,1000) # first challange
        if timer <= 1320 and timer >= 900:
           ex2 =  calculate_xp_decrease(timer/60,2000) # second challange
        if timer <= 1000 and timer >= 700:
           ex3 =  calculate_xp_decrease(timer/60,2000) # third challange
        if timer < 500 and timer >= 10:
           ex4 =  calculate_xp_decrease(timer/60,3000) # third challange
        time.sleep(1)  # Wait for 2 minutes
        timer -= 1  # Decrease timer by 2 minutes
        if (timer % 120 == 0):
          global scada_value
          scada_value=scada_value+100
        #   modbus.write_reg(scada_value)
          speed += 1  # Increase speed
           

       
# Start the speed update thread
threading.Thread(target=update_speed, daemon=True).start()


def get_db_connection(): #for new, direct use
    conn = sqlite3.connect('DataBase.db')
    conn.row_factory = sqlite3.Row  # This allows column access by name: row['column_name']
    return conn

def get_db(): #reused DB connection
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    if 'username' not in session:
        return redirect('/register')
    global timer, speed
    return render_template('ransom.html', timer=timer, speed=speed)


@app.route('/password.txt')
def serve_password():
    return send_from_directory('static', 'password.txt')



@app.route('/get_timer')
def get_timer():
    global timer
    return {"timer": timer}

@app.route('/malwareinfo', methods=['GET', 'POST'])
def malwareinfo():
    if request.method == 'GET':
        return render_template('malwareinfo.html')  # make sure this file exists

    # POST request starts here
    if 'username' not in session:
        return redirect(url_for('register'))  # redirect if not logged in

    username = session['username']
    password = request.form.get('password')

    if password == shutdown_password:
        with get_db() as users:
            cursor = users.cursor()
            cursor.execute("SELECT * FROM users WHERE name = ?", (username,))
            user = cursor.fetchone()

            if user:
                if user[3] == 1:
                    print(f"User '{username}' has already completed this challenge. No XP added.")
                    image_path = 'static/hi.jpg'
                    response = make_response(send_file(image_path, mimetype='image/jpg'))
                    response.headers["Content-Disposition"] = "attachment; filename=hi.jpg"
                    return response

                # Update XP and mark challenge as complete
                new_xp = user[2] + int(ex1)
                cursor.execute("UPDATE users SET xp = ?, malwareinfo = 1 WHERE name = ?", (new_xp, username))
                users.commit()

                image_path = 'static/hi.jpg'
                response = make_response(send_file(image_path, mimetype='image/jpg'))
                response.headers["Content-Disposition"] = "attachment; filename=hi.jpg"
                return response

            else:
                return "User not found in database.", 401
    else:
        return "Invalid password. Please try again.", 401

    

@app.route('/register')
def register():
   return render_template('register.html')

@app.route('/submit_register',  methods=['POST'])
def submit_register():
   username = request.form.get('Username')
   email = request.form.get('email')
   with get_db() as users:
        cursor = users.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO users  (name ,email, xp, malwareinfo, sqlinjection1,  sqlinjection2, shutdown , final) VALUES(?,?,?,?,?,?,?,?)",
            (username , email,0,0,0,0,0,0))
        users.commit()
        session['username'] = username  # ✅ Set session here
        if cursor.rowcount == 0:
            print(f"User '{username}' already exists in the database.")
        else:
            print(f"User '{username}' added to the database.")
        return redirect('/')
   
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/register')   




@app.route('/decrypt')
def decrypt():
  path_to_pdf = 'static/data.txt'
  return send_file(path_to_pdf, as_attachment=True)

@app.route('/cc-stealer')
def payfordecrypt():
   return render_template('cc-stealer.html')

flag = False
@app.route('/pay',  methods=['POST'])
def pay():
  global flag ,timer
  cardNumber = request.form.get('cardNumber')

  if cardNumber == "4005321443334322" and flag == False:
      flag = True
      timer = timer - 60
      return {"HAHAHAHAHA": ["- 1 minute for being gullible"]}
  else:
      return redirect("/cc-stealer")

    
def process_sql_query(input_query ,username):
    # Regex pattern for matching a query that resembles asking for table names
    tables_query_pattern = re.compile(r'select\s+.+\s+from\s+(information_schema\.tables|all_tables|dba_tables)', re.IGNORECASE)
    
    # Regex pattern for matching a query specifically requesting all from the decryption key table
    decryption_key_pattern = re.compile(r'select\s+\*\s+from\s+decryption_key', re.IGNORECASE)

    with get_db() as users:
            cursor = users.cursor()
            
            # First, check if the user exists by selecting them
            cursor.execute("SELECT * FROM users WHERE name = ?", (username,))
            user = cursor.fetchone()
    
            if decryption_key_pattern.match(input_query):
                if user:
                    if user[5] == 1:
                        return {"Decryption_Keys": ["12345-ABCDE3@193m!i3en$KjILN","67890FGHIJK420DJCNCI69ENDK","11223-KLMNOeo449fj4fnf4dsds"],
                                "route": ["/shutdown"]}
                    
                
                    new_xp = user[2] + int(ex2)  
                    cursor.execute("UPDATE users SET xp = ?, sqlinjection2 = 1 WHERE name = ?", (new_xp, username))
                    print(f"User '{username}' already exists. XP updated.")
                    users.commit()
                    response = {"Decryption_Keys": ["12345-ABCDE3@193m!i3en$KjILN","67890FGHIJK420DJCNCI69ENDK","11223-KLMNOeo449fj4fnf4dsds"],
                                "route": ["/shutdown"]}
                else:
                    response = {"Message": "wrong username"}

    
    
            elif tables_query_pattern.match(input_query):
                if user:
                    if user[4] == 1:
                        return {"Available Tables": ["credit_cards", "Decryption_Keys", "Hitmen_for_hire"]}
                    
                
                    new_xp = user[2] + int(ex3)  
                    cursor.execute("UPDATE users SET xp = ?, sqlinjection1 = 1 WHERE name = ?", (new_xp, username))
                    print(f"User '{username}' already exists. XP updated.")
                    users.commit()
                    response = {"Available Tables": ["credit_cards", "Decryption_Keys", "Hitmen_for_hire"]}
                else:
                    response = {"Message": "Missing username"}
            
            
            else:
                response = {"Message": "Query processed. No results."}

    
    return response  


@app.route('/instalogin', methods=['GET'])
def instalogin():
   return render_template('instagram-login.html')

@app.route('/submit', methods=['POST'])
def submit():
  username = request.form.get('Username')
  passwrd = request.form.get('Password')
  out = process_sql_query(passwrd ,username )
  print(out)
  return jsonify(out) 

@app.route('/malak', methods=['GET', 'POST'])
def malak():
    if request.method == 'GET':
        return render_template('malak.html')
    
    # POST
    submitted_password = request.form.get('password')
    correct_password = 'supersecretPAssword123'  # The password hidden in the image

    if submitted_password == correct_password:
        # Show two lists and a form for the next answer
        return render_template('youcantsolveme.html')
    else:
        return render_template('malak.html', error="Wrong password, try again.")
    
from flask import Flask, render_template, request

@app.route("/youcantsolveme", methods=["GET", "POST"])
def youcantsolveme():
    correct_line = "login from 10.0.0.9"
    message = None
    error = None

    if request.method == "POST":
        user_input = request.form["line"].strip()
        if user_input == correct_line:
            message = '''=== WELCOME TO THE CHALLENGE 4 ===

I am a magic sentence you send to the guard:
"If the guard isn’t careful, they’ll give you the list of all rooms!"

Hint: Think DB 
Use me wisely 😉

=== END OF MESSAGE ==='''
        else:
            error = "Incorrect input. Try again carefully."

    return render_template("youcantsolveme.html", message=message, error=error)


def get_db_connection():
    conn = sqlite3.connect('DataBase.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/dbui')
def dbui():
    # For demo, list all three tables; in your app you can control visibility per user/session
    tables = ['credit_cards', 'Decryption_Keys', 'Hitmen_for_hire']
    return render_template('dbui.html', tables=tables)

@app.route('/dbui/<table_name>')
def view_table(table_name):
    allowed_tables = ['credit_cards', 'Decryption_Keys', 'Hitmen_for_hire']
    if table_name not in allowed_tables:
        return "Table not accessible", 403

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    conn.close()

    return render_template('table_view.html', table_name=table_name, rows=rows)







@app.route('/scoreboard', methods=['GET'])
def scoreboard():
  
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM users')
    users_rows = cur.fetchall()

    # Convert the query result to a list of dictionaries
    users = [dict(row) for row in users_rows]    
    json_data = json.dumps(users, indent=4)
    
    # Create a response object with the JSON data
    response = Response(json_data, content_type='application/json')
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response



@app.route('/shutdown', methods=['post'])
def shutdown():
    global scada_value, timer
    password = request.form.get('password')
    username = request.headers.get('username')
    final = '67890FGHIJK420DJCNCI69ENDK'
    if password == final and bool(username)== True:
        with get_db() as users:
            cursor = users.cursor()
            
            # First, check if the user exists by selecting them
            cursor.execute("SELECT * FROM users WHERE name = ?", (username,))
            user = cursor.fetchone()
            print(user)
            
            if user:
                if user[6] == 1:  
                    print(f"User '{username}' has already completed this challenge. No XP added.")
                    scada_value=1
                    # modbus.write_reg(scada_value)
                    timer = 0  
                    return "Challenge already completed. No XP added.", 403
                # User exists, so update their XP and challenge status
                new_xp = user[2] + int(ex4)  # Assuming 'xp' is the column name for XP in your table
                cursor.execute("UPDATE users SET xp = ?, shutdown = 1 WHERE name = ?", (new_xp, username))
                print(f"User '{username}' already exists. XP updated.")
                users.commit()
                scada_value=1
                # modbus.write_reg(scada_value)
                timer = 0  
                return "succesful ShutDown, congratulations!!" , 202
    else:
        return "Wrong Password" , 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

