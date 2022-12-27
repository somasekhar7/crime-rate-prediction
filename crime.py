from asyncio import windows_events
from flask import Flask, render_template,request,flash,redirect,session,logging,url_for,session
from wtforms import Form, StringField,PasswordField,TextAreaField,DateField,SubmitField,IntegerField, BooleanField,  validators
from wtforms.fields import EmailField,DateTimeField
from passlib.hash import sha256_crypt
from functools import wraps
from datetime import datetime
from flask_mysqldb import MySQL
from flask_mail import Mail,Message
import random
import numpy as np
import matplotlib.pyplot as pyplot
from sklearn.cluster import KMeans
from werkzeug.utils import secure_filename
import os 
from utils import RegistrationForm, plot_variation_graph, plot_pi_graph, plot_bar_graph
import sys, asyncio


if sys.platform == "win32" and (3, 8, 0) <= sys.version_info < (3, 9, 0):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

UPLOAD_FOLDER='static/profile_pic'
ALLOWED_EXTENSIONS = set(['gif','jpeg','jpg','png'])


app= Flask(__name__)

app.config['UPLOAD_FOLDER']=UPLOAD_FOLDER

#config MySql database
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='Sekhar6300302356'
app.config['MYSQL_DB']='crime_rate'
app.config['MYSQL_CURSORCLASS']='DictCursor'

mysql=MySQL(app)


#configuring Mail settings
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT']=465
app.config['MAIL_USE_SSL']=True
app.config['MAIL_USERNAME']='somasekhardarisi7@gmail.com'
app.config['MAIL_PASSWORD']='jhrqpidzkdcqowdh'


mail= Mail(app)

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact',methods=['GET','POST'])
def contact():
    sendmessage=""
    errormessage=""
    if request.method == 'POST':
        name=request.form['name']
        email=request.form['email']
        subject=request.form['subject']
        message=request.form['message']
        date=str(datetime.now().strftime("%Y-%m-%d"))
        flash(date)
        cursor=mysql.connection.cursor()
        try:
            cursor.execute("Insert into contact(name,email,subject,message,date_feedback) values(%s,%s,%s,%s,%s)",[name,email,subject,message,date])
            mysql.connection.commit()
            sendmessage="Thank you for contacting us !.Your message has been sent."
        except Exception as e:
            errormessage="Error : "+ str(e)
        finally:
            cursor.close()


    return render_template('contact.html',sendmessage=sendmessage,errormessage=errormessage)


#creating  function corresponding to the Registration Form
@app.route('/register', methods=['GET','POST'])
def register():
    form = RegistrationForm(request.form)
    #print form.errors
    if request.method =='POST' and form.validate():
        mobile=form.mobile.data
        name=form.name.data
        addhar=form.addhar.data
        email=form.email.data
        password=sha256_crypt.encrypt(str(form.password.data))
        # date_register=str(datetime.utcnow().strftime('%s'))
        date_register = '1671954912'
        ip=request.environ.get('HTTP_X_REAL_IP', request.remote_addr)

        #creating cursor
        cursor=mysql.connection.cursor()

        #checking if email and addhar not exists
        result=cursor.execute("Select email,aadhar from users ")
        email_status=""
        addhar_status=""
        if(result>0):
            data=cursor.fetchall()
            for db in data:
                if db['email'] == email:
                    flash('Email already exists...!','danger')
                    email_status="exist"
                elif db['aadhar']== addhar:
                    flash('Aadhar already exists..!', 'danger')
                    addhar_status="exist"

        if email_status != "exist" and addhar_status != "exist":
            #inserting data
            cursor.execute("INSERT INTO users(name,email,mobile,aadhar,password ,date_register,ip_address) VALUES(%s,%s,%s,%s,%s,%s,%s)", (name,email,mobile,addhar,password,date_register,ip))

            #commitng inserted data
            mysql.connection.commit()

            #closng connection
            cursor.close()
            otp_contents="ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
            otp_contents=list(otp_contents)
            random.shuffle(otp_contents)
            otp=random.sample(otp_contents,6)
            otp=''.join(otp)
            session['otp_send_to_mail']=otp
            session['candidate_email']=email

            #sending Email to the users
            mail_sent =False
            try:
                msg =Message(
                    'Crime Rate Prediction',
                    sender='somasekhardarisi7@gmail.com',
                    recipients=["%s" %(email)]
                )
                msg.html=("Hi! %s<br><br>Thank you for registering with Crime Rate Prediction.<b>%s</b> is the OTP for your verification.Please Enter this OTP to Actiavte your Account.<br>Thank You !<br><br>Best Regards form<br>Crime Rate Prediction Team<br>" %(name,otp))
                mail.send(msg)
                mail_sent=True
            except Exception as e:
                mail_not_send=str(e)


            if mail_sent == True:
                flash('An OTP is sent to your registered Email. Please Verify Your Email', 'info')
            else:
                flash(mail_not_send, 'danger')


            return redirect(url_for('register_verify'))
    return render_template('register.html', form=form)



# verify OTP
@app.route('/register_verify', methods=['GET','POST'])
def register_verify():
    if request.method== 'POST':
        otp_entered=request.form['otp']
        if otp_entered == session['otp_send_to_mail']:
            #creating cursor
            cursor =mysql.connection.cursor()

            #updating status of user
            cursor.execute("UPDATE users set status=1 where email='%s'" %(session['candidate_email']))

            #commitng inserted data
            mysql.connection.commit()

            #closng connection
            cursor.close()
            flash('You have successfully registered. You can login now.','success')
            return redirect(url_for('login'))
        else:
            flash('OTP does not matched ! Emter a valid OTP','danger')

    return render_template('register_verify.html')




#creating login form and its logic
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method =='POST':

        #getting the form fields data
        email_candidate = request.form['email']
        password_candidate = request.form['password']

        #creating cursor
        cursor =mysql.connection.cursor()

        #executing the query to fetch the user data
        result = cursor.execute("SELECT * from users where email=%s",[email_candidate])

        if result >0:
            #fetching the selected data
            data=cursor.fetchone()
            print(data)
            passowrd_db = data['password']

            if data['status'] != 0:
                #comparing passwords
                if sha256_crypt.verify(password_candidate,passowrd_db):
                    #app.logger.info('PASSWORD MATCH')
                    session['logged_in']=True
                    session['username']=data['name']
                    session['userid']=data['id']
                    session['user_role']=data['role']

                    flash("You are now login", 'success')
                    if data['role'] == 'administrator':
                        return redirect(url_for('dashboard'))
                    else:
                        return redirect(url_for('user_dashboard'))
                else:
                    #app.logger.info('PASSWORD NOT MATCH')
                    error = "Invalid login Credientials"
                    return render_template('login.html',error = error )
            else:
                flash('First verify your Email to Activate your account','danger')

        else:
            error =  "User does not exists "
            #app.logger.info('User does not exists ')
            return render_template('login.html',error = error )


    return render_template('login.html')


