from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
import time

# set up driver
service = Service("/usr/local/bin/chromedriver")
driver = webdriver.Chrome(service=service)

#open router's login page
driver.get('https://192.168.100.1/cgi-bin/luci')
time.sleep(2)

driver.find_element(By.ID, "details-button").click()
time.sleep(1)

driver.find_element(By.ID, "proceed-link").click()
time.sleep(2)

#Enter username
username = driver.find_element(By.ID, "cbi-input-user")
username.send_keys('root')

#Enter password
password = driver.find_element(By.ID, "cbi-input-password")
password.send_keys('admin')

#Click login button
login = driver.find_element(By.XPATH, "//input[@type='submit' and @value='Login']")
login.click()
time.sleep(1)

#Click to top System
system_tab = driver.find_element(By.XPATH, "//a[@class='menu' and @data-title='System']")
system_tab.click()
time.sleep(1)

#Click the dropdown system item
system_dropdown = driver.find_element(By.XPATH, "//a[@data-title='System' and contains(@href, '/admin/system/system/')]")
system_dropdown.click()
time.sleep(1)

#Select the timezone
timezone_utc = Select(driver.find_element(By.ID, 'cbid.system.main.zonename'))
timezone_utc.select_by_value('UTC')
time.sleep(1)

#Save and apply
save_apply = driver.find_element(By.XPATH, "//input[@class='cbi-button cbi-button-apply' and @value='Save & Apply']")
save_apply.click()
time.sleep(2)

#print utc time
utc_time_info = driver.find_element(By.ID, '_systime-clock-status').text
print(f'Router UTC Time: {utc_time_info}')
time.sleep(3)

#select dublin timezone
timezone_dublin = Select(driver.find_element(By.ID, 'cbid.system.main.zonename'))
timezone_dublin.select_by_value('Europe/Dublin')
time.sleep(1)

#save and apply
save_apply = driver.find_element(By.XPATH, "//input[@class='cbi-button cbi-button-apply' and @value='Save & Apply']")
save_apply.click()
time.sleep(5)

#print dublin time
dublin_time_info = driver.find_element(By.ID, '_systime-clock-status').text
print(f'Router Dublin Time: {dublin_time_info}')
time.sleep(3)