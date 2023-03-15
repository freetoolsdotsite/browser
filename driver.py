import os
import re
import json
import string
import random
import win32event
import win32api
import winerror
from contextlib import redirect_stdout, redirect_stderr
from selenium.webdriver import Chrome
from selenium.webdriver import ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager

class Driver(Chrome):

    def __init__(self, headless=True, proxy=None):

        self.headless = headless
        self.proxy = proxy
        self.handles = set()
        super().__init__(**self.CreateKwargs())

    def MaskExecutable(self, executable_path):

        self.mutex = win32event.CreateMutex(None, False, 'chromedriver_mutex')
        last_error = win32api.GetLastError()

        win32event.WaitForSingleObject(self.mutex, win32event.INFINITE)
        if last_error != winerror.ERROR_ALREADY_EXISTS:
            key = ''.join(random.choices(string.ascii_letters, k=26)).encode('ascii')
            with open(executable_path, 'rb') as file:
                bytes = file.read()

            bytes = re.sub(b'cdc_[A-Za-z0-9]+', key, bytes)
            with open(executable_path, 'wb') as file:
                file.write(bytes)

        win32event.ReleaseMutex(self.mutex)

    def CreateKwargs(self):

        with redirect_stdout(None), redirect_stderr(None):
            executable_path = ChromeDriverManager().install()
        self.MaskExecutable(executable_path)

        options = ChromeOptions()
        options.set_capability('unhandledPromptBehavior', 'dismiss')
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        options.add_experimental_option('prefs', {'credentials_enable_service': False, 'profile.password_manager_enabled': False,
                                                  'download_restrictions': 3})

        options.add_argument('start-maximized')
        options.add_argument('--incognito')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-site-isolation-trials')
        options.add_argument('--simulate-outdated-no-au="Tue, 31 Dec 2099 23:59:59 GMT"')

        if self.headless:
            options.add_argument('--headless')
            options.add_argument('--window-size=1366,768')

        if self.proxy:
            options.add_argument('--proxy-server=%s' % self.proxy)
        else:
            options.add_argument('--no-proxy-server')
            options.add_argument('--proxy-server="direct://"')
            options.add_argument('--proxy-bypass-list=*')

        return {'executable_path': executable_path, 'options': options}

    def GetPlatform(self, user_agent, extended=False):
        
        if 'Mac OS X' in user_agent:
            platform = 'Mac OS X' if extended else 'MacIntel'
        elif 'Linux' in user_agent:
            platform = 'Linux'
        else:
            platform = 'Windows' if extended else 'Win32'

        return platform

    def GetBrands(self, ua_version):

        seed = ua_version.split('.')[0] 
        orders = [[0, 1, 2], [0, 2, 1], [1, 0, 2], [1, 2, 0], [2, 0, 1], [2, 1, 0]]
        order = orders[int(seed) % 6]
        escaped_chars = [' ', ' ', ';']

        greasey_brand = '%sNot%sA%sBrand' % (escaped_chars[order[0]], escaped_chars[order[1]], escaped_chars[order[2]])
        greased_brand_versions = [None] * 3
        greased_brand_versions[order[0]] = {'brand': greasey_brand, 'version': '99'}
        greased_brand_versions[order[1]] = {'brand': 'Chromium', 'version': seed}
        greased_brand_versions[order[2]] = {'brand': 'Google Chrome', 'version': seed}

        return greased_brand_versions 

    def GetPlatformVersion(self, user_agent):
        
        if 'Mac OS X ' in user_agent:
            platform_version = re.search(r'Mac OS X ([^)]+)', user_agent)[1]
        elif 'Windows ' in user_agent:
            platform_version = re.search(r'Windows .*?([\d|.]+);', user_agent)[1]
        else:
            platform_version = ''

        return platform_version

    def OverrideUserAgent(self):

        user_agent = self.execute_script('return navigator.userAgent')
        user_agent = user_agent.replace('HeadlessChrome', 'Chrome')

        if 'Chrome/' in user_agent:
            ua_version = re.search(r'Chrome\/([\d|.]+)', user_agent)[1]  
        else:
            browser_version = self.execute_script('return navigator.appVersion')
            ua_version = re.search(r'\/([\d|.]+)', browser_version)[1]

        platform = self.GetPlatform(user_agent)
        extended_platform = self.GetPlatform(user_agent, extended=True)
        brands = self.GetBrands(ua_version)
        platform_version = self.GetPlatformVersion(user_agent)  
    
        ua_metadata = {'fullVersion': ua_version, 'platform': extended_platform, 'brands': brands, 
                       'platformVersion': platform_version, 'architecture': 'x86', 'model': '', 'mobile': False}
        ua_override = {'userAgent': user_agent, 'platform': platform, 'userAgentMetadata': ua_metadata}
        if self.headless:
            ua_override['acceptLanguage'] = 'en-US,en'

        self.execute_cdp_cmd('Network.setUserAgentOverride', ua_override)

    def ApplyEvasions(self):

        evasions = [['utils.js'], ['chrome.app.js'], ['chrome.runtime.js', False], ['iframe.contentWindow.js'],
                    ['media.codecs.js'], ['navigator.hardwareConcurrency.js', 4], 
                    ['navigator.languages.js', ['en-US', 'en']], ['navigator.permissions.js'], ['navigator.plugins.js'], 
                    ['navigator.vendor.js', 'Google Inc.'], ['navigator.webdriver.js'], 
                    ['webgl.vendor.js', 'Intel Inc.', 'Intel Iris OpenGL Engine'], ['window.outerdimensions.js']]

        for evasion in evasions:
            file_name, *args = evasion
            path = os.path.join('evasions', file_name)
            with open(path, 'r') as file:
                func = file.read() 
                
            args = ', '.join(json.dumps('undefined' if arg == None else arg) for arg in args)
            source = '(%s)(%s)' % (func, args)
            self.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': source})

        self.OverrideUserAgent()

    def get(self, *args, **kwargs):

        if self.current_window_handle not in self.handles:
            self.ApplyEvasions()
            self.handles.add(self.current_window_handle)

        return super().get(*args, **kwargs)