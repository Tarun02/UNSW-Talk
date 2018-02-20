#!/web/cs2041/bin/python3.6.3

# written by z5152892@unsw.edu.au October 2017
# as a starting point for COMP[29]041 assignment 2
# https://cgi.cse.unsw.edu.au/~cs2041/assignments/UNSWtalk/

from collections import defaultdict
from flask import *
import os,re
import sys
import datetime
import fileinput
import time
non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)




students_dir = os.path.join("static","dataset-medium")

app = Flask(__name__)

##Start url
@app.route('/', methods=['GET','POST'])
@app.route('/start', methods=['GET','POST'])
def start():
    return render_template('login.html')

##For login
@app.route('/login',methods = ['GET','POST'])
def login():
    zid = request.form.get('login', '')
    zid = re.sub(r"/s*$",'',zid)
    password = request.form.get('password', '')

    Flag = 0
    if zid:
        for file_names in os.listdir(students_dir):
            if file_names == zid:
                Flag = 1
                req_file = file_names
                break
    else:
        return render_template("login.html")
        
    if Flag ==1:
        req_file_name = os.path.join(students_dir, req_file, "student.txt")
        with open(req_file_name) as f:
            details_list = f.readlines()
        for j in range(len(details_list)):
            password_line = re.search(r"password: (\w+).*",details_list[j])
            if password_line:
                password_req = password_line.group(1)
                details_list.remove(details_list[j])
                break

        if password_req == password:
            image_file = os.path.join(students_dir, req_file, "img.jpg")
            session['zid'] = encryption(zid)
            return redirect(url_for('profile',name = encryption(zid)))
        else:
            return render_template("login.html",error = "Wrong Password")
    else:
        return render_template("login.html",error = "Unknown loginid - are you a student of UNSW?")
    
##For logout clears the session
@app.route('/logout',methods = ['GET','POST'])
def logout():
    session.pop('zid',None)
    return render_template("login.html")

##After login we go to profile page
@app.route('/profile<name>',methods=['GET','POST'])
def profile(name):
    zid = decryption(name)

    image_file = os.path.join(students_dir, zid, "img.jpg")
    frnd_req,real_frnd = friend_req(zid)
    return render_template("profile.html",rp = 1,e = name,results = all_name(),\
                           profile = profile_extracting(zid),\
                           f_r = frnd_req,friends = real_frnd,\
                           image = image_file,messages = posts(zid))

##This is for just viewing the profile page
@app.route('/<zid>',methods = ['GET','POST'])
def just_profile(zid):
    if 'zid' in session:
        zid = re.sub(r'^\s*','',zid)
        if zid != "logout":
            frnd_req,real_frnd = friend_req(zid)
            d_zid = session['zid']
            image_file_name = os.path.join(students_dir, zid, "img.jpg")
            return render_template("profile.html",rp=0,e=d_zid,results = all_name(),\
                                   profile = profile_extracting(zid),\
                                   friends = real_frnd,\
                                   image = image_file_name,\
                                   messages = posts(zid))
        else:
            return render_template("login.html",error = None)
    else:
        return render_template("login.html", error = "Please login first.")

##This url is for making posts
@app.route('/make_posts',methods = ['GET','POST'])
def make_posts():
    if 'zid' in session:
        zid = session['zid']
    else:
        return render_template("login.html", error = "Please login first.")
    o_zid = decryption(zid)
    
    message = request.form.get('message','')
    if message != "":
        message_file = os.path.join(students_dir,o_zid,str(max_message(o_zid)+1) + ".txt")
        temp_message = message
        message = []
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        timestamp = st.split(" ")
        try:
            with open(message_file,"w") as f:
                f.write("message: %s\n" %temp_message)
                f.write("from: %s\n" %o_zid)
                f.write("time: %sT%s+0000\n"%(timestamp[0],timestamp[1]))
                f.close()
            
        except OSError:
            message = ''

    return redirect(url_for('profile', name = zid))
    
 ##For accepting friend request   
@app.route('/add_friend<a_f>',methods = ['POST','GET'])
def add_friend(a_f):
    if 'zid' in session:
        zid = session['zid']
    else:
        return render_template("login.html", error = "Please login first.")
    o_zid = decryption(zid)
    frnd_zid = a_f

    frnd_file = os.path.join(students_dir, o_zid, "student.txt") 
    with open(frnd_file) as f:
        frnds_ext = f.readlines()

    for i in range(len(frnds_ext)):
        friends = re.match(r"friends: \((.*)\)",frnds_ext[i])
        if friends:
            old_frnds = friends.group(1) + ')'
            new_frnds = friends.group(1) + ', '+ frnd_zid+ ')'
            break
    newline = []

    req_file = os.path.join(students_dir,o_zid,"student.txt")
    for line in fileinput.input(req_file, inplace=1):
        newline.append(line.replace(old_frnds, new_frnds))

    with open(req_file,"w") as f:
        for line in newline:
            f.writelines(line)
        

    return redirect(url_for('profile',name = zid))

