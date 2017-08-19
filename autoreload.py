import logging
import os
import pathlib
import pyinotify
import signal
import sys
import termios
import _thread
import time
import traceback
import typing

from contextlib import suppress

logger = logging.getLogger(__name__)

RUN_RELOADER = True
FILE_MODIFIED = 1

_mtimes = {}
_exception = None
_error_files = []
_cached_modules = set()
_cached_file_names = []


class EventHandler(pyinotify.ProcessEvent):
    """

    """
    modified_code = None

    def process_default(self, event):
        print('EventHandler processing default event.')
        EventHandler.modified_code = FILE_MODIFIED


def inotify_code_changed():
    """
    Checks for changed code using inotify. After being called
    it blocks until a change event has been fired.
    """
    wm = pyinotify.WatchManager()
    notifier = pyinotify.Notifier(wm, EventHandler())

    def update_watch(sender=None, **kwargs):
        if sender and getattr(sender, 'handles_files', False):
            # No need to update watches when request serves files.
            # (sender is supposed to be a django.core.handlers.BaseHandler subclass)
            return

        mask = (
            pyinotify.IN_MODIFY |
            pyinotify.IN_DELETE |
            pyinotify.IN_ATTRIB |
            pyinotify.IN_MOVED_FROM |
            pyinotify.IN_MOVED_TO |
            pyinotify.IN_CREATE |
            pyinotify.IN_DELETE_SELF |
            pyinotify.IN_MOVE_SELF
        )

        wm.add_watch('/home/matthew/Projects/mattbot', mask)

    # Block until an event happens.
    update_watch()
    notifier.check_events(timeout=None)
    notifier.read_events()
    notifier.process_events()
    notifier.stop()

    # If we are here the code must have changed.
    return EventHandler.modified_code


def ensure_echo_on():
    """

    """
    fd = sys.stdin
    if not fd.isatty():
        return

    attr_list = termios.tcgetattr(fd)

    if not attr_list[3] & termios.ECHO:
        attr_list[3] |= termios.ECHO

        termios.tcsetattr(fd, termios.TCSANOW, attr_list)

        if hasattr(signal, 'SIGTTOU'):
            signal.signal(signal.SIGTTOU, signal.signal(signal.SIGTTOU, signal.SIG_IGN))


def reloader_thread():
    """

    """
    ensure_echo_on()
    while RUN_RELOADER:
        if inotify_code_changed() == FILE_MODIFIED:
            sys.exit(3)  # force reload

        time.sleep(1)


def restart_with_reloader():
    """
    Restart with the reloader active

    """
    while True:
        print(f'Restarting with reloader')
        args = [sys.executable] + ['-W%s' % o for o in sys.warnoptions] + sys.argv
        new_environ = os.environ.copy()
        new_environ["RUN_MAIN"] = 'true'
        exit_code = os.spawnve(os.P_WAIT, sys.executable, args, new_environ)
        if exit_code != 3:
            return exit_code


def python_reloader(main_func: typing.Callable, args: typing.Optional[tuple]=None, kwargs: typing.Optional[dict]=None):
    """
    Args:
        main_func: The main function to execute
        args: The program arguments
        kwargs: The program kwargs

    """
    if os.environ.get("RUN_MAIN") == "true":
        args = args if args else ()
        kwargs = kwargs if kwargs else {}
        _thread.start_new_thread(main_func, args, kwargs)
        with suppress(KeyboardInterrupt):
            return reloader_thread()

    # @TODO: Do we have to restart? Can we just run the thread from the start?
    with suppress(KeyboardInterrupt):
        exit_code = restart_with_reloader()

        if exit_code >= 0:
            sys.exit(exit_code)

        os.kill(os.getpid(), -exit_code)


def main_func():
    print(f'Running the application')

if __name__ == '__main__':
    python_reloader(main_func)
