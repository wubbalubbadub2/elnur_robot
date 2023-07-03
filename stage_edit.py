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

#Тест загрузки файла:
#tRes = uploadElnurFile(r"C:\EOKNO_temp\report_3161699.pdf")
#print(tRes.content)
#sleep(50000)

#Токен для работы с API Elnur:
headers = { 'Authorization' : 'Basic cm9ib3Q6cm9ib3RfMTIz'}
#Пароль от БД KeePass
kp = PyKeePass('C:\KeePass\Database.kdbx', password='!mYP3TD=txAcb(Cr')
#ИД заявки для теста:
#elnurId = '78430'   
#Словарик значений по шаблону:
eoknoList = []
elnStatus = 'ready_rpa'
repSavePath = r"C:\EOKNO_temp"

def stage_edit(elnurId, headers, kpLoc, repSavePath = r"C:\EOKNO_temp"):
    kp = kpLoc
    elnStatus = 'ready_rpa'
    elnStatus2 = 'templ_approval'
    tFPath = os.path.join(repSavePath, 'new') #место сохранения новых шаблонов
    repExtension = 'pdf' #расширение файла
    #resPath = os.path.join(tFPath, 'report_.' + repExtension)
    #print(resPath)
    #sleep(5000)

    #очистить файлы с прошлого раза, если остались:
    for path in os.listdir(tFPath):
        if os.path.isfile(os.path.join(tFPath, path)):
            os.replace(os.path.join(tFPath, path), os.path.join(os.path.join(repSavePath, 'errorReports'), path))

    #Получить данные по заявке
    c = requests.get('http://cloud.ipcs.kz:60180/restapi/services/run/getReqInfo?id=' + elnurId, headers=headers)
    tData = c.text
    #print(tData)
    jsonData = json.loads(tData)
    #
    #
    # Костыль
    jsonData["items"][0]["status"] = "templ_agreed"
    roles = roleSelector(jsonData)
    elnStatus = roles["rpaStatus"]
    elnStatus2 = roles["newStatus"]
    #Обновить статус заявки:
    r = sendElnurStatus(elnStatus, elnurId)
    print("Status was updated: " + str(r))

    ##############
    # TEST BLOCK #
    ##############

    #tJsons = jsonData["items"][0]["jur_contacts"]
    #for tJson in tJsons:
    #    print(tJson["cont"])
    #sleep(10)

    #####################
    # END OF TEST BLOCK #
    #####################

    #Настройки браузера для использования
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("disable-infobars")
    chrome_options.add_experimental_option("excludeSwitches",["enable-automation"])
    chrome_options.add_experimental_option("prefs", {
    "download.default_directory": tFPath,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
    })
    #6chrome_options.add_experimental_option("prefs", {'profile.managed_default_content_settings.javascript':2})

    browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    #browser = webdriver.Firefox()
    browser.maximize_window()
    browser.get('https://eokno.gov.kz')

    #Блок для входа на сайт EOKNO

    #Загрузка и выбор языка
    #Навести курсор на выбор языков
    wait = WebDriverWait(browser, 30)
    download_menu = browser.find_element(By.XPATH, '/html/body/div[2]/div[1]/div[2]/div')
    action = ActionChains(browser)
    action.move_to_element(download_menu).perform()
    #Навести и кликнуть русский язык
    ruBtn = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="j_idt14"]/a')))
    #sleep(1)
    #ruBtn = browser.find_element(By.XPATH, '//*[@id="j_idt14"]/a')
    ruBtn.click()
    #Нажать кнопку "Войти"
    enterBtn = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Войти")))
    #enterBtn = browser.find_element(By.LINK_TEXT, "Войти")
    enterBtn = enterBtn.click()

    #Взять логин из API:
    elLogin = jsonData["items"][0]["initiator"]
    elLogin = roles["initiator"]
    cUrl = browser.current_url
    #Костыль:
    #######################
    #if elLogin == "800404400921":
    #    elLogin = '800422402470'
    

    #######################
    #Указать логин
    login = wait.until(EC.presence_of_element_located((By.NAME, 'login:username')))
    #login = browser.find_element(By.NAME, 'login:username')
    tEntry = kp.find_entries(title=elLogin, first=True)
    tLogin = tEntry.username
    login.send_keys(tLogin)
    #Указать пароль
    pwd = wait.until(EC.presence_of_element_located((By.NAME, 'login:password')))
    #pwd = browser.find_element(By.NAME, 'login:password')
    tEntry = kp.find_entries(title=elLogin, first=True)
    tPwd = tEntry.password
    pwd.send_keys(tPwd)
    #Нажать кнопку входа
    enterBtn2 = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="login"]/div[4]/input')))
    #enterBtn2 = browser.find_element(By.XPATH, '//*[@id="login"]/div[4]/input')
    enterBtn2.click()

    #Загрузка страницы:
    #if wait.until(EC.presence_of_element_located((By.XPATH, '//h1[@class="c-dashboard__title"]'))).text == "Орган по подтверждению соответствия":
    #    print("page was loaded")

    #Этап 1: внесение новой заявки:
    browser.get("https://eokno.gov.kz/ktrm/ktrmApp.xhtml?id=" + jsonData["items"][0]["eokno_reg_num"])

    #######################################################################
    #Прочитать JSON:
    #debugJsonData = json.dumps(jsonData, ensure_ascii=False).encode('utf8')
    #print(debugJsonData.decode())
    #sleep(30)
    #######################################################################
    # Тест блок
    #print("current URL is: " + browser.current_url)
    #sleep(500)
    #tUrl = 'https://eokno.gov.kz/ktrm/ktrmApp.xhtml?id=3187121'
    #tId = tUrl.split('=')[1].split('&')[0]
    #print("temp id is: " + tId)
    #sleep(500)
    #######################################################################

    #Открыть через кнопки страницу:
    #wait.until(EC.presence_of_element_located((By.XPATH, '//span[@class="section-title"]'))).click()
    #wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="sidebar"]/div[2]/ul/li[1]/a'))).click() #//*[@id="sidebar"]/div[2]/ul/li[1]/a
    #wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Создать заявление"))).click()
    #wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="sidebar"]/div[2]/ul/li[1]/ul/li[1]/a'))).click()
    #wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Создать Заявку"))).click()
    #wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="sidebar"]/div[2]/ul/li[1]/ul/li[1]/ul/li/a'))).click()

    #Выбрать документ сертификации, если ЕАЭС -- выбрать его, если нет -- РК
    #if jsonData['items'][0]["confirm_country_id"] == 'ЕАЭС':
    #    EAESDoc = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="mainTab:certificateTypeForm:certificateType"]/tbody/tr/td[2]/div/div[2]')))
    #    EAESDoc.click()
    #else:
    #    EAESDoc = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="mainTab:certificateTypeForm:certificateType"]/tbody/tr/td[1]/div/div[2]')))
    #    EAESDoc.click()

    #Вкладка общие данные

    #п.1 Выбрать тип документа подтверждения соответствия и раскрыть меню
    #docType = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="mainTab:kindDocumentForm:certificateKindCode_label"]')))
    #docType.click()

    #п.2 Найти все возможные меню выбора документов подтверждения соответствия:
    #Ulelems = wait.until(EC.presence_of_element_located((By.ID, "mainTab:kindDocumentForm:certificateKindCode_items")))
    #elems = Ulelems.find_elements(By.TAG_NAME, "li")
    #for elem in elems:
        #Если нашли нужный элемент -- кликнуть
        #print("EOKNO: " + elem.text + " ELNUR: " + jsonData['items'][0]["confirm_doc_type_id"])
    #    if elem.text.lower() == jsonData['items'][0]["confirm_doc_type_id"].lower():
    #        elem.click()
    #        break

    #п.3 Заявитель
    #Добавить заявителя
    #!elem = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[contains(@id, "mainTab:applicants:companyDTForm:companyDT:j_idt")]')))
    #elem = browser.find_element(By.XPATH, '//*[contains(@id, "mainTab:applicants:companyDTForm:companyDT:j_idt")]')
    #elem.click()
    #elem.send_keys(Keys.LEFT_CONTROL + 'q')


    #Удалить чат
    #xpath = '//vue-widget'
    #elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
    #elem.remove()

    #Block chat
    browser.execute_script("document.getElementsByTagName('vue-widget')[0].remove();")
    
    #Раскрыть детали о заявителе:
    #xpath = '//div[@class="ui-row-toggler ui-icon ui-icon-circle-triangle-e"]'
    #elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
    #elem.click()
    #sleep(0.5)

    #Определить признак резидентства. Если не резидент -- указать страну. Если резидент -- указать тип ЮЛ и ввести БИН:
    #if jsonData["items"][0]["jur_resident"] == "1":
        #Если резидент, то выбрать тип ЮЛ и указать БИН
        #Вытащить таблицу, в которой все типы ЮЛ:
        #tTable = wait.until(EC.presence_of_element_located((By.ID, 'mainTab:applicants:companyDTForm:companyDT:0:inputIdentificationType')))
        #Вытащить все колонки в которых ЮЛ:
        #tTds = tTable.find_elements(By.TAG_NAME, 'td')
        #for tTd in tTds:
        #    #В каждой колонке вытащить текстовое описание типа ЮЛ:
        #    tLabel = tTd.find_element(By.TAG_NAME, 'label')
        #    #Если тип ЮЛ соответствует заявке, кликнуть:
        #    if tLabel.text.lower() == jsonData["items"][0]["jur_client_type"].lower():
        #        tClass = tTd.find_element(By.XPATH, '//*[contains(@class, "ui-radiobutton-box")]')
        #        tClass.click()
        #        print('Clicked: ' + tLabel.text)
        #xpath = '//table[@id="mainTab:applicants:companyDTForm:companyDT:0:inputIdentificationType"]'
        #table = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        #tds = table.find_elements(By.TAG_NAME, 'td')
    #    xpath = '//span[@class="ui-radiobutton-icon ui-icon ui-icon-bullet ui-c"]'
    #    spans = wait.until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
    #    print("Trying to find jur client type")
    #    if jsonData["items"][0]["jur_client_type"] == "БИН":
    #        #tds[0].click()
    #        #print(tds[0].text)
            #tDiv = tds[0].find_element(By.XPATH, '//div[@class="ui-radiobutton ui-widget"]')
            #tDiv.click()
            #spans[0].click()
            #xpath = '//input[@id="mainTab:applicants:companyDTForm:companyDT:0:inputIdentificationType:0"]'
            #wait.until(EC.presence_of_element_located((By.XPATH, xpath))).click()
    #        xpath = '//label[@for="mainTab:applicants:companyDTForm:companyDT:0:inputIdentificationType:0"]'
    #        tbtn = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
    #       tbtn.click()
    #        sleep(2)
    #        tBin = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="mainTab:applicants:companyDTForm:companyDT:0:companyBin"]')))
    #        tBin.send_keys(jsonData["items"][0]["jur_bin_iin"])
    #        tBin.send_keys(Keys.TAB)
    #    else:
            #tds[1].click()
            #print(tds[1].text)
            #xpath = '//input[@id="mainTab:applicants:companyDTForm:companyDT:0:inputIdentificationType:1"]'
            #wait.until(EC.presence_of_element_located((By.XPATH, xpath))).click()
            #tDiv = tds[1].find_element(By.XPATH, '//div[@class="ui-radiobutton ui-widget"]')
            #tDiv.click()
    #        xpath = '//label[@for="mainTab:applicants:companyDTForm:companyDT:0:inputIdentificationType:1"]'
    #        tbtn = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
    #        tbtn.click()
    #        sleep(2)
            #spans[1].click()
    #        xpath = '//input[@id="mainTab:applicants:companyDTForm:companyDT:0:personIin"]'
    #        tIin = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
    #        tIin.send_keys(jsonData["items"][0]["jur_bin_iin"])
    #        tIin.send_keys(Keys.TAB)
        #Указать БИН компании:
        
        #while browser.find_element(By.XPATH, '//*[@id="mainTab:applicants:companyDTForm:companyDT:0:companyBin"]') == False:
        #    sleep(1)
        #tBin = browser.find_element(By.XPATH, '//*[@id="mainTab:applicants:companyDTForm:companyDT:0:companyBin"]')
        
        #sleep(90)
        #loader(browser)
        #tTimer(1)
    #    sleep(2)

        #Чистка наименования компании, если находится
        #Ручная доп.проверка
    #    tK = 0
    #    if browser.find_element(By.XPATH, '//*[@id="mainTab:applicants:companyDTForm:companyDT:0:companyName"]').text == "":
    #        while browser.find_element(By.XPATH, '//*[@id="mainTab:applicants:companyDTForm:companyDT:0:companyName"]').text == "":
    #            sleep(0.5)
    #            tK+=1
    #            if tK == 4:
    #                break
    #    if browser.find_element(By.XPATH, '//*[@id="mainTab:applicants:companyDTForm:companyDT:0:companyName"]').text != "":
    #        browser.find_element(By.XPATH, '//*[@id="mainTab:applicants:companyDTForm:companyDT:0:companyName"]').clear()
        
        #!while wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="mainTab:applicants:companyDTForm:companyDT:0:companyName"]'))).text == "":
        #!    sleep(5)
        #!wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="mainTab:applicants:companyDTForm:companyDT:0:companyName"]'))).clear()
        #loader(browser)
        #while check_exists_by_xpath('//*[@id="mainTab:applicants:companyDTForm:companyDT:0:companyName"]', browser, secs=1) == False:
        #    print("loading company title")
        #    tTimer(1)
            #sleep(0.5)
        #Блок для очистки наименования компании
        #try: 
        #    while wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="mainTab:applicants:companyDTForm:companyDT:0:companyName"]'))).text == "":
        #        tTimer(1)
        #        #sleep(0.5)
        #    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="mainTab:applicants:companyDTForm:companyDT:0:companyName"]'))).clear()
        #except:
        #    while wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="mainTab:applicants:companyDTForm:companyDT:0:companyName"]'))).text == "":
        #        tTimer()
        #        #sleep(0.5)
        #    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="mainTab:applicants:companyDTForm:companyDT:0:companyName"]'))).clear()

    #else:
        #Убрать галку о резидентстве
    #    elem = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@class="ui-chkbox-box ui-widget ui-corner-all ui-state-default ui-state-active"]')))
    #    elem.click()
        #loader(browser)
    #    tTimer(1)
        #sleep(1)
        #Открыть выбор стран:
    #    elem = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="mainTab:applicants:companyDTForm:companyDT:0:inputCompanyUnctytab"]')))
    #    elem.click()
        #loader(browser)
    #    elem = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="mainTab:applicants:companyDTForm:companyDT:0:inputCompanyUnctytab_filter"]')))
    #    elem.send_keys(jsonData["items"][0]["jur_country"])
    #    elem.send_keys(Keys.ENTER)
        #loader(browser)
        #sleep(1)
    #Указать наименование компании:
    #!tTitle = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="mainTab:applicants:companyDTForm:companyDT:0:companyName"]')))
    #tTitle = browser.find_element(By.XPATH, '//*[@id="mainTab:applicants:companyDTForm:companyDT:0:companyName"]')
    #!print("trying to add company title")
    #tTitle.send_keys(jsonData["items"][0]["jur_fullname"] + Keys.TAB + Keys.ENTER)
    #sleep(1)
    #print("company title added")
    #loader(browser)
    #Сохранить информацию о компании
    #tTitle.send_keys(Keys.TAB + Keys.ENTER)

    #Проверить, что информация о компании сохранена:
    #confirmAction(tText = "Компания отредактирована", browser=browser, x2Time=10)
    #while check_exists_by_xpath('//span[@class="ui-growl-title"]', "Компания отредактирована") == False:
    #    sleep(0.1)
    #while check_exists_by_xpath('//span[@class="ui-growl-title"]', "Компания отредактирована") == True:
    #    sleep(0.1)

    #Раскрыть детали о заявителе
    elem = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="ui-row-toggler ui-icon ui-icon-circle-triangle-e" and @role="button" and @aria-label="Toggle Row"]')))
    elem.click()
    sleep(0.5)
    #loader(browser)

    #3.1.1
    #Проверить, что элементы загрузились:
    #while check_exists_by_xpath('//button[contains(@id, "mainTab:applicants:companyDTForm:companyDT:0:addressesApplicant:adressesDT:j_idt") and @type="submit" and @title="Адрес"]', browser, secs=1) == False:
    #    tTimer()
    #    print("Ожидание загрузки элементов")
        #sleep(0.5)
    #Удалить старые адреса:
    print("trying to delete old address")
    #print("Addresses status: " + str(check_exists_by_xpath('//*[@id="mainTab:applicants:companyDTForm:companyDT:0:addressesApplicant:adressesDT:0:deleteAddressButton"]')))
    #xpath = '//tbody[@id="mainTab:applicants:companyDTForm:companyDT:0:addressesApplicant:adressesDT_data"]'
    xpath = '//button[@id="mainTab:applicants:companyDTForm:companyDT:0:addressesApplicant:adressesDT:0:deleteAddressButton" and @title="Удалить"]'
    xpath = '//button[contains(@id,"mainTab:applicant") and contains(@id, "companyDTForm:companyDT:0:addressesApplicant:adressesDT:0:deleteAddressButton") and @title="Удалить"]'
    delElement(Xpath=xpath, browser=browser,tText="Адрес удален")
    #while check_exists_by_xpath('//button[@id="mainTab:applicants:companyDTForm:companyDT:0:addressesApplicant:adressesDT:0:deleteAddressButton" and @title="Удалить"]', browser, secs=2):
    #    wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@id="mainTab:applicants:companyDTForm:companyDT:0:addressesApplicant:adressesDT:0:deleteAddressButton" and @title="Удалить"]'))).click()
    #    print("Удален старый адрес компании")
    #    confirmAction(tText = "Адрес удален",browser=browser, x2Time=10)
    #    while check_exists_by_xpath('//span[@class="ui-growl-title"]', secs=0.5, tText="Адрес удален") == False:
    #        print("waiting for old address removal approval to appear")
    #        sleep(0.2)
    #    while check_exists_by_xpath('//span[@class="ui-growl-title"]', secs=0.5, tText="Адрес удален") == True:
    #        print("waitig for old address removal confirmation to dissappear")
    #        sleep(0.2)
    #    tTimer()
        #sleep(0.5)
    #Добавить адреса компании:
    print("trying to add new address")
    jurAddresses = jsonData["items"][0]["jur_addresses"]
    i = 0 #Индекс адреса
    for jurAddress in jurAddresses:
        #Ввод только актуального адреса:
        if jurAddress["actual"] == "1":
            #Начало ввода адресов компании
            #Кликнуть по кнопке добавления адресов
            xpath = '//button[contains(@id, "mainTab:applicant:companyDTForm:companyDT:0:addressesApplicant:adressesDT:j_idt") and @type="submit" and @title="Адрес"]'
            wait.until(EC.element_to_be_clickable((By.XPATH, xpath))).click()
            #Нажать выбор типа адреса: //Отключено, нет в API
            #elem = wait.until(EC.element_to_be_clickable((By.XPATH, '//label[@id="mainTab:applicants:companyDTForm:companyDT:0:addressesApplicant:adressesDT:'+str(i)+':addressTypeInput_label"]')))
            #elem.click()
            #Выбрать тип адреса:
            #tTable = wait.until(EC.presence_of_element_located((By.XPATH, '//table[@id="mainTab:applicants:companyDTForm:companyDT:0:addressesApplicant:adressesDT:'+str(i)+':addressTypeInput_panel"]')))
            #tTds = tTable.find_element(By.TAG_NAME, 'td')
            #for tTd in tTds:
            #    if tTd.text == jurAddress[]
            #elem.send_keys(jsonData["items"][0]["jur_country"])
            #elem.send_keys(Keys.ENTER)
            
            #Выбрать меню доступных стран адреса:
            #while check_exists_by_xpath('//div[@id="mainTab:applicants:companyDTForm:companyDT:0:addressesApplicant:adressesDT:'+str(i)+':сompanyAddressUnctytabInput"]', browser) == False:
            #    tTimer()
                #sleep(0.5)
            #mainTab:applicant:companyDTForm:companyDT:0:addressesApplicant:adressesDT:0:addressTypeInput_label #New label
            #mainTab:applicant:companyDTForm:companyDT:0:addressesApplicant:adressesDT:0:addressTypeInput
            #mainTab:applicants:companyDTForm:companyDT:0:addressesApplicant:adressesDT:0:сompanyAddressUnctytabInput
            #xpath = '//div[@id="mainTab:applicant:companyDTForm:companyDT:0:addressesApplicant:adressesDT:'+str(i)+':addressTypeInput"]'
            xpath = '//div[@id="mainTab:applicant:companyDTForm:companyDT:0:addressesApplicant:adressesDT:'+str(i)+':сompanyAddressUnctytabInput"]'
            wait.until(EC.element_to_be_clickable((By.XPATH, xpath))).click()
            #Указать страну:
            xpath = '//input[@id="mainTab:applicant:companyDTForm:companyDT:0:addressesApplicant:adressesDT:'+str(i)+':сompanyAddressUnctytabInput_filter"]'
            elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            elem.send_keys("398" + Keys.ENTER)
            #Элементы для ввода подробностей по адресу (область + район)
            #xpath = '//div[contains(@id, "mainTab:applicants:companyDTForm:companyDT:0:addressesApplicant:adressesDT:'+str(i)+'")]/input'
            xpath = '//div[contains(@id, "mainTab:applicant:companyDTForm:companyDT:0:addressesApplicant:adressesDT:'+str(i)+'")]/input'
            elems = wait.until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
            #elems = elems.find_elements(By.TAG_NAME, 'input')
            k = 1
            for elem in elems:
                #Начало ввода области, района
                print("k is: " + str(k))
                if k == 100:
                    k += 1
                    continue
                elif k == 1:
                    #Указать область:
                    print('oblast')
                    try:
                        elem.send_keys(jurAddress["region"])
                    except:
                        elem.send_keys(jurAddress["region"])
                elif k == 2:
                    #Указать район:
                    print('region')
                    try:
                        elem.send_keys(jurAddress["area"])
                    except:
                        elem.send_keys(jurAddress["area"])
                k += 1
                #Конец ввода области, района
            #Указать город:
            elem = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@id="mainTab:applicant:companyDTForm:companyDT:0:addressesApplicant:adressesDT:'+str(i)+':cityInput"]')))
            elem.send_keys(jurAddress["city"])
            #Указать улицу:
            elem = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@id="mainTab:applicant:companyDTForm:companyDT:0:addressesApplicant:adressesDT:'+str(i)+':streetNameInput"]')))
            elem.send_keys(jurAddress["street"])
            #Указать дом:
            elem = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@id="mainTab:applicant:companyDTForm:companyDT:0:addressesApplicant:adressesDT:'+str(i)+':buildingNoInput"]')))
            elem.send_keys(jurAddress["home"])      
            #Указать квартиру:
            elem = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@id="mainTab:applicant:companyDTForm:companyDT:0:addressesApplicant:adressesDT:'+str(i)+':poBoxInput"]')))
            elem.send_keys(jurAddress["flat"])
            #Указать почтовый индекс:
            elem = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@id="mainTab:applicant:companyDTForm:companyDT:0:addressesApplicant:adressesDT:'+str(i)+':postCodeInput"]')))
            elem.send_keys(jurAddress["post"])
            #Сохранить адрес
            elem.send_keys(Keys.TAB + Keys.TAB + Keys.ENTER)
            tTimer(1)
            #sleep(1)
            confirmAction("Адрес отредактирован",browser, 1)
            i += 1
        else:
            continue
        #Конец ввода адресов
    #3.1.2 Контактные данные
    i = 0
    #Удалить старые контакты
    xpath = '//button[contains(@id, "mainTab:applicant:companyDTForm:companyDT:0:contactsApplicant:contactsDT:0:j_i") and @title="Удалить"]'
    delElement(Xpath=xpath, browser=browser, tText="Контакт удален")
    #while check_exists_by_xpath('//*[contains(@id, "mainTab:applicants:companyDTForm:companyDT:0:contactsApplicant:contactsDT:0:j_idt")]/span[1]"]', browser, secs=2):
    #    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[contains(@id, "mainTab:applicants:companyDTForm:companyDT:0:contactsApplicant:contactsDT:0:j_idt")]/span[1]]'))).click()
    #    print("Удален старый контакт компании")
    #    confirmAction("Контакт удален",browser, 10)
    #    tTimer()
        #sleep(0.5)
    for jurContact in jsonData["items"][0]["jur_contacts"]:
        #Начало ввода контактных данных
        #Добавить контакт:
        print('Ввод контактных данных')
        wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@title="Контактные данные"]'))).click()
        #Активировать выбор типа контактов:
        elem = wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(@id, "mainTab:applicant:companyDTForm:companyDT:0:contactsApplicant:contactsDT:'+str(i)+':j_idt")]')))
        elem.click()
        tTimer()
        #sleep(0.5)
        #Найти нужный тип контакта:
        #print("Entering following contact: " + jurContact["cont_type"])
        tdElems = wait.until(EC.presence_of_element_located((By.XPATH, '//table[@aria-activedescendant="mainTab:applicant:companyDTForm:companyDT:0:contactsApplicant:contactsDT:'+str(i)+':communicationDetailTypeInput_4"]')))
        elems = tdElems.find_elements(By.TAG_NAME, 'td')
        for elem in elems:
            #Выбрать тип контакта
            #print(elem.text)
            if elem.text == (jurContact["cont_type"]):
                elem.click()
                tTimer(1)
                #sleep(1)
                break
        #Ввести значение контакта
        elem = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@id="mainTab:applicant:companyDTForm:companyDT:0:contactsApplicant:contactsDT:'+str(i)+':communicationValueInput"]')))
        sleep(1)
        elem.send_keys(jurContact["cont"] + Keys.TAB + Keys.TAB + Keys.ENTER)
        #Сохранить контакт
        #elem.send_keys(Keys.TAB + Keys.TAB + Keys.ENTER)
        confirmAction("Контакт отредактирован",browser, 10)
        #elem.send_keys(Keys.TAB + Keys.TAB + Keys.ENTER)
        i += 1
        #Конец ввода контактов

    #3.1.3 Банковский счет
    #Удалить старые банквоские данные
    xpath = '//button[contains(@id, "mainTab:applicant:companyDTForm:companyDT:0:ktrmBankDetailApplicant:bankDetailsDT:0:j") and @title="Удалить"]'
    delElement(Xpath=xpath, browser=browser, tText="bank-detail-deleted")
    #while check_exists_by_xpath('//*[contains(@id, "mainTab:applicants:companyDTForm:companyDT:0:ktrmBankDetailApplicant:bankDetailsDT:0:j_idt")]/span[1]"]', browser, secs=2):
    #    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[contains(@id, "mainTab:applicants:companyDTForm:companyDT:0:ktrmBankDetailApplicant:bankDetailsDT:0:j_idt")]/span[1]]'))).click()
    #    #print("Удален старый контакт компании")
    #    confirmAction("bank-detail-deleted", browser)
    #    tTimer()
    #    #sleep(0.5)
    i = 1
    #Добавление новых банковских данных:
    #Записать параметры для банковских деталей
    bankDict = {}
    bankTable = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="mainTab:applicant:companyDTForm:companyDT:0:ktrmBankDetailApplicant:bankDetailsDT_head"]')))
    ths = bankTable.find_elements(By.TAG_NAME, "th")
    maxI = 0
    #Собрать номера колонок для имеющихся атрибутов
    for th in ths:
        if th.text == "Наименование банковского счета":
            bankDict["name"] = i
        elif th.text == "БИК банка":
            bankDict["bik"] = i
        elif th.text == "ИИК (расчетный счет)":
            bankDict["code"] = i
        elif th.text == "Валюта":
            bankDict["currency"] = i
        elif th.text == "Наименование банка":
            bankDict["bank"] = i
        elif th.text == "Адрес банка":
            bankDict["bank_address"] = i
        elif th.text == "Код SWIFT":
            bankDict["swift"] = i
        i+=1
    #Получить значение последней колонки:
    i=0
    maxAttr = ""
    for key in bankDict:
        print("testing key: " + key)
        if i > maxI:
            maxI = i
            maxAttr = key
        i+=1
    print("max i: " + str(i) + " max attr: " + maxAttr)
    i = 0
    for jurBankAcc in jsonData["items"][0]["jur_account_accs"]:
        if jurBankAcc["actual"] == "1":
            #Нажать кнопку добавления банковских деталей:
            wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@title="Банковский счет"]'))).click()
            #Перебор доступных атрибутов в API
            for attr in jurBankAcc:
                #Вставка значений, если это не меню выбора валют, и лишние атрибуты
                if attr != "currency" and attr != "actual" and attr != "type":
                    if i == 0:
                        tPath = '//tbody[@id="mainTab:applicant:companyDTForm:companyDT:0:ktrmBankDetailApplicant:bankDetailsDT_data"]/tr/td['+str(bankDict[attr])+']/div/div[2]/input'
                    else:
                        tPath = '//tbody[@id="mainTab:applicant:companyDTForm:companyDT:0:ktrmBankDetailApplicant:bankDetailsDT_data"]/tr['+str(i)+']/td['+str(bankDict[attr])+']/div/div[2]/input'
                    #Ввести значение в ЕОКНО
                    elem = wait.until(EC.presence_of_element_located((By.XPATH, tPath)))
                    elem.send_keys(jurBankAcc[attr])
                #Выбор валюты банковских данных
                elif attr == "currency":
                    if i == 0:
                        tPath = '//tbody[@id="mainTab:applicant:companyDTForm:companyDT:0:ktrmBankDetailApplicant:bankDetailsDT_data"]/tr/td['+str(bankDict[attr])+']/div/div[2]/div/label'
                    else:
                        tPath = '//tbody[@id="mainTab:applicant:companyDTForm:companyDT:0:ktrmBankDetailApplicant:bankDetailsDT_data"]/tr['+str(i)+']/td['+str(bankDict[attr])+']/div/div[2]/div/label'
                    elem = wait.until(EC.presence_of_element_located((By.XPATH, tPath)))
                    elem.click()
                    elem = wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(@id, "mainTab:applicant:companyDTForm:companyDT:0:ktrmBankDetailApplicant:bankDetailsDT:'+str(i)+':j_idt") and contains(@id,"_filter")]')))
                    elem.send_keys(jurBankAcc[attr] + Keys.ENTER)
            i+=1
        else:
            continue
        #Сохранить данные
        tPath = '//tbody[@id="mainTab:applicant:companyDTForm:companyDT:0:ktrmBankDetailApplicant:bankDetailsDT_data"]/tr/td['+str(bankDict[maxAttr])+']/div/div[2]/input'
        elem = wait.until(EC.presence_of_element_located((By.XPATH, tPath)))
        elem.send_keys(Keys.TAB + Keys.TAB + Keys.ENTER)
        #Дождаться сохранения банковских данных:
        sleep(1)
        confirmAction("bank-detail-edited",browser, 10)

    #Конец добавления банковских данных

    #4 Заявитель в лице
    #Добавление информации о заявителе
    #Должность + должность Р.П.
    elem = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//input[@placeholder="Должность"]')))
    elem[0].send_keys(Keys.LEFT_CONTROL + "A")
    elem[0].send_keys(Keys.DELETE)
    elem[0].send_keys(jsonData["items"][0]["position"])
    elem[1].send_keys(Keys.LEFT_CONTROL + "A")
    elem[1].send_keys(Keys.DELETE)
    elem[1].send_keys(jsonData["items"][0]["position_rp"])
    #Определение признака резидента
    #Если резилент -- активировать галку
    print("Adding field sector 4")
    if jsonData["items"][0]["resident"] == "1":
        xpath = '//div[@class="ui-chkbox-box ui-widget ui-corner-all ui-state-default ui-state-active"]'
        if wait.until(EC.presence_of_element_located((By.XPATH, xpath))):
            t = 1
        else:
            wait.until(EC.presence_of_element_located((By.XPATH, '//div[@class="ui-chkbox-box ui-widget ui-corner-all ui-state-default"]'))).click()
        #while check_exists_by_xpath('//input[@id="j_id1:javax.faces.ViewState:11"]', browser, secs=1) == False:
        while wait.until(EC.presence_of_all_elements_located((By.XPATH, '//input[@placeholder="Фамилия"]')))[0].get_attribute('aria-disabled') == "false":
            print('Waiting, until field is deactivated')
            tTimer(1)
            #sleep(0.2)
        #Указать ИИН заявителя
        elem = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@id="mainTab:declarant:declarantForm:declarantIinInput"]')))
        elem.send_keys(Keys.LEFT_CONTROL + "A")
        elem.send_keys(Keys.DELETE)
        elem.send_keys(jsonData["items"][0]["iin"] + Keys.TAB)
        #tTimer(1)
        #sleep(1)
        if wait.until(EC.presence_of_all_elements_located((By.XPATH, '//input[@placeholder="Фамилия"]')))[0].get_attribute('value') == "":
            print("FIO empty")
        elif wait.until(EC.presence_of_all_elements_located((By.XPATH, '//input[@placeholder="Фамилия"]')))[0].get_attribute('value') == NULL:
            print("No VALUE is set")

        while (wait.until(EC.presence_of_all_elements_located((By.XPATH, '//input[@placeholder="Фамилия"]')))[0].get_attribute('value') == NULL or 
                wait.until(EC.presence_of_all_elements_located((By.XPATH, '//input[@placeholder="Фамилия"]')))[0].get_attribute('value') == ""):
            print("wait while IIN is processed")
            #tTimer(1)
            sleep(1)
        #sleep(10)
        print("val is: " + wait.until(EC.presence_of_all_elements_located((By.XPATH, '//input[@placeholder="Фамилия"]')))[0].get_attribute('value'))
        sleep(3)
            
    #Если не резидент -- указать ФИО в И.П.
    else:
        xpath = '//div[@class="ui-chkbox-box ui-widget ui-corner-all ui-state-default ui-state-active"]'
        if wait.until(EC.presence_of_element_located((By.XPATH, xpath))):
            sleep(0.5)
            wait.until(EC.presence_of_element_located((By.XPATH, '//div[@class="ui-chkbox-box ui-widget ui-corner-all ui-state-default ui-state-active"]'))).click()
        elem = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//input[@placeholder="Фамилия"]')))
        elem[0].send_keys(Keys.LEFT_CONTROL + "A")
        elem[0].send_keys(Keys.DELETE)
        elem[0].send_keys(jsonData["items"][0]["name1"])
        elem = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//input[@placeholder="Имя"]')))
        elem[0].send_keys(Keys.LEFT_CONTROL + "A")
        elem[0].send_keys(Keys.DELETE)
        elem[0].send_keys(jsonData["items"][0]["name2"])
        elem = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//input[@placeholder="Отчество"]')))
        elem[0].send_keys(Keys.LEFT_CONTROL + "A")
        elem[0].send_keys(Keys.DELETE)
        elem[0].send_keys(jsonData["items"][0]["name3"])
    #Указать ФИО в Р.П.
    #sleep(2)
    print("processing names in r.p.")
    #sleep(15)
    #while wait.until(EC.presence_of_all_elements_located((By.XPATH, '//input[@placeholder="Фамилия"]')))[0].get_attribute('value') == "":
    #    print("wait while IIN is processed")
    #    #tTimer(1)
    #    sleep(3)
    elem = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//input[@placeholder="Фамилия"]')))
    #elem[1].setAttribute('value', jsonData["items"][0]["name1_rp"])
    elem[1].send_keys(Keys.LEFT_CONTROL + "A")
    elem[1].send_keys(Keys.DELETE)
    elem[1].send_keys(jsonData["items"][0]["name1_rp"])
    #sleep(3)
    elem = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//input[@placeholder="Имя"]')))
    for tt in elem:
        print(tt.get_attribute('placeholder'))
    #elem[1].setAttribute('value', jsonData["items"][0]["name2_rp"])
    elem[1].send_keys(Keys.LEFT_CONTROL + "A")
    elem[1].send_keys(Keys.DELETE)
    elem[1].send_keys(jsonData["items"][0]["name2_rp"])
    #sleep(3)
    elem = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//input[@placeholder="Отчество"]')))
    #elem[1].setAttribute('value', jsonData["items"][0]["name3_rp"])
    elem[1].send_keys(Keys.LEFT_CONTROL + "A")
    elem[1].send_keys(Keys.DELETE)
    elem[1].send_keys(jsonData["items"][0]["name3_rp"])
    print("Все добавлены")

    #Указать номер документа заявителя:
    #doc_number
    elem = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Номер паспорта (удостоверения личности)"]')))
    elem.send_keys(Keys.LEFT_CONTROL + "A")
    elem.send_keys(Keys.DELETE)
    elem.send_keys(jsonData["items"][0]["doc_number"])

    #Дата выдачи:
    elem = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Дата выдачи"]')))
    #elem.click()
    tDate = jsonData["items"][0]["doc_date"]
    if tDate != "":
        tDate2 = datetime.strptime(tDate, "%Y-%m-%d")
        elem.send_keys(Keys.LEFT_CONTROL + "A")
        elem.send_keys(Keys.DELETE)
        elem.send_keys(tDate2.strftime("%d.%m.%y") + Keys.TAB)
    

    #Наименование документа-основания:
    elem = wait.until(EC.presence_of_element_located((By.XPATH, '//label[@id="mainTab:declarant:declarantForm:actingInput_label"]')))
    elem.click()
    elem = wait.until(EC.presence_of_element_located((By.XPATH, '//table[contains(@aria-activedescendant, "mainTab:declarant:declarantForm:actingInput_")]')))
    elems = elem.find_elements(By.TAG_NAME, 'td')
    print('Processing 4: document, starting to view Документ-основание')
    for td in elems:
        print(td.text.split(' ')[0].lower()[0:-1] + "|" + jsonData["items"][0]["based_on_id"].lower())
        #if jsonData["items"][0]["based_on_id"] == "Приказ":
        #    based_on_id = "Приказа"
        #else:
        #    based_on_id = jsonData["items"][0]["based_on_id"][0:-1]
        based_on_id = jsonData["items"][0]["based_on_id"]
        #if td.text != "--" and td.text.split(' ')[0].lower()[0:-1] == jsonData["items"][0]["based_on_id"].lower():
        #if td.text != "--" and td.text.split(' ')[0].lower()[0:-1] == based_on_id.lower():
        if td.text != "--" and td.text.split(' ')[0].lower() == based_on_id.lower():
            td.click()
            break
    #Номер документа-основания:
    elem = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Номер документа"]')))
    elem.send_keys(Keys.LEFT_CONTROL + "A")
    elem.send_keys(Keys.DELETE)
    elem.send_keys(jsonData["items"][0]["based_on_number"])

    #Дата документа-основания:
    #Дата документа
    elem = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Дата документа"]')))
    #elem.click()
    tDate = jsonData["items"][0]["based_on_date"]
    if tDate != "":
        tDate2 = datetime.strptime(tDate, "%Y-%m-%d")
        elem.send_keys(Keys.LEFT_CONTROL + "A")
        elem.send_keys(Keys.DELETE)
        elem.send_keys(tDate2.strftime("%d.%m.%y"))
        #sleep(60)
        #elem.click()
    sleep(1)
    xpath = '//table[@class="ui-datepicker-calendar"]'
    elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
    aS = elem.find_elements(By.TAG_NAME, 'a')
    for aE in aS:
        if aE.get_attribute("class") == 'ui-state-default ui-state-active':
            print("Found searched date")
            aE.click()
            break
    sleep(1)
    #Конец добавления информации о заявителе


    #5. Заявитель:
    #Выбрать заявителя:
    elem = wait.until(EC.presence_of_element_located((By.XPATH, '//table[@role="presentation" and contains(@id, "mainTab:j_")]')))
    elems = elem.find_elements(By.TAG_NAME, 'td')
    print('Выбор типа заявителя')
    for td in elems:
        print(td.text + "|" + jsonData["items"][0]["app_type_id"])
        if td.text == jsonData["items"][0]["app_type_id"]:
            td.click()
            break

    #6. ПРИЗНАК ВКЛЮЧЕНИЯ ПРОДУКЦИИ В ЕДИНЫЙ ПЕРЕЧЕНЬ ПРОДУКЦИИ, ПОДЛЕЖАЩЕЙ ОБЯЗАТЕЛЬНОМУ ПОДТВЕРЖДЕНИЮ
    #Проставить, если необходимо, признак
    #is_in_list == 1

    if jsonData["items"][0]["is_in_list"] == "1":
        xpath = '//div[contains(@class, "ui-chkbox-box ui-widget ui-corner-all ui-state-default ui-state-")]'
        elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        if elem.get_attribute("class") == "ui-chkbox-box ui-widget ui-corner-all ui-state-default ui-state-default":
            elem.click()
        #elem = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@class="ui-chkbox-box ui-widget ui-corner-all ui-state-default"]')))
        #elem.click()

    #7. ВИД ОБЪЕКТА ТЕХНИЧЕСКОГО РЕГУЛИРОВАНИЯ
    #Выбрать объект:
    wait.until(EC.presence_of_element_located((By.XPATH, '//label[@id="mainTab:techRegDocForm:techRegDocEAEU_label"]'))).click()
    elem = wait.until(EC.presence_of_element_located((By.XPATH, '//ul[@id="mainTab:techRegDocForm:techRegDocEAEU_items"]')))
    elems = elem.find_elements(By.TAG_NAME, 'li')
    for li in elems:
        if li.text.lower() == jsonData["items"][0]["part_type_id"].lower():
            li.click()
            break

    #8. СХЕМА:
    #Выбрать схему - scheme_id
    wait.until(EC.presence_of_element_located((By.XPATH, '//label[@id="mainTab:schemaForm:schemaCode_label"]'))).click()
    elem = wait.until(EC.presence_of_element_located((By.XPATH, '//ul[@id="mainTab:schemaForm:schemaCode_items"]')))
    elems = elem.find_elements(By.TAG_NAME, 'li')
    for li in elems:
        if li.text.lower() == jsonData["items"][0]["scheme_id"].lower():
            li.click()
            break

    #9. Документ, представленный Заявителем
    i = 0
    xpath = '//button[contains(@id, "mainTab:dKtrmDocSubmittApplicant:docDetailForm:docDetailDT:0:j_idt") and @title="Удалить"]'
    elem = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
    #elem.send_keys(Keys.PAGE_DOWN)
    delElement(Xpath=xpath, browser=browser)
    for doc in jsonData["items"][0]["req_docs"]:
        #Нажать кнопку создания документов
        btns = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//span[@class="ui-button-text ui-c"]')))
        for btn in btns:
            #print(btn.text)
            if btn.text.lower() == "Документ, представленный Заявителем".lower():
                print("button for #9 pressed")
                btn.click()
                break
        #Выбрать поиск документа 93:
        wait.until(EC.presence_of_element_located((By.XPATH, '//button[contains(@id, "mainTab:dKtrmDocSubmittApplicant:docDetailForm:docDetailDT:'+str(i)+':j_idt") and @title="Выбрать документ"]'))).click()
        #wait.until(EC.visibility_of_element_located((By.XPATH, '//span[@id="mainTab:dKtrmDocSubmittApplicant:dGeneralDocSbm:dialogSelectGeneralDocSbm_title"]')))
        k = 0
        while wait.until(EC.presence_of_element_located((By.XPATH, '//div[@id="mainTab:dKtrmDocSubmittApplicant:dGeneralDocSbm:dialogSelectGeneralDocSbm"]'))).get_attribute('aria-hidden') == "true":
            print("element is sleeping...zZzZ")
            sleep(0.5)
            k+=1
            if k == 10:
                break
        #wait.until(EC.presence_of_element_located((By.XPATH, '//button[contains(@id, "mainTab:dKtrmDocSubmittApplicant:docDetailForm:docDetailDT:'+str(i)+':j_idt") and @title="Выбрать документ"]'))).click()
        #Выбрать документ 93:
        elems = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//tbody[@id="mainTab:dKtrmDocSubmittApplicant:dGeneralDocSbm:selectGeneralDocSbmForm:generalDocSbmDT_data"]/tr/td')))
        for td in elems:
            print(td.text)
            if td.text == "93":
                print("93 clicked")
                td.click()
                break
        
        #Дождаться закрытия окна
        while wait.until(EC.presence_of_element_located((By.XPATH, '//div[@id="mainTab:dKtrmDocSubmittApplicant:dGeneralDocSbm:dialogSelectGeneralDocSbm"]'))).get_attribute('aria-hidden') == "false":
            print("element is active...zZzZ")
            sleep(0.5)
        #Удалить и ввести новое название документа:
        #mainTab:dKtrmDocSubmittApplicant:docDetailForm:docDetailDT:0:j_idt3289
        xpath = '//textarea[contains(@id, "mainTab:dKtrmDocSubmittApplicant:docDetailForm:docDetailDT:'+str(i)+':j_idt")]'
        
        print("trying to find path: " + xpath)
        elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        elem.clear()
        sleep(1)
        elem.send_keys(doc["docs_from_app_id"])

        #Указать номер документа:
        elem = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Номер" and contains(@id, "mainTab:dKtrmDocSubmittApplicant:docDetailForm:docDetailDT:'+str(i)+':j_id")]')))
        elem.send_keys(doc["doc_num"])
        #sleep(0.5)

        #Указать дату документа:
        if doc["doc_date"] != "" and doc["doc_date"] != NULL:
            elem = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Дата" and contains(@id, "mainTab:dKtrmDocSubmittApplicant:docDetailForm:docDetailDT:'+str(i)+':j_id")]')))
            tDt = datetime.strptime(doc["doc_date"], "%Y-%m-%d")
            elem.send_keys(tDt.strftime("%d.%m.%Y") + Keys.TAB)
        #sleep(0.5)

        #Сохранить доки:
        xpath = '//input[contains(@id, "mainTab:dKtrmDocSubmittApplicant:docDetailForm:docDetailDT:'+str(i)+':j_idt") and @placeholder="Номер аккредитации"]'
        elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        elem.click()
        elem.send_keys(Keys.TAB + Keys.TAB + Keys.TAB + Keys.TAB + Keys.TAB + Keys.ENTER)

        confirmAction("Документ отредактирован", browser)
        i+=1

    #10. Товаросопроводительная документация
    i = 0
    xpath = '//button[contains(@id, "mainTab:dKtrmDocDetailShip:docDetailForm:docDetailDT:0:j_idt") and @title="Удалить"]'
    delElement(Xpath=xpath, browser=browser)
    for doc in jsonData["items"][0]["ship_docs"]:
        if doc["ship_docs_id"] != "" and doc["ship_docs_id"] != NULL:
            #Нажать кнопку
            xpath = '//button[contains(@id, "mainTab:dKtrmDocDetailShip:docDetailForm:docDetailDT:j_idt") and @title="Товаросопроводительная документация"]'
            wait.until(EC.presence_of_element_located((By.XPATH, xpath))).click()
            #Удалить от 22.11 до строки 795
            #Поиск документа, нажать кнопку:
            #wait.until(EC.presence_of_element_located((By.XPATH, '//button[contains(@id, "mainTab:dKtrmDocDetailShip:docDetailForm:docDetailDT:'+str(i)+':j_idt") and @title="Выбрать документ"]'))).click()
            #Дождаться загрузки всплывающего окна
            #k=0
            #while wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(@id, "mainTab:dKtrmDocDetailShip:dUnatdtab:j_idt")]'))).get_attribute('aria-hidden') == "true":
            #    print("element is sleeping...zZzZ")
            #    sleep(0.5)
            #    k+=1
            #    if k == 10:
            #        break
            #Ввести наименование документа
            #elem = wait.until(EC.presence_of_element_located((By.XPATH, '//input[contains(@id, "mainTab:dKtrmDocDetailShip:dUnatdtab:selectUnatdtabForm:unatdTabDT:j_idt") and contains(@id, ":filter")]')))
            #elem.send_keys(doc["ship_docs_id"])
            #sleep(2)
            #Выбрать документ:
            #tBody = wait.until(EC.presence_of_element_located((By.XPATH, '//tbody[@id="mainTab:dKtrmDocDetailShip:dUnatdtab:selectUnatdtabForm:unatdTabDT_data"]')))
            #tds = tBody.find_elements(By.TAG_NAME, 'td')
            #for td in tds:
            #    if td.text == doc["ship_docs_id"]:
            #        td.click()
            #        break
            #Дождаться закрытия всплывающего окна
            #k = 0
            #while wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(@id, "mainTab:dKtrmDocDetailShip:dUnatdtab:j_idt")]'))).get_attribute('aria-hidden') == "false":
            #    print("element is sleeping...zZzZ")
            #    sleep(0.5)
            #    k+=1
            #    if k == 10:
            #        break
            #Ввести наименование документа:
            xpath = '//textarea[contains(@id, "mainTab:dKtrmDocDetailShip:docDetailForm:docDetailDT:'+str(i)+':j_idt")]'
            elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            elem.send_keys(doc["ship_docs_id"])

            #Ввести номер документа:
            elem = wait.until(EC.presence_of_element_located((By.XPATH, '//input[contains(@id, "mainTab:dKtrmDocDetailShip:docDetailForm:docDetailDT:'+str(i)+':j_idt") and @placeholder="Номер"]')))
            elem.send_keys(doc["doc_num"])

            #Ввести дату документа:
            elem = wait.until(EC.presence_of_element_located((By.XPATH, '//input[contains(@id, "mainTab:dKtrmDocDetailShip:docDetailForm:docDetailDT:'+str(i)+':j_idt") and @placeholder="Дата"]')))
            if doc["doc_date"] != "":
                tDt = datetime.strptime(doc["doc_date"], "%Y-%m-%d")
                elem.send_keys(tDt.strftime("%d.%m.%Y") + Keys.TAB)

            #Поставить признак печати в приложении, если необходимо:
            if doc["is_print"] == "1":
                elem = wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(@id, "mainTab:dKtrmDocDetailShip:docDetailForm:docDetailDT:'+str(i)+':j_idt")]/input[contains(@id, "mainTab:dKtrmDocDetailShip:docDetailForm:docDetailDT:'+str(i)+':j_idt")]')))
                elem.click()

            #Сохранить результаты:
            elem = wait.until(EC.presence_of_element_located((By.XPATH, '//input[contains(@id, "mainTab:dKtrmDocDetailShip:docDetailForm:docDetailDT:'+str(i)+':j_idt") and @placeholder="Номер"]')))
            elem.send_keys(Keys.TAB + Keys.TAB + Keys.TAB + Keys.ENTER)
            confirmAction("Документ отредактирован", browser)
            i+=1
            #Завершен ввод товаросопроводительного документа

    i=0
    xpath = '//button[contains(@id, "mainTab:dKtrmDocDetailTech:docDetailForm:docDetailDT:0:j_idt") and @title="Удалить"]'
    delElement(Xpath=xpath, browser=browser)
    #11. ТЕХНИЧЕСКИЙ РЕГЛАМЕНТ, НА СООТВЕТСТВИЕ ТРЕБОВАНИЯМ КОТОРОГО ПРОВОДИТСЯ ОЦЕНКА СООТВЕТСТВИЯ
    #Для всех, кроме Сертификата/декларации 620
    if (jsonData["items"][0]["confirm_doc_type_id"] != "Сертификат соответствия ЕАЭС по перечню №620" and 
        jsonData["items"][0]["confirm_doc_type_id"] != "Декларация о соответствии ЕАЭС по перечню №620"):
        for doc in jsonData["items"][0]["tech_regs"]:
            if doc["tech_reg_id"] != "" and doc["tech_reg_id"] != NULL:
                #Нажать кнопку добавления регламента:
                btns = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//span[@class="ui-button-text ui-c"]')))
                for btn in btns:
                    if btn.text == "ТЕХНИЧЕСКИЙ РЕГЛАМЕНТ, НА СООТВЕТСТВИЕ ТРЕБОВАНИЯМ КОТОРОГО ПРОВОДИТСЯ ОЦЕНКА СООТВЕТСТВИЯ":
                        btn.click()
                        break
                sleep(1)
                #Раскрыть поиск по коду ТН ВЭД:
                xpath = '//button[contains(@id, "mainTab:dKtrmDocDetailTech:docDetailForm:docDetailDT:'+str(i)+':j_idt") and @title="Выбрать документ"]'
                print("trying... " + xpath)
                wait.until(EC.presence_of_element_located((By.XPATH, xpath))).click()
                k=0
                while wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(@id, "mainTab:dKtrmDocDetailTech:dKzDocCca:j_idt")]'))).get_attribute('aria-hidden') == "true":
                    print("element is sleeping...zZzZ")
                    sleep(0.5)
                    k+=1
                    if k == 10:
                        break
                #Ввод кода ТН ВЭД для фильтра:
                elem = wait.until(EC.presence_of_element_located((By.XPATH, '//input[contains(@id, "mainTab:dKtrmDocDetailTech:dKzDocCca:selectKzDocCcaForm:kzDocCcaDT:j_idt") and contains(@id, "filter")]')))
                elem.send_keys(doc["tech_reg_id"])
                sleep(2)
                #Выбрать элемент из списка:
                tBody = wait.until(EC.presence_of_element_located((By.XPATH, '//tbody[@id="mainTab:dKtrmDocDetailTech:dKzDocCca:selectKzDocCcaForm:kzDocCcaDT_data"]')))
                tds = tBody.find_elements(By.TAG_NAME, 'td')
                for td in tds:
                    if td.text == doc["tech_reg_id"]:
                        print("Найден тех регламент, кликнут")
                        td.click()
                        break
                #Дождаться закрытия всплывающего окна
                k =0 
                while wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(@id, "mainTab:dKtrmDocDetailTech:dKzDocCca:j_idt")]'))).get_attribute('aria-hidden') == "false":
                    print("element is closing...zZzZ")
                    sleep(0.5)
                    k+=1
                    if k == 10:
                        break
                #Определить отметку о печати в приложении:
                if doc["is_print"] != "0":
                    #Поставить галку:
                    elem = wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(@id, "mainTab:dKtrmDocDetailTech:docDetailForm:docDetailDT:'+str(i)+':j_idt") and @class="ui-chkbox ui-widget kaz-checkbox"]')))
                    elem.click()
                #Сохранить изменения:
                elem = wait.until(EC.presence_of_element_located((By.XPATH, '//input[contains(@id, "mainTab:dKtrmDocDetailTech:docDetailForm:docDetailDT:'+str(i)+':j_idt") and @placeholder="Номер"]')))
                elem.send_keys(Keys.TAB + Keys.TAB + Keys.ENTER)
                confirmAction("Документ отредактирован", browser)
            i+=1
            #Конец ввода тех.регламента
    #12. --
    #
    #
    #
    #
    #

    #13. Документ, представленный в качестве доказательства соответствия обязательным требованиям или документ, на основании которого принято решение
    #xpath: id: mainTab:dKtrmDocDetailMand:docDetailForm:docDetailDT:j_idt3601
    i = 0
    xpath = '//button[contains(@id, "mainTab:dKtrmDocDetailMand:docDetailForm:docDetailDT:0:j_idt") and @title="Удалить"]'
    delElement(Xpath=xpath, browser=browser)
    for doc in jsonData["items"][0]["approve_docs"]:
        wait.until(EC.presence_of_element_located((By.XPATH, '//button[@title="Документ, представленный в качестве доказательства соответствия обязательным требованиям или документ, на основании которого принято решение"]'))).click()
        sleep(2)
        #Ввод наименования документа
        elem = wait.until(EC.presence_of_element_located((By.XPATH, '//textarea[contains(@id, "mainTab:dKtrmDocDetailMand:docDetailForm:docDetailDT:'+str(i)+':j_idt")]')))
        elem.send_keys(doc["docs_approve_name"])
        #Ввод номера документа
        elem = wait.until(EC.presence_of_element_located((By.XPATH, '//input[contains(@id, "mainTab:dKtrmDocDetailMand:docDetailForm:docDetailDT:'+str(i)+':j_idt") and @placeholder="Номер аккредитации"]')))
        elem.send_keys(doc["accr_num"])
        #Ввод даты документа:
        elem = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//input[contains(@id, "mainTab:dKtrmDocDetailMand:docDetailForm:docDetailDT:'+str(i)+':j_idt") and @placeholder="Дата"]')))
        elem = elem[1]
        if doc["accr_date_from"] != "":
            tDt = datetime.strptime(doc["accr_date_from"], "%Y-%m-%d")
            elem.send_keys(tDt.strftime("%d.%m.%Y") + Keys.TAB)
        #elem.send_keys(doc["accr_date_from"])
        #Поставить галку, если необходимо:
        if doc["is_print"] != "0":
            elem = wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(@id, "mainTab:dKtrmDocDetailMand:docDetailForm:docDetailDT:'+str(i)+':j_idt") and @class="ui-chkbox ui-widget kaz-checkbox"]')))
            elem.click()
        #Кем выдан:
        elem = wait.until(EC.presence_of_element_located((By.XPATH, '//textarea[contains(@id, "mainTab:dKtrmDocDetailMand:docDetailForm:docDetailDT:'+str(i)+':j_idt") and @placeholder="Выдан"]')))
        elem.send_keys(doc["labs_name"])
        #Сохранить документы:
        elem.send_keys(Keys.TAB + Keys.TAB + Keys.TAB + Keys.TAB + Keys.ENTER)
        confirmAction("Документ отредактирован", browser)
        i+=1
        #Конец ввода информации по п.13

    #14. СТАНДАРТ ИЛИ ИНОЙ ДОКУМЕНТ, В РЕЗУЛЬТАТЕ КОТОРОГО ОБЕСПЕЧИВАЕТСЯ СОБЛЮДЕНИЕ ТРЕБОВАНИЙ
    i=0
    xpath = '//button[contains(@id, "mainTab:dKtrmDocDetailStan:docDetailForm:docDetailDT:0:j_idt") and @title="Удалить"]'
    delElement(Xpath=xpath, browser=browser)
    print("Step 14...")
    for doc in jsonData["items"][0]["norm_docs"]:
        if doc["tech_reg"] != "":
            #Нажать кнопку открытия ввода сведений:
            wait.until(EC.presence_of_element_located((By.XPATH, '//button[contains(@id, "mainTab:dKtrmDocDetailStan:docDetailForm:docDetailDT:j_idt") and @title="СТАНДАРТ ИЛИ ИНОЙ ДОКУМЕНТ, В РЕЗУЛЬТАТЕ КОТОРОГО ОБЕСПЕЧИВАЕТСЯ СОБЛЮДЕНИЕ ТРЕБОВАНИЙ"]'))).click()
            #Ввод наименования:
            elem = wait.until(EC.presence_of_element_located((By.XPATH, '//textarea[contains(@id, "mainTab:dKtrmDocDetailStan:docDetailForm:docDetailDT:'+str(i)+':j_idt")]')))
            elem.send_keys(doc["gost_fullname"])
            #Ввод даты:
            elem = wait.until(EC.presence_of_element_located((By.XPATH, '//input[contains(@id, "mainTab:dKtrmDocDetailStan:docDetailForm:docDetailDT:'+str(i)+':j_idt") and contains(@id, "input") and @placeholder="Дата"]')))
            if doc["doc_date"] != "":
                tDt = datetime.strptime(doc["doc_date"], "%Y-%m-%d")
                elem.send_keys(tDt.strftime("%d.%m.%Y") + Keys.TAB)
            #Индикатор печати в файле:   
            if doc["is_print"] != "0":
                elem = wait.until(EC.presence_of_element_located((By.XPATH, '//input[contains(@id, "mainTab:dKtrmDocDetailStan:docDetailForm:docDetailDT:'+str(i)+':j_idt") and contains(@id, "input") and @placeholder="Дата"]')))
                elem.send_keys(Keys.TAB + Keys.SPACE)
            #Сохранить
            xpath = '//div[@id="mainTab:dKtrmDocDetailStan:docDetailForm:docDetailDT:'+str(i)+':docDetailDTelName"]'
            #print("trying xpath: " + xpath)
            elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            elem = elem.find_element(By.TAG_NAME, 'textarea')
            elem.send_keys(Keys.TAB + Keys.ENTER)
            confirmAction("Документ отредактирован", browser)
            i+=1
            #Конец ввода п.14

    #Переход на вкладку с Продукцией:
    elem = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Продукция")))
    elem.click()

    i = 0
    ii = 0
    iii = 0
    iiii = 0
    #Заполнение Продукции
    xpath = '//button[contains(@id, "mainTab:products:productDTForm:productDT:0:j_idt") and @title="Удалить"]'
    delElement(Xpath=xpath, browser=browser)
    for prod in jsonData["items"][0]["products"]:
        #Добавить продукцию
        xpath = '//button[contains(@id, "mainTab:products:productDTForm:productDT:j_id") and @title="Продукция"]'
        wait.until(EC.presence_of_element_located((By.XPATH, xpath))).click()
        #Наименование продукции:
        xpath ='//textarea[@id="mainTab:products:productDTForm:productDT:'+str(i)+':productNameInput" and @placeholder="Наименование продукта"]'
        elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        elem.send_keys(prod["title"])
        #Дополнительные сведения о продукции:
        xpath = '//textarea[@id="mainTab:products:productDTForm:productDT:'+str(i)+':productTextInput" and @placeholder="Дополнительные сведения о продукции"]'
        elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        elem.send_keys(prod["prod_additional_info"])
        #Дополнительная информация:
        xpath = '//textarea[@id="mainTab:products:productDTForm:productDT:'+str(i)+':additionalInfoTextInput" and @placeholder="Дополнительная информация"]'
        elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        elem.send_keys(prod["additional_information"])
        #Сохранить:
        elem.send_keys(Keys.TAB + Keys.TAB + Keys.ENTER)
        #Дождаться сохранения продукции
        confirmAction("Продукция отредактирована", browser)

        #Раскрыть папку для коммерческого названия:
        # get_attribute : aria-expanded : false
        #xpath = '//tbody[@id="mainTab:products:productDTForm:productDT_data"]/tr/td[2]/div[@id="ui-row-toggler ui-icon ui-icon-circle-triangle-e"]'
        xpath = '//tbody[@id="mainTab:products:productDTForm:productDT_data"]/tr/td[2]'
        expandFolder(browser=browser, xpath=xpath)
        #elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        #if elem.get_attribute("aria-expanded") == "false":
        #    elem.click()
        #Раскрыть папку для комм названий и пр.:
        #tBody = wait.until(EC.presence_of_element_located((By.XPATH, '//tbody[@id="mainTab:products:productDTForm:productDT_data"]')))
        #tds = tBody.find_elements(By.TAG_NAME, 'td')
        #for td in tds:
        #    print("td is: " + td.text)
        #    if td.text == str(i+1):
        #        #td.find_element(By.TAG_NAME, 'div').send_keys(Keys.TAB + Keys.ENTER)
        #        action.move_to_element(td).send_keys(Keys.TAB + Keys.ENTER).perform()
        #        #td.click()
        #        #td.send_keys(Keys.TAB + Keys.ENTER)
        #        break
        #1.1. Коммерческое название:
        #Новый блок
        ii = 0
        for comm in prod["comm_names"]:
            #Добавить коммерческое название:
            xpath = '//button[contains(@id, "mainTab:products:productDTForm:productDT:'+str(i)+':productTradeNames:tradeNameDT:j_idt") and @title="Коммерческое название"]'
            wait.until(EC.presence_of_element_located((By.XPATH, xpath))).click()
            #Указать краткое название:
            xpath = '//textarea[contains(@id, "mainTab:products:productDTForm:productDT:'+str(i)+':productTradeNames:tradeNameDT:'+str(ii)+':productTradeNameInput") and @placeholder="Коммерческое название"]'
            elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            elem.send_keys(comm["comm_name"])
            #Признак печати в приложении:
            if comm["is_print"] != "0":
                elem.send_keys(Keys.TAB + Keys.SPACE)
            #Сохранить:
            elem.send_keys(Keys.TAB + Keys.TAB + Keys.TAB + Keys.ENTER)
            confirmAction("Коммерческое наименование отредактировано", browser)
            #Раскрыть детали по коммерческому названию:
            #xpath = '//tbody[@id="mainTab:products:productDTForm:productDT_data"]/tr/td[2]'
            xpath = '//tbody[@id="mainTab:products:productDTForm:productDT:0:productTradeNames:tradeNameDT_data"]/tr/td[2]'
            expandFolder(browser=browser, xpath=xpath)
            #xpath = '//tbody[@id="mainTab:products:productDTForm:productDT:'+str(ii)+':productTradeNames:tradeNameDT_data"]/tr[@data-ri="'+str(iii)+'"]/td[2]/div'
            #elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            #elem.click()
            #1.1.1. Тип, марка, модель, артикул
            iii = 0
            for tmma in comm["tmma"]:
                #Открыть ввод информации
                xpath = '//button[contains(@id, "mainTab:products:productDTForm:productDT:'+str(i)+':productTradeNames:tradeNameDT:'+str(ii)+':productIdentifiers:productIdentifierDT:j_idt") and @title="Тип, марка, модель, артикул"]'
                elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                elem.click()
                #Ввести тип, марку, модель, артикул:
                xpath = '//textarea[contains(@id, "mainTab:products:productDTForm:productDT:'+str(i)+':productTradeNames:tradeNameDT:'+str(ii)+':productIdentifiers:productIdentifierDT:'+str(iii)+':productIdentifierNameInput") and @placeholder="Тип, марка, модель, артикул"]'
                elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                elem.send_keys(tmma["tmma"])
                #Размер партии:
                #Удалить от 22.11.2022
                #if tmma["part_size"] != "" and tmma["part_size"] != NULL:
                #    xpath = '//input[contains(@id, "mainTab:products:productDTForm:productDT:'+str(i)+':productTradeNames:tradeNameDT:'+str(ii)+':productIdentifiers:productIdentifierDT:'+str(iii)+':batchSizeInput_input") and @placeholder="Размер партии"]'
                #    elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                #    elem.send_keys(tmma["part_size"])
                #Код единицы измерения:
                #Удалить
                #if tmma["tmma_unit_id"] != "" and tmma["tmma_unit_id"] != NULL:
                #    xpath = '//div[@id="mainTab:products:productDTForm:productDT:'+str(i)+':productTradeNames:tradeNameDT:'+str(ii)+':productIdentifiers:productIdentifierDT:'+str(iii)+':cellEditorUnuomtab"]'
                #    wait.until(EC.presence_of_element_located((By.XPATH, xpath))).click()
                #    xpath = '//input[@id="mainTab:products:productDTForm:productDT:'+str(i)+':productTradeNames:tradeNameDT:'+str(ii)+':productIdentifiers:productIdentifierDT:'+str(iii)+':inputInstanceUnuomtab_filter" and @class="ui-selectonemenu-filter ui-inputfield ui-inputtext ui-widget ui-state-default ui-corner-all"]'
                #    elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                #    elem.send_keys(tmma["tmma_unit_id"] + Keys.ENTER)
                #Признак печати в приложении:
                if tmma["is_print"] != "0":
                    xpath = '//input[contains(@id, "mainTab:products:productDTForm:productDT:'+str(i)+':productTradeNames:tradeNameDT:'+str(ii)+':productIdentifiers:productIdentifierDT:'+str(iii)+':batchSizeInput_input") and @placeholder="Размер партии"]'
                    elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                    elem.send_keys(Keys.TAB + Keys.TAB + Keys.SPACE)
                #Сохранить:
                xpath = '//input[contains(@id, "mainTab:products:productDTForm:productDT:'+str(i)+':productTradeNames:tradeNameDT:'+str(ii)+':productIdentifiers:productIdentifierDT:'+str(iii)+':batchSizeInput_input") and @placeholder="Размер партии"]'
                elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                elem.send_keys(Keys.TAB + Keys.TAB + Keys.TAB + Keys.TAB + Keys.ENTER)
                confirmAction(tText="Коммерческое наименование отредактировано", browser=browser)

                #Раскрыть детали по следующему блоку
                #mainTab:products:productDTForm:productDT:0:productTradeNames:tradeNameDT:0:productIdentifiers:productIdentifierDT_data
                #mainTab:products:productDTForm:productDT:0:productTradeNames:tradeNameDT:0:productIdentifiers:productIdentifierDT_data
                #xpath = '//tbody[@id="mainTab:products:productDTForm:productDT:'+str(i)+':productTradeNames:tradeNameDT:'+str(ii)+':productIdentifiers:productIdentifierDT_data"]/tr[@data-ri="'+str(iii)+'"]/td[2]/div'
                xpath = '//tbody[@id="mainTab:products:productDTForm:productDT:'+str(i)+':productTradeNames:tradeNameDT:'+str(ii)+':productIdentifiers:productIdentifierDT_data"]/tr[@data-ri="'+str(iii)+'"]/td[2]'
                expandFolder(browser=browser, xpath=xpath)
                print("Tried to expand 1.1.1.")
                #print("Trying to to expand 1.1.1.1....")
                #elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                #elem.click()
                #sleep(1)

                #Блок ввода информации по единицы продукции:
                iiii = 0
                for unit_prods in tmma["unit_prods"]:
                    #Прожать кнопку:
                    xpath = '//button[contains(@id, "mainTab:products:productDTForm:productDT:'+str(i)+':productTradeNames:tradeNameDT:'+str(ii)+':productIdentifiers:productIdentifierDT:'+str(iii)+':productInstances:productInstanceDT:j_idt") and @title="Единица продукции или группа одинаковых единиц продукции"]'
                    wait.until(EC.presence_of_element_located((By.XPATH, xpath))).click()
                    #Поиск по ТН ВЭД:
                    if iiii == 0:
                        xpath = '//button[@id="mainTab:products:productDTForm:productDT:'+str(i)+':productTradeNames:tradeNameDT:'+str(ii)+':productIdentifiers:productIdentifierDT:'+str(iii)+':productInstances:productInstanceDT:'+str(iiii)+':loadCommodityCode" and @title="Поиск (Код ТН ВЭД)"]'
                        wait.until(EC.presence_of_element_located((By.XPATH, xpath))).click()
                        #Загрузка поиска:
                        xpath = '//div[@id="mainTab:products:productDTForm:productDT:'+str(i)+':productTradeNames:tradeNameDT:'+str(ii)+':productIdentifiers:productIdentifierDT:'+str(iii)+':productInstances:dSearchCommodityCode:hsCommodityCode"]'
                        k=0
                        while wait.until(EC.presence_of_element_located((By.XPATH, xpath))).get_attribute("aria-hidden") == "true":
                            print('Wait, until dialog pop-up...zZzZ')
                            sleep(0.5)
                            k+=1
                            if k == 10:
                                break
                        #Ввести ТН ВЭД:
                        xpath = '//input[contains(@id, "mainTab:products:productDTForm:productDT:'+str(i)+':productTradeNames:tradeNameDT:'+str(ii)+':productIdentifiers:productIdentifierDT:'+str(iii)+':productInstances:dSearchCommodityCode:commodityCodeDatatableForm:commodityCodeDatatable:j_idt") and contains(@id, "filter")]'
                        elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                        elem.send_keys(unit_prods["tn_ved"])
                        sleep(3)
                        #Выбрать ТН ВЭД:
                        xpath = '//tbody[@id="mainTab:products:productDTForm:productDT:'+str(i)+':productTradeNames:tradeNameDT:'+str(ii)+':productIdentifiers:productIdentifierDT:'+str(iii)+':productInstances:dSearchCommodityCode:commodityCodeDatatableForm:commodityCodeDatatable_data"]'
                        tBody = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                        tds = tBody.find_elements(By.TAG_NAME, 'td')
                        for td in tds:
                            print("processing TD..." + td.text)
                            if td.text == unit_prods["tn_ved"]:
                                print("TD found...")
                                td.click()
                                break
                        #sleep(1000)
                        #Дождаться загрузки данных по ТН ВЭД:
                        xpath = '//div[@id="mainTab:products:productDTForm:productDT:'+str(i)+':productTradeNames:tradeNameDT:'+str(ii)+':productIdentifiers:productIdentifierDT:'+str(iii)+':productInstances:dSearchCommodityCode:hsCommodityCode"]'
                        k = 0
                        while wait.until(EC.presence_of_element_located((By.XPATH, xpath))).get_attribute("aria-hidden") == "false":
                            print('wait until dialog is closed...zZzZ')
                            sleep(0.5)
                            k+=1
                            if k == 10:
                                break
                    #Заводской номер:
                    #Удалить?
                    xpath = '//textarea[@id="mainTab:products:productDTForm:productDT:'+str(i)+':productTradeNames:tradeNameDT:'+str(ii)+':productIdentifiers:productIdentifierDT:'+str(iii)+':productInstances:productInstanceDT:'+str(iiii)+':productInstanceIdInput" and @placeholder="Заводской номер единичного изделия или обозначение у группы одинаковых единиц продукции"]'
                    elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                    elem.send_keys(unit_prods["prod_num"])
                    #Наименование группы товаров:
                    #Удалить?
                    xpath = '//textarea[@id="mainTab:products:productDTForm:productDT:'+str(i)+':productTradeNames:tradeNameDT:'+str(ii)+':productIdentifiers:productIdentifierDT:'+str(iii)+':productInstances:productInstanceDT:'+str(iiii)+':productNameInsDetailInput" and @placeholder="Наименование"]'
                    elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                    elem.send_keys(unit_prods["title"])
                    #Количество в партии:
                    xpath = '//input[@id="mainTab:products:productDTForm:productDT:'+str(i)+':productTradeNames:tradeNameDT:'+str(ii)+':productIdentifiers:productIdentifierDT:'+str(iii)+':productInstances:productInstanceDT:'+str(iiii)+':productQuantityInput_input" and @placeholder="Количество"]'
                    elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                    elem.send_keys(unit_prods["amount"])
                    #Выбор кода единицы измерения:
                    xpath = '//div[@id="mainTab:products:productDTForm:productDT:'+str(i)+':productTradeNames:tradeNameDT:'+str(ii)+':productIdentifiers:productIdentifierDT:'+str(iii)+':productInstances:productInstanceDT:'+str(iiii)+':cellEditorUnuomtab"]'
                    wait.until(EC.presence_of_element_located((By.XPATH, xpath))).click()
                    #Ввод кода единицы измерения:
                    xpath = '//input[@id="mainTab:products:productDTForm:productDT:'+str(i)+':productTradeNames:tradeNameDT:'+str(ii)+':productIdentifiers:productIdentifierDT:'+str(iii)+':productInstances:productInstanceDT:'+str(iiii)+':inputInstanceUnuomtab_filter"]'
                    elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                    elem.send_keys(unit_prods["prod_unit_id"] + Keys.ENTER)
                    sleep(2)
                    #Дата c:
                    if unit_prods["prod_date_from"] != "" and unit_prods["prod_date_from"] != NULL:
                        tDt = datetime.strptime(unit_prods["prod_date_from"], "%Y-%m-%d")
                        xpath = '//input[@id="mainTab:products:productDTForm:productDT:'+str(i)+':productTradeNames:tradeNameDT:'+str(ii)+':productIdentifiers:productIdentifierDT:'+str(iii)+':productInstances:productInstanceDT:'+str(iiii)+':manufacturedDateInput_input" and @placeholder="Выберите дату"]'
                        elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                        elem.send_keys(tDt.strftime("%d.%m.%Y") + Keys.TAB)
                    #Срок годности:
                    if unit_prods["prod_date_to"] != "" and unit_prods["prod_date_to"] != NULL:
                        xpath = '//input[@id="mainTab:products:productDTForm:productDT:'+str(i)+':productTradeNames:tradeNameDT:'+str(ii)+':productIdentifiers:productIdentifierDT:'+str(iii)+':productInstances:productInstanceDT:'+str(iiii)+':expiryDateInput_input" and @title="Срок годности"]'
                        tDt = datetime.strptime(unit_prods["prod_date_to"], "%Y-%m-%d")
                        elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                        elem.send_keys(tDt.strftime("%d.%m.%Y") + Keys.TAB)
                    #Дополнительные сведения:
                    xpath = '//textarea[@id="mainTab:products:productDTForm:productDT:'+str(i)+':productTradeNames:tradeNameDT:'+str(ii)+':productIdentifiers:productIdentifierDT:'+str(iii)+':productInstances:productInstanceDT:'+str(iiii)+':productTextInsDetailInput" and @placeholder="Дополнительные сведения о продукции, обеспечивающие ее идентификацию"]'
                    elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                    elem.send_keys(unit_prods["additional_info"])
                    #Признак печати в приложении:
                    if unit_prods["is_print"] != "0":
                        elem.send_keys(Keys.TAB + Keys.SPACE)
                    #Сохранить:
                    elem.send_keys(Keys.TAB + Keys.TAB + Keys.TAB + Keys.ENTER)
                    #Конец ввода информации о единицы продукции
                    iiii+=1
                iii+=1
                #Конец ввода Типа, марки, модели, артикула
            ii+=1
            #Конец блока коммерческого названия

        #Ввод ТН ВЭД 1.2
        #items-0-tnveds, если больше 1 ТН ВЭД, то надо ввести только первые 4 цифры
        #print("TnVeds: " + str(len(jsonData["items"][0]["tnveds"])))
        n = 0
        tnveds = jsonData["items"][0]["tnveds"]
        print("tnveds count: " + str(len(tnveds)))
        for tnved in tnveds:
            #Раскрыть:
            print("processing tnved: " + tnved["tn_ved_id"])
            xpath = '//button[contains(@id, "mainTab:products:productDTForm:productDT:'+str(i)+':ProductCommodities:commodityDT:j_idt") and @title="ТН ВЭД"]'
            wait.until(EC.presence_of_element_located((By.XPATH, xpath))).click()
            #Поиск по Коду ТН ВЭД
            xpath = '//button[@id="mainTab:products:productDTForm:productDT:'+str(i)+':ProductCommodities:commodityDT:'+str(n)+':loadProductCommodityCodeInput" and @title="Поиск (Код ТН ВЭД)"]'
            wait.until(EC.presence_of_element_located((By.XPATH, xpath))).click()
            #Ожидание прогрузки меню кодов ТН ВЭД:
            xpath = '//div[contains(@id, "mainTab:products:productDTForm:productDT:'+str(i)+':ProductCommodities:j_idt") and contains(@id, ":hsCommodityCode")]'
            k=0
            while wait.until(EC.presence_of_element_located((By.XPATH, xpath))).get_attribute("aria-hidden") == "true":
                print("(TNVeds) element is inactive...zZzZ")
                sleep(0.5)
                k+=1
                if k == 10:
                    break
            #После загрузки, выполнить поиск ТН ВЭД. Если больше 1, то только первые 4 цифры:
            xpath = '//input[contains(@id, "mainTab:products:productDTForm:productDT:'+str(i)+':ProductCommodities:j_idt") and contains(@id, "commodityCodeDatatableForm:commodityCodeDatatable:j_idt") and contains(@id, ":filter")]'
            elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            if len(tnveds) > 1:
                elem.send_keys(tnved["tn_ved_id"][0:4])
                print('more than one TN VED')
            else:
                elem.send_keys(tnved["tn_ved_id"])
                print('only one TN VED is available')

            sleep(3)
            #mainTab:products:productDTForm:productDT:0:ProductCommodities:j_idt4503:commodityCodeDatatableForm:commodityCodeDatatable_data
            #Кликнуть по элементу:
            tBodyX = '//tbody[contains(@id, "mainTab:products:productDTForm:productDT:'+str(i)+':ProductCommodities:j_idt") and contains(@id, ":commodityCodeDatatableForm:commodityCodeDatatable_data")]'
            tBody = wait.until(EC.presence_of_element_located((By.XPATH, tBodyX)))
            tds = tBody.find_elements(By.TAG_NAME, "td")
            for td in tds:
                #print("TN Veds: " + td.text)
                if len(tnveds) > 1:
                    if td.text[0:4] == tnved["tn_ved_id"][0:4]:
                        td.click()
                        break
                else:
                    if td.text == tnved["tn_ved_id"]:
                        td.click()
                        break
            #Ожидание закрытия блока
            k=0
            while wait.until(EC.presence_of_element_located((By.XPATH, xpath))).get_attribute("aria-hidden") == "false":
                print("(TNVEDs - closing) element is still active...zZzZ")
                sleep(0.5)
                k+=1
                if k == 10:
                    break
            #Сохранить:
            sleep(3)
            xpath = '//textarea[@id="mainTab:products:productDTForm:productDT:'+str(i)+':ProductCommodities:commodityDT:'+str(n)+':commodityNameInput"]'
            elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            elem.send_keys(Keys.TAB + Keys.ENTER)
            confirmAction("ТН ВЭД отредактирована", browser)
            if len(tnveds) > 1:
                break
            n+=1
            #Конец блока ввода ТН ВЭД
        i+=1
        #Конец блока с продукцией

    #Блок ввода данных о производителе:
    #Добавить производителя:
    print("Добавить производителя")
    xpath = '//button[contains(@id, "mainTab:manufacturers:companyDTForm:companyDT:0:deleteCompanyButton") and @title="Удалить"]'
    delElement(Xpath=xpath, browser=browser)
    xpath = '//button[contains(@id, "mainTab:manufacturers:companyDTForm:companyDT:j_idt") and @title="Производитель"]'
    wait.until(EC.presence_of_element_located((By.XPATH, xpath))).click()
    sleep(2)
    #xpath = '//tbody[@id="mainTab:manufacturers:companyDTForm:companyDT_data"]/tr/td[2]/div'
    #elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
    #elem.click()
    #elem.send_keys(Keys.TAB + Keys.ENTER)
    if jsonData["items"][0]["manufacturer_resident"] != "":
        if jsonData["items"][0]["manufacturer_resident"] == "0":
            #Убрать признак резидента:
            xpath = '//div[@id="mainTab:manufacturers:companyDTForm:companyDT:0:inputCompanyResident" and @class="ui-chkbox ui-widget kaz-checkbox"]'
            wait.until(EC.presence_of_element_located((By.XPATH, xpath))).click()
            sleep(2)
            #Раскрыть меню стран:
            xpath = '//div[@id="mainTab:manufacturers:companyDTForm:companyDT:0:inputCompanyUnctytab"]'
            wait.until(EC.presence_of_element_located((By.XPATH, xpath))).click()
            #Ввести страну в фильтр:
            xpath = '//input[@id="mainTab:manufacturers:companyDTForm:companyDT:0:inputCompanyUnctytab_filter"]'
            elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            elem.send_keys(jsonData["items"][0]["manufacturer_country"] + Keys.ENTER)
        else:
            #Если резидент
            #Выбрать тип идентификации:
            xpath = '//table[@id="mainTab:manufacturers:companyDTForm:companyDT:0:inputIdentificationType" and @class="ui-selectoneradio ui-widget kaz-radio kaz-radio-mini"]'
            tTable = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            #Кнопки:
            btns = tTable.find_elements(By.TAG_NAME, "label")
            for btn in btns:
                if btn.text == "БИН":
                    btn.click()
                    break
            #Указать ИИН/БИН:
            xpath = '//input[@id="mainTab:manufacturers:companyDTForm:companyDT:0:companyBin"]'
            elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            elem.send_keys(jsonData["items"][0]["manufacturer_idn"] + Keys.TAB)
        sleep(3)
        #Ввести наименование компании и сохранить
        xpath = '//textarea[@id="mainTab:manufacturers:companyDTForm:companyDT:0:companyName" and @placeholder="Наименование"]'
        elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        #actions = ActionChains(browser)
        #actions.move_to_element(elem).key_down(Keys.LEFT_SHIFT).send_keys(Keys.TAB).send_keys(Keys.TAB).send_keys(Keys.TAB).key_up(Keys.LEFT_SHIFT).send_keys(Keys.ENTER).perform()
        elem.send_keys(jsonData["items"][0]["manufacturer_name"] + Keys.TAB + Keys.ENTER)
        confirmAction('Компания отредактирована', browser)
        xpath = '//tbody[@id="mainTab:manufacturers:companyDTForm:companyDT_data"]/tr/td[2]/div'
        elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        elem.click()
        #Раскрыть адреса:
        #xpath = '//tbody[@id="mainTab:manufacturers:companyDTForm:companyDT_data"]'
        #xpath = '//div[@id="mainTab:manufacturers:companyDTForm:companyDT:0:cellEditorCountry"]'
        #elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        #elem.send_keys(Keys.LEFT_SHIFT + Keys.TAB + Keys.ENTER)
        #actions = ActionChains(browser)
        #actions.move_to_element(elem).key_down(Keys.LEFT_SHIFT).send_keys(Keys.TAB).key_up(Keys.LEFT_SHIFT).send_keys(Keys.ENTER).perform()
        #actions.move_to_element(elem).send_keys(Keys.TAB).send_keys(Keys.ENTER).perform()
        #elem.key_down(Keys.LEFT_SHIFT).send_keys(Keys.TAB).key_up(Keys.LEFT_SHIFT).send_keys(Keys.ENTER)
        #xpath = '//tbody[@id="mainTab:manufacturers:companyDTForm:companyDT_data"]'
        #tBody = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        #divs = tBody.find_elements(By.TAG_NAME, "div")
        #for div in divs:
        #    if div.get_attribute("class") == "ui-row-toggler ui-icon ui-icon-circle-triangle-e" and div.get_attribute("aria-label") == "Toggle Row":
        #        print('found manufacturer expanding button')
        #        div.click()
        #        break
        #Дождаться раскрытия адресов:
        #tr = tBody.find_element(By.TAG_NAME, 'tr')
        sleep(2)
        k =0
        xpath = '//span[@id="mainTab:manufacturers:companyDTForm:companyDT:0:companyRowExpansionPG"]'
        if wait.until(EC.presence_of_element_located((By.XPATH, xpath))):
            print("Адреса производителя раскрыты")
        else:
            print("Адреса еще скрыты")
        #while tBody.find_element(By.TAG_NAME, 'tr').get_attribute("class") == "ui-widget-content ui-datatable-even":
        #    print("Ожидание раскрытия адресов производителя")
        #    sleep(1)
        #    k+=1
        #    if k == 10:
        #        break
        #sleep(2)

        #Блок ввода адресов производителя:
        i=0
        print("Блок ввода адресов производителя")
        for manF in jsonData["items"][0]["manufacturer_addresses"]:
            #КОСТЫЛЬ по адресу
            if manF["actual"] != "0" or manF["actual"] == "0":
                #Добавить адрес
                print("Добавление актуального адреса производителя")
                xpath = '//button[contains(@id, "mainTab:manufacturers:companyDTForm:companyDT:0:addressesManufacturer:adressesDT:j_idt") and @title="Адрес"]'
                wait.until(EC.presence_of_element_located((By.XPATH, xpath))).click()
                #Выбрать тип адреса:
                #Раскрыть меню типов адресов:
                xpath = '//div[@id="mainTab:manufacturers:companyDTForm:companyDT:0:addressesManufacturer:adressesDT:'+str(i)+':addressTypeInput"]'
                wait.until(EC.presence_of_element_located((By.XPATH, xpath))).click()
                #Выбрать адрес:
                xpath = '//table[@class="ui-selectonemenu-items ui-selectonemenu-table ui-widget-content ui-widget ui-corner-all ui-helper-reset" and @aria-activedescendant="mainTab:manufacturers:companyDTForm:companyDT:0:addressesManufacturer:adressesDT:'+str(i)+':addressTypeInput_0"]'
                tTable = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                tds = tTable.find_elements(By.TAG_NAME, 'td')
                for td in tds:
                    if td.text == manF["type_id"]:
                        td.click()
                        break
                #Раскрыть страны:
                xpath = '//div[@id="mainTab:manufacturers:companyDTForm:companyDT:0:addressesManufacturer:adressesDT:'+str(i)+':сompanyAddressUnctytabInput"]'
                wait.until(EC.presence_of_element_located((By.XPATH, xpath))).click()
                #Ввести наименование страны:
                xpath = '//input[@id="mainTab:manufacturers:companyDTForm:companyDT:0:addressesManufacturer:adressesDT:'+str(i)+':сompanyAddressUnctytabInput_filter"]'
                elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                if jsonData["items"][0]["manufacturer_country"] == "Республика Казахстан":
                    elem.send_keys("398")
                else:
                    elem.send_keys(jsonData["items"][0]["manufacturer_country"])
                elem.send_keys(Keys.ENTER)
                sleep(2)
                xpath = '//input[contains(@id, "mainTab:manufacturers:companyDTForm:companyDT:0:addressesManufacturer:adressesDT:'+str(i)+':j_idt")]'
                print('searching xpath: ' + xpath)
                elems = wait.until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
                #Указать область:
                elems[0].send_keys(manF["region"])
                #Указать район
                elems[1].send_keys(manF["area"])
                #Указать город:
                xpath = '//input[@id="mainTab:manufacturers:companyDTForm:companyDT:0:addressesManufacturer:adressesDT:'+str(i)+':cityInput" and @placeholder="Город"]'
                elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                elem.send_keys(manF["city"])
                #Указать населенный пункт:
                xpath = '//input[@id="mainTab:manufacturers:companyDTForm:companyDT:0:addressesManufacturer:adressesDT:'+str(i)+':settlementInput" and @placeholder="Населенный пункт"]'
                elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                elem.send_keys(manF["locality"])
                #Указать улицу:
                xpath = '//input[@id="mainTab:manufacturers:companyDTForm:companyDT:0:addressesManufacturer:adressesDT:'+str(i)+':streetNameInput" and @placeholder="Улица"]'
                elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                elem.send_keys(manF["street"])
                #Указать дом:
                xpath = '//input[@id="mainTab:manufacturers:companyDTForm:companyDT:0:addressesManufacturer:adressesDT:'+str(i)+':buildingNoInput" and @placeholder="Дом"]'
                elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                elem.send_keys(manF["home"])
                #Указать офис/квартиру:
                xpath = '//input[@id="mainTab:manufacturers:companyDTForm:companyDT:0:addressesManufacturer:adressesDT:'+str(i)+':poBoxInput" and @placeholder="Офис (квартира)"]'
                elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                elem.send_keys(manF["flat"])
                #Указать почтовый индекс:
                xpath = '//input[@id="mainTab:manufacturers:companyDTForm:companyDT:0:addressesManufacturer:adressesDT:'+str(i)+':postCodeInput" and @placeholder="Почтовый индекс"]'
                elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                elem.send_keys(manF["post"])
                #Сохранить:
                elem.send_keys(Keys.TAB + Keys.TAB + Keys.ENTER)
                confirmAction("Адрес отредактирован", browser)
            i+=1
    #Конец блока ввода информации по производителю
    #Открыть вкладку с экспертами:
    wait.until(EC.presence_of_element_located((By.LINK_TEXT, 'Орган, подтверждающий соответствие'))).click()
    #Указать эксперта:
    #Добавить эксперта:
    if len(jsonData["items"][0]["experts"]) > 0:
        xpath = '//button[contains(@id, "mainTab:dKtrmExperts:expertsForm:expertsDT:0:j_idt") and @title="Удалить"]'
        delElement(Xpath=xpath, browser=browser)
        xpath = '//button[contains(@id, "mainTab:dKtrmExperts:expertsForm:expertsDT:j_idt") and @title="Эксперт"]'
        wait.until(EC.presence_of_element_located((By.XPATH, xpath))).click()
        sleep(2)
        #Ввести ИИН эксперта
        xpath = '//input[contains(@id, "mainTab:dKtrmExperts:dSearchActiveCertExpert:searchUsersForm:foundUsersDT:j_idt") and contains(@id, ":filter")]'
        elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        for exp in jsonData["items"][0]["experts"]:
            if exp["expert_role_id"] == "Эксперт-аудитор на оценку":
                expId = exp["expert_idn"]
                elem.send_keys(exp["expert_idn"])
                break
        #Выбрать в таблице после поиска
        sleep(2)
        xpath = '//tbody[@id="mainTab:dKtrmExperts:dSearchActiveCertExpert:searchUsersForm:foundUsersDT_data"]'
        tBody = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        tds = tBody.find_elements(By.TAG_NAME, 'td')
        for td in tds:
            if td.text == expId:
                td.click()
                break
        sleep(2)

        #Указать руководителя:
        #Добавить руководителя:
        xpath = '//button[contains(@id, "mainTab:dKtrmChiefs:expertsForm:expertsDT:0:j_idt") and @title="Удалить"]'
        delElement(Xpath=xpath, browser=browser)
        xpath = '//button[contains(@id, "mainTab:dKtrmChiefs:expertsForm:expertsDT:j_idt") and @title="Руководитель"]'
        wait.until(EC.presence_of_element_located((By.XPATH, xpath))).click()
        sleep(2)
        #Ввести ИИН руководителя
        xpath = '//input[contains(@id, "mainTab:dKtrmChiefs:dSearchActiveCertExpert:searchUsersForm:foundUsersDT:j_idt") and contains(@id, ":filter")]'
        elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        for exp in jsonData["items"][0]["experts"]:
            if exp["expert_role_id"] == "Руководитель ОПС П - принятие решения о выдаче сертификата/регистарции декларации":
                expId = exp["expert_idn"]
                elem.send_keys(exp["expert_idn"])
                break
        #Выбрать в таблице после поиска
        sleep(2)
        xpath = '//tbody[@id="mainTab:dKtrmChiefs:dSearchActiveCertExpert:searchUsersForm:foundUsersDT_data"]'
        tBody = wait.until((EC.presence_of_element_located((By.XPATH, xpath))))
        tds = tBody.find_elements(By.TAG_NAME, 'td')
        for td in tds:
            if td.text == expId:
                td.click()
                break
        sleep(2)
    #Конeц блока добавления Органа, подтверждающего соответствие
    sleep(2)
    #Данные для печати формы:
    #Открыть вкладку:
    wait.until(EC.presence_of_element_located((By.LINK_TEXT, 'Данные для печати формы'))).click()
    #попытаться перевести:
    wait.until(EC.presence_of_element_located((By.XPATH, '//button[contains(@id, "mainTab:reportDataForm:j_idt") and @title="Перевести"]'))).click()
    confirmAction('Гугл переводчик недоступен', browser, 3)

    #Прочитать шаблон:
    sleep(2)
    xpath = '//table[@id="mainTab:reportDataForm:reportDataPG"]'
    tTable = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
    print("Data table is: " + str(tTable))
    #Построчный перебор:
    trs = tTable.find_elements(By.TAG_NAME, 'tr')
    r = 0
    for tr in trs:
        #Для каждой строки посмотреть колонки:
        tds = tr.find_elements(By.TAG_NAME, 'td')
        #Считать данные колонок
        if r == 0:
            #Прочитать наименование колонок:
            col = 0
            #Записать номера колонок, в которых нужные нам данные
            for td in tds:
                print("td in translation table: " + td.text)
                if td.text == "Наименование строки формы:":
                    rowNameId = col
                elif td.text == "Текст на русском языке:":
                    rowRuId = col
                elif td.text == "Текст на казахском языке:":
                    rowKzId = col
                col+=1
        else:
            #Прочитать значения:
            #Убрать пустые строки:
            if tds[rowNameId].text != "" and tds[rowNameId].text != NULL:
                #Взять перевод:
                #print("id is: " + tds[rowKzId].get_attribute('id'))
                #kzValue = tds[rowKzId].find_element(By.TAG_NAME, 'textarea').text
                #tVal = tds[rowKzId].find_element(By.TAG_NAME, 'textarea')
                #print(tVal.get_attribute('id'))
                tVal = tds[rowKzId].text
                kzValue = tVal
                if kzValue == "" or kzValue == NULL:
                    kzValue = "Переводчик не доступен"
                ruValue = tds[rowRuId].text
                rowName = tds[rowNameId].text
                eoknoList.append({
                    "row":str(r), 
                    "rowName":rowName, 
                    "rowRuValue":ruValue, 
                    "rowKzValue":kzValue
                })
        print("translation row num: " + str(r))
        r+=1
        #Конец построчного перебора
    print("debuggin translation: ")
    for eList in eoknoList:
        print(eList)
    #sleep(50000)
    requestTranslation = sendElnurTranslation(elnurId, eoknoList)
    print("translation sent: " + str(requestTranslation.content))

    #Сохранить
    #Нажать кнопку сохранить:
    xpath = '//button[contains(@id, "buttonsForm:j_idt")]'
    print('save button')
    btns = wait.until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
    for btn in btns:
        #print(btn.text)
        if btn.text.lower() == "СОХРАНИТЬ ЗАЯВЛЕНИЕ".lower():
            btn.click()
            break
    #sleep(180)
    #Подтверждение сохранения:
    confirmAction(tText="Заявление сохранено", browser=browser)
    sleep(2)
    #print("saved doc...")
    #xpath = '//div[@id="dialogSaved:dialogApplicationSaved"]'
    #if wait.until(EC.presence_of_element_located((By.XPATH, xpath))).get_attribute("aria-hidden") == "false":
    #    k=0
    #    print("doc saved menu is hidden")
    #    while wait.until(EC.presence_of_element_located((By.XPATH, xpath))).get_attribute("aria-hidden") == "true":
    #        sleep(0.5)
    #        k+=1
    #        if k == 10:
    #            print("timeout override")
    #            break
    #    print("doc saved menu is visible")
    #print("trying to click the button")

    #btnsDiv = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
    #btns = btnsDiv.find_elements(By.TAG_NAME, 'button')
    #for btn in btns:
    #    print("Button text: " + btn.text)
    #    if btn.text == "ЗАКРЫТЬ":
    #        btn.click()
    #        print("Clicked the button")
    #        break
    #xpath = '//span[@type="submit"]'
    #btns = wait.until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
    #for btn in btns:
    #    if btn.text == "Закрыть":
    #        btn.click()
    #        break
    #xpath = '//button[contains(@id, "dialogSaved:j_idt")]'
    #xpath = '//button[contains(@id, "dialogSaved:j_idt")]'
    #print(wait.until(EC.presence_of_element_located((By.XPATH, xpath))).text)
    #btn = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
    #btn.click()
    sleep(5)

    #Пока не сменится адрес страницы, надо ждать
    #k = 0
    #while cUrl == browser.current_url:
    #    sleep(1)
    #    k+=1
    #    if k == 10:
    #        break

    #Дебаг ждем
    #sleep(180)

    #Получить ИД заявки:
    #tId = browser.current_url.split('=')[1].split('&')[0]
    #res = sendElnurStatus(elnStatus2, elnurId, tId)
    #print("sent status and EOKNO number")

    #Перейти во вкладку с отчетом:
    elem = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Шаблоны печати")))
    elem.click()
    sleep(1)

    #Печать шаблона:
    xpath = '//button[@id="buttonsForm:printButtonCert"]'
    elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
    elem.click()

    #Дождаться открытия формы
    xpath = '//div[@id="dialogBeforePrintWithTemplate:dBeforePrint"]'
    k=0
    while wait.until(EC.presence_of_element_located((By.XPATH, xpath))).get_attribute('aria-hidden') == "true":
        sleep(0.5)
        k+=1
        if k == 10:
            break

    #Кнопка подтверждения печати формы:
    xpath = '//button[@id="dialogBeforePrintWithTemplate:beforePrintForm:continueButton"]'
    elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
    elem.click()

    #Дождаться прогрузки формы:
    xpath = '//div[@id="dialogKtrmPrint:dPrint"]'
    k=0
    while wait.until(EC.presence_of_element_located((By.XPATH, xpath))).get_attribute('aria-hidden') == "true":
        sleep(0.5)
        k+=1
        if k == 10:
            break
    sleep(2)
    #Заполнить доп форму для загрузки:
    xpath = '//textarea[@id="dialogKtrmPrint:printForm:docAnnexDetailDT:0:inputFormNumberId"]'
    elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
    elem.send_keys('1')
    #Загрузить отчет:
    xpath = '//button[@id="dialogKtrmPrint:printForm:saveAndDownloadButton"]'
    wait.until(EC.presence_of_element_located((By.XPATH, xpath))).click()

    #Дождаться окончания загрузки:
    #Если в директории нет файла, дождаться, пока загрузиться
    k = 0 
    while len(os.listdir(tFPath)) == 0:
        sleep(0.5)
        print("Waiting for file to be appeared")
        k+=1
        if k == 10:
            break
    #Проверить, что файл загрузился полностью (расширение соответствует ожиданиям)
    k = 0
    for path in os.listdir(tFPath):
        if os.path.isfile(os.path.join(tFPath, path)):
            while path[len(repExtension)*(-1):] != repExtension:
                sleep(0.5)
                print("Finding existing file")
                k+=1
                if k == 10:
                    break

    #Загрузить файл на сервер
    #resPath = tFPath + "report_" + tId + "." + repExtension
    resPath = os.path.join(tFPath, 'report_' + jsonData["items"][0]["eokno_reg_num"] + '.' + repExtension)
    print("File to be sent to Elnur: " + resPath)
    res = uploadElnurFile(resPath)
    if res["result"] == "ok":
        fileGuid = res["guid"]
        print("file on server: " + fileGuid)
    else:
        print("Couldn't upload the file")
    print(res)

    #Прикрутить файл к заявке:
    res = sendElnurStatus(elnStatus2, elnurId, jsonData["items"][0]["eokno_reg_num"], fileGuid)
    print(res)

    #Переместить файл в папку отправленных:
    for path in os.listdir(tFPath):
        if os.path.isfile(os.path.join(tFPath, path)):
            os.replace(os.path.join(tFPath, path), os.path.join(os.path.join(repSavePath, 'sent'), path))

    #Отправить на исполнение:
    #Только если сертификат:
    if "сертификат" in jsonData["items"][0]["confirm_doc_type_id"].lower() and roles["rpaStatus"] == "ready_rpa":
        xpath = '//button[@id="bpAction:bpButtonsForm:bpRepeat:0:threadButton"]'
        btn = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        btn.click()
        sleep(0.5)
        #Подтвердить отправление:
        sleep(1)
        xpath = '//button[contains(@id, "bpAction:dAction:actionForm:j_idt")]'
        btns = wait.until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
        
        for btn in btns:
            if btn.text.lower() == "подтвердить":
                btn.click()
                break
        sleep(1)

    #ДС, шаблон согласован:
    if roles["rpaStatus"] == "templ_agreed_rpa":
        xpath = '//button[@id="bpAction:bpButtonsForm:bpRepeat:0:threadButton"]'
        btn = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        btn.click()
        sleep(1.5)
        xpath = '//button[contains(@id, "bpAction:dAction:actionForm:j_idt")]'
        btns = wait.until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
        
        for btn in btns:
            if btn.text.lower() == "подтвердить":
                btn.click()
                break
    print("Finished stage x")
    tTimer(600)
    #sleep(60)
    browser.quit()