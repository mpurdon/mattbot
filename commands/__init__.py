import os
import importlib
import inspect

#
# Dynamic imports for commands
#

dir_path = os.path.dirname(os.path.realpath(__file__))
for path, subdirs, files in os.walk(dir_path):
    for name in files:
        if '__init__' not in name and name.endswith('.py'):
            module_name = f'.{name[:-3]}'
            command_module = importlib.import_module(module_name, 'commands')
            for member_name, member_item in inspect.getmembers(command_module):
                if inspect.isclass(member_item) and inspect.getmodule(member_item) is command_module:
                    globals()[member_name] = member_item
