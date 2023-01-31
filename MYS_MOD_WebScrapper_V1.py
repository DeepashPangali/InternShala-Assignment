from asyncio import constants
from selenium import webdriver
from tqdm import tqdm
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import configparser
import re
from dateparser import parse
import os
import time
import utils.constants as const
import pandas as pd
from datetime import datetime as dt

class Fetcher:
    def __init__(self) -> None:
        self.__initial_configs()
        self.final_data={
            'Title':[],
            'Quotation number':[],
            'Ministry':[],
            'Date':[],
            'PTJ':[],
            'Duration':[],
            'Closing Date':[],
            'Sample Delivery Closing Date':[],
            'Offer Validity':[],
            'Valid Expired Offer':[],
            'Procurement Method':[]
            
        }
        self.final_dict={}

    def convert_date(self,date_str):
        date_obj = parse(date_str)
        return date_obj.strftime(r'%d/%m/%Y')

    def __initial_configs(self):
        self.config=configparser.ConfigParser()
        self.config.read('config.ini')
        self.base_config=self.config['BASE_CONFIG']
        self.BASE_URL=self.base_config['URL']
        self.from_date=self.base_config['FROM_DATE']
        self.from_date=self.convert_date(self.from_date)
        print(self.from_date)
        self.export_dir=self.base_config['EXPORT_DIR']
        self.export_type=self.base_config['EXPORT_TYPE']
        self.export_filename='MYS_MOD_'+dt.now().strftime('%m%d%Y')

        #os.makedirs(self.export_dir,exist_ok=True)
        self.driver=self.__intialize_driver()

    def __intialize_driver(self):
        self.driver_config=self.config['FIREFOX_WEBDRIVERS_CONFIG']
        isHeadless=self.driver_config.getboolean('HEADLESS')
        driverPath=self.driver_config['GECKODRIVER_PATH']
        if bool(self.driver_config['USE_TOR'])==True:
            torexe = os.popen(r'tor.exe')
            profile = FirefoxProfile(r'profile.default')
            
            PROXY = '111.221.54.48:33527' #malaysia
            #PROXY= '41.65.236.41:1981' #    EGYPT

            proxy = Proxy({
                'proxyType': ProxyType.MANUAL,
                'httpProxy': PROXY,
                'ftpProxy': PROXY,
                'sslProxy': PROXY,
                'noProxy': PROXY #set this value as desired
                })
            profile.set_preference('network.proxy.type', 1)
            profile.set_preference('network.proxy.socks', '127.0.0.1')
            profile.set_preference('network.proxy.socks_port', 9150)
            profile.set_preference("network.proxy.socks_remote_dns", False)
            profile.set_preference( "places.history.enabled", False )
            profile.set_preference( "privacy.clearOnShutdown.offlineApps", True )
            profile.set_preference( "privacy.clearOnShutdown.passwords", True )
            profile.set_preference( "privacy.clearOnShutdown.siteSettings", True )
            profile.set_preference( "privacy.sanitize.sanitizeOnShutdown", True )
            profile.set_preference( "signon.rememberSignons", False )
            profile.set_preference( "network.cookie.lifetimePolicy", 2 )
            profile.set_preference( "network.dns.disablePrefetch", False )
            profile.set_preference( "network.http.sendRefererHeader", 0 )
            profile.set_preference( "permissions.default.image", 2 )
            profile.update_preferences()
            
            firefox_options = webdriver.FirefoxOptions()
            PROXY_STR = "1.9.155.14:8080"
            firefox_options.add_argument('--proxy-server=%s' % PROXY_STR)
            firefox_options.binary_location = r'C:/Program Files/Mozilla Firefox/firefox.exe'
            firefox_options.headless=isHeadless
            self.driver = webdriver.Firefox(firefox_profile= profile ,options=firefox_options,proxy=proxy, executable_path=driverPath)
            
            self.driver.maximize_window()
            time.sleep(10)
            print(f'Driver Initialization Mode:{"Headless" if isHeadless else "Windowed"}')
            self.driver.get(self.BASE_URL)
            return self.driver
        
        profile = webdriver.FirefoxProfile()
        profile.set_preference("browser.download.folderList", 2)
        profile.set_preference("browser.download.manager.showWhenStarting", False)
        #profile.set_preference("browser.download.dir",self.__temp_download_directory)
        profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/json,application/pdf")
        profile.set_preference("dom.push.enabled", False)
        profile.update_preferences()
        firefox_options=FirefoxOptions()
        firefox_options.headless=isHeadless
        driverPath=self.driver_config['GECKODRIVER_PATH']
        self.driver=webdriver.Firefox(firefox_profile=profile,options=firefox_options,executable_path=driverPath)
        self.driver.maximize_window()
        print(f'Driver Initialization Mode:{"Headless" if isHeadless else "Windowed"}')
        self.driver.get(self.BASE_URL)
        return self.driver
    
    def scroll_page(self):
        continue_scrap=True
        final_list=[]
        page_number=1
        try:
            while True:
                rfq_url=[]
                next_button=self.driver.find_element(By.XPATH,const.next_page)
                if next_button:
                    href_elem=self.driver.find_elements(By.XPATH,const.rfq_links)
                    for i in href_elem:
                        rfq_url.append(i.get_attribute('onclick'))
    
                    #print(rfq_url)
                    
                    
                    rfq_url=self.filter_list(rfq_url)
                    # print(rfq_url)
                    for i,_ in enumerate(rfq_url):
                        final_dict={}
                        time.sleep(5)
                        ok_to_go=self.driver.find_element(By.XPATH,"//div[@class='titleheader']")
                        if not ok_to_go:
                            print('Not Ready to Execute')
                            continue
    
                        #print('\n')
                        #print(url)
                        url=rfq_url[i]
                        self.driver.execute_script(url)
                        
                        print(f'Executed {url}')
                        print('Extracting Data')
                        key_list=[]
                        value_list=[]
                   
                        view_xpath = '//td[@class="columnWidth20"]'
                        element_present = EC.presence_of_element_located((By.XPATH, view_xpath))
                        WebDriverWait(self.driver, 40).until(element_present)
                        key_list_sel=self.driver.find_elements_by_xpath(view_xpath)
                        for elem in key_list_sel:
                            key=elem.get_attribute('textContent')
                            key_list.append(key)
                        #print(key_list)
                        time.sleep(3)
    
                        view_xpath = '//td[@class="columnWidth100"]'
                        element_present = EC.presence_of_element_located((By.XPATH, view_xpath))
                        WebDriverWait(self.driver, 40).until(element_present)
                        value_list_sel=self.driver.find_elements_by_xpath(view_xpath)
                        for elem in value_list_sel:
                            value=elem.get_attribute('textContent')
                            value_list.append(value)
                        time.sleep(3)
                        #print(value_list)
                        length_value_list=len(value_list)
                        key_list=key_list[0:length_value_list]
    
                        zipped_list=zip(key_list,value_list)
                        for m,n in zipped_list:
                            final_dict[m]=n
    
                        title=final_dict['Tajuk Perolehan']
                        print('\n')
                        print(title)
                        print('\n')
                        published_date_text=final_dict['Tarikh Iklan']
                        published_date=self.convert_date(published_date_text)
                        if published_date< self.from_date:
                            continue_scrap=False
                            print('Date Out of Range')
                            print('published date =>',published_date)
                            print('self.from_date=>',self.from_date)
                            break
                        final_list.append(final_dict)
                        time.sleep(5)
                        try:
                            self.driver.execute_script("PrimeFaces.ab({source:'_scNoticeBoard_WAR_NGePportlet_:form:j_idt9'})")
                            print('Clicked Back Button')
                        except:
                            break
                        
                    if not continue_scrap:
                        break
                    
                    next_button_x_path=f'//span[@class="ui-paginator-page ui-state-default ui-corner-all"][contains(text(),"{page_number+1}")]'
                    WebDriverWait(self.driver,40).until(EC.element_to_be_clickable((By.XPATH,next_button_x_path))).click()
                    time.sleep(5)
                    page_number=page_number+1
            return final_list

        except:
            return final_list
                    
    def apply_filter(self):
        filter_input=self.driver.find_element(By.XPATH,const.filter)
        self.driver.implicitly_wait(10)
        for i in range(6):
            time.sleep(3)
            filter_input.send_keys(Keys.DOWN)
            if i==4:
                filter_input.send_keys(Keys.ENTER)
                break
        time.sleep(5)
        operator=self.driver.find_element(By.XPATH,const.operator)
        self.driver.implicitly_wait(10)
        for i in range(3):
            time.sleep(3)
            operator.send_keys(Keys.DOWN)
            if i==1:
                break
        date_filter=self.driver.find_element(By.XPATH,const.date_filter)
        self.driver.implicitly_wait(10)
        date_filter.send_keys(self.from_date)
        time.sleep(1)
        self.driver.execute_script(const.apply_changes)
        time.sleep(2)

   
    
    def filter_list(self,lst):
        del lst[1::2]
        lst=[x.split(';')[0] for x in lst]
        return lst

    def save(self,final_data):
        post_data=pd.DataFrame(final_data)
        post_data.to_csv(f"{self.export_dir}/{self.export_filename}.csv",encoding="utf-8",sep="|",index=False)
    
    def scrape(self):
        data=self.scroll_page()
        print('Saving Data Fetched')
        self.save(data)
        #self.driver.close()

if __name__ == '__main__':
    a=Fetcher()
    # a.scroll_page()
    a.scrape()
print('Done Running')