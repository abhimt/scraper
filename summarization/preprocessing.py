# Common imports
import re

def eliminate_numbers(text):
  pattern = r'[0-9]'
  text = re.sub(pattern, 'X', text)
  return text