#checking if logged_in or not
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in  session:
            return f(*args, **kwargs)
        else:
            flash("Unauthorized User",'danger')
            return redirect(url_for('login'))
    return wrap



#creating dashboards and its logics
@app.route('/dashboard', methods=['GET',"POST"])
@login_required
def dashboard():
    if 'logged_in' in  session:
        return render_template('dashboard.html')
    else:
        return redirect(url_for('login'))





@app.route('/dashboard_users',methods=['POST','GET'])
@login_required
def dashboard_users():
    cursor=mysql.connection.cursor()
    cursor.execute("Select * from users")
    users=cursor.fetchall()

    return render_template('dashboard_users.html',users=users)


@app.route('/deactivate_activate_user/<int:user_id>',methods=['POST','GET'])
@login_required
def deactivate_activate_user(user_id):
    cursor=mysql.connection.cursor()
    cursor.execute("select status from users where id=%s"%(user_id))
    status=cursor.fetchall()
    if status[0]['status'] == 1:
        cursor.execute("UPDATE users set status=0 where id=%s", [user_id])
    else:
        cursor.execute("UPDATE users set status=1 where id=%s", [user_id])

    mysql.connection.commit()
    cursor.close()
    return redirect('/dashboard_users')


@app.route('/edit_user/<int:user_id>', methods=['GET','POST'])
@login_required
def edit_user(user_id):
    #creating cursor
    cursor=mysql.connection.cursor()
    user_id=int(user_id)
    result = cursor.execute("SELECT * from users where id=%s",[user_id])
    if result >0:
        user_data=cursor.fetchone()
    if request.method == 'POST':
        name=request.form['name']
        email=request.form['email']
        mobile=request.form['mobile']
        aadhar=request.form['aadhar']
        try:
            cursor.execute("UPDATE users set name=%s,email=%s,mobile=%s,aadhar=%s where id=%s", [name,email,mobile,aadhar,user_id])
            mysql.connection.commit()
            flash("Data updated successfully",'success')
            return redirect('/dashboard_users')
        except Exception as e:
            flash(e.message+"Duplicate Entry ",'danger')
        cursor.close()
    return render_template('edit_user.html',user_data=user_data)





@app.route('/dashboard_crimes',methods=['GET','POST'])
@login_required
def dashboard_crimes():
    if 'logged_in' in session:

        #creating cursor
        cursor =mysql.connection.cursor()

        #executing the query to fetch the user data
        result = cursor.execute("SELECT * from crimes where crime_status=1 order by crime_id asc")

        if result >0:
            #fetching the selected data
            data=cursor.fetchall()
        else:
            data="Empty"


        result1 = cursor.execute("SELECT * from crimes where crime_status=0 order by crime_id asc")
        if result1>0:
            crime_deleted=cursor.fetchall()
        else:
            crime_deleted="Empty"

        #closng connection
        cursor.close()
        return render_template('dashboard_crimes.html', crime_data=data,crime_deleted=crime_deleted)
    else:
        return redirect(url_for('login'))


@app.route('/add_crime',methods=['GET','POST'])
@login_required
def add_crime():
    if request.method == 'POST':
        crime_type=request.form['crime_type']

        #creating cursor
        cursor =mysql.connection.cursor()

        #checking if already exists
        result=cursor.execute("SELECT * from crimes where crime_type=%s",[crime_type])


        if result == 0:
            #executing the query to fetch the user data
            res=cursor.execute("INSERT INTO crimes(crime_type, crime_status) VALUES(%s,1)",[crime_type])

            #commting the cries data inserted
            mysql.connection.commit()
            #closng connection
            cursor.close()
            flash("Crime Added Successfully",'success')
            return redirect(url_for('dashboard_crimes'))
        else:
            flash("Duplicate Entry for already exists crime..!",'danger')
    return render_template('add_crime.html')



@app.route('/edit_crime/<int:crime_id>', methods=['GET','POST'])
@login_required
def edit_crime(crime_id):
    #creating cursor
    cursor=mysql.connection.cursor()
    crime_id=int(crime_id)
    result=cursor.execute("SELECT * from crimes where crime_id=%s",[crime_id])
    if result >0:
        crime_data=cursor.fetchone()
    if request.method == 'POST':
        crime_type=request.form['crime_type']
        cursor.execute("UPDATE crimes set crime_type=%s where crime_id=%s", (crime_type,crime_id))
        mysql.connection.commit()
        cursor.close()
        flash("Data updated successfully",'success')
        return redirect('/dashboard_crimes')
    return render_template('edit_crime.html',crime_data=crime_data)


@app.route('/delete_crime/<int:crime_id>')
@login_required
def delete_crime(crime_id):
    #creating cursor
    cursor=mysql.connection.cursor()

    #deleting th record
    cursor.execute("UPDATE crimes set crime_status=0 where crime_id=%s", [crime_id])

    mysql.connection.commit()
    cursor.close()
    flash("Data deleted successfully",'success')
    return redirect('/dashboard_crimes')




@app.route('/restore_crime/<int:crime_id>')
@login_required
def restore_crime(crime_id):
    #creating cursor
    cursor=mysql.connection.cursor()

    #deleting th record
    cursor.execute("UPDATE crimes set crime_status=1 where crime_id=%s", [crime_id])

    mysql.connection.commit()
    cursor.close()
    flash("Data restored successfully",'success')
    return redirect('/dashboard_crimes')



