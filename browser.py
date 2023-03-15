import uuid
import time
import string
import base64
import selenium_mod
from selenium.common.exceptions import WebDriverException, InvalidSessionIdException, NoSuchWindowException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait, Select
import selenium.webdriver.support.expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains 
from selenium.webdriver.common.keys import Keys
from driver import Driver
from simulator import Simulator

class Browser:

    def __init__(self, headless=True, proxy=None): 
       
        self.headless = headless
        self.proxy = proxy
        self.driver = Driver(headless, proxy)
        self.driver.set_page_load_timeout(30)
        self.simulator = Simulator()
        self.id = uuid.uuid4().hex

    def Restart(self):

        self.driver.quit()
        while 1:
            try:
                self.driver = Driver(self.headless, self.proxy)
                break
            except WebDriverException:
                continue

        self.driver.set_page_load_timeout(30)

    def Quit(self):

        self.driver.quit()

    def NeedsRestart(self, exception):

        if isinstance(exception, InvalidSessionIdException):
            return True

        if isinstance(exception, NoSuchWindowException):
            return True

        return False

    def GetAttributes(self):

        proxies = {'http': 'http://%s' % self.proxy, 'https': 'https://%s' % self.proxy} if self.proxy else None
        headers = {'User-Agent': self.driver.execute_script('return navigator.userAgent')}
        cookies = {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()}

        return proxies, headers, cookies

    def BlockUrls(self, urls):

        self.driver.execute_cdp_cmd('Network.setBlockedURLs', {'urls': urls})
        self.driver.execute_cdp_cmd('Network.enable', {})

    def ExecuteScript(self, script, args=(), async=False):

        if async:
            result = self.driver.execute_async_script(script, *args)
        else:
            result = self.driver.execute_script(script, *args)

        return result

    def Back(self):

        self.driver.back()

    def Refresh(self):
        
        self.driver.refresh()

    def Stop(self):

        self.driver.execute_script('window.top.stop()')

    def DeleteCookies(self):

        self.driver.delete_all_cookies()
        self.driver.execute_script('sessionStorage.clear(); localStorage.clear()')

    def Url(self):
        
        return self.driver.current_url

    def TabsCount(self):

        return len(self.driver.window_handles)

    def OpenTab(self, timeout=30):

        tabs_count = len(self.driver.window_handles)
        self.driver.execute_script('window.top.open("")')
        wait = WebDriverWait(self.driver, timeout)
        wait.until(lambda driver: len(driver.window_handles) == tabs_count + 1)

    def CloseTab(self, timeout=30):

        tabs_count = len(self.driver.window_handles)
        self.driver.close()
        wait = WebDriverWait(self.driver, timeout)
        wait.until(lambda driver: len(driver.window_handles) == tabs_count - 1)

    def SwitchToTab(self, idx):

        window_handle = self.driver.window_handles[idx]
        self.driver.switch_to.window(window_handle)

    def SwitchToFrame(self, frame):
        
        if frame == 'parent':
            self.driver.switch_to.parent_frame()
        elif frame == 'default':
            self.driver.switch_to.default_content()
        else:
            self.driver.switch_to.frame(frame)          

    def Load(self, url, timeout=30):

        self.driver.get(url)
        wait = WebDriverWait(self.driver, timeout)
        try:
            wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
        except TimeoutException:
            return False

        return True

    def WaitForElement(self, selector, timeout=30, multiple=False):

        wait = WebDriverWait(self.driver, timeout)
        try:
            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, selector)))
        except TimeoutException:
            return None

        find_func = self.driver.find_elements_by_css_selector if multiple else self.driver.find_element_by_css_selector
        return find_func(selector)

    def IsElementPresent(self, selector, timeout=30):

        wait = WebDriverWait(self.driver, timeout)
        try:
            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, selector)))
        except TimeoutException:
            return False

        return True

    def GetElement(self, selector, multiple=False):
       
        find_func = self.driver.find_elements_by_css_selector if multiple else self.driver.find_element_by_css_selector
        try:
            element = find_func(selector)
        except:
            element = None

        return element

    def GetElementByText(self, text, case_sensitive=False, multiple=False):

        find_func = self.driver.find_elements_by_xpath if multiple else self.driver.find_element_by_xpath
        if case_sensitive:
            xpath = '//*[contains(text(), "%s")]' % text
        else:
            xpath = '//*[contains(translate(text(), "%s", "%s"), "%s")]' % (string.ascii_uppercase, string.ascii_lowercase, text)

        try:
            element = find_func(xpath)
        except:
            element = None

        return element

    def GetIframesOffset(self):

        script = '''
                 var x_offset = 0, y_offset = 0, current_window = window;
	             while(1)
	             {
                     var iframe = current_window.frameElement;
                     if(iframe == null)
                     {
                         break;
                     }

		             var rect = iframe.getBoundingClientRect();
		             x_offset += rect['x'];
		             y_offset += rect['y'];
		             current_window = current_window.parent;
	             }
	
	             return [x_offset, y_offset];
                 '''

        return self.driver.execute_script(script)

    def IsInViewport(self, element):

        script = '''
                 var rect = arguments[0].getBoundingClientRect();
                 return rect.left >= 0 && rect.top >= 0 && rect.right <= window.top.innerWidth && rect.bottom <= window.top.innerHeight; 
                 '''

        return self.driver.execute_script(script, element)

    def GetCursorPosition(self):

        variable = 'window._%s' % self.id
        script = '''
                 var listener = function(event) { %s = [event.clientX, event.clientY]; };
                 window.addEventListener("mousemove", listener, { once: true });
                 '''
        self.driver.execute_script(script % variable)

        chain = ActionChains(self.driver) 
        chain.move_by_offset(0, 0)
        chain.perform()

        x, y = self.driver.execute_script('return %s' % variable)
        iframes_offset = self.GetIframesOffset()
        x += iframes_offset[0]
        y += iframes_offset[1]

        return x, y

    def MoveToPosition(self, position):

        clip = lambda value, min, max: min if value < min else max if value > max else value
        window_width, window_height = self.driver.execute_script('return [window.top.innerWidth, window.top.innerHeight]')
        prev_position = self.GetCursorPosition()
        movements = self.simulator.GetMouseMovements(prev_position, position)

        chain = ActionChains(self.driver) 
        prev_x, prev_y = prev_position
        for x, y, delay in movements:
            x, y = clip(x, 1, window_width - 1), clip(y, 1, window_height - 1)
            chain.move_by_offset(x - prev_x, y - prev_y)
            chain.pause(delay)
            prev_x, prev_y = x, y

        chain.perform()

    def Click(self, element):
     
        rect = self.driver.execute_script('return arguments[0].getBoundingClientRect()', element)
        iframes_offset = self.GetIframesOffset()
        click_offset = self.simulator.GetClickPosition(rect['width'], rect['height'])
        x = round(rect['x'] + iframes_offset[0] + click_offset[0])
        y = round(rect['y'] + iframes_offset[1] + click_offset[1])
        self.MoveToPosition((x, y))

        chain = ActionChains(self.driver)
        delays = self.simulator.GetClickDelays(click_count=1) 
        for button_down_delay, inter_click_delay in delays:
            chain.click_and_hold()
            chain.pause(button_down_delay)
            chain.release()
            chain.pause(inter_click_delay)

        chain.perform()

    def Type(self, text):

        chain = ActionChains(self.driver)
        delays = self.simulator.GetPressDelays(press_count=len(text))
        for char, (button_down_delay, inter_press_delay) in zip(text, delays):
            chain.key_down(char)
            chain.pause(button_down_delay)
            chain.key_up(char)
            chain.pause(inter_press_delay)

        chain.perform()

    def Clear(self, text):

        chain = ActionChains(self.driver)
        delays = self.simulator.GetPressDelays(press_count=len(text))
        for button_down_delay, inter_press_delay in delays:
            chain.key_down(Keys.BACKSPACE)
            chain.pause(button_down_delay)
            chain.key_up(Keys.BACKSPACE)
            chain.pause(inter_press_delay)

        chain.perform()

    def ScrollIntoView(self, element):

        y_offset = -1
        x, y = self.GetCursorPosition()
        self.driver.execute_script('window.top.document.documentElement.style.overflow = "auto"')

        while not self.IsInViewport(element):
            start_y, window_height = self.driver.execute_script('return [window.top.pageYOffset, window.top.innerHeight]')
            end_y = max(0, element.location['y'] - round(window_height / 2))
            if start_y == y_offset:
                break

            y_offset = start_y
            deltas = self.simulator.GetWheelDeltas(start_y, end_y)
            for delta, delay in deltas:
                event_params = {'type': 'mouseWheel', 'x': x, 'y': y, 'deltaX': 0, 'deltaY': delta}
                self.driver.execute_cdp_cmd('Input.dispatchMouseEvent', event_params)
                time.sleep(delay)

    def ScrollToBottom(self):

        y_offset = -1
        x, y = self.GetCursorPosition()
        self.driver.execute_script('window.top.document.documentElement.style.overflow = "auto"')
        script = 'return [window.top.pageYOffset, window.top.innerHeight, window.top.document.documentElement.scrollHeight]'

        while 1:
            start_y, window_height, scroll_height = self.driver.execute_script(script)
            if start_y + window_height >= scroll_height or scroll_height > 20000 or start_y == y_offset:
                break

            y_offset = start_y
            deltas = self.simulator.GetWheelDeltas(start_y, scroll_height)
            for delta, delay in deltas:
                event_params = {'type': 'mouseWheel', 'x': x, 'y': y, 'deltaX': 0, 'deltaY': delta}
                self.driver.execute_cdp_cmd('Input.dispatchMouseEvent', event_params)
                time.sleep(delay)

    def SelectOption(self, element, text):

        select = Select(element)
        select.select_by_visible_text(text)

    def Delay(self, delay):

        if isinstance(delay, float):
            time.sleep(delay)
            return

        if delay == 'move_click':
            delay = self.simulator.GetMoveClickDelay()
        elif delay == 'press_click':
            delay = self.simulator.GetPressClickDelay()
        elif delay == 'reaction':
            delay = self.simulator.GetReactionDelay()
        else:
            raise Exception('Invalid delay value: %s' % delay)

        time.sleep(delay)

    def DropFile(self, path, element, offset_x=0, offset_y=0):

        script = '''
                 var element = arguments[0], offset_x = arguments[1], offset_y = arguments[2];

                 var input = document.createElement('input');
                 input.type = 'file';
                 input.onchange = function () 
                 {
                     var rect = element.getBoundingClientRect();
                     var x = rect.left + (offset_x || parseInt(rect.width / 2));
                     var y = rect.top + (offset_y || parseInt(rect.height / 2));
                     var data_transfer = { 'files': this.files };

                     var events = ['dragenter', 'dragover', 'drop'];
                     for (var i = 0; i < events.length; ++i)
                     {
                         var event = document.createEvent('MouseEvent');
                         event.initMouseEvent(events[i], true, true, window, 0, 0, 0, x, y, false, false, false, false, 0, null);
                         event.dataTransfer = data_transfer;
                         element.dispatchEvent(event);
                     }

                     setTimeout(function () { document.body.removeChild(input); }, 1000);
                 };

                 document.body.appendChild(input);
                 return input;
                 '''

        input = self.driver.execute_script(script, element, offset_x, offset_y)
        input.send_keys(path)

    def GetImage(self, element):

        script = '''
                 var element = arguments[0], callback = arguments[1];
                 var canvas = document.createElement('canvas');
                 canvas.width = element.naturalWidth; 
                 canvas.height = element.naturalHeight;
                 var context = canvas.getContext('2d');
                 context.drawImage(element, 0, 0);
                 var data = canvas.toDataURL('image/jpeg', 1.0);
                 callback(data);
                 '''

        image = self.driver.execute_async_script(script, element)
        image = image.split('data:image/jpeg;base64,', 1)[1]
        image = base64.b64decode(image)

        return image

    def RemoveOverlappingElements(self, element):

        script = '''
                 var element = arguments[0];
                 var labels = Array.from(element.labels || []);
                 var rect = element.getBoundingClientRect();
                 var x = rect['x'] + rect['width'] / 2;
                 var y = rect['y'] + rect['height'] / 2;

                 while (1)
                 {
                     var top_element = document.elementFromPoint(x, y);
                     var is_same_node = element.isSameNode(top_element);
                     var contains = element.contains(top_element);
                     var is_label = labels.includes(top_element);

                     if(!top_element || is_same_node || contains || is_label)
                     {
                         break;
                     }
                     top_element.remove();
                 }
                 '''

        self.driver.execute_script(script, element)

    def GetUniqueSelector(self, element):

        script = '''
                 var element = arguments[0], path = [];
                 while (1) 
                 {
                    var parent = element.parentNode;
                    if(!parent)
                    {
                        break;
                    }

                    var tag = element.tagName;
                    var children = Array.from(parent.children);
                    var siblings = children.filter(children => children.tagName == tag);
                    if(siblings.length > 1)
                    {
                        var idx = siblings.indexOf(element);
                        tag += `:nth-of-type(${idx + 1})`;
                    }
                    path.push(tag);
                    element = parent;
                };

                path = path.reverse();
                return path.join(' > ').toLowerCase();
                '''

        return self.driver.execute_script(script, element)