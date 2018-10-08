import requests
import itertools
from bs4 import BeautifulSoup
from collections import OrderedDict
import datetime
import getpass

from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

#Login page
POST_LOGIN_URL = 'https://moodle.nu.edu.kz/login/index.php'
#Target page
REQUEST_URL = 'https://moodle.nu.edu.kz/my/'

#Accessing Dashboard
s = requests.Session()
def enter():
    user = raw_input('Enter Username of Your Moodle Account: ')
    passw = getpass.getpass('Enter Password of Your Moodle Account (password wont be shown on screen): ')

    payload = {
        'username': user,
        'password': passw  #Preferably set your password in an env variable and sub it in.
    }
    post = s.post(POST_LOGIN_URL, data=payload)
    page = s.get(REQUEST_URL)
    soup = BeautifulSoup(page.content, 'html.parser')

    title = soup.find("title").text
    title_comp = "moodle.nu.edu.kz: Log in to the site"
    title_req = "Dashboard"
    print

    if title == title_req:
        print "Page has been entered succesfully"
    elif title == title_comp:
        print "Page has not been accessed, please retry"
        enter()
    else:
        print "Something weird brah... I dunno. Retry ur input"
        enter()

enter()

page = s.get(REQUEST_URL)
soup = BeautifulSoup(page.content, 'html.parser')

#Web Scrapping Moodle for dates and events
dates = []
eventz = []
links = []
for events in soup.find_all("div", class_="event"):
    date = [event.text for event in events.find_all("div", class_="date")]
    dates.append(date)
    event_one = [event.text for event in events.find_all("a")]
    eventz.append(event_one)
    for link in events.find_all("a"):
        links.append(link.get("href"))
del links[1::2]

names = []
for link in links:
    page_new = s.get(link)
    soup_new = BeautifulSoup(page_new.content, 'html.parser')
    for name in soup_new.find_all("h1"):
        head, sep, tail = name.text.partition('-')
        names.append(head)

#Transforming date into understandable for Google API format
#Example:
#'Monday, 8 October, 11:59 PM' => '2018-10-8T23:59:00'
def transform_date(date_old):
    now = datetime.datetime.now()
    #Today, Tommorow
    parts=[]
    parts = date_old.split(",")
    if (len(parts)==2):
        p1,p2 = parts[1].split(":")
        pmam = ''.join(i for i in p2 if not i.isdigit()).strip()
        if pmam=="PM":
            h=int(p1)+12
        else:
            h=int(p1)
            min = ''.join(i for i in p2 if i.isdigit()).strip()
            if (parts[0]=='Today'):
                date = str(now.year) + '-' + str(now.month) + '-' + str(now.day) + 'T' + str(h) + ':' + min + ':00'
                return date
            elif (parts[0]=='Tommorow'):
                date = str(now.year) + '-' + str(now.month) + '-' + str(now.day + 1) + 'T' + str(h) + ':' + min + ':00'
                return date
    else:
        #Standard
        a,b,c = date_old.split(",")
        month = ''.join(i for i in b if not i.isdigit()).strip()
        month_num = month_converter(month)
        day = ''.join(i for i in b if i.isdigit()).strip()
        part1,part2 = c.split(":")
        time = ''.join(i for i in part2 if not i.isdigit()).strip()
        if time=="PM":
            hour=int(part1)+12
        else:
            hour=int(part1)
        minute = ''.join(i for i in part2 if i.isdigit()).strip()
        date_final = str(now.year) + "-" + str(month_num) + "-" + str(day) + "T" + str(hour) + ":" + minute + ":00"
        return date_final

def month_converter(month):
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    return months.index(month) + 1

#Holding dates of old and new format in lists
listD = []
listD_new = []
for element in dates:
    data = transform_date(element[0])
    listD.append(element[0])
    listD_new.append(data)

#Holding events in list
listE = []
i=0
for element in eventz:
    string = element[0].replace('is due', '')
    new_string = names[i] +" "+ string
    i+=1
    listE.append(new_string)

length = len(listD)
print
print 'There are', length, 'event(s) on your Moodle'
if length == 0:
    print 'ZERO EVENTS. LUCKY BASTARD'
    exit()
print 'Events:'
for i in range(len(listD)):
    print i+1,'-', listE[i], "on", listD[i]

#Transferring events?
def cont_main():
    print
    print "Do you want to transfer these events into your calendar? [Y/N]"
    choice = raw_input().lower()
    yes = {'yes','y', 'ye'}
    no = {'no','n'}
    if choice in yes:
       print 'You pressed YES'
    elif choice in no:
        print 'You pressed NO'
        print 'Thanks for using this code'
        exit()
    else:
        print 'You pressed some weird shit'
        print "Please respond with 'yes/Y' or 'no/N"
        cont_main()

cont_main()

print
mail_name = raw_input('Enter your email: ')


#Google Calendar API
#Adding events into Google Calendar

SCOPES = 'https://www.googleapis.com/auth/calendar'

store = file.Storage('token.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
    creds = tools.run_flow(flow, store)
service = build('calendar', 'v3', http=creds.authorize(Http()))

for i in range(len(listD)):
    event = {
      'summary': listE[i],
      'start': {
        'dateTime': listD_new[i],
        'timeZone': 'Asia/Almaty',
      },
      'end': {
        'dateTime': listD_new[i],
        'timeZone': 'Asia/Almaty',
      },
      'attendees': [
        {'email': mail_name},
      ],
    }
    event = service.events().insert(calendarId='primary', body=event).execute()

print
print '', len(listD), ' event(s) has(ve) been added to your Google Calendar'

#moodle.calendar.real
#moodlecalendar123
