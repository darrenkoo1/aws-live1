from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
from config import *

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'employee'


@app.route("/")
def home():
    return render_template('home.html')

@app.route("/addemp", methods=['GET', 'POST'])
def addEmp():
    return render_template('AddEmp.html')

# add employee output
@app.route("/addemp/output", methods=['GET','POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    hire_date = request.form['hire_date']
    payroll = request.form['payroll']
    attendance = request.form['attendance']
    emp_image_file = request.files['emp_image_file']
    
    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:

        cursor.execute(insert_sql, (emp_id, first_name, last_name, pri_skill, location,hore_date,payroll,attendance))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + ".jpg"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('AddEmpOutput.html', name=emp_name)

#Get Employee 
@app.route("/getemp")
def getEmp():
    return render_template('GetEmp.html')

#Get Employee output
@app.route("/getemp/output",methods=['GET','POST'])
def GetEmp():
    emp_id = request.form['emp_id']
   
    select_sql = "SELECT * FROM employee WHERE emp_id = %(emp_id)s"

    cursor = db_conn.cursor()

    try:
        cursor.execute(select_sql, {'emp_id': int(emp_id)})
        for result in cursor:
            print(result)
        
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + ".jpg"
        s3_image_url = "https://wyelum-employee.s3.amazonaws.com/"+emp_image_file_name_in_s3

    except Exception as e:
        return str(e)

    finally:
        cursor.close()

    print("result done...")
    return render_template('GetEmpOutput.html', result=result,image=s3_image_url)

# delete emp
@app.route("/deleteemp", methods=['GET', 'POST'])
def deleteEmp():
    return render_template('DeleteEmp.html')

#Delete Employee output
@app.route("/deleteemp/output",methods=['POST'])
def DeleteEmp():
    emp_id = request.form['emp_id']
    
    select_sql = "SELECT * FROM employee WHERE emp_id = %(emp_id)s"
    cursor = db_conn.cursor()
    cursor.execute(select_sql, {'emp_id': int(emp_id)})
    result = cursor.fetchone()

    if(len(result)>0):
        full_name = result[1]+" "+result[2]
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + ".jpg"
        s3 = boto3.resource('s3')

        try:
            select_sql = "DELETE FROM employee WHERE emp_id = %(emp_id)s"
            cursor.execute(select_sql, {'emp_id': int(emp_id)})
            db_conn.commit()
            print("Data deleted... deleting image from S3...")
            boto3.client('s3').delete_object(Bucket=custombucket, Key=emp_image_file_name_in_s3)
        
        except Exception as e:
            return str(e)

        finally:
            cursor.close()
        print("result done...")
        return render_template('DeleteEmpOutput.html',name=full_name) 
    else:
        cursor.close()
        return("Employee Not Found")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
