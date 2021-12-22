# Python Imports
import pandas as pd
import numpy as np
import time
from bs4 import BeautifulSoup
from tqdm import trange

# Local Imports
from scraper.utils import *

#TODO: delete the 'study start' course

class SduScraper():
  def __init__(self):
    self.home_url = 'https://www.sdu.dk/en'
    self.university_name = 'University of Southern Denmark'
    self.university_id = 5
    self.bachelors_url = 'https://mitsdu.dk/en/mit_studie/bachelor'
    self.masters_url = 'https://mitsdu.dk/en/mit_studie/kandidat'

  def update_programs_info(self):
    browser = connect_to_browser()
    browser.get(self.bachelors_url)
    cookies_reject = browser.find_element_by_css_selector("div#cookiescript_reject")
    browser.execute_script("$(arguments[0]).click();", cookies_reject)
    programs_list, programs_url, grades = _get_programs(browser)
    browser.get(self.masters_url)
    masters_list, masters_url, masters_grades = _get_programs(browser)
    programs_list += masters_list
    programs_url += masters_url
    grades += masters_grades
    data = {'program': programs_list, 'grade': grades, 'url': programs_url}
    self.programs_info = pd.DataFrame(data=data)
    browser.quit()

  def navigate_to_courses(self, browser):
    table_urls = []
    name_index = None
    menus = browser.find_elements_by_css_selector("div.sidebox-links a")
    menus_names = [menu.text.lower() for menu in menus]
    # WEBPAGE TYPE 1
    if 'curriculum and course descriptions' in menus_names:
      press_element(menus, 'curriculum and course descriptions')
      try:
        cookies_reject = browser.find_element_by_css_selector("div#cookiescript_reject")
        time.sleep(2)
        browser.execute_script("$(arguments[0]).click();", cookies_reject)
      except: pass
      links_in_page = browser.find_elements_by_css_selector("div#article__body__main a")
      table_urls = [link.get_attribute("href") for link in links_in_page if 'course' in link.text.lower()]
      name_index = 3
    # WEBPAGE TYPE 2
    elif 'courses and timetable' in menus_names:
      press_element(menus, 'courses and timetable')
      blocks_in_page = browser.find_elements_by_css_selector("div.large-12.columns a")
      try:
        url = blocks_in_page[0].get_attribute("href")
        table_urls.append(url)
        table_urls.append(url + '/naeste_periode')
      except: pass
      name_index = 3
    # WEBPAGE TYPE 3
    elif 'programme structure' in menus_names:
      press_element(menus, 'programme structure')
      side_menus = browser.find_elements_by_css_selector("div.link-list a")
      press_element(side_menus, 'course descriptions')
      links_in_page = browser.find_elements_by_css_selector("div#article__body__main a")
      table_urls = [link for link in links_in_page if 'course' in link.text.lower()]
      table_urls = [link.get_attribute("href") for link in links_in_page if 'course' in link.text.lower()]
      name_index = 2
    return table_urls, name_index

  def update_programs_courses(self):
    self.programs_courses = pd.DataFrame(columns=['program', 'course', 'url'])
    browser = connect_to_browser()
    browser.get(self.bachelors_url)
    time.sleep(1)
    cookies_reject = browser.find_element_by_css_selector("div#cookiescript_reject")
    browser.execute_script("$(arguments[0]).click();", cookies_reject)
    for i in trange(len(self.programs_info), desc='Scraping programs courses'):
      program, grade, program_url = self.programs_info.iloc[i]
      browser.get(program_url)
      table_urls, name_index = self.navigate_to_courses(browser)
      program_courses, courses_urls = _extract_courses(browser, table_urls,
                                                       name_index)
      program_list = [program] * len(program_courses)                                                          
      df = pd.DataFrame(data={'program':program_list, 'course':program_courses,
                              'url': courses_urls})
      self.programs_courses = self.programs_courses.append(df)
    browser.quit()
    
  def update_courses_info(self):
    self.courses_info = pd.DataFrame(columns=['course', 'program', 'description'])
    browser = connect_to_browser()
    browser.get(self.bachelors_url)
    time.sleep(1)
    cookies_reject = browser.find_element_by_css_selector("div#cookiescript_reject")
    browser.execute_script("$(arguments[0]).click();", cookies_reject)
    for i in trange(len(self.programs_courses), desc='Scraping courses info'):
      program_name, course_name, course_url = self.programs_courses.iloc[i]
      df = self.courses_info.loc[self.courses_info.course == course_name]
      if not df.empty: continue
      browser.get(course_url)
      show_button = browser.find_element_by_css_selector("button.btn.btn-default.pull-right")
      browser.execute_script("$(arguments[0]).click();", show_button)
      description = _extract_course_description(browser)
      df = pd.DataFrame(data={'course':[course_name], 'program':[program_name],
                                  'description':[description]})
      self.courses_info = self.courses_info.append(df)
    browser.quit()

  # AUTO SCRAPER
  def update(self):
    work_time = time.localtime()
    print('Starting update at {}:{}'.format(work_time.tm_hour, work_time.tm_min))
    print('This will take several minutes')
    self.update_programs_info()
    print('1/3 Updates Finished')
    self.update_programs_courses()
    print('2/3 Updates Finished')
    self.update_courses_info()
    print('3/3 Updates Finished')
    work_time = time.localtime()
    print('Finished at {}:{}'.format(work_time.tm_hour, work_time.tm_min))

  def export_data(self):
    programs_info = self.programs_info.drop(labels='url',
                                            axis=1).dropna().reset_index(drop=True)
    programs_info.insert(1, 'university_id', self.university_id)
    programs_courses = self.programs_courses.drop(labels='url',
                                                  axis=1).dropna().reset_index(drop=True)
    programs_courses.insert(2, 'university_id', self.university_id)
    courses_info = self.courses_info.reset_index(drop=True)
    courses_info.insert(2, 'university_id', self.university_id)
    data = {'programs_info': programs_info,
            'courses_info': courses_info,
            'programs_courses': programs_courses
            }
    return data

