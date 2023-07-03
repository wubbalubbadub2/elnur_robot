from email import header
from platform import release
from time import sleep
from urllib import request
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from pykeepass import PyKeePass
import json
import  requests
from http.client import HTTPConnection
from bs4 import BeautifulSoup
from html.parser import HTMLParser
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException 
from time import time
import os

#Функция проверки наличия элемента:
def check_exists_by_xpath(xpath, browser, tText="", secs=10):
    #chrome_options = webdriver.ChromeOptions()
    #chrome_options.add_argument("--incognito")
    #chrome_options.add_argument("--ignore-certificate-errors")
    #browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    sWait = WebDriverWait(browser, secs)
    if tText == "":
        #print('trying with no text')
        try:
            sWait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        except NoSuchElementException:
            #print('no element found with no text')
            return False
        except:
            return False
        #print('element with no text found')
        return True
    else:
        try:
            sWait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        except NoSuchElementException:
            return False
        except:
            return False
        elem = sWait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        if elem.text == tText:
            return True
        else:
            return False  

#Функция проверки подтверждения действий
def confirmAction2(tText,browser, tTime = 1):
    while check_exists_by_xpath('//span[@class="ui-growl-title"]', browser, secs=0.5, tText=tText) == False:
        print("waiting for " + tText + " to appear")
        tTimer(tTime)
        #sleep(tTime)
    while check_exists_by_xpath('//span[@class="ui-growl-title"]', browser, secs=10, tText=tText) == True:
        print("waitig for "+ tText +" to disappear")
        tTimer(tTime)
        #sleep(tTime)
    return True

#Новая функция валидации
def confirmAction(tText,browser, x2Time = 10):
    sleep(0.5)
    print("Confirming text to disappear: " + tText)
    sWait = WebDriverWait(browser, x2Time)
    elems = sWait.until(EC.presence_of_all_elements_located((By.XPATH, '//span[@class="ui-growl-title"]')))
    for elem in elems:
        print('Confirm action, debug: found element text is: ' + elem.text)
        #sleep(0.5)
        if elem.text.lower() == tText.lower():
            sWait = WebDriverWait(browser, x2Time*2)
            elem = sWait.until(EC.presence_of_element_located((By.XPATH, '//span[@class="ui-growl-title"]')))
            sleep(5)
            return True
        else:
            continue
    return False

#Новый таймер
def tTimer(secs = 1):
    start_time = time()
    seconds = secs
    while True:
        current_time = time()
        elapsed_time = current_time - start_time

        if elapsed_time > seconds:
            break

def loader(browser):
    sWait = WebDriverWait(browser, 10)
    xpath = '//div[@class="loader2"]/div[@class="sk-circle"]'
    start_time = time()
    while sWait.until(EC.presence_of_element_located((By.XPATH, xpath))):
        current_time = time()
        print("processing loader")
        if current_time - start_time > 60:
            return False
        else:
            sleep(3)
    return True

#Отправка нового статуса
def sendElnurStatus(status, elnurId, eoknoNum = '', fileGuid = ''):
    print("updating Elnur status to " + status)
    headers = { 'Authorization' : 'Basic cm9ib3Q6cm9ib3RfMTIz'}
    if eoknoNum == '' and fileGuid == '':
        r = requests.post('http://cloud.ipcs.kz:60180/restapi/services/run/setReqStatus', headers=headers, json={
        "reqId": elnurId,
        "code": status
    })
    elif fileGuid == '' and eoknoNum != '':
        r = requests.post('http://cloud.ipcs.kz:60180/restapi/services/run/setReqStatus', headers=headers, json={
        "reqId": elnurId,
        "code": status, 
        "regNum": eoknoNum
    })
    elif fileGuid != '' and eoknoNum != '':
        r = requests.post('http://cloud.ipcs.kz:60180/restapi/services/run/setReqStatus', headers=headers, json={
        "reqId": elnurId,
        "code": status, 
        "regNum": eoknoNum, 
        "fileGuid": fileGuid
    })
    print("Elnur status updated")
    return json.loads(r.content)