@app.route('/dashboard_crimes_records',methods=['GET','POST'])
@login_required
def dashboard_crimes_records():
    #creating cursor
    cursor=mysql.connection.cursor()

    #fetching the crime record
    cursor.execute("SELECT * from crimes;")

    crime_data=cursor.fetchall()

    #fetching the state records
    cursor.execute("SELECT * from state")

    state_data = cursor.fetchall()
    if request.method == "POST":
        victim_name=request.form['victim_name']
        victim_father_name=request.form['victim_father_name']
        victim_age=request.form['victim_age']
        victim_gender=request.form['victim_gender']
        victim_address=request.form['victim_address']
        victim_state=request.form['victim_state']
        victim_district=request.form['victim_district']
        victim_police_station=request.form['victim_police_station']

        criminal_name=request.form['criminal_name']
        criminal_father_name=request.form['criminal_father_name']
        criminal_age=request.form['criminal_age']
        criminal_gender=request.form['criminal_gender']
        criminal_address=request.form['criminal_address']
        criminal_state=request.form['criminal_state']
        criminal_district=request.form['criminal_district']
        criminal_police_station=request.form['criminal_police_station']

        crime_type=request.form['crime_type']
        crime_location=request.form['crime_location']
        happen_when=request.form['happened_when']
        crime_state=request.form['crime_state']
        crime_district=request.form['crime_district']
        crime_police_station=request.form['crime_police_station']


        try:
            cursor.execute("INSERT into victim_table(victim_name,victim_father_name,age,gender,address,state_id,district_id,police_station_id) values(%s,%s,%s,%s,%s,%s,%s,%s)",(victim_name,victim_father_name,victim_age,victim_gender,victim_address,victim_state,victim_district,victim_police_station))
            victim_id=cursor.lastrowid
            cursor.execute("INSERT into criminal_table(criminal_name,criminal_father_name,age,gender,address,state_id,district_id,police_station_id) values(%s,%s,%s,%s,%s,%s,%s,%s)",(criminal_name,criminal_father_name,criminal_age,criminal_gender,criminal_address,criminal_state,criminal_district,criminal_police_station))
            criminal_id=cursor.lastrowid
            cursor.execute("INSERT into crime_table(crime_id,location,dateTime,state_id,district_id,police_station_id,victim_id,criminal_id) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",(crime_type,crime_location,happen_when,crime_state,crime_district,crime_police_station,victim_id,criminal_id))
            mysql.connection.commit()
            flash("Data Inserted Successfully","success")
        except Exception as e:
            flash(str(e),'danger')
        finally:
            cursor.close()
    return render_template('dashboard_crimes_records.html',crime_data=crime_data,state_data=state_data)


@app.route('/show_district/<int:state_id>',methods=["POST","GET"])
@login_required
def show_district(state_id):
    if request.method == "POST":
        cursor=mysql.connection.cursor();
        cursor.execute("SELECT * from district where state_id=%d"%state_id);
        print("-----------------------")
        dist_data=cursor.fetchall();
        print(dist_data)
        div_type=request.args.get('div_type')
        cursor.close()
    return render_template("/show_district.html",dist_data=dist_data,div_type=div_type)


@app.route('/show_police_station/<int:dist_id>',methods=["POST","GET"])
@login_required
def show_police_station(dist_id):
    if request.method == "POST":
        cursor=mysql.connection.cursor();
        cursor.execute("SELECT * from police_station where dist_id=%d" % dist_id);
        police_station_data=cursor.fetchall();
        div_type=request.args.get('div_type')
        cursor.close()
    return render_template("/show_police_station.html",police_station_data=police_station_data,div_type=div_type)





#making a class for kmeans clustering
class kmeans_clustering():
    cluster_array=[]
    centroids=[]
    labels=[]
    size_cluster=[]
    cluster_title=""
    cluster_x_name=""
    cluster_y_name=""
    n_clusters=0
    def __init__(self,cluster_array,cluster_title,cluster_x_name,cluster_y_name):
        self.cluster_array=cluster_array
        self.cluster_title=cluster_title
        self.cluster_x_name=cluster_x_name
        self.cluster_y_name=cluster_y_name
        self.size_cluster=[]
        self.n_clusters=0
        self.cencentroids=[]
        self.labels=[]
        pyplot.close('all')

    def make_kmeans_cluster(self):
        self.n_clusters=random.randint(2,5)
        kmeans = KMeans(self.n_clusters)
        kmeans.fit(self.cluster_array)
        colors=["g.","r.","c.","m.","b."]
        self.centroids = kmeans.cluster_centers_
        self.labels=kmeans.labels_


        for k in range(len(self.cluster_array)):
            pyplot.plot(self.cluster_array[k][0],self.cluster_array[k][1],colors[self.labels[k]], markersize=10)

        pyplot.scatter(self.centroids[:, 0],self.centroids[:,1],marker="x", s=130, linewidths=5, zorder=10)
        pyplot.title(self.cluster_title)
        pyplot.xlabel(self.cluster_x_name)
        pyplot.ylabel(self.cluster_y_name)

        for i in range(self.n_clusters):
            self.size_cluster += [[len(self.ClusterIndicesNumpy(i,self.labels)),colors[i]]]
        pyplot.show()
        pyplot.close()

    def ClusterIndicesNumpy(self,clustNum, labels_array): #numpy
        return np.where(labels_array == clustNum)[0]


#class for yearwise gaph analysis
class dashboard_yearwise_graph_analysis_class():
    year=""
    crime_id_data=[]
    crime_type_data=[]
    number_times_crime=[]
    def __init__(self,year):
        self.crime_id_data=[]
        self.crime_type_data=[]
        self.number_times_crime=[]
        self.year=year

    def fetch_data_for_graph(self):
        cursor=mysql.connection.cursor()
        cursor.execute("SELECT * from crimes where crime_status=1")
        if cursor.rowcount >0:
            data=cursor.fetchall()
            for d in data:
                self.crime_id_data += [d['crime_id']]
                self.crime_type_data +=[d['crime_type']]
        for i in self.crime_id_data:
            cursor.execute("select count(crime_id) from (select crime_id from crime_table where extract(year from dateTime)=%s AND crime_id=%s) as cr"%(self.year,i))
            data=cursor.fetchall()
            self.number_times_crime +=[data[0]['count(crime_id)']]



