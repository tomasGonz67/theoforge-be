import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from text_cleaning import TextCleaningService

raw_text = """
Mark created the app in his Harvard dorm room in 2004. 
He later expanded it to other universities and eventually 
it became the largest social network. He also acquired 
Instagram in 2012 for $1 billion.
"""

cleaning_service = TextCleaningService()
structured_data = cleaning_service.process_text(raw_text)
print(structured_data)