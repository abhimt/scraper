from os import ctermid
import pandas as pd
import numpy as np
import time
from bs4 import BeautifulSoup
from tqdm import trange, tqdm

# Local Imports
from scraper.utils import *

class CbsScraper():
  def __init__(self):
    self.home_url = 'https://www.cbs.dk/en'
    self.university_name = 'Copenhagen Business School'
    self.university_id = 6
    self.bachelors_url = '/study/bachelor/all-bachelor-programmes'
    self.masters_url = '/study/graduate/graduate-teaching-language'
    self.slide_programs = ['bsc business language and culture', 
                           'bsc business administration and digital management',
                           'bsc business administration and service management',
                           'bsc business administration and sociology',
                           'bsc international business',
                           'bsc international business and politics',
                           'bsc international shipping and trade']
  
  def update_programs_info(self):
    browser = connect_to_browser()
    browser.get(self.home_url + self.bachelors_url)
    bachelors = browser.find_elements_by_css_selector("div.ready-accordion#acc-0-9 a")
    programs_list, programs_url, grades = _get_programs(bachelors)
    browser.get(self.home_url + self.masters_url)
    masters = browser.find_elements_by_css_selector("div.ready-accordion#acc-0-0 a")
    masters_list, masters_url, masters_grades = _get_programs(masters)
    programs_list += masters_list
    programs_url += masters_url
    grades += masters_grades
    data = {'program': programs_list, 'grade': grades, 'url': programs_url}
    self.programs_info = pd.DataFrame(data=data)
    browser.quit()

  def update_programs_courses(self):
    self.programs_courses = pd.DataFrame(columns=['program', 'course', 'url'])
    browser = connect_to_browser()
    banned = ['', "elective 1", "elective 2", "master's thesis",
              "master's thesis defence", "master’s thesis"
              "electives / exchange / academic internship (30 ects)"]
    for i in trange(len(self.programs_info), desc='Scraping programs courses'):
      program, grade, program_url = self.programs_info.iloc[i]
      program_courses = []
      courses_urls = []
      if program in self.slide_programs: continue
      elif program == 'bsc business asian language and culture international business asia':
        browser.get(program_url)
        courses = browser.find_elements_by_css_selector("tbody td a")
        for course in courses:
          course_name = _process_course_name(course.text)
          if course_name in banned: continue
          if course_name in program_courses: continue
          course_url = course.get_attribute("href")
          program_courses.append(course_name)
          courses_urls.append(course_url)
      else:
        browser.get(program_url)
        links = browser.find_elements_by_css_selector("div.field-cbs-graduate-body p a")
        for link in links:
          if 'https://studieordninger.cbs.dk/' in link.get_attribute("href"):
            browser.get(link.get_attribute("href"))
            break
          else:
            continue
        courses = browser.find_elements_by_css_selector("tbody td a")
        for course in courses:
          course_name = _process_course_name(course.text)
          if course_name in banned: continue
          if course_name in program_courses: continue
          course_url = course.get_attribute("href")
          program_courses.append(course_name)
          courses_urls.append(course_url)
      program_list = [program] * len(program_courses)
      df = pd.DataFrame(data={'program':program_list, 'course':program_courses,
                              'url': courses_urls})
      self.programs_courses = self.programs_courses.append(df)
    browser.quit()

  def update_courses_info(self):
    self.courses_info = pd.DataFrame(columns=['course', 'program', 'description'])
    browser = connect_to_browser()
    sections_to_extract = ['course content, structure and pedagogical approach',
                           'learning objectives',]
    for i in trange(len(self.programs_courses), desc='Scraping courses info'):
      program_name, course_name, course_url = self.programs_courses.iloc[i]
      df = self.courses_info.loc[self.courses_info.course == course_name]
      if not df.empty: continue
      browser.get(course_url)
      if 'https://kurser.ku.dk/' in course_url:
        try:
          cookies_reject = browser.find_element_by_css_selector("button.btn.btn-default.btn-lg")
          browser.execute_script("$(arguments[0]).click();", cookies_reject)
        except: pass
        output = _extract_ku_course_description(browser)
      else:
        browser.get(course_url)
        course_html = BeautifulSoup(browser.page_source, 'html.parser')
        labels = course_html.find_all("td", {"class":"label"})
        output = ''
        for label in labels:
          if label.text.lower().replace('\n',' ') in sections_to_extract:
            text = label.find_next("td", {"class":"value"})
            output += '{} '.format(text.text)
      df = pd.DataFrame(data={'course':[course_name], 'program':[program_name],
                                  'description':[output]})
      self.courses_info = self.courses_info.append(df)
    self.add_slide_programs(browser)
    #TODO: add more electives
    browser.quit()

  def add_slide_programs(self, browser):
    for program in tqdm(self.slide_programs, desc='Adding slide programs'):
      df = self.programs_info.loc[self.programs_info["program"]==program]
      browser.get(df.url.item())
      courses_list = []
      descriptions = []
      course_html = BeautifulSoup(browser.page_source, 'html.parser')
      courses = course_html.find_all("div", {"class":"course-description"})
      for course in courses:
        course_text = course.find_all(text=True)
        course_name = _process_course_name(course_text[0])
        if course_name == 'electives': continue
        courses_list.append(course_name)
        output = ''
        for i in range(1, len(course_text)):
          if 'Learning Objectives' in course_text[i]: continue
          if 'ECTS' in course_text[i]: break
          output += '{} '.format(course_text[i])
        df = self.courses_info.loc[self.courses_info.course == course_name]
        if not df.empty: continue
        df = pd.DataFrame(data={'course':[course_name], 'program':[program],
                                  'description':[output]})
        self.programs_courses = self.programs_courses.append(df)
        descriptions.append(output)
      program_list = [program] * len(courses_list)
      df = pd.DataFrame(data={'program':program_list, 'course':courses_list,
                              'url': program_list})
      df = self.courses_info.loc[self.courses_info.course == course_name]
      self.programs_courses = self.programs_courses.append(df)

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

