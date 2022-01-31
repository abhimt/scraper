
from re import VERBOSE
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

import logging
import pandas as pd
import time

def connect_to_browser():
  chrome_options = webdriver.ChromeOptions()
  # chrome_options.add_argument('--headless')
  chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36')
  #chrome_options.add_argument('--no-sandbox')
  #chrome_options.add_argument('--disable-dev-shm-usage')
  chrome_options.add_argument('--disable-logging')
  #return webdriver.Chrome('chromedriver', options=chrome_options)
  return webdriver.Chrome(ChromeDriverManager(print_first_line=False).install(),
                          options=chrome_options)

def press_element(element_list, element_name):
  for element in element_list:
    if element_name.lower() in element.text.lower():
      element.click()
      time.sleep(1)
      break

# TESTING FUNCTIONS
def set_data(scraper, name, data):
  if name == 'programs_info':
    scraper.programs_info = data.copy()
  if name == 'programs_courses':
    scraper.programs_courses = data.copy()
  if name == 'courses_info':
    scraper.courses_info = data.copy()