def sendElnurTranslation(elnurId, json):
    #print("uploading Elnur status")
    headers = { 'Authorization' : 'Basic cm9ib3Q6cm9ib3RfMTIz'}
    r = requests.post('http://cloud.ipcs.kz:60180/restapi/services/run/printData?id=' + elnurId, headers=headers, json=json)
    return r

def uploadElnurFile(fileName):
    print("Sending file started")
    url = "http://cloud.ipcs.kz:60180/restapi/upload"
    headers = { 'Authorization' : 'Basic cm9ib3Q6cm9ib3RfMTIz'}
    data = {"dir":"DOCS"}
    #my_file = open(fileName, 'rb')
    files = {
        'file': (
            fileName, 
            open(fileName, 'rb'), 
            'multipart/form-data'
        )
    }
    print(fileName)
    r = requests.post(url, headers=headers, data=data, files=files)
    print("File was uploaded to Elnur")
    return json.loads(r.content)

def uploadElnurFile2(fileName):
    print("Sending file started")
    url = "http://cloud.ipcs.kz:60180/restapi/upload"
    headers = { 'Authorization' : 'Basic cm9ib3Q6cm9ib3RfMTIz'}
    data = {"dir":"DOCS"}
    #my_file = open(fileName, 'rb')
    files = {
        'file': (
            fileName,
            os.path.basename(fileName), 
            'multipart/form-data'
        )
    }
    r = requests.post(url, headers=headers, data=data, files=files)
    print("Filed was uploaded to Elnur")
    return json.loads(r.content)

#Функция очистики сведений (построчно)
def clearRowEokno(xpath, browser):
    wait = WebDriverWait(browser, '10')
    while wait.until(EC.presence_of_element_located((By.XPATH, xpath))):
        wait.until(EC.presence_of_element_located((By.XPATH, xpath))).click()
    return True

#Функция проверки загрузки файлов
def wait_for_downloads(driver, file_download_path, headless=False, num_files=1):
    max_delay = 60
    interval_delay = 0.5
    if headless:
        total_delay = 0
        done = False
        while not done and total_delay < max_delay:
            files = os.listdir(file_download_path)
            # Remove system files if present: Mac adds the .DS_Store file
            if '.DS_Store' in files:
                files.remove('.DS_Store')
            if len(files) == num_files and not [f for f in files if f.endswith('.crdownload')]:
                done = True
            else:
                total_delay += interval_delay
                time.sleep(interval_delay)
        if not done:
            logging.error("File(s) couldn't be downloaded")
    else:
        def all_downloads_completed(driver, num_files):
            return driver.executeScript("""
                var items = document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList').items;
                var i;
                var done = false;
                var count = 0;
                for (i = 0; i < items.length; i++) {
                    if (items[i].state === 'COMPLETE') {count++;}
                }
                if (count === %d) {done = true;}
                return done;
                """ % (num_files))

        driver.executeScript("window.open();")
        driver.switch_to.window(driver.window_handles[1])
        driver.get('chrome://downloads/')
        # Wait for downloads to complete
        WebDriverWait(driver, max_delay, interval_delay).until(lambda d: all_downloads_completed(d, num_files))
        # Clear all downloads from chrome://downloads/
        driver.executeScript("""
            document.querySelector('downloads-manager').shadowRoot
            .querySelector('#toolbar').shadowRoot
            .querySelector('#moreActionsMenu')
            .querySelector('button.clear-all').click()
            """)
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

def debugSetEoknoNum(elnurId, eoknoNum):
    sendElnurStatus('templ_agreed', elnurId, eoknoNum)

def download_wait(directory, timeout, nfiles=None):
    """
    Wait for downloads to finish with a specified timeout.

    Args
    ----
    directory : str
        The path to the folder where the files will be downloaded.
    timeout : int
        How many seconds to wait until timing out.
    nfiles : int, defaults to None
        If provided, also wait for the expected number of files.

    """
    seconds = 0
    dl_wait = True
    while dl_wait and seconds < timeout:
        sleep(1)
        dl_wait = False
        files = os.listdir(directory)
        if nfiles and len(files) != nfiles:
            dl_wait = True

        for fname in files:
            if fname.endswith('.crdownload'):
                dl_wait = True

        seconds += 1
    return seconds