# SDU.UTILS
def _process_program_name(program):
  program = program.replace(' in ', ' ')
  program = program.replace('bachelor of', 'bsc')
  program = program.replace('master of science', 'msc')
  program = program.replace(' (ba int.)', '')
  program = program.replace('master of', 'msc')
  program = program.replace('m.sc.', 'msc')
  program = program.replace('msc.', 'msc')
  program = program.replace('american studies', 'ma american studies')
  program = program.replace('english studies', 'ma english studies')
  program = program.replace(' (msc)', '')
  if program[:3] not in ['msc','bsc', 'ma ']:
    program = 'msc ' + program
  return program

def _process_toggle_text(toggle):
  text = toggle.text.lower()
  text = text.lstrip()
  text = text.rstrip()
  return text

def _get_programs(browser):
  programs_list = []
  programs_url = []
  grades = []
  programs = browser.find_elements_by_css_selector("div.article__link-list a")
  for program in programs:
    program_name = _process_program_name(program.text.lower())
    programs_list.append(program_name)
    programs_url.append(program.get_attribute("href"))
    grade = program_name[0:3]
    if 'bsc' in grade:
      grades.append('bsc')
    elif 'ma' in grade:
      grades.append('ma')
    else:
      grades.append('msc')
  return programs_list, programs_url, grades

def _extract_courses(browser, table_urls, name_index):
  program_courses = []
  courses_urls = []
  if name_index:
    for url in table_urls:
      browser.get(url)
      time.sleep(1)
      courses_rows = browser.find_elements_by_css_selector("tbody tr.border")
      for course in courses_rows:
        course_link = course.get_attribute("onclick")[13:-12]
        column_elements = course.find_elements_by_css_selector("td")
        course_name = column_elements[name_index].text.lower()
        if (course_name not in program_courses) and (course_link not in courses_urls):
          program_courses.append(course_name)
          courses_urls.append(course_link)
  return program_courses, courses_urls

def _extract_course_description(browser):
  course_html = BeautifulSoup(browser.page_source, 'html.parser')
  to_extract = ['description of outcome - skills', 'aim and purpose', 
                'description of outcome - knowledge', 'learning goals',
                'description of outcome - competences', 'content']
  toggles = course_html.find_all("h2", {"class": "base-hover-class"})
  #description = course_html.find("div", {"id": "course-description"})
  output = ''
  for toggle in toggles:
    if _process_toggle_text(toggle) in to_extract:
      text_div = toggle.find_next("div")
      text = text_div.find_all(text=True)
      for txt in text:
        output += '{} '.format(txt)
  return output