@app.route('/dashboard_yearwise_graph_analysis',methods=['POST',"GET"])
@login_required
def dashboard_yearwise_graph_analysis():
    crime_type=[]
    number_times=[]
    max_index=[]
    max_value=""
    pair={}
    year_to_graph=""
    previous_year=""
    total_crime=0
    previous_crime_type=[]
    previous_number_times=[]
    previous_max_index=[]
    previous_max_value=""
    previous_pair={}
    previous_total_crime=0
    if request.method == 'POST':
        year_to_graph=request.form['year_graph']
        previous_year=int(year_to_graph)-1
        #flash(previous_year,"danger")
        dashboard_yearwise_graph_analysis_obj = dashboard_yearwise_graph_analysis_class(year=year_to_graph)
        dashboard_yearwise_graph_analysis_obj.fetch_data_for_graph()

        previous_dashboard_yearwise_graph_analysis_obj = dashboard_yearwise_graph_analysis_class(year=previous_year)
        previous_dashboard_yearwise_graph_analysis_obj.fetch_data_for_graph()

        crime_type = dashboard_yearwise_graph_analysis_obj.crime_type_data
        number_times = dashboard_yearwise_graph_analysis_obj.number_times_crime
        max_value=max(number_times)
        pair=dict(zip(crime_type,number_times))

        previous_crime_type = previous_dashboard_yearwise_graph_analysis_obj.crime_type_data
        previous_number_times = previous_dashboard_yearwise_graph_analysis_obj.number_times_crime
        previous_max_value=max(previous_number_times)
        #flash(previous_crime_type,"information")
        #flash(previous_number_times,"success")
        previous_pair=dict(zip(previous_crime_type,previous_number_times))

        #calculating the max index
        for i,j in pair.items():
            total_crime += j
            if max_value == j:
                max_index += [i]


        #calculating the max index
        for i,j in previous_pair.items():
            previous_total_crime += j
            if previous_max_value == j:
                previous_max_index += [i]


        #flash(previous_pair,"danger")
        #flash(previous_total_crime,"success")
        #flash(pair,"danger")

        flash(dashboard_yearwise_graph_analysis_obj.year+" Graph Analysis","success")
        plot_bar_graph_crime_id_times=plot_bar_graph(x=dashboard_yearwise_graph_analysis_obj.crime_type_data,y=dashboard_yearwise_graph_analysis_obj.number_times_crime,graph_title=year_to_graph+" Graph Analysis",graph_xlabel="Crime Type",graph_ylabel="Number of times crime Happened",width=0.5)
        plot_bar_graph_crime_id_times.make_plot()

    return render_template('dashboard_yearwise_graph_analysis.html',year=year_to_graph,previous_year=previous_year,crime_type_data=crime_type,number_times_crime=number_times,max_index=max_index,max_value=max_value,pair=pair.items(),total_crime=total_crime,previous_max_index=previous_max_index,previous_max_value=previous_max_value,previous_pair=previous_pair.items(),previous_total_crime=previous_total_crime)




#class for the crimewise graph analysis
class dashboard_crimewise_graph_analysis_class():
    crime_id=""
    crime_name=""
    number_times_crime=[]
    year=[1990,1991,1992,1993,1994,1995,1996,1997,1998,1999,2000,2001,2002,2003,2004,2005,2006,2007,2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018,2019,2020,2021,2022,2023]
    def __init__(self,crime_id):
        self.crime_id=crime_id
        self.crime_name=""
        self.number_times_crime=[]

    def fetch_data_for_graph(self):
        cursor=mysql.connection.cursor()
        cursor.execute("Select crime_type from crimes where crime_id=%s"%(self.crime_id))
        crimename=cursor.fetchall()
        self.crime_name= crimename[0]['crime_type']

        for i in self.year:
            cursor.execute("select count(crime_id) from(select crime_id,dateTime from crime_table where crime_id=%s AND extract(year from dateTime)=%s) as tbl"%(self.crime_id,i))
            number_crime_data=cursor.fetchall()
            self.number_times_crime += [number_crime_data[0]['count(crime_id)']]


class dashboard_crimewise_year_range_data():
    crime_id=""
    crime_name=""
    number_times_crime=[]
    start_year=""
    end_year=""
    year=[]

    def __init__(self,start_year,end_year,crime_id):
        self.start_year=start_year
        self.end_year=end_year
        self.crime_id=crime_id
        self.crime_name=""
        self.number_times_crime=[]
        self.year=[]



    def fetch_required_data(self):
        cursor=mysql.connection.cursor()
        cursor.execute("Select crime_type from crimes where crime_id=%s"%(self.crime_id))
        crimename=cursor.fetchall()
        self.crime_name = crimename[0]['crime_type']

        self.year=range(self.start_year,self.end_year+1,1)

        for i in self.year:
            cursor.execute("select count(crime_id) from(select crime_id,dateTime from crime_table where crime_id=%s AND extract(year from dateTime)=%s) as tbl"%(self.crime_id,i))
            number_crime_data=cursor.fetchall()
            self.number_times_crime += [number_crime_data[0]['count(crime_id)']]








@app.route('/dashboard_crimewise_graph_analysis',methods=['POST','GET'])
@login_required
def dashboard_crimewise_graph_analysis():
    crime_name=""
    total_crime=0
    after_total_crime=0
    pair={}
    after_pair={}
    max_value=""
    after_max_value=""
    max_index=[]
    after_max_index=[]
    cursor=mysql.connection.cursor()
    cursor.execute("select * from crimes where crime_status=1")
    data=cursor.fetchall()
    if request.method == 'POST':
        crime_id=request.form['crime_id_graph']
        dashboard_crimewise_graph_analysis_obj=dashboard_crimewise_graph_analysis_class(crime_id)
        dashboard_crimewise_graph_analysis_obj.fetch_data_for_graph()
        crime_name=dashboard_crimewise_graph_analysis_obj.crime_name
        #flash(dashboard_crimewise_graph_analysis_obj.number_times_crime,"danger")
        flash(dashboard_crimewise_graph_analysis_obj.crime_name,"success")

        plot_bar = plot_bar_graph(x=dashboard_crimewise_graph_analysis_obj.year,y=dashboard_crimewise_graph_analysis_obj.number_times_crime,graph_title=dashboard_crimewise_graph_analysis_obj.crime_name+" Graph analysis",graph_xlabel="Year",graph_ylabel="Number of times crime happened",width=0.5)
        plot_bar.make_plot()
        cursor.close()

        dashboard_crimewise_year_range_data_obj=dashboard_crimewise_year_range_data(start_year=2001,end_year=2009,crime_id=crime_id)
        dashboard_crimewise_year_range_data_obj.fetch_required_data()
        max_value=max(dashboard_crimewise_year_range_data_obj.number_times_crime)
        pair=dict(zip(dashboard_crimewise_year_range_data_obj.year,dashboard_crimewise_year_range_data_obj.number_times_crime))
        for i,j in pair.items():
            total_crime += j
            if max_value == j:
                max_index += [i]

        #flash(pair)

        #after year range data calculation
        after_dashboard_crimewise_year_range_data_obj=dashboard_crimewise_year_range_data(start_year=2010,end_year=2018,crime_id=crime_id)
        after_dashboard_crimewise_year_range_data_obj.fetch_required_data()
        after_max_value=max(after_dashboard_crimewise_year_range_data_obj.number_times_crime)
        after_pair=dict(zip(after_dashboard_crimewise_year_range_data_obj.year,after_dashboard_crimewise_year_range_data_obj.number_times_crime))
        for i,j in after_pair.items():
            after_total_crime += j
            if after_max_value == j:
                after_max_index += [i]
        #flash(after_dashboard_crimewise_year_range_data_obj.year)
        #flash(after_pair)




    return render_template('dashboard_crimewise_graph_analysis.html',crime_data=data,crime_name=crime_name,total_crime=total_crime,pair=pair.items(),max_value=max_value,after_total_crime=after_total_crime,after_pair=after_pair.items(),after_max_value=after_max_value)

