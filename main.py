from selenium import webdriver
from selenium.webdriver.support.ui import Select
import requests
import time
from datetime import datetime
import ConfigParser

config = ConfigParser.ConfigParser()
config.read('config.ini')

# open driver
driver = webdriver.Chrome(config.get('Webdriver', 'path'))

# camp sites
ALL_CAMP_SITES = ['1-132,C1-C2?Map', '133-293,B1-B2?Map']

# date params
arrival_month = 'Jul'
arrival_day = '21st'
num_nights = '2'

#url
url = 'https://www.midnrreservations.com/HoffmasterStatePark/'
reserve_url = 'https://www.midnrreservations.com/HoffmasterStatePark?Map'

# constants
TIME_LAST_EMAIL_SENT = None
EMAIL_NOTIFICATION_INTERVAL = 180 # 3 minutes


def send_email(sites, timestamp):
  print 'Sending email...'

  payload = {
    'secret'      : config.get('Email', 'secret'),
    'website_url' : reserve_url,
    'timestamp'   : prettify_time(timestamp),
    'camp_sites'  : ', '.join(sites),
    'addresses'   : config.get('Email', 'addresses'),
  }

  print payload

  r = requests.post(config.get('Email', 'api_url'), payload)
  print(r.text)


def prettify_time(timestamp):
  format = '%Y-%m-%dT%H:%M:%S'
  return datetime.fromtimestamp(timestamp).strftime(format)


def get_avail(site_range_url):
  # access website
  driver.get(url+site_range_url)

  # config month element
  elem_month = Select(driver.find_element_by_name('selArrMth'))
  elem_month.select_by_visible_text(arrival_month)

  # config day element
  elem_day = Select(driver.find_element_by_name('selArrDay'))
  elem_day.select_by_visible_text(arrival_day)

  # config number-of-nights element
  elem_nights = Select(driver.find_element_by_name('selNumNights'))
  elem_nights.select_by_visible_text(num_nights)

  # give some time for the browser to finish loading
  print 'page loading...(%s)'%(site_range_url)
  time.sleep(3)

  # css select the available dots on ze map!
  avail_sites = driver.find_elements_by_css_selector('div#map > div[id^=rce_] > .avail:first-child')

  out = []
  for node in avail_sites:
    parent = node.find_element_by_xpath('..')
    site_num = parent.get_attribute('id').split('_')[1]
    if site_num.isdigit():
      out.append(site_num)


  return out


def run():
  
  cnt = 0
  avail = []
  for s in ALL_CAMP_SITES:
    avail += get_avail(s)
    time.sleep(3)

  for site_num in avail:
    cnt += 1
    print site_num + ',',

  if not cnt:
    print '\nThere are NO available sites :('
  else:
    print '\n\n%s site(s) AVAILABLE !!!!!!!!!'%(cnt)

    # only send email if it has been over n minutes
    global TIME_LAST_EMAIL_SENT, EMAIL_NOTIFICATION_INTERVAL
    now = time.time()

    if not TIME_LAST_EMAIL_SENT or (now - TIME_LAST_EMAIL_SENT) >= EMAIL_NOTIFICATION_INTERVAL:
      TIME_LAST_EMAIL_SENT = now
      send_email(avail, now)

  print '-----------------------------------------------\n\n'



if __name__ == "__main__":

  while True:
    try:
      run()

    except KeyboardInterrupt:
      driver.close()
      print 'shutting down.'
      break