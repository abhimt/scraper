from database.database import *

def select_university(university_id):
  university_dict = get_universities()
  try:
    university = university_dict[university_id]
    return university
  except Error as e:
    print(e, 'Wrong university id')

def show_universities():
  university_dict = get_universities()
  for id, university in university_dict.items():
    print(f'ID: {id} | {university}')

def select_program(university_id, program_id):
  programs = get_program_list(university_id)
  try:
    return programs[program_id]
  except Error as e:
    print(e, 'Wrong index')

def show_programs(university_id):
  university_dict = get_universities()
  programs = get_program_list(university_id)
  try:
    university = university_dict[university_id]
  except Error as e:
    print(e, 'Wrong index')
  print('Showing the programs of the university {}:'.format(university))
  for t, program in enumerate(programs):
    print(t, ':', program)

def select_courses(program, university_id, courses_list):
  courses_df = get_courses(program, university_id)
  descriptions = []
  courses = []
  for _, (_, course, _) in courses_df.iloc[courses_list].iterrows():
    descriptions.append(get_course_description(course, university_id))
    courses.append(course)
  return courses, descriptions

def show_courses(program_id, university_id):
  university_dict = get_universities()
  programs = get_program_list(university_id)
  try:
    university = university_dict[university_id]
    program = programs[program_id]
  except Error as e:
    print(e, 'Wrong index')
  courses_df = get_courses(program, university_id)
  print('University:', university)
  print('Showing available courses for the program:', program)
  for t, (_, course, _) in courses_df.iterrows():
    print(t,':',course)

def test_summarization():
  '''
  Test function that selects automatically the university, the program and a  
  selection courses with the following selection:
    - University: IT University
    - Program: msc data science
    - Courses: [0, 4, 5, 7, 9, 10, 12]
  '''
  university_id = 1
  university = select_university(university_id)
  program = select_program(university_id, 0)
  courses_list = [0, 4, 5, 7, 9, 10, 12]
  courses, descriptions = select_courses(program, university_id, courses_list)
  return courses, descriptions, university, program