#fetching crime_id criminal_age and number of times crime happened
class fetch_id_age_times():
    crime_type_data=[]
    crime_id_data=[]
    criminal_age_data=[]
    cluster_array_id_age =[]
    crime_number_count=[]
    cluster_array_crime_number_count=[]
    def __init__(self):
        self.crime_type_data=[]
        self.crime_id_data=[]
        self.criminal_age_data=[]
        self.cluster_array_id_age =[]
        self.crime_number_count=[]
        self.cluster_array_crime_number_count=[]

    def fetch_data(self):
        cursor=mysql.connection.cursor()
        cursor.execute("SELECT * from crimes where crime_status=1")
        if cursor.rowcount >0:
            data=cursor.fetchall()
            for d in data:
                self.crime_id_data += [d['crime_id']]
                self.crime_type_data += [d['crime_type']]

        for i in self.crime_id_data:
            cursor.execute("SELECT AVG(tble_derived.age) from (select c.crime_id,c.criminal_id,ct.age from crime_table as c join criminal_table as ct on c.criminal_id = ct.criminal_id and c.crime_id=%s) as tble_derived"%(i))
            if cursor.rowcount >0:
                data=cursor.fetchall()
                if data[0]['AVG(tble_derived.age)'] != None:
                    self.criminal_age_data += [data[0]['AVG(tble_derived.age)']]
                else:
                    self.criminal_age_data += [0.0]
            else:
                print("Error in fetching data")

        for i in range(len(self.crime_id_data)):
            self.cluster_array_id_age += [
                                [ self.crime_id_data[i]
                                 ,self.criminal_age_data[i]
                                ]
                             ]

        self.cluster_array_id_age = np.array(self.cluster_array_id_age)

        for k in self.crime_id_data:
            cursor.execute("select *from crime_table where crime_id=%s"%(k))
            self.crime_number_count += [cursor.rowcount]

        for i in range(len(self.crime_id_data)):
            self.cluster_array_crime_number_count += [
                                                    [ self.crime_id_data[i]
                                                      ,self.crime_number_count[i]
                                                    ]
                                                    ]


#making graph analysis
@app.route('/dashboard_graph_analysis',methods=["POST","GET"])
@login_required
def dashboard_graph_analysis():
    centroids=""
    size_cluster_color=[]
    length_cluster=0
    crime_data_cluster=fetch_id_age_times()
    crime_data_cluster.fetch_data()
    if request.method == 'POST':
        if request.form['submit']== "See Graph Crime Type And Criminal Age":
            class_kmeans_id_age =kmeans_clustering(cluster_array=crime_data_cluster.cluster_array_id_age,cluster_title="Criminal age and Crime Type",cluster_x_name="Crime Type",cluster_y_name="Criminal Age")
            class_kmeans_id_age.make_kmeans_cluster()

            #flash(class_kmeans_id_age.centroids,"danger")
            #flash(class_kmeans_id_age.size_cluster)

            centroids=class_kmeans_id_age.centroids
            size_cluster_color=class_kmeans_id_age.size_cluster
            length_cluster=class_kmeans_id_age.n_clusters
        if request.form['submit']== "See Graph Crime Type And Number of Times":
            class_kmeans_number_crime =kmeans_clustering(cluster_array=crime_data_cluster.cluster_array_crime_number_count,cluster_title="Number of crime happened",cluster_x_name="Crime Type",cluster_y_name="Number of times crime happened")
            class_kmeans_number_crime.make_kmeans_cluster()

            #flash(class_kmeans_number_crime.centroids,"danger")
            #flash(class_kmeans_number_crime.size_cluster)
            #flash(class_kmeans_number_crime.labels)

            centroids=class_kmeans_number_crime.centroids
            size_cluster_color=class_kmeans_number_crime.size_cluster
            length_cluster=class_kmeans_number_crime.n_clusters
    return render_template("/dashboard_graph_analysis.html",crime_type_data=crime_data_cluster.crime_type_data,crime_id_data=crime_data_cluster.crime_id_data,centroids=centroids,size_cluster_color=size_cluster_color,length_cluster=length_cluster)