##For canceling the friend request
@app.route('/cancel_friend<c_f>',methods = ['POST','GET'])
def cancel_friend(c_f):
    if 'zid' in session:
        zid = session['zid']
    else:
        return render_template("login.html", error = "Please login first.")
    o_zid = decryption(zid)

    cancel_friend = c_f
    cancel_file = os.path.join(students_dir,cancel_friend,"student.txt")
    student_data = open(cancel_file,"r").readlines()
    zid_comma=o_zid+','
    comma_zid=", "+o_zid
    comma_flag=0
    for word in student_data:
        if zid_comma in word:
            comma_flag=1
            break
    if comma_flag==0:
        for word in student_data:
            if comma_zid in word:
                comma_flag=-1
                break

    if comma_flag==-1:
            o_zid=comma_zid
    elif comma_flag	==1:
            o_zid=zid_comma
    newline=[]

    change_file = os.path.join(students_dir,cancel_friend,'student.txt')
    for line in fileinput.input(change_file, inplace=1):
        newline.append(line.replace(o_zid,""))

    with open(change_file,"w") as f:
        for line in newline:
            f.writelines(line)

    return redirect(url_for('profile',name = zid))

##For searching the friends and posts
@app.route('/search',methods = ['GET','POST'])
def search():
    string = request.form.get("name_search","")

    if 'zid' in session:
        decrypt_zid = session['zid']
    else:
        return render_template("login.html", error = "Please login first.")
    
    if string!="":
        results = {}
        profiles = all_name()
        for key in profiles:
            name = profiles[key]['Name']
            if re.search(string,name,re.IGNORECASE):
                image_file_name = os.path.join(students_dir, key, "img.jpg")
                results[key] = [name,image_file_name]
                


        zid = decryption(decrypt_zid)
        messages = posts(zid)
        search = {}
        for m in messages:
            if re.search(string,m[1][0],re.IGNORECASE):
                
                search[profiles[m[1][1]]['Name']] = m[1][0]
            
                
        return render_template("search.html",e = decrypt_zid,results = results,post_search = search)
    else:
        return redirect(url_for('profile',name = decrypt_zid))

## For finding out all names so that we can get results in search
def all_name():
    all_names = os.listdir(students_dir)

    all_profiles = {}
    for zid in all_names:
        all_profiles[zid] = profile_extracting(zid)

    return all_profiles

## For extracting each profile in the dataset
def profile_extracting(zid):
    zid = re.sub(r'^\s*','',zid)
    name_file = os.path.join(students_dir, zid, "student.txt")
    profile = {'Name':'','D.O.B':'','Courses':'','Email':'','Suburb':'','About me':''}
    with open(name_file) as n:
        name_extraction = n.readlines()

    for n in name_extraction:
        name = re.match(r"full_name: (.*)",n)
        bday = re.match(r"birthday: (.*)",n)
        course = re.match(r"courses: \((.*)\)",n)
        email_id = re.match(r"email: (.*)",n)
        suburb = re.match(r"home_suburb: (.*)",n)
        about_me = re.match(r"about me: (.*)$",n)
        if name:
            profile['Name'] = name.group(1)
        
        if bday:
            profile['D.O.B'] = bday.group(1)
        
        if course:
            profile['Courses'] = course.group(1)
        
        if email_id:
            profile['Email'] = email_id.group(1)

        if suburb:
            profile['Suburb'] = suburb.group(1)

        if about_me:
            profile['About me'] = about_me.group(1)

            
    profile['img'] =  os.path.join(students_dir, zid, "img.jpg")

    return profile

##For extracting friends
def friends_extract(zid):
    zid = re.sub(r'^\s*','',zid)
    frnd_file = os.path.join(students_dir, zid, "student.txt")
    
    with open(frnd_file) as f:
        frnds_ext = f.readlines()

    for f_e in frnds_ext:
        friends = re.match(r"friends: \((.*)\)",f_e)
        if friends:
            f_req = friends.group(1)
            break

    friends_name = {}
    friends_zid = f_req.split(",")
    for f_z in friends_zid:
        f_z = re.sub(r'^\s*','',f_z)
        p = profile_extracting(f_z)
        image_file_name = os.path.join(students_dir,f_z,"img.jpg")
        friends_name[f_z] = [p['Name'],image_file_name]
        image_file_name = ''

    return friends_name
