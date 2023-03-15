import win32event
import win32api
import winerror
import importlib

mutex = win32event.CreateMutex(None, False, 'selenium_mod_mutex')
last_error = win32api.GetLastError()

win32event.WaitForSingleObject(mutex, win32event.INFINITE)
if last_error != winerror.ERROR_ALREADY_EXISTS:
    module_name = 'selenium.webdriver.common.actions.pointer_input'
    spec = importlib.util.find_spec(module_name)
    with open(spec.origin, 'r') as file:
        source = file.read()

    source = source.replace('DEFAULT_MOVE_DURATION = 250', 'DEFAULT_MOVE_DURATION = 0')
    with open(spec.origin, 'w') as file:
        file.write(source)

win32event.ReleaseMutex(mutex)