@app.route('/dashboard_variation_graph',methods=['POST','GET'])
@login_required
def dashboard_variation_graph():
    first_criminal_age_under18=0
    first_criminal_age_18_25=0
    first_criminal_age_beyond_25=0
    first_total_crime=0
    first_crime_count={}
    year1=""
    second_criminal_age_under18=0
    second_criminal_age_18_25=0
    second_criminal_age_beyond_25=0
    second_total_crime=0
    second_crime_count={}
    year2=""
    max1=0
    max2=0


    crime_data=fetch_id_age_times()
    crime_data.fetch_data()

    if request.method == 'POST':
        if request.form['submit']== "See Graph Crime Type And Criminal Age" :
            variation_graph_id_age=plot_variation_graph(x=crime_data.crime_type_data,y=crime_data.criminal_age_data,graph_title="Graph Between Crime Id and Criminal Age",graph_xlabel="Crime Type",graph_ylabel="Criminal Age",graph_color_style="r--^")
            variation_graph_id_age.make_plot()

            crime_obj=fetch_data_for_age_yearwise(start_year=2009,end_year=2013)
            crime_obj.fetch_data()
            year1=crime_obj.year
            first_crime_count=crime_obj.crime_number_count

            #flash(crime_data_bar.criminal_age_data)
            for i in crime_obj.criminal_age_data:
                if i>0 and i<19:
                    first_criminal_age_under18 +=1
                elif i>18 and i<26:
                    first_criminal_age_18_25 +=1
                else:
                    first_criminal_age_beyond_25 +=1
            first_total_crime = first_criminal_age_under18 + first_criminal_age_18_25 +  first_criminal_age_beyond_25


            #analysis another half year
            crime_obj2=fetch_data_for_age_yearwise(start_year=2014,end_year=2018)
            crime_obj2.fetch_data()
            year2=crime_obj2.year

            #flash(crime_data_bar.criminal_age_data)
            for i in crime_obj2.criminal_age_data:
                if i>0 and i<19:
                    second_criminal_age_under18 +=1
                elif i>18 and i<26:
                    second_criminal_age_18_25 +=1
                else:
                    second_criminal_age_beyond_25 +=1
            second_total_crime = second_criminal_age_under18 + second_criminal_age_18_25 +  second_criminal_age_beyond_25

        if request.form['submit'] == "See Graph Crime Type And Number of Times":
            variation_graph_id_number_times=plot_variation_graph(x=crime_data.crime_type_data,y=crime_data.crime_number_count,graph_title="Graph Between Crime Id and Number of times Crime Happened",graph_xlabel="Crime Type",graph_ylabel="Number Of times Crime Happened",graph_color_style="g--*")
            variation_graph_id_number_times.make_plot()


            crime_obj=fetch_data_for_age_yearwise(start_year=2009,end_year=2013)
            crime_obj.fetch_data()
            year1=crime_obj.year
            first_crime_count=crime_obj.crime_number_count
            max1=max(first_crime_count)
            #flash(first_crime_count)
            crime_obj2=fetch_data_for_age_yearwise(start_year=2014,end_year=2018)
            crime_obj2.fetch_data()
            year2=crime_obj2.year
            second_crime_count=crime_obj2.crime_number_count
            max2=max(second_crime_count)
            #flash(second_crime_count)
            first_crime_count= dict(zip(crime_obj.crime_type_data,first_crime_count))
            #flash(first_crime_count)
            first_crime_count=first_crime_count.items()
            second_crime_count= dict(zip(crime_obj.crime_type_data,second_crime_count))
            #flash(second_crime_count)
            second_crime_count=second_crime_count.items()
    return render_template('/dashboard_variation_graph.html',first_year=year1,first_total_crime=first_total_crime,first_criminal_age_under18=first_criminal_age_under18,first_criminal_age_18_25=first_criminal_age_18_25,first_criminal_age_beyond_25=first_criminal_age_beyond_25,second_year=year2,second_total_crime=second_total_crime,second_criminal_age_under18=second_criminal_age_under18,second_criminal_age_18_25=second_criminal_age_18_25,second_criminal_age_beyond_25=second_criminal_age_beyond_25,first_crime_count=first_crime_count,second_crime_count=second_crime_count,max1=max1,max2=max2)


class fetch_data_for_age_yearwise:
    crime_type_data=[]
    crime_id_data=[]
    criminal_age_data=[]
    year=[]
    crime_number_count=[]

    def __init__(self,start_year,end_year):
        self.crime_type_data=[]
        self.crime_id_data=[]
        self.criminal_age_data=[]
        self.year=[]
        self.crime_number_count=[]
        for i in range(start_year,end_year+1,1):
            self.year += [i]
        self.year= tuple(self.year)


    def fetch_data(self):
        cursor=mysql.connection.cursor()
        cursor.execute("SELECT * from crimes where crime_status=1")
        if cursor.rowcount >0:
            data=cursor.fetchall()
            for d in data:
                self.crime_id_data += [d['crime_id']]
                self.crime_type_data += [d['crime_type']]

        for i in self.crime_id_data:
            cursor.execute("SELECT AVG(tble_derived.age) from (select c.crime_id,c.criminal_id,ct.age from crime_table as c join criminal_table as ct on c.criminal_id = ct.criminal_id and c.crime_id=%s and extract(year from c.dateTime) in %s) as tble_derived"%(i,self.year))
            if cursor.rowcount >0:
                data=cursor.fetchall()
                if data[0]['AVG(tble_derived.age)'] != None:
                    self.criminal_age_data += [data[0]['AVG(tble_derived.age)']]
                else:
                    self.criminal_age_data += [0.0]
            else:
                print("Error in fetching data")

        for k in self.crime_id_data:
            cursor.execute("select *from crime_table where crime_id=%s and extract(year from dateTime) in %s"%(k,self.year))
            self.crime_number_count += [cursor.rowcount]