##For knwoing their zid we can do it in the above function but i have come a long to change it
def friend_zid(zid):
    zid = re.sub(r"^\s+",'',zid)
    frnd_file = os.path.join(students_dir, zid, "student.txt")
    
    with open(frnd_file) as f:
        frnds_ext = f.readlines()

    for f_e in frnds_ext:
        friends = re.match(r"friends: \((.*)\)",f_e)
        if friends:
            f_req = friends.group(1)
            break

    friends_zid_dict = {}
    friends_zid = f_req.split(",")
    for i in range(len(friends_zid)):
        friends_zid[i] = re.sub(r'^\s*','',friends_zid[i])

    friends_zid_dict[zid] = friends_zid

    return friends_zid_dict
#This function is for knowing our friend requests from other persons
def friend_req(zid):
    all_friends = os.listdir(students_dir)

    friends_list = []
    for z in all_friends:
        friends_list.append(friend_zid(z))
            
    consider_frnds = []
    fake_frnds = []
    for i in friends_list:
        for j in i:
            if zid in i[j]:
                consider_frnds.append(j)
            else:
                fake_frnds.append(j)

    present_frnds = friend_zid(zid)
    frnd_req = set(consider_frnds) - set(present_frnds[zid])
    real_frnds = set(present_frnds[zid]) - set(fake_frnds)

    return frnd_req,real_frnds
        

#for message of each post and comment and replies
def message_extraction(file,zid):
    needed_file = os.path.join(students_dir,zid,file+".txt")
    with open(needed_file,encoding='utf-8') as f:
        posts_extract = f.readlines()

    msg = 0
    msg_from = 0
    for content in posts_extract:
        if re.match(r"^\s*from: (.*)\s*$",content):
            msg_from = re.match(r"^\s*from: (.*)\s*$",content).group(1)
            continue
        if re.match(r"\s*message: (.*)\s*$",content):
            message = re.match(r"\s*message: (.*)\s*$",content).group(1)
            if re.search(r"(z[\d]+)",message):
                number = re.findall(r"(z[\d]+)",message)
                for i in number:
                    name = profile_extracting(i)
                    message = re.sub(i,"<a href=/"+i+">"+name['Name']+"</a>",message)
            message = message.translate(non_bmp_map)
            msg = re.sub(r'\\n','<br>',message)
            continue

    if msg == 0:
        msg = ''
    if msg_from == 0:
        msg_from = ''

    tup = (msg,msg_from)
    return tup
##For arraging each post and commenst and replies in list of lists
def posts(zid):
    posts_content_file = os.path.join(students_dir,zid)
    posts_content = os.listdir(posts_content_file)

    messages = []
    original_messages = []
    for p in posts_content:
        if re.match(r"^\s*(\d)+-?(\d)*-?(\d)*.txt",p):
            p = re.sub(r".txt",'',p)
            messages.append((p.split("-")))

    messages = sorted(messages,key = len)
    for p in messages:
        if len(p) == 1:
            original_messages.append([p[0],message_extraction(p[0],zid)])
        if len(p) == 2:
            for i in original_messages:
                if i[0] == p[0]:
                    i.append([p[0]+'-'+p[1],message_extraction(p[0]+'-'+p[1],zid)])
                    break
        if len(p) == 3:
            for i in original_messages:
                for j in range(2,len(i)):
                    if i[j][0] == (p[0]+'-'+p[1]):
                        i[j].append(message_extraction(p[0]+'-'+p[1]+'-'+p[2],zid))

    return original_messages

##To get the max number of posts so that new post will get the next number
def max_message(zid):
    req_file_path = os.path.join(students_dir,zid)
    req_file = os.listdir(req_file_path)
    max_number = 0
    for i in range(len(req_file)):
        if re.match(r"^\s*(\d+).txt\s*$",req_file[i]):
            number = int(re.match(r"^\s*(\d+).txt\s*$",req_file[i]).group(1))
            if number > max_number:
                max_number = number
    
    return max_number

def encryption(zid):
    result = ""
    for c in range(0,len(zid)):
        if zid[c].isalpha():
            result = result + chr(ord(zid[c]) + 1)
        else:
            if zid[c] == '9':
                result = result + str(0)
            else:
                result = result + str(int(zid[c]) + 1)         
        
    return result

def decryption(zid):
    result = ""
    for c in range(0,len(zid)):
        if zid[c].isalpha():
            result = result + chr(ord(zid[c]) - 1)
        if zid[c].isdigit():
            if zid[c] == '0':
                result = result + str(9)
            else:
                result = result + str(int(zid[c]) - 1)
        else:
            result = result + chr(ord(zid[c]) - 1)         
        
    return result



if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(debug=True, port = 4343)
