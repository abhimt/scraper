# Python Imports
import time
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import trange

# Local Imports
from scraper.utils import *

# DTU Scraper

class DtuScraper():
  def __init__(self):
    self.home_url = 'https://sdb.dtu.dk'
    self.university_name = 'Technical University of Denmark'
    self.university_id = 2

  def update_programs_info(self):
    browser = connect_to_browser()
    browser.get(self.home_url)
    programs_html = BeautifulSoup(browser.page_source, 'html.parser')
    programs_url = []
    programs_name = []
    grades = []
    all_programs = programs_html.find_all("div", "banner__item")
    for program in all_programs:
      name = _dtu_coursename_processing(program.text)
      link = program.find("a")["href"]
      programs_url.append(link)
      if '/109/' in link:
        grade = 'beng'
      elif '/108/' in link:
        grade = 'bsc'
      elif '/112/' in link:
        grade = 'msc'
      grades.append(grade)
      programs_name.append(grade + ' ' + name)
    browser.quit()
    data = {'program': programs_name, 'grade': grades, 'url': programs_url}
    self.programs_info = pd.DataFrame(data=data)

  def update_programs_courses(self):
    self.programs_courses = pd.DataFrame(columns=['program','course_code'])
    browser = connect_to_browser()
    for i in trange(len(self.programs_info), desc='Scraping programs courses'):
      program, _, program_url = self.programs_info.iloc[i]
      browser.get(program_url)
      program_html = BeautifulSoup(browser.page_source, 'html.parser')
      tables = program_html.find_all("div", "table-slide-container remove-gradient")
      all_courses = []
      for table in tables:
        courses_in_table = table.find_all('a')
        for course in courses_in_table:
          all_courses.append(course.text)
      for i in range(len(all_courses)):
        all_courses[i] = _dtu_coursename_processing(all_courses[i])
      all_courses = list(dict.fromkeys(all_courses))
      program_list = [program]*len(all_courses)
      df = pd.DataFrame(data={'program':program_list, 'course_code':all_courses})
      self.programs_courses = self.programs_courses.append(df)
    browser.quit()

  def update_courses_info(self):
    self.courses_info = pd.DataFrame(columns=['course', 'course_code',
                                              'program', 'description'])
    self.programs_courses['course'] = np.nan
    browser = connect_to_browser()
    # TODO: check some courses that doesn't belong to the 2021-2022
    url = 'https://kurser.dtu.dk/course/2021-2022/'
    #TODO: solve courses that are twice
    for i in trange(len(self.programs_courses), desc='Scraping courses description'):
      program, course_code, _ = self.programs_courses.iloc[i]
      df = self.courses_info.loc[self.courses_info.course_code==course_code]
      if not df.empty: continue
      course_url = url + course_code
      browser.get(course_url)
      time.sleep(0.5)
      course_html = BeautifulSoup(browser.page_source, 'html.parser')
      sections = ['General course objectives', 'Learning objectives', 'Content']
      blacklist = ['Remarks', 'CourseLiterature', 'Last updated']  
      output = ''
      try:
        title = course_html.find("div", "col-xs-8").text[7:].lower()
        df = self.courses_info.loc[self.courses_info.course == title]
        if not df.empty: continue
        box = course_html.find_all("div", "box")
        text = box[1].find_all(text=True)
        for i in range(len(text)):
            if text[i] in sections:
                for j in range(i+1, len(text)):
                  if (text[j] in sections) or (text[j] in blacklist):
                    i = j
                    break
                  output += '{} '.format(text[j])
        self.courses_info = self.courses_info.append(pd.DataFrame([[title, course_code, program, output]],
                                        columns=['course', 'course_code', 'program', 'description']))
        self.programs_courses.loc[self.programs_courses['course_code']==course_code, 'course'] = title
      except AttributeError:
        pass
        # TODO: Check if it's possible to add these courses
        # print the courses that are not found on the list
        # print(course_code)
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
                                            axis=1).reset_index(drop=True)
    programs_info.insert(1, 'university_id', self.university_id)
    programs_courses = self.programs_courses.drop(labels='course_code',
                                                  axis=1).dropna().reset_index(drop=True)
    programs_courses.insert(2, 'university_id', self.university_id)
    courses_info = self.courses_info.drop(labels='course_code',
                                           axis=1).reset_index(drop=True)
    courses_info.insert(2, 'university_id', self.university_id)
    data = {'programs_info': programs_info,
            'courses_info': courses_info,
            'programs_courses': programs_courses}
    return data

# DTU.UTILS
def _dtu_coursename_processing(course_name):
  course_name = course_name.lower()
  course_name = course_name.replace('\n', '')
  # Format
  course_name = course_name.rstrip()
  course_name = course_name.lstrip()
  return course_name