@app.route('/dashboard_bar_graph',methods=['GET','POST'])
@login_required
def dashboard_bar_graph():
    first_criminal_age_under18=0
    first_criminal_age_18_25=0
    first_criminal_age_beyond_25=0
    first_total_crime=0
    first_crime_count={}
    year1=""
    second_criminal_age_under18=0
    second_criminal_age_18_25=0
    second_criminal_age_beyond_25=0
    second_total_crime=0
    second_crime_count={}
    year2=""
    max1=0
    max2=0

    crime_data_bar=fetch_id_age_times()
    crime_data_bar.fetch_data()

    if request.method == 'POST':
        if request.form['submit'] =="See Graph Crime Type And Criminal Age":
            bar_graph_id_age=plot_bar_graph(x=crime_data_bar.crime_type_data,y=crime_data_bar.criminal_age_data,graph_title="Graph Between Crime Id and Criminal Age",graph_xlabel="Crime Type",graph_ylabel="Criminal Age",width=0.5)
            bar_graph_id_age.make_plot()

            crime_obj=fetch_data_for_age_yearwise(start_year=2009,end_year=2013)
            crime_obj.fetch_data()
            year1=crime_obj.year
            first_crime_count=crime_obj.crime_number_count

            #flash(crime_data_bar.criminal_age_data)
            for i in crime_obj.criminal_age_data:
                if i>0 and i<19:
                    first_criminal_age_under18 +=1
                elif i>18 and i<26:
                    first_criminal_age_18_25 +=1
                else:
                    first_criminal_age_beyond_25 +=1
            first_total_crime = first_criminal_age_under18 + first_criminal_age_18_25 +  first_criminal_age_beyond_25


            #analysis another half year
            crime_obj2=fetch_data_for_age_yearwise(start_year=2014,end_year=2018)
            crime_obj2.fetch_data()
            year2=crime_obj2.year

            #flash(crime_data_bar.criminal_age_data)
            for i in crime_obj2.criminal_age_data:
                if i>0 and i<19:
                    second_criminal_age_under18 +=1
                elif i>18 and i<26:
                    second_criminal_age_18_25 +=1
                else:
                    second_criminal_age_beyond_25 +=1
            second_total_crime = second_criminal_age_under18 + second_criminal_age_18_25 +  second_criminal_age_beyond_25


        if request.form['submit'] == "See Graph Crime Type And Number of Times":
            bar_graph_id_number=plot_bar_graph(x=crime_data_bar.crime_type_data,y=crime_data_bar.crime_number_count,graph_title="Graph Between Crime Id and Number of times Crime happened",graph_xlabel="Crime Type",graph_ylabel="Number of times Crime Happened",width=0.5)
            bar_graph_id_number.make_plot()


            crime_obj=fetch_data_for_age_yearwise(start_year=2009,end_year=2013)
            crime_obj.fetch_data()
            year1=crime_obj.year
            first_crime_count=crime_obj.crime_number_count
            max1=max(first_crime_count)
            #flash(first_crime_count)
            crime_obj2=fetch_data_for_age_yearwise(start_year=2014,end_year=2018)
            crime_obj2.fetch_data()
            year2=crime_obj2.year
            second_crime_count=crime_obj2.crime_number_count
            max2=max(second_crime_count)
            #flash(second_crime_count)
            first_crime_count= dict(zip(crime_obj.crime_type_data,first_crime_count))
            #flash(first_crime_count)
            first_crime_count=first_crime_count.items()
            second_crime_count= dict(zip(crime_obj.crime_type_data,second_crime_count))
            #flash(second_crime_count)
            second_crime_count=second_crime_count.items()

    return render_template('/dashboard_bar_graph.html',first_year=year1,first_total_crime=first_total_crime,first_criminal_age_under18=first_criminal_age_under18,first_criminal_age_18_25=first_criminal_age_18_25,first_criminal_age_beyond_25=first_criminal_age_beyond_25,second_year=year2,second_total_crime=second_total_crime,second_criminal_age_under18=second_criminal_age_under18,second_criminal_age_18_25=second_criminal_age_18_25,second_criminal_age_beyond_25=second_criminal_age_beyond_25,first_crime_count=first_crime_count,second_crime_count=second_crime_count,max1=max1,max2=max2)





@app.route('/dashboard_pi_graph',methods=['POST','GET'])
@login_required
def dashboard_pi_graph():
    crime_data_pi=fetch_id_age_times()
    crime_data_pi.fetch_data()
    year1=""
    first_crime_count={}
    max1=0
    sum1=0
    year2=""
    second_crime_count={}
    max2=0
    sum2=0

    if request.method == 'POST':
        pi_graph_id_number = plot_pi_graph(labels=crime_data_pi.crime_type_data,sizes=crime_data_pi.crime_number_count,graph_title="Graph Between Crime and Number of times Crime happened")
        pi_graph_id_number.make_plot()


        crime_obj=fetch_data_for_age_yearwise(start_year=2009,end_year=2013)
        crime_obj.fetch_data()
        year1=crime_obj.year
        first_crime_count=crime_obj.crime_number_count
        max1=max(first_crime_count)
        sum1=sum(first_crime_count)
        #flash(first_crime_count)
        crime_obj2=fetch_data_for_age_yearwise(start_year=2014,end_year=2018)
        crime_obj2.fetch_data()
        year2=crime_obj2.year
        second_crime_count=crime_obj2.crime_number_count
        max2=max(second_crime_count)
        sum2=sum(second_crime_count)
        #flash(second_crime_count)
        first_crime_count= dict(zip(crime_obj.crime_type_data,first_crime_count))
        #flash(first_crime_count)
        first_crime_count=first_crime_count.items()
        second_crime_count= dict(zip(crime_obj.crime_type_data,second_crime_count))
        #flash(second_crime_count)
        second_crime_count=second_crime_count.items()

    return render_template('/dashboard_pi_graph.html',year1=year1,year2=year2,first_crime_count=first_crime_count,second_crime_count=second_crime_count,max1=max1,max2=max2,sum1=sum1,sum2=sum2)



@app.route('/dashboard_feedback',methods=['GET','POST'])
@login_required
def dashboard_feedback():
    data=None
    cursor=mysql.connection.cursor()
    result=cursor.execute("Select * from contact")
    if(result>0):
        data=cursor.fetchall()
        #flash(data)
    return render_template('/dashboard_feedback.html',data=data)


@app.route('/reply_to_feedback/<int:f_id>',methods=['GET',"POST"])
@login_required
def reply_to_feedback(f_id):
    cursor=mysql.connection.cursor()
    cursor.execute("Select * from contact where id=%s",[f_id])
    data=cursor.fetchone()
    email=data['email']
    name=data['name']
    #flash(email)
    if request.method=='POST':
        subject=request.form['subject']
        message=request.form['msg']
        #flash(subject)
        try:
            msg =Message(
                'Crime Rate Prediction',
                sender='prince.crimerate@gmail.com',
                recipients=["%s" %(email)]
            )
            address="Hi %s !"%(name)
            msg.html=( address+"<br>"+ message + "<br><br>Best Regards from<br>Crime Rate Prediction Team<br>" )
            #flash(msg.html)
            mail.send(msg)

            flash("Replied Successfully",'success')
            return redirect('/dashboard_feedback')

        except Exception as e:
            flash(e,'danger')
            #return redirect('/forget_password')


    return render_template('reply_to_feedback.html',data=data)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/profile',methods=['GET','POST'])