# CBS.UTILS
def _get_programs(programs):
  programs_list = []
  programs_url = []
  grades = []
  for program in programs:
    program_url = program.get_attribute("href")
    program_name = _process_program_name(program_url)
    if program_name in programs_list: continue
    grades.append(program_name[0:3].rstrip())
    programs_list.append(program_name)
    programs_url.append(program_url)
  return programs_list, programs_url, grades

def _process_program_name(program):
  program = program.lower()
  program = program.replace('https://www.cbs.dk/en/study/bachelor/', '')
  program = program.replace('https://www.cbs.dk/uddannelse/kandidat/', '')
  program = program.replace('https://www.cbs.dk/en/study/graduate/', '')
  program = program.replace('http://www.cbs.dk/en/study/graduate/', '')
  program = program.replace('msc-in-business-language-and-culture/', '')
  program = program.replace('msc-in-economics-and-business-administration/', '')
  program = program.replace('economics-finance-and-accounting/', '')
  program = program.replace('organisation-and-innovation/', '')  
  program = program.replace('marketing/', '')
  program = program.replace('global-business/', '')
  program = program.replace('candsoc-msc-in-social-science/', '')
  program = program.replace('sino-danish-centre/', '')
  
  program = program.replace('master', 'msc')
  program = program.replace('-', ' ')
  program = program.replace(' in ', ' ')
  return program

def _process_course_name(course):
  course = course.lower()
  course = course.replace('(15 ects)', '')
  course = course.replace('(7.5 ects)', '')
  course = course.replace('(7.5)', '')
  
  course = course.rstrip()
  course = course.lstrip()
  return course

def _extract_ku_course_description(browser):
  course_html = BeautifulSoup(browser.page_source, 'html.parser')      
  content = course_html.find("div", {"id": "course-content"})
  description = course_html.find("div", {"id": "course-description"})
  text = content.find_all(text=True)
  text += description.find_all(text=True)
  output = ''
  for txt in text:
    output += '{} '.format(txt)
  return output