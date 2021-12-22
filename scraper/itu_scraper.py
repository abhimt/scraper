# Python Imports
import time
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm, trange

# Local Imports
from scraper.utils import *

# ITU Scraper
class ItuScraper():
  def __init__(self):
    self.home_url = 'https://en.itu.dk'
    self.university_name = 'IT University of Copenhagen'
    self.university_id = 1
      
  def update_programs_info(self):
    url = self.home_url + '/Programmes'
    browser = connect_to_browser()
    browser.get(url)
    programs_html = BeautifulSoup(browser.page_source, 'html.parser')
    programs_url = []
    programs_name = []
    grade = []
    programs = programs_html.find_all("div", "col-sm-12 highlight")
    for program in programs:
      link = program.find("a")
      program_url = self.home_url + link["href"]
      programs_url.append(program_url)
      name = program.text.lower()
      if 'msc-program' in program_url.lower():
        grade.append('msc')
        programs_name.append('msc ' + name)
      if 'bsc-program' in program_url.lower():
        grade.append('bsc')
        programs_name.append('bsc ' + name)
    browser.quit()
    # Creating the dataframe
    data = {'program': programs_name, 'grade': grade, 'url': programs_url}
    self.programs_info = pd.DataFrame(data=data)
  
  def update_courses_info(self):
    self.courses_info = pd.DataFrame(columns=['course', 'period', 'program', 'description'])
    periods = _get_itu_periods()
    browser = connect_to_browser()
    for period in periods:
      url = f'https://learnit.itu.dk/local/coursebase/course_catalogue.php?period={period}&perpage=200'
      browser.get(url)
      time.sleep(5)
      courses_in_page = browser.find_elements_by_class_name("card-header")
      for i in trange(len(courses_in_page),
                      desc=f'Scraping courses information period {period}'):
        courses_in_page[i].click()
        time.sleep(0.5)
        language = browser.find_elements_by_class_name("col-sm-12.cb-icon.cb-language")
        if 'LanguageDanish' == language[i].text.rstrip(): continue
        program = browser.find_elements_by_class_name("col-sm-12.cb-icon.cb-studyprogramme")
        program = program[i].text.rstrip()[9:]
        program = _itu_program_processing(program[:3].lower() + ' ' + program[7:].lower())
        if self.programs_info.loc[(self.programs_info['program']==program)].empty: continue
        # TODO: check the name of the course best for processing
        course = _itu_modify_course(courses_in_page[i].text[:-12])
        df = self.courses_info.loc[self.courses_info['course']==course]
        buttons = browser.find_elements_by_class_name("btn.btn-secondary.btn-sm")
        if df.empty or df.period.values[0] < int(period):
          course_browser = connect_to_browser()
          text = self.extract_course_description(course_browser,
                                                 buttons[i].get_attribute("href"))
          course_browser.quit()
          if text:
            self.courses_info = self.courses_info.append(pd.DataFrame([[course, int(period), program , text]], 
                                                      columns=['course', 'period', 'program', 'description']))
          else:
            print(course)
    browser.quit()

  def extract_course_description(self, course_browser, url):
    course_browser.get(url)
    time.sleep(0.5)
    course_html = BeautifulSoup(course_browser.page_source, 'html.parser')
    soup = course_html.find("div", "col-md-8 cb-content")
    sections = ['Abstract', 'Description', 'Intended learning outcomes',
                'Learning activities']
    blacklist = ['Formal prerequisites', 'Student Activity Budget',
                 'Course literature', 'Ordinary exam', 'Time and date',
                 'Mandatory activities']
    output = ''
    try:
      text = soup.find_all(text=True)
      for i in range(len(text)):
        if text[i] in sections:
            for j in range(i+1, len(text)):
              if (text[j] in sections) or (text[j] in blacklist):
                i = j
                break
              output += '{}'.format(text[j])
      output = output.rstrip()
      output = output.lstrip()
      return output
    except AttributeError:
      return None

  def update_programs_courses(self):
    # Software development program is left out because the courses titles are in
    # danish. Its courses were already added by the update_courses_info()
    self.programs_courses = pd.DataFrame(columns=['program','course'])
    programs_out = ['bsc software development']
    browser = connect_to_browser()
    for i in trange(len(self.programs_info), desc='Scraping programs courses'):
      program, _, program_url = self.programs_info.iloc[i]
      df = self.courses_info.loc[self.courses_info.program==\
                                 program][['program', 'course']]
      self.programs_courses = self.programs_courses.append(df)
      if program in programs_out: continue
      browser.get(program_url)
      time.sleep(0.5)
      program_html = BeautifulSoup(browser.page_source, 'html.parser')
      courses_table = program_html.find_all("td")
      courses_list = []
      for element in courses_table:
        if element.find("strong"):
          courses_list.append(element.find("strong").text)
      #TODO: Split the OR course
      courses_list = _itu_process_course_name(courses_list)
      for program_course in courses_list:
        if df.loc[df.course==program_course].empty:
          if not self.courses_info.loc[self.courses_info.course==program_course].empty:
            self.programs_courses = self.programs_courses.append(pd.DataFrame([[program, program_course]],
                                        columns=['program', 'course']))
    browser.quit()
  
  # AUTO SCRAPER
  def update(self):
    work_time = time.localtime()
    print('Starting update at {}:{}'.format(work_time.tm_hour, work_time.tm_min))
    print('This will take several minutes')
    print('Updating Programs Information...')
    self.update_programs_info()
    print('1/3 Updates Finished')
    self.update_courses_info()
    print('2/3 Updates Finished')
    self.update_programs_courses()
    print('3/3 Updates Finished')
    work_time = time.localtime()
    print('Finished at {}:{}'.format(work_time.tm_hour, work_time.tm_min))

  def export_data(self):
    programs_info = self.programs_info.drop(labels='url',
                                            axis=1).reset_index(drop=True)
    programs_info.insert(1, 'university_id', self.university_id)
    courses_info = self.courses_info.drop(labels='period',
                                          axis=1).reset_index(drop=True)
    courses_info.insert(2, 'university_id', self.university_id)
    programs_courses = self.programs_courses.reset_index(drop=True)
    programs_courses.insert(2, 'university_id', self.university_id)
    data = {'programs_info': programs_info,
            'courses_info': courses_info,
            'programs_courses': programs_courses}
    return data

