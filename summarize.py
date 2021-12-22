# Common imports
import argparse
import os
from re import sub
from tqdm import tqdm

# HuggingFace
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

# Local imports
from summarization.retrieve_data import *

def summarize(courses, descriptions, model_name='facebook/bart-large-cnn'):
  summaries = []
  data = {}
  tokenizer = AutoTokenizer.from_pretrained(model_name)
  model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
  for description in tqdm(descriptions, desc='Summarizing courses'):
    inputs = tokenizer(description, max_length=1024, return_tensors='pt',
                       truncation=True, padding=True)
    # this change with the models.                      
    outputs = model.generate(inputs['input_ids'], num_beams=4,
                                 max_length=1024, early_stopping=True)
    summary = [tokenizer.decode(g, skip_special_tokens=True,
                          clean_up_tokenization_spaces=False) for g in outputs]                                 
    summaries.append(summary[0])
  for i in range(len(courses)):
    data[courses[i]] = summaries[i]
  return data

def bold_print(text):
  BOLD = '\033[1m'
  END = '\033[0m'
  print(BOLD + text + END)

def print_to_terminal(data, university, program):
  bold_print(f'University: {university}')
  bold_print(f'Program: {program}\n')
  for course, summary in data.items():
    bold_print(course)
    print(summary, '\n')
    
def save_to_file(data, university, program, path, name):
  path = os.path.join(path, name)
  with open(path, 'w') as f: 
    # TODO: change to path instead of a summary
    for course, summary in data.items():
      f.write(f'University: {university}\n')
      f.write(f'Program: {program}\n')
      f.write(course + '\n')
      f.write(summary + '\n')
      f.write('\n')

def parse_summarize_arguments(args):
  arguments = {}
  if args.university == None:
    raise AttributeError('Missing university argument')
  else:
    arguments['university'] = args.university
  if args.program == None:
    raise AttributeError('Missing program argument')
  else:
    arguments['program'] = args.program
  if args.courses == None:
    raise AttributeError('Missing courses argument')
  else:
    arguments['courses'] = args.courses
  return arguments

if __name__ == '__main__':
  parser = argparse.ArgumentParser()

  parser.add_argument("-p","--print", help="Print to terminal", required=False,
                    action="store_true")

  save = parser.add_argument_group("save")
  save.add_argument("-s","--save", help="Save to file", required=False,
                      action='store_true')
  save.add_argument("-n", "--name", default='summary.txt', type=str,
                           required=False, help="Name of the file")
  save.add_argument("-d", "--directory", default='./summarization/results', type=str, required=False,
                    help="Specify directory path to save file")
  
  summarization = parser.add_argument_group("summarization")
  summarization.add_argument("-t", "--test", required=False, action='store_true',
                             help="Run a test with default values")
  summarization.add_argument("-sh", "--show", action='store_true', required=False, 
                             help="Consult the database")
  summarization.add_argument("-u", "--university", type=int, default=None)
  summarization.add_argument("-pr", "--program", type=int, default=None)
  summarization.add_argument("-cl", "--courses", nargs='+', default=None,
                            required=False, help="IDs list to scrap")

  args = parser.parse_args()

  if args.test:
    courses, descriptions, univeristy, program = test_summarization()
    data = summarize(courses, descriptions)
    print_to_terminal(data, univeristy, program)
    if args.save:
      save_to_file(data, univeristy, program, args.directory, args.name)
  elif args.show:
    if args.university == None:
      show_universities()
    if args.university != None:
      if args.program != None:
        show_courses(args.program, args.university)
      else:
        show_programs(args.university)
  else:
    arguments = parse_summarize_arguments(args)
    university_id = arguments['university']
    univeristy = select_university(university_id)
    program = select_program(university_id, arguments['program'])
    courses, descriptions = select_courses(program, university_id, arguments['courses'])
    data = summarize(courses, descriptions)
    if args.print:
      print_to_terminal(data, univeristy, program)
    if args.save:
      save_to_file(data, univeristy, program, args.directory, args.name)