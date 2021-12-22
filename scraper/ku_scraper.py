# Python Imports
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import time
from tqdm import tqdm, trange

# Local Imports
from scraper.utils import *


class KuScraper():
  def __init__(self):
    self.masters_url = 'https://studies.ku.dk/masters/programmes/'
    self.university_name = 'University of Copenhagen'
    self.university_id = 4

  def update_programs_info(self):
    browser = connect_to_browser()
    browser.get(self.masters_url)
    cookies_reject = browser.find_element_by_class_name("btn.btn-default.btn-lg")
    browser.execute_script("$(arguments[0]).click();", cookies_reject)
    boxes = browser.find_elements_by_class_name("boxlink")
    programs_list = []
    programs_urls = []
    for box in tqdm(boxes, desc='Scraping programs:'):
      time.sleep(0.5)
      programs_list.append(box.text.lower())
      programs_urls.append(box.get_attribute("href"))
    grade = ["msc"]*len(programs_list)
    data = {'program': programs_list, 'grade': grade, 'url': programs_urls}
    self.programs_info = pd.DataFrame(data=data)
    browser.quit()

  def extract_courses_with_link(self, browser, courses_list, courses_url):
    links = browser.find_elements_by_tag_name("a")
    for link in links:
      url = link.get_attribute("href")
      name = link.text.lower()
      try:
        if _is_course(name, url):
          if (name not in courses_list) and (url not in courses_url):
            courses_list.append(name)
            courses_url.append(url)
      except:
        continue
    return courses_list, courses_url
  
  def extract_specialisation(self, browser, program, program_url, courses_list,
                             courses_url, special_layouts):
    banned = ["global health", "it and cognition", "anthropology"]
    if program in special_layouts:
      specialisations = browser.find_elements_by_css_selector("li.active a")
    elif program not in banned:
      browser.get(program_url + 'specialisations/')
      specialisations = browser.find_elements_by_css_selector("li.active li a")
    else:
      if program == "global health":
        courses_list, courses_url = self.extract_courses_with_link(browser,
                                                                   courses_list,
                                                                   courses_url)
      return courses_list, courses_url
    for specialisation in specialisations:
      url = specialisation.get_attribute("href")
      subbrowser = connect_to_browser()
      subbrowser.get(url)
      courses_list, courses_url = self.extract_courses_with_link(subbrowser,
                                                                  courses_list,
                                                                  courses_url)
      subbrowser.quit()
    return courses_list, courses_url

  def update_programs_courses(self):
    self.programs_courses = pd.DataFrame(columns=['program', 'course', 'url'])
    browser = connect_to_browser()
    browser.get(self.masters_url)
    cookies_reject = browser.find_element_by_class_name("btn.btn-default.btn-lg")
    browser.execute_script("$(arguments[0]).click();", cookies_reject)
    special_layouts = ["medicinal chemistry", "bioinformatics",
                       "pharmaceutical sciences"]
    for i in trange(len(self.programs_info), desc='Scraping programs courses'):
      program, _, program_url = self.programs_info.iloc[i]
      program_url += 'programme-structure/'
      browser.get(program_url)
      courses_list = []
      courses_url = []
      if _has_specialisations(browser) or program in special_layouts:
        courses_list, courses_url = self.extract_specialisation(browser, program,
                                                                program_url,
                                                                courses_list,
                                                                courses_url,
                                                                special_layouts)
      else:
        courses_list, courses_url = self.extract_courses_with_link(browser, 
                                                                   courses_list,
                                                                   courses_url)
      program_list = [program] * len(courses_list)                                                          
      df = pd.DataFrame(data={'program':program_list, 'course':courses_list,
                              'url': courses_url})
      self.programs_courses = self.programs_courses.append(df)
    browser.quit()
    # TODO: extend to the courses with only a table but no links
    # TODO: delete programs without courses in the programs_info (?)

  def extract_course_description(self, browser):
    course_html = BeautifulSoup(browser.page_source, 'html.parser')      
    content = course_html.find("div", {"id": "course-content"})
    description = course_html.find("div", {"id": "course-description"})
    text = content.find_all(text=True)
    text += description.find_all(text=True)
    output = ''
    for txt in text:
      output += '{} '.format(txt)
    return output

  def update_courses_info(self):
    self.courses_info = pd.DataFrame(columns=['course', 'program', 'description'])
    browser = connect_to_browser()
    browser.get(self.masters_url)
    cookies_reject = browser.find_element_by_class_name("btn.btn-default.btn-lg")
    browser.execute_script("$(arguments[0]).click();", cookies_reject)
    for i in trange(len(self.programs_courses), desc='Scraping courses info'):
      program_name, course_name, course_url = self.programs_courses.iloc[i]
      browser.get(course_url)
      df = self.courses_info.loc[self.courses_info.course == course_name]
      if not df.empty: continue
      try:
        output = self.extract_course_description(browser)
        df = pd.DataFrame(data={'course':[course_name], 'program':[program_name],
                                  'description':[output]})
        self.courses_info = self.courses_info.append(df)
      except:
        try:
          options = browser.find_elements_by_css_selector("ul.list-unstyled a")
          course_url = options[-1].get_attribute("href")
          browser.get(course_url)
          output = self.extract_course_description(browser)
          df = pd.DataFrame(data={'course':[course_name], 'program':[program_name],
                                  'description':[output]})
          self.courses_info = self.courses_info.append(df)
        except:
          self.programs_courses.loc[(self.programs_courses.program == program_name) \
                                  & (self.programs_courses.course == course_name),
                                   'url'] = np.nan
          print("Problem adding course:", course_url)
          continue
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
            'programs_courses': programs_courses}
    return data

# KU.UTILS
def _is_course(name, url):
  banned = ['see the course catalogue', 'course catalog', 'see the courses', '', 
            'the course catalogue', 'thesis 45 ects', 'master thesis project',
            "master’s thesis 30 ects", "master's thesis", "master’s thesis", " ", 
            "medicinal chemistry courses in the ucph course catalogue"]
  if "kurser.ku" in url:
    if url != "https://kurser.ku.dk/":
      if name not in banned:
        return True
  return False

def _has_specialisations(browser):
  left_menu = browser.find_elements_by_css_selector("ul.nav#leftmenu a")
  for item in left_menu:
    if item.text == 'Specialisations':
      return True
  body_links = browser.find_elements_by_css_selector("div.col-xs-12.col-sm-8.col-md-6.main-content a")
  for link in body_links:
    try:
      if "specialisation" in link.get_attribute("href"):
        return True
    except:
      continue
  return False