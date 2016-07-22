# Initialize output before importing any module, that can use colorama.
from .system import init_output

init_output()

from argparse import ArgumentParser
from warnings import warn
from pprint import pformat
import sys
import json
from six import text_type
from . import logs, types
from .shells import shell
from .conf import settings
from .corrector import get_corrected_commands
from .exceptions import EmptyCommand
from .utils import get_installation_info, get_alias
from .ui import select_command
from .types import CorrectedCommand


def get_corrected_command_from_history(wrong_command):
    history_path_obj = settings.user_dir.joinpath("history.json")
    history_path = text_type(history_path_obj)
    if not history_path_obj.is_file():
        with open(history_path, "w") as f:
            json.dump(dict(), f, indent=4)
        return None
    with open(history_path) as f:
        historical_commands = json.load(f)
        corrected_command = historical_commands.get(wrong_command, None)
    return corrected_command


def add_corrected_command_to_history(wrong_command, corrected_command):
    history_path_obj = settings.user_dir.joinpath("history.json")
    history_path = text_type(history_path_obj)
    with open(history_path, "r+") as f:
        commands = json.load(f)
        commands[wrong_command] = corrected_command
        f.seek(0)
        json.dump(commands, f, indent=4)


def fix_command():
    """Fixes previous command. Used when `thefuck` called without arguments."""
    settings.init()
    with logs.debug_time('Total'):
        logs.debug(u'Run with settings: {}'.format(pformat(settings)))

        try:
            command = types.Command.from_raw_script(sys.argv[1:])
        except EmptyCommand:
            logs.debug('Empty command, nothing to do')
            return

        corrected_command = get_corrected_command_from_history(command.script)
        if corrected_command:
            sys.stderr.write(corrected_command + "\n")
            CorrectedCommand(corrected_command, None, 1000).run(command)
            return

        corrected_commands = get_corrected_commands(command)
        selected_command = select_command(corrected_commands)

        if selected_command:
            add_corrected_command_to_history(command.script,
                                             selected_command.script)
            selected_command.run(command)
        else:
            sys.exit(1)


def print_alias(entry_point=True):
    """Prints alias for current shell."""
    if entry_point:
        warn('`thefuck-alias` is deprecated, use `thefuck --alias` instead.')
        position = 1
    else:
        position = 2

    alias = get_alias()
    if len(sys.argv) > position:
        alias = sys.argv[position]
    print(shell.app_alias(alias))


def how_to_configure_alias():
    """Shows useful information about how-to configure alias.

    It'll be only visible when user type fuck and when alias isn't configured.

    """
    settings.init()
    logs.how_to_configure_alias(shell.how_to_configure())


def main():
    parser = ArgumentParser(prog='thefuck')
    version = get_installation_info().version
    parser.add_argument(
            '-v', '--version',
            action='version',
            version='The Fuck {} using Python {}'.format(
                    version, sys.version.split()[0]))
    parser.add_argument('-a', '--alias',
                        action='store_true',
                        help='[custom-alias-name] prints alias for current shell')
    parser.add_argument('command',
                        nargs='*',
                        help='command that should be fixed')
    known_args = parser.parse_args(sys.argv[1:2])
    if known_args.alias:
        print_alias(False)
    elif known_args.command:
        fix_command()
    else:
        parser.print_usage()