# ITU.UTILS
def _itu_process_course_name(courses_list):
  courses_list = [i for i in courses_list if 'Elective' not in i]
  courses_list = [i for i in courses_list if 'Thesis' not in i]
  courses_list = [i for i in courses_list if 'Specialisation' not in i]
  courses_list = [i for i in courses_list if 'Bachelor Project' not in i]
  courses_list = [i for i in courses_list if 'Research Project' not in i]

  for i in range(len(courses_list)):
    courses_list[i] = _itu_modify_course(courses_list[i])
  return courses_list

def _itu_modify_course(course_name):
  # Symbnols
  course_name = course_name.replace('&', 'and')
  course_name = course_name.replace('\xa0', '')
  course_name = course_name.replace('*', '')
  course_name = course_name.replace('7', '')
  course_name = course_name.replace(',', '')
  course_name = course_name.replace('-', ' ')
  # Format
  course_name = course_name.lower()
  # Particularities
  course_name = course_name.replace('second year project: ', '')
  course_name = course_name.replace('2nd yearproject: ', '')
  course_name = course_name.replace('globalization', 'globalisation')
  course_name = course_name.replace('visualizing', 'visualising')
  course_name = course_name.replace('mediaand', 'media and')
  course_name = course_name.replace('anddesign', 'and design')
  course_name = course_name.replace('co design', 'co-design')
  course_name = course_name.replace('processes innovation', 'process innovation')
  course_name = course_name.replace(' dmd/b ddit', '')
  course_name = course_name.replace(' gbi', '')
  course_name = course_name.replace(' msc cs', '')
  course_name = course_name.replace(' 15 ects', '')
  # Format
  course_name = course_name.rstrip()
  course_name = course_name.lstrip()
  return course_name

def _itu_program_processing(program_name):
  program_name = program_name.replace('&', 'and')
  return program_name

def _get_itu_periods(actual_year=2022, actual_period=1, use_all=False):
  period = []
  if use_all: start_year = 2019
  if actual_period == 1:
    if not use_all: start_year = actual_year - 1
    period.append(str(actual_year)+str(actual_period))
    year = list(range(start_year, actual_year))
  else:
    if not use_all: start_year = actual_year
    year = list(range(start_year, actual_year+1))
  for year in reversed(year):
    period.append(str(year) + str(2))
    period.append(str(year) + str(1))
  return period
