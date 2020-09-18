import requests
from bs4 import BeautifulSoup
import datetime
import time
import os
import telegram
import psycopg2

import config   # config.py
import settings # settings.py


def sendTelegramMessage(msg): # Send msg to my Telegram channel
	try:
		bot = telegram.Bot(token = config.telbot_token)
		bot.sendMessage(config.telbot_channel, u''+msg)

	except Exception as error: # error exception
		print ("Error while sendgind Telegram message", error)



def updateLastDate(date): # Update the last-updated-date in database with theater code and date
	try:
		conn = psycopg2.connect(
			dbname =   config.DB_dbname,
			user =     config.DB_user,
			password = config.DB_password,
			host =     config.DB_host,
			port =     config.DB_port)


		cur = conn.cursor()
		cur.execute("""UPDATE lastdate set lastdate = %s
			WHERE areacode = %s AND theatercode = %s AND screentype = %s;""",
			(date, settings.areacode, settings.theatercode, settings.screentype))


		conn.commit()

		cur.close()
		conn.close()

	except (Exception, psycopg2.Error) as error: # Error exception
		print ("Error while updating data from PostgreSQL", error)






def getLastDate(): # Get last-updated-date in database with theater code and date
	try:
		conn = psycopg2.connect(
			dbname =   config.DB_dbname,
			user =     config.DB_user,
			password = config.DB_password,
			host =     config.DB_host,
			port =     config.DB_port)


		cur = conn.cursor()
		cur.execute("""SELECT lastdate FROM lastdate
			WHERE areacode = %s AND theatercode = %s AND screentype = %s;""",
			(settings.areacode, settings.theatercode, settings.screentype))


		lastDate = cur.fetchone()[0]

		cur.close()
		conn.close()

		return lastDate

	except (Exception, psycopg2.Error) as error: # Error exception
		print ("Error while getting data from PostgreSQL", error)


def screenTypeAvailable(date): # Check if there's available movie

	url = 'http://www.cgv.co.kr/common/showtimes/iframeTheater.aspx?'
	url += 'areacode=' + settings.areacode
	url += '&theatercode=' + settings.theatercode
	url += '&date=' + date

	html = requests.get(url).text # Get html grom cgv homepage with theater code and date
	
	if("derror" in html):
		print('http error')	    
		return False

	soup = BeautifulSoup(html, 'html.parser')

	data = soup.find("div", {"class":"sect-showtimes"}) # Get showtime table from html
	
	try:
		columns = data.find_all("div", {"class":"col-times"}) # Get each rows
	except: # Error exception for if there's no showtime table
		print("Can't find showtimes")
		return False
	

	detected = 0

	for item in columns: # For each movies and types
		title = item.find("strong").text.strip()
		if settings.screentype in str(item): # Check if there's target type of movie e.g. IMAX
			print(settings.screentype,"Detacted\nTitle:",title)
			print(str(date)[:4] + "/" + str(date)[4:6] + "/" + str(date)[6:], settings.screentype, "Available\n")
			
			msg = "OPEN: "
			msg += str(date)[:4]+"/"+str(date)[4:6]+"/"+str(date)[6:]
			msg += " - <" + title
			msg += "> " + settings.screentype
			
			sendTelegramMessage(msg) # Send message to telegram channel
			detected = 1


	return detected == 1


def main():
	sendTelegramMessage("Application rebooted")
	
	while True:
		lastDate = getLastDate()

		date = datetime.datetime.strptime(lastDate,"%Y%m%d").date()
		ndate = date + datetime.timedelta(days=1)
		dateStr = ndate.strftime("%Y%m%d")
		if screenTypeAvailable(dateStr): # The program find available reservation
			updateLastDate(dateStr) # Update the last-updated-date in database

		else: # There's no movie reservation of the type
			print("Can't find new reservation\nLast Date:", lastDate,"\n")
		time.sleep(settings.refresh_time) # Time interval of while loop


main()




