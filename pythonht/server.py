import mysql.connector
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse as parse
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("server.log"),
        logging.StreamHandler()
    ]
)

# Database connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="demo"
)

cursor = db.cursor()

# CREATE
def create_college_form(name, age, department, email):
    try:
        sql = "INSERT INTO CollegeForm (name, age, department, email) VALUES (%s, %s, %s, %s)"
        val = (name, age, department, email)
        cursor.execute(sql, val)
        db.commit()
        return {"message": "Record inserted", "id": cursor.lastrowid}
    except mysql.connector.Error as err:
        return {"error": str(err)}

# READ ALL
def read_all_college_forms():
    try:
        cursor.execute("SELECT * FROM CollegeForm")
        results = cursor.fetchall()
        forms = []
        for row in results:
            form = {
                "id": row[0],
                "name": row[1],
                "age": row[2],
                "department": row[3],
                "email": row[4]
            }
            forms.append(form)
        return forms
    except mysql.connector.Error as err:
        return {"error": str(err)}

# READ BY ID
def get_college_form_by_id(id):
    try:
        cursor.execute("SELECT * FROM CollegeForm WHERE id = %s", (id,))
        result = cursor.fetchone()
        if result:
            return {
                "id": result[0],
                "name": result[1],
                "age": result[2],
                "department": result[3],
                "email": result[4]
            }
        else:
            return {"error": f"No record found with ID: {id}"}
    except mysql.connector.Error as err:
        return {"error": str(err)}

# UPDATE
def update_college_form(id, name=None, age=None, department=None, email=None):
    try:
        # Check if the ID exists
        cursor.execute("SELECT * FROM CollegeForm WHERE id = %s", (id,))
        result = cursor.fetchone()
        if not result:
            return {"error": f"No record found with ID: {id}"}

        # Build the SQL update statement
        sql = "UPDATE CollegeForm SET "
        params = []
        if name is not None:
            sql += "name = %s, "
            params.append(name)
        if age is not None:
            sql += "age = %s, "
            params.append(age)
        if department is not None:
            sql += "department = %s, "
            params.append(department)
        if email is not None:
            sql += "email = %s, "
            params.append(email)

        # Remove trailing comma and space
        sql = sql[:-2]

        # Add WHERE clause
        sql += " WHERE id = %s"
        params.append(id)

        # Execute the update query
        cursor.execute(sql, params)
        db.commit()

        # Return the updated record
        return get_college_form_by_id(id)
    except mysql.connector.Error as err:
        return {"error": str(err)}

# DELETE
def delete_college_form(id):
    try:
        # Check if the ID exists
        cursor.execute("SELECT * FROM CollegeForm WHERE id = %s", (id,))
        result = cursor.fetchone()
        if not result:
            return {"error": f"No record found with ID: {id}"}

        # Delete the record
        sql = "DELETE FROM CollegeForm WHERE id = %s"
        cursor.execute(sql, (id,))
        db.commit()

        # Return success message
        return {"message": f"Record deleted, ID: {id}"}
    except mysql.connector.Error as err:
        return {"error": str(err)}

# Request handler class
class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('index.html', 'r') as file:
                self.wfile.write(file.read().encode())
        elif self.path.startswith('/get?id='):
            try:
                id = int(self.path.split('=')[1])
                result = get_college_form_by_id(id)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
            except ValueError:
                self.send_response(400)
                self.end_headers()
        elif self.path == '/list':
            forms = read_all_college_forms()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(forms).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        logging.debug(f"Handling POST request for {self.path}")
        if self.path == '/create':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = parse.parse_qs(post_data.decode())
            logging.debug(f"Received data for creation: {data}")
            name = data['name'][0]
            age = int(data['age'][0])
            department = data['department'][0]
            email = data['email'][0]
            result = create_college_form(name, age, department, email)
            logging.debug(f"Created record with ID: {result.get('id')}")
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        elif self.path == '/update':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = parse.parse_qs(post_data.decode())
            logging.debug(f"Received data for update: {data}")
            
            id = int(data['id'][0])
            name = data.get('name', [None])[0]
            age = int(data.get('age', [None])[0]) if data.get('age') else None
            department = data.get('department', [None])[0]
            email = data.get('email', [None])[0]

            result = update_college_form(id, name, age, department, email)
            logging.debug(f"Updated record with ID: {id}")
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        elif self.path == '/delete':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = parse.parse_qs(post_data.decode())
            logging.debug(f"Received data for deletion: {data}")
            id = int(data['id'][0])
            result = delete_college_form(id)
            logging.debug(f"Deleted record with ID: {id}")
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        else:
            self.send_response(404)
            self.end_headers()

def run(server_class=HTTPServer, handler_class=RequestHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.info(f'Starting server on port {port}...')
    httpd.serve_forever()

if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        pass
    cursor.close()
    db.close()
