import os
import time
from browser import Browser

browser = Browser(headless=False)
browser.Load('https://freetools.site/')
browser.WaitForElement('body')

dropdowns = browser.GetElement('.form-select', multiple=True)
last_dropdown = dropdowns[-1]
browser.ScrollIntoView(last_dropdown)
browser.RemoveOverlappingElements(last_dropdown)
time.sleep(1)

browser.SelectOption(last_dropdown, 'ZIP')
browser.WaitForElement('body')
time.sleep(1)

dropzone = browser.GetElement('form[id="dropzone"]')
browser.RemoveOverlappingElements(dropzone)
time.sleep(1)

absolute_path = os.path.abspath('test_file.txt')
browser.DropFile(absolute_path, dropzone)
compress_button = browser.WaitForElement('#info-container > button')
browser.Click(compress_button)

print('that is it')
