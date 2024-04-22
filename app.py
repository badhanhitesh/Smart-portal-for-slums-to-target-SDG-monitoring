from flask import Flask, render_template, redirect, request, session
import pymongo
import bcrypt
import os
import math
import datetime
from werkzeug.utils import secure_filename
import urllib.request, json
from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent="Your_Name")
import requests
from bson.objectid import ObjectId
from bs4 import BeautifulSoup
import stripe
import smtplib
import cv2
import numpy as np
import base64

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['EXPLAIN_TEMPLATE_LOADING'] = True
stripe.api_key = "sk_test_51Mk5HKSGzT4olYzPNLGLAFfZ6477nDkagicbnpSkAVze7J2EmkxbUaNNXS5QLlw3zy8f1wiqSaybKr6KWe2Tlytz00qipZKY5b"

smtp_server = 'smtp.office365.com'
port = 587 # for TLS
username = 'sdgforslums@outlook.com'
password = 'LBSwinner'
smtp = smtplib.SMTP(smtp_server, port)
smtp.starttls()
smtp.login(username, password)

from email.message import EmailMessage

def page_not_found(e):
    return render_template('404.html'), 404

app.register_error_handler(404, page_not_found)

client = pymongo.MongoClient("mongodb://localhost:27017")  # Updated MongoDB connection string
mapbox_access_token = 'pk.eyJ1IjoidmlyYXQxOCIsImEiOiJjbGVlbXdiNjEwM2djM25vZHZtZXQ0djdiIn0.SPzS-O44BQeMfiYWNWC_aA'

db = client.get_database('LBS')
users = db.users
slums = db.slum_details
activities = db.activities
activityReq = db.requests
jobs = db.Jobs
jobReqs = db.jobRequests

YOUR_DOMAIN = "http://127.0.0.1:5000"

# Remaining code remains unchanged




@app.route('/create-checkout-session',methods=["POST"])
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            line_items = [
                {
                    # "price":"price_1Mk6PHSGzT4olYzPOpTOKlq0",
                    "price":"price_1MkB0gSGzT4olYzPnAEojX5p",
                    "quantity":1
                }
            ],
            mode="payment",
            success_url=YOUR_DOMAIN + "/success.html",
            cancel_url = YOUR_DOMAIN + "/cancel.html"
        )
    except Exception as e:
        return str(e)

    return redirect(checkout_session.url,code=303)


def getTemp(lat,lon):
    api_key = '542ffd081e67f4512b705f89d2a611b2'
    url=f'http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}'
    response = requests.get(url)
    weather_data = response.json()

    return {'temperature':math.floor(weather_data['list'][0]['main']['temp']-273.15),'sky':weather_data['list'][0]['weather'][0]['description'],"icon":weather_data['list'][0]['weather'][0]['icon']}



for slum in slums.find():
    data=getTemp(slum['latitude'],slum['longitude'])
    slums.update_one({'city':slum['city']},
                        { '$set': { "temp" :data} }) 

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"



def formatMail(to,sub,name,body):
     msg = EmailMessage()
     msg['Subject'] = sub
     msg['From'] = 'sdgforslums@outlook.com'
     msg['To'] = to
     msg.set_content(
         '''
                <!DOCTYPE html>
                <html>
                    <body>
                        <div style="background-color:#eee;padding:10px 20px;">
                            <h2 style="font-family:Georgia, 'Times New Roman', Times, serif;color#454349;">'''+sub+'''</h2>
                        </div>
                        <div style="padding:20px 0px">
                            <div>
                                <img src="https://www.un.org/sites/un2.un.org/files/2019/12/sdg_wheel_print_transparent.png" style="height: 150px;  margin-left: auto;margin-right: auto;display: block;"/>
                                <div>
                                   <p>
                                    Dear '''+name+''',<br/><br/>
                                    '''+body+'''
                                    Best regards,<br/>
                                    SDG for Slums<br/>
                                    </p>
                                </div>
                            </div>
                        </div>
                    </body>
                </html>
                ''', subtype='html')
     smtp.send_message(msg)
    
@app.route("/")
def index():
    return render_template('home.html');

