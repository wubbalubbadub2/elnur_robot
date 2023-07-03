from asyncio.windows_events import NULL
from distutils.log import debug
from email import header
from platform import release
from time import sleep
from urllib import request
from selenium import webdriver
#from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from pykeepass import PyKeePass
import json
import requests
from http.client import HTTPConnection
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from funcs.browserFuncs import *
from datetime import datetime

elnurId = '78437'

headers = { 'Authorization' : 'Basic cm9ib3Q6cm9ib3RfMTIz'}
c = requests.get('http://ipcs.kz:60180/restapi/services/run/getReqInfo?id=' + elnurId, headers=headers)
tData = c.text
jsonData = json.loads(tData)
#Прочитать JSON:
debugJsonData = json.dumps(jsonData, ensure_ascii=False).encode('utf8')
print(debugJsonData.decode())
sleep(30)