#
def delElement(Xpath, browser, secs=5, tText='', all=True):
    #span class = ui-button-icon-left ui-icon ui-c fa fa-trash
    #tbody id = mainTab:applicants:companyDTForm:companyDT:0:addressesApplicant:adressesDT_data
    
    wait = WebDriverWait(browser, secs)
    xpath = Xpath
    if  check_exists_by_xpath(xpath=xpath, browser=browser):
        elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        elem.send_keys(Keys.ARROW_DOWN)
        elem.send_keys(Keys.ARROW_DOWN)
        elem.send_keys(Keys.ARROW_DOWN)
        #action = ActionChains(browser)
        #action.move_to_element(elem).perform()
        sleep(1)

        if all == True:
            while check_exists_by_xpath(xpath, browser, secs=2):
                wait.until(EC.presence_of_element_located((By.XPATH, xpath))).click()
                if tText != '':
                    confirmAction(tText, browser)
                sleep(1)
        else:
            wait.until(EC.presence_of_element_located((By.XPATH, xpath))).click()
            if tText != '':
                confirmAction(tText, browser)
        sleep(1)    

def stageTest(elnurId, headers, kpLoc, repSavePath = r"C:\EOKNO_temp"):
    t = 1

def highlight(element, effect_time, color, border):
    """Highlights (blinks) a Selenium Webdriver element"""
    driver = element._parent
    def apply_style(s):
        driver.execute_script("arguments[0].setAttribute('style', arguments[1]);",
                              element, s)
    original_style = element.get_attribute('style')
    apply_style("border: {0}px solid {1};".format(border, color))
    sleep(effect_time)
    apply_style(original_style)

def expandFolder(browser, xpath, secs=5):
    t = 1
    wait = WebDriverWait(browser, secs)
    xpath1 = '/div[contains(@class, "ui-row-toggler ui-icon ui-icon-circle-triangle")]'
    #                      ui-row-toggler ui-icon ui-icon-circle-triangle-s
    xpath = xpath + xpath1
    elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
    highlight(element=elem, color="red", border=1, effect_time=2)
    expandedStat = elem.get_attribute("aria-expanded")
    print("Element stat is: " + expandedStat)
    if expandedStat == 'false':
        print('Element is not expanded, expanding')
        elem.click()
        sleep(1)

def roleSelector(jsonData):
    t=1
    res = {"rpaStatus":"", "newStatus":"", "initiator":""}
    elnurCurrStatus = jsonData["items"][0]["status"]
    if elnurCurrStatus == "send_expert": #Если статус = Отправить к эксперту
        res["rpaStatus"] = "send_expert_rpa"
        res["newStatus"] = "templ_approval"
        for role in jsonData["items"][0]["experts"]:
            if role["expert_role_id"] == "Руководитель ОПС П - принятие решения по заявке":
                res["initiator"] = role["expert_idn"]
    if elnurCurrStatus == "rejected": #Отказано в принятии заявки
        res["rpaStatus"] = "rejected_rpa"
        res["newStatus"] = "rejected_complete"
        for role in jsonData["items"][0]["experts"]:
            if role["expert_role_id"] == "Эксперт-аудитор на оценку":
                res["initiator"] = role["expert_idn"]
    if elnurCurrStatus == "changed": #Имеется изменения
        res["rpaStatus"] = "changed_rpa"
        res["newStatus"] = "templ_approval"
        for role in jsonData["items"][0]["experts"]:
            if role["expert_role_id"] == "Эксперт-аудитор на оценку":
                res["initiator"] = role["expert_idn"]
    if elnurCurrStatus == "templ_agreed": #Шаблон согласован
        res["rpaStatus"] = "templ_agreed_rpa"
        res["newStatus"] = "release_ready"
        for role in jsonData["items"][0]["experts"]:
            if role["expert_role_id"] == "Эксперт-аудитор на оценку":
                res["initiator"] = role["expert_idn"]
    if elnurCurrStatus == "ready": #Первое редактирование
        res["rpaStatus"] = "ready_rpa"
        res["newStatus"] = "templ_approval"
        res["initiator"] = jsonData["items"][0]["initiator"]
    print("Initiator login: " + res["initiator"])
    return res