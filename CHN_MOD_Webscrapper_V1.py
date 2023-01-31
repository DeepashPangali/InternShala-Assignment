#importing the required libraries
from selenium import webdriver
import warnings 
warnings.filterwarnings('ignore')
import configparser
from datetime import datetime as dt
import time
from dateparser import parse
from utility.dateHandler import parseDate
import pandas as pd

def convert_date(date_str):
        date_obj = parse(date_str)
        return date_obj.strftime(r'%d/%m/%Y')
class Scraper:
    def __init__(self) -> None:
        self.__initial_configs()

    def __initial_configs(self):
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.base_config=self.config['BASE_CONFIGS']
        self.BASE_URL=self.base_config['URL']
        self.export_dir=self.base_config['EXPORT_DIR']
        self.export_filename='CHN_MOD_'+str(dt.now())[:10]
        self.driver=self.__intialize_driver()
        
        
    def __intialize_driver(self):
        self.driver_config = self.config['GECKO_WEBDRIVERS_CONFIG']
        isHeadless = self.driver_config.getboolean('HEADLESS')
        self.driver_path=self.driver_config['GECKODRIVERS_PATH']
        self.driver = webdriver.Chrome(executable_path=self.driver_path)
        self.driver.maximize_window()
        print(f'Driver Initialization Mode:{"Headless" if isHeadless else "Windowed"}')
        self.driver.get(self.BASE_URL)
        time.sleep(2)
        return self.driver
    def acquire_page(self):
        title=[]
        date=[]
        content=[]
        dict_all={}
        try:
            for j in range(34):
                new_links=[]
                news_t = self.driver.find_elements('xpath','//a[@target="_blank"]')
                k=0
                for i in news_t:
                    if k==0 or k==1 or k==len(news_t)-1:
                        k+=1
                        continue
                    else:
                        new_links.append(i)
                        k+=1
                for i in new_links: 
                    i.click()
                    time.sleep(3)
                    self.driver.switch_to.window(self.driver.window_handles[1])
                    time.sleep(8)
                    title.append(self.driver.find_element('xpath','//h1[@class="wzbiaoti"]').get_attribute('textContent'))
                    date_strr=self.driver.find_element('xpath','//div[@class="times"]').get_attribute('textContent')
                    content.append(self.driver.find_element('xpath','//div[@class="content"]').get_attribute('textContent'))
                    published_date=convert_date(date_strr)
                    print('\n\n')
                    print(type(date_strr))
                    print(date_strr)
                    print(published_date)
                    print('\n\n')
                    date.append(published_date)
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                
                next_btn = self.driver.find_elements('xpath','//a[@target="_self"]')
                if j==0:
                    next_btn[0].click()
                    time.sleep(3)
                elif j>24:
                    l=3
                    next_btn[l].click()
                    l+=1
                    time.sleep(3)
                else:
                    next_btn[2].click()
                    time.sleep(3)
                
                time.sleep(5)
            dict_all['Title']=title
            dict_all['Date']=date
            dict_all['Content']=content
            return dict_all
        except:
            dict_all['Title']=title
            dict_all['Date']=date
            dict_all['Content']=content
            return dict_all
    def save(self,final_data):
        post_data=pd.DataFrame(final_data)
        # post_data['Date']=pd.to_datetime(post_data['Date'])
        post_data.to_csv(f"{self.export_dir}/{self.export_filename}.csv",index=False)
    def scrape(self):
        data=self.acquire_page()
        print('Saving Data Fetched')
        self.save(data) 
if __name__=='__main__':
    a=Scraper()
    a.scrape()
print('Done Running')
    