@app.route('/dashboard/admin/slum/info/<string:slumName>', methods=["POST", "GET"])
def infoSlum(slumName):
    try:
        if request.method == 'POST':
            data=slums.find_one({'slumName':slumName})
            lat=data['latitude']
            lon=data['longitude']
            name=data['slumName']
            address=data['address']
            api_key = '542ffd081e67f4512b705f89d2a611b2'
            url = f'http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}'
            response = requests.get(url)
            url1=f'http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}'
            response1 = requests.get(url1)
            
            weather_data = response.json()
            forcast_data = response1.json()
            activities=activityReq.find({"slumName":slumName,"status":"Approve"}).sort('date', -1)            
            garbageData=db.GarbageData
            garbageStatus=[];
            garbage=garbageData.find()
            for i in garbage:
                placeImg='<img src=\'data:image/jpeg;base64,'+str(i['image'])+'\''+'/>'
                decoded_data = base64.b64decode(i['image'])
                # convert the bytes object to a numpy array
                np_data = np.frombuffer(decoded_data, dtype=np.uint8)

                # decode the numpy array as an image using cv2
                img = cv2.imdecode(np_data, cv2.IMREAD_COLOR)
                # Converting image to grayscale
                gray= cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

                # Applying SIFT detector
                sift = cv2.xfeatures2d.SIFT_create()
                kp = sift.detect(gray, None)

                # Marking the keypoint on the image using circles
                img=cv2.drawKeypoints(gray ,
                                    kp ,
                                    img ,
                                    flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

                cv2.imwrite('./static/GarbageData/Garbage.jpg', img)

                kp , des = sift.detectAndCompute(gray,None)
                print(len(kp))

                if(len(kp) >= 500):
                    garbageStatus.append("Garbage is Not collected");
                else:
                    garbageStatus.append("Garbage is Successfully Collected");
            formatMail('abhishek.a.patil112@gmail.com',"Garbage not collected in "+name,'Officer','&emsp;&emsp;This mail is to inform you about the garbage collection status at '+name+' ,'+address + '. Please collect it on urgent basis.'+'<br/><br/>')
            return render_template('slumInfo.html',slumName=slumName,data=data,mapbox_access_token=mapbox_access_token,weather_data=weather_data,forcast_data=forcast_data,activities=activities,garbageData=garbageData.find(),garbageStatus=garbageStatus)
        
    except:
        return render_template('slumInfo.html',slumName=slumName,data=data,mapbox_access_token=mapbox_access_token,weather_data=weather_data,forcast_data=forcast_data,activities=activities,garbageData=garbageData.find(),garbageStatus=garbageStatus,message="Error in sending mail please try later")
        

    data=slums.find_one({'slumName':slumName})
    lat=data['latitude']
    lon=data['longitude']
    api_key = '542ffd081e67f4512b705f89d2a611b2'
    url = f'http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}'
    response = requests.get(url)
    url1=f'http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}'
    response1 = requests.get(url1)
    
    weather_data = response.json()
    forcast_data = response1.json()
    activities=activityReq.find({"slumName":slumName,"status":"Approve"}).sort('date', -1)
    garbageData=db.GarbageData
    garbageStatus=[];
    garbage=garbageData.find()
    for i in garbage:
        decoded_data = base64.b64decode(i['image'])
        # convert the bytes object to a numpy array
        np_data = np.frombuffer(decoded_data, dtype=np.uint8)

        # decode the numpy array as an image using cv2
        img = cv2.imdecode(np_data, cv2.IMREAD_COLOR)
        # Converting image to grayscale
        gray= cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

        # Applying SIFT detector
        sift = cv2.xfeatures2d.SIFT_create()
        kp = sift.detect(gray, None)

        # Marking the keypoint on the image using circles
        img=cv2.drawKeypoints(gray ,
                            kp ,
                            img ,
                            flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

        cv2.imwrite('./static/data/GarbageData/Garbage.jpg', img)

        kp , des = sift.detectAndCompute(gray,None)
        print(len(kp))

        if(len(kp) >= 450):
            garbageStatus.append("Garbage is Not collected");
        else:
            garbageStatus.append("Garbage is Successfully Collected");
    
    return render_template('slumInfo.html',slumName=slumName,data=data,mapbox_access_token=mapbox_access_token,weather_data=weather_data,forcast_data=forcast_data,activities=activities,garbageData=garbageData.find(),garbageStatus=garbageStatus)


@app.route('/dashboard/user/job/info/<string:jobName>', methods=["POST", "GET"])
def info(jobName):
    if request.method == "POST":
        try:
            name = request.form['name']
            dob = request.form['dob']
            slumName = request.form['slumName']
            DiscoveredSlum=slums.find({'slumName':slumName})
            for i in DiscoveredSlum:
                authority=i['authority']
            aadharNo=request.form['aadhaar']
            gender = request.form['gender']
            occupation = request.form['occupation']
            education = request.form['education']
            contact = request.form['contact']
            email = request.form['email']
            address = request.form['address']
            user_input = {'name': name,'slumName':slumName, 'dob': dob,'aadharNo':aadharNo, 'gender': gender, 'occupation':occupation,'education':education,'contact':contact,'email':email,'address':address,'authority':authority,'status':"pending"}
            jobReqs.insert_one(user_input)
            now = datetime.datetime.now()
            hour = now.hour

            if hour < 12:
                greeting = "Good Morning"
            elif hour < 18:
                greeting = "Good Afternoon"
            else:
                greeting = "Good Night"
            formatMail(session['email'],"Thank you for applying for "+occupation,session['name'],'&emsp;&emsp;Thank you for submitting your job application to SDG Platform. We are delighted to know that you are interested in jobs related to this '+occupation+'.<br/> Soon we will contact you regarding status of your job application.<br/><br/>')
            return render_template('dashboardUser.html',greeting=greeting,onGoingActivites=activityReq.find({"status":"Approve"}),no_ofActivities=len(list(activityReq.find({"status":"Approve"}))));
        except:
            return render_template('dashboardUser.html',greeting=greeting,onGoingActivites=activityReq.find({"status":"Approve"}),no_ofActivities=len(list(activityReq.find({"status":"Approve"}))));
    else:
        return render_template('jobForm.html',jobName=jobName,slums=slums.find())
    

@app.route("/dashboard/Admin")
def dashboardAdmin():
    now = datetime.datetime.now()
    hour = now.hour

    if hour < 12:
        greeting = "Good Morning"
    elif hour < 18:
        greeting = "Good Afternoon"
    else:
        greeting = "Good Night"
    return render_template('dashboardAdmin.html',greeting=greeting,slums=slums.find(),no_ofSlums=len(list(slums.find())));


@app.route("/dashboard/User")
def dashboardUser():
    now = datetime.datetime.now()
    hour = now.hour

    if hour < 12:
        greeting = "Good Morning"
    elif hour < 18:
        greeting = "Good Afternoon"
    else:
        greeting = "Good Night"
    return render_template('dashboardUser.html',greeting=greeting,onGoingActivites=activityReq.find({"status":"Approve"}),no_ofActivities=len(list(activityReq.find({"status":"Approve"}))));


@app.route("/login", methods=["POST", "GET"])
def login():
    message = ''

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

       
        email_found = users.find_one({"email": email})
        if email_found:
            user=email_found['name']
            email_val = email_found['email']
            passwordcheck = email_found['password']
            pic=email_found['profilePic']
            role=email_found['role']
            
            if (password==passwordcheck):
                session['name'] = user;
                session['profilePic'] = pic
                session['email']=email
                session['role']=role
                if(role=='admin'):
                    return redirect('/dashboard/Admin')
                else:
                    return redirect('/dashboard/User')

            message = 'Wrong password'
            return render_template('login.html', message=message)
        else:
            message = 'Email not found'
            return render_template('login.html', message=message)
    return render_template('login.html', message=message)




     


@app.route("/register" , methods=["POST", "GET"])
def register():
   if request.method =="POST":
        try:
            user = request.form.get("fullname")
            email = request.form.get("email")
            file = request.files['img']
            if file:
                filename = secure_filename(file.filename)
                file.save(os.path.join('./static/data/profilePics/', filename))
                path='/data/profilePics/'+filename;
            else :
                path="/data/profilePics/default_user.png"

            password1 = request.form.get("password1")
            password2 = request.form.get("password2")

            user_found = users.find_one({"name": user})
            email_found = users.find_one({"email": email})
            if user_found:
                message = 'There already is a user by that name'
                return render_template('register.html', message=message)
            if email_found:
                message = 'This email already exists in database'
                return render_template('register.html', message=message)
            if password1 != password2:
                message = 'Passwords should match!'
                return render_template('register.html', message=message)
            else:
                user_input = {'name': user, 'email': email, 'password': password1,'profilePic':path,'role':'user'}
                users.insert_one(user_input)
                session['name']=user;
                session['profilePic']=path;
                session['email']=email
                session['role']='user'
                formatMail(session['email'],"Thank you for registering for a nobel cause",session['name'],'&emsp;&emsp;We are delighted to welcome you to our website dedicated to the development of slum areas. By registering with us, you have taken the first step towards making a positive impact on the lives of people living in impoverished urban areas. Our mission is to improve the living conditions and opportunities for the millions of people who live in slums. We believe that by working together, we can achieve lasting change and create a better future for these communities. <br/><br/> &emsp;&emsp;As a registered user, you will have access to a wealth of information and resources related to slum development. You can browse our website to learn about our projects, read success stories, and find out how you can get involved. We also encourage you to share your ideas and experiences with us. Your input and feedback are crucial to helping us improve our programs and services. <br/><br/> &emsp;&emsp;Thank you for joining us in our efforts to make a difference in the lives of people living in slums. We look forward to working with you and seeing the positive impact we can create together. <br/><br/>')
                return redirect('/login')
        except:
            return redirect('/login')

   return render_template('register.html')




@app.route("/logout", methods=["POST", "GET"])
def logout():
    session["name"] = "";
    return redirect("/")


@app.route("/dashboard/admin/addSlum", methods=["POST", "GET"])
def addSlum():
    if request.method == "POST":
        slumName = request.form.get("slumName")
        city = request.form.get("city")
        authority = request.form.get("authority")
        latitude=request.form.get("latitude")
        longitude=request.form.get("longitude")
        address=geolocator.geocode(city).address
        slum_input = {'slumName': slumName, 'city':city,'authority':authority,'latitude':latitude,'longitude':longitude,'address':address}
        slums.insert_one(slum_input)
        
        return render_template('slumform.html',message="Slum added successfully")
    return render_template('slumform.html',message="",mapbox_access_token=mapbox_access_token)
    
@app.route("/dashboard/user/activities", methods=["POST", "GET"])
def showActivites():
    return render_template('UserActivity.html',activities=activities.find())

@app.route("/dashboard/user/jobs", methods=["POST", "GET"])
def showJobs():
    return render_template('userJobs.html',jobs=jobs.find())

@app.route("/dashboard/user/activity/status", methods=["POST", "GET"])
def userActivityStatus():
    return render_template('UserActivityRequestStatus.html',activityRequests=activityReq.find({"userName": session['name'], "userEmail": session['email'] }))

@app.route("/dashboard/admin/activity/status", methods=["POST", "GET"])
def adminActivityStatus():
    return render_template('AdminActivityRequestStatus.html',activityRequests=activityReq.find({"authority": session['name']}))

@app.route("/dashboard/admin/jobs/requests", methods=["POST", "GET"])
def adminJobsStatus():
    return render_template('AdminJobRequests.html',jobReqs=jobReqs.find({"authority": session['name'],"status":"pending"}),jobAppr=jobReqs.find({"authority": session['name'],"status":"approved"}))

@app.route('/dashboard/admin/activity/review/<string:activityId>',methods=["POST", "GET"])
def approveActivity(activityId):
    if request.method == 'POST':
        try:
            status=request.form.get('status')
            remarks=request.form.get('remarks')
            activityReq.find_one_and_update({"_id": ObjectId(activityId)},{'$set':{"status":status,"remark":remarks}})
            Details=activityReq.find({'_id':ObjectId(activityId)})
            for i in Details:
                slumName=i['slumName']
                event=i['event']
                status=i['status']
                authority=i['authority']
                userEmail=i['userEmail']
                userName=i['userName']

            formatMail(userEmail,"Update regarding to activity request",userName,'&emsp;&emsp;Thank you for submitting your application for hosting '+event+' in '+slumName+'. Your application has been '+ status+ ' by '+authority+'.<br/><br/>')
            return render_template('activityApprove.html',activity=activityReq.find_one({"_id": ObjectId(activityId)}),message="Approved")
        except:
            return render_template('activityApprove.html',activity=activityReq.find_one({"_id": ObjectId(activityId)}),message="Approved")
    else:
        return render_template('activityApprove.html',activity=activityReq.find_one({"_id": ObjectId(activityId)}))
    
@app.route('/dashboard/user/activity/review/<string:activityId>',methods=["POST", "GET"])
def approveActivityStatus(activityId):
        return render_template('activityApproveDetails.html',activity=activityReq.find_one({"_id": ObjectId(activityId)}))
    
@app.route('/dashboard/user/activity/unregister/<string:activityId>',methods=["POST", "GET"])
def unregisterActivity(activityId):
    activityReq.find_one_and_update({"_id": ObjectId(activityId)},{'$pull':{"participants":{"name":session['name'],"email":session['email']}}})
    now = datetime.datetime.now()
    hour = now.hour

    if hour < 12:
        greeting = "Good Morning"
    elif hour < 18:
        greeting = "Good Afternoon"
    else:
        greeting = "Good Night"
    return render_template('dashboardUser.html',greeting=greeting,onGoingActivites=activityReq.find({"status":"Approve"}),no_ofActivities=len(list(activityReq.find({"status":"Approve"}))));

@app.route('/dashboard/user/activity/cancelRequest/<string:activityId>',methods=["POST", "GET"])
def cancelActivity(activityId):
    activityReq.delete_one({"_id": ObjectId(activityId)})
    return render_template('UserActivityRequestStatus.html',activityRequests=activityReq.find({"userName": session['name'], "userEmail": session['email'] }))
    
@app.route('/dashboard/user/activity/register/<string:activityId>',methods=["POST", "GET"])
def activityRegister(activityId):
    if request.method == 'POST':
        activity=activityReq.find_one({"_id": ObjectId(activityId)})
        slum=slums.find_one({"slumName":activity['slumName'] })
        activityReq.find_one_and_update({"_id": ObjectId(activityId)},{'$addToSet':{"participants":{"name":session['name'],"email":session['email']}}})
        now = datetime.datetime.now()
        hour = now.hour

        if hour < 12:
            greeting = "Good Morning"
        elif hour < 18:
            greeting = "Good Afternoon"
        else:
            greeting = "Good Night"
        return render_template('dashboardUser.html',greeting=greeting,onGoingActivites=activityReq.find({"status":"Approve"}),no_ofActivities=len(list(activityReq.find({"status":"Approve"}))));
    else:
        activity=activityReq.find_one({"_id": ObjectId(activityId)})
        slum=slums.find_one({"slumName":activity['slumName'] })
        return render_template('activityRegister.html',slum=slum,activity=activity,message="Approved",mapbox_access_token=mapbox_access_token,no_of_participents=len(activity['participants']))
    

@app.route('/dashboard/user/activity/info/<string:activityName>',methods=["POST", "GET"])
def infoActivity(activityName):
    if request.method == "POST":
        slumName = request.form.get("slumName")
        userName=  request.form.get("userName")
        userEmail=request.form.get("userEmail")
        userContactNumber=request.form.get("userContactNumber")
        designation=request.form.get("designation")
        address=request.form.get("address")
        date_str = request.form.get("date") # Get the date string from the form
        time_str = request.form.get("time") # Get the time string from the form
        
        # Convert the date and time strings to datetime objects
        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        time_obj = datetime.datetime.strptime(time_str, '%H:%M')
        organization=request.form.get("organisation")
        description=request.form.get('description')
        reasources=request.form.get("reasources")
        status="Pending"
        Remark="No Remark";
        DiscoveredSlum=slums.find({'slumName':slumName})
        for i in DiscoveredSlum:
            authority=i['authority']

        request_input={'slumName':slumName,'userName':userName,'userContactNumber':userContactNumber,'userEmail':userEmail,'designation':designation,'address':address,'date':date_obj,'time':time_obj,'organization':organization,'description':description,'reasources':reasources,'status':status,'remark':Remark,'event':activityName,'authority':authority,'participants':[{"name":session['name'],'email':session['email']}]}
        activityReq.insert_one(request_input)
        return render_template('ActivityInfo.html',activityName=activityName,slums=slums.find(),message="You can see the status in status tab")
        
    else:
        return render_template('ActivityInfo.html',activityName=activityName,slums=slums.find())

@app.route('/dashboard/user/activity/registered',methods=["POST", "GET"])
def regiteredActivity():
    return render_template('myRegisteredActivity.html', MyActivities=activityReq.find())

@app.route('/dashboard/admin/job/remove/<string:jobId>',methods=["POST", "GET"])
def jobFullfilled(jobId):
    try:
        jobReqs.update_one({"_id": ObjectId(jobId)},{ '$set': { "status" :"approved"} })
        Details=jobReqs.find({'_id':ObjectId(jobId)})
        for i in Details:
            occupiation=i['occupation']
            authority=i['authority']
            userEmail=i['email']
            userName=i['name']
        formatMail(userEmail,"Update regarding to your job request",userName,'&emsp;&emsp;Congratulations as your application regarding job in '+occupiation+ ' is accepted.<br/> Kindly share your basic details at '+username+ '. Your designated authority is '+ authority +'. Kindly do the needful.<br/><br/>')
        return redirect('/dashboard/admin/jobs/requests')
    except:
        return redirect('/dashboard/admin/jobs/requests')
    
@app.route('/about',methods=["POST", "GET"])
def about():
    return render_template('about.html')


if __name__ == "__main__":
    app.run()