@login_required
def profile():
    cursor=mysql.connection.cursor()
    cursor.execute("SELECT * from users where id=%s",[session['userid']])
    data=cursor.fetchall()
    if request.method == 'POST':

        #check whether file is selected
        if 'profile_pic' not in request.files:
            flash("No file Part available",'danger')
            return redirect(request.url)

        profile_pic=request.files['profile_pic']
        if profile_pic.filename == '':
            flash("No file selected ",'danger')
            return redirect(request.url)

        if profile_pic and allowed_file(profile_pic.filename):
            filename = secure_filename(profile_pic.filename)
            profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
            #flash('Uploaded :'+filename)
            filename = 'static/profile_pic/' + filename
            cursor.execute("UPDATE users set profile_pic=%s where id=%s",[filename,session['userid']])
            mysql.connection.commit()
            cursor.close()
            return redirect(request.url)



        #cursor.execute("UPDATE users set profile_pic=")
    return render_template('/profile.html',data=data)


@app.route('/edit_user_details',methods=['GET','POST'])
@login_required
def edit_user_details():
    #creating cursor
    cursor=mysql.connection.cursor()
    user_id=session['userid']
    result = cursor.execute("SELECT * from users where id=%s",[user_id])
    if result >0:
        user_data=cursor.fetchone()
    if request.method == 'POST':
        name=request.form['name']
        email=request.form['email']
        mobile=request.form['mobile']
        aadhar=request.form['aadhar']
        try:
            cursor.execute("UPDATE users set name=%s,email=%s,mobile=%s,aadhar=%s where id=%s", [name,email,mobile,aadhar,user_id])
            mysql.connection.commit()
            flash("Data updated successfully",'success')
            return redirect('/profile')
        except Exception as e:
            flash(e.message+"Duplicate Entry ",'danger')
        cursor.close()
    return render_template('/edit_user_details.html',user_data=user_data)


@app.route('/user_dashboard',methods=['GET','POST'])
@login_required
def user_dashboard():
    return render_template('/user_dashboard.html')





@app.route('/change_user_password',methods=['GET','POST'])
@login_required
def change_user_password():
    if request.method == 'POST':
        old_password=request.form['old_password']
        #request.form['old_password']
        new_password=sha256_crypt.encrypt(str(request.form['new_password']))
        #reques.form['new_password']
        confirm_new_password=request.form['confirm_new_password']
        #request.form['confir_new_password']


        cursor=mysql.connection.cursor()
        cursor.execute("Select * from users where id=%s",[session['userid']])
        data=cursor.fetchone()
        if sha256_crypt.verify(old_password,data['password']):
            if sha256_crypt.verify(confirm_new_password,new_password):
                try:
                    cursor.execute("UPDATE users set password=%s where id=%s",[new_password,session['userid']])
                    mysql.connection.commit()
                    session.clear()
                    flash('Password Changed Successfully','success')
                    return redirect('/login')
                except Exception as e:
                    flash(str(e.message),'danger')
                    return redirect('/change_user_password')
                finally:
                    cursor.close()

            else:
                flash("Confirm Password does not atch",'danger')
                return redirect(request.url)
        else:
            flash("Old Password Wrong",'danger')
            return redirect(request.url)




    return render_template('/change_user_password.html')



@app.route('/forget_password',methods=['GET','POST'])
def forget_password():
    email_form=True
    otp_form=False
    set_password_form=False
    if request.method == 'POST':
        cursor=mysql.connection.cursor()
        if request.form['submit'] == "Send OTP":
            email=request.form['email']
            result=cursor.execute("Select * from users where email=%s",[email])
            if result>0:
                otp_contents="ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
                otp_contents=list(otp_contents)
                random.shuffle(otp_contents)
                otp=random.sample(otp_contents,6)
                otp=''.join(otp)
                session['otp_send_to_mail']=otp
                session['candidate_email']=email

                #sending Email to the users
                mail_sent =False
                try:
                    msg =Message(
                        'Crime Rate Prediction',
                        sender='somasekhardarisi7@gmail.com',
                        recipients=["%s" %(email)]
                    )
                    msg.html=("%s</b> is the OTP for your verification.Please Enter this OTP to reset your Account Password.<br>Thank You !<br><br>Best Regards from<br>Crime Rate Prediction Team<br>" %(otp))
                    mail.send(msg)
                    mail_sent=True
                    email_form=False
                    otp_form=True
                    set_password_form=False
                    flash("An OTP has send to your email.Enter this to verify",'info')
                    #return redirect('/forget_password')

                except Exception as e:
                    mail_not_send=str(e)
                    email_form=True
                    otp_form=False
                    set_password_form=False
                    flash(mail_not_send,'danger')
                    #return redirect('/forget_password')

            else:
                flash("Email does not belong to registered id.Plsease enter a valid email",'danger')
                #return redirect('/forget_password')

        if request.form['submit'] == "Verify OTP":
            otp_send=request.form['OTP_SEND']

            if otp_send != session['otp_send_to_mail']:
                email_form=False
                otp_form=True
                set_password_form=False
                flash("OTP does not match",'danger')
                #return redirect('/forget_password')
            else:
                email_form=False
                otp_form=False
                set_password_form=True
                #return redirect('/forget_password')
        if request.form['submit'] == "Change Password":
            password=sha256_crypt.encrypt(str(request.form['password']))
            confirm_password=request.form['confirm_password']
            if sha256_crypt.verify(confirm_password,password):
                try:
                    cursor.execute("UPDATE users set password=%s where email=%s",[password,session['candidate_email']])
                    mysql.connection.commit()
                    session.clear()
                    flash('Password Changed Successfully','success')
                    return redirect('/login')
                except Exception as e:
                    email_form=False
                    otp_form=False
                    set_password_form=True
                    flash(str(e.message),'danger')
                    return redirect('/forget_password')
                finally:
                    cursor.close()
            else:
                email_form=False
                otp_form=False
                set_password_form=True
                flash("Confirm Password does not match",'danger')

    return render_template('/forget_password.html',otp_form=otp_form,set_password_form=set_password_form,email_form=email_form)

#creating logout functionality
@app.route('/logout')
def logout():
    del session['logged_in']
    session.clear()
    flash("You are successfully logout",'success')
    return redirect(url_for('login'))

if __name__=='__main__':
    app.secret_key='$0pi@123'
    app.run(debug=True)
