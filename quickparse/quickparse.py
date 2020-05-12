import sys

from .lib import validate_commands_config, validate_attrs_config, humblecall, get_arg_type, get_attrs_equivalency_from_config, expand_commands_config_keys


class QuickParse(object):

    raw_args = None
    commands_config = None
    attrs_config = None
    commands = list()
    params = list()
    attrs = dict()
    numeric = None
    plusnumeric = None
    to_execute = None

    _attrs_equivalency = dict()

    def __init__(self, commands_config = None, attrs_config = None, *, cli_args = None):
        if cli_args is None:
            self.raw_args = sys.argv[:]
        else:
            if not (isinstance(cli_args, (list, tuple)) and all(isinstance(element, str) for element in cli_args)):
                raise ValueError(f"cli_args must be a list of strings")
            self.raw_args = cli_args[:]
        if commands_config is None:
            self.commands_config = dict()
        elif not isinstance(commands_config, dict):
            self.commands_config = { '': commands_config }
        else:
            self.commands_config = commands_config
        self.attrs_config = attrs_config or tuple()
        try:
            validate_commands_config(self.commands_config)
            validate_attrs_config(self.attrs_config)
        except AssertionError as ae:
            raise ValueError(ae) from ae
        self.commands_config = expand_commands_config_keys(self.commands_config)
        self._attrs_equivalency = get_attrs_equivalency_from_config(self.attrs_config)
        self._process_args()

    def execute(self, *args, **kwargs):
        kwargs.setdefault('quickparse', self)
        return_values = list()
        if isinstance(self.to_execute, list):
            for try_to_call in self.to_execute:
                return_values.append(humblecall(try_to_call, *args, **kwargs))
        else:
            return_values = humblecall(self.to_execute, *args, **kwargs)
        return return_values

    def _process_args(self):
        command_level = self.commands_config
        arg_index = 0
        while arg_index < len(self.raw_args):
            arg = self.raw_args[arg_index]
            arg_index += 1
            arg_type = get_arg_type(arg)
            if arg_type in ('minus letter block', 'plus letter block') and arg not in self._attrs_equivalency:
                for letter in arg[1:]:
                    flag = f"{arg[0]}{letter}"
                    if flag in self._attrs_equivalency:
                        if self._attrs_equivalency[flag]['type'] != bool:
                            raise RuntimeError(f"{flag} found in block parameter while expecting {self._attrs_equivalency[flag]['type']} value")
                        for eq_param in self._attrs_equivalency[flag]['equivalents']:
                            self.attrs[eq_param] = True
                    else:
                        self.attrs[flag] = True
            if arg_type in ('minus char', 'plus char', 'minus string', 'doubleminus string'):
                # TODO: check attrs_config if it expects value and process it
                pass
            if arg_type == 'minus numeric':
                self.numeric = int(arg[1:])
            if arg_type == 'plus numeric':
                self.plusnumeric = int(arg[1:])
            if arg_type == 'param or command':
                if arg in command_level:
                    self.commands.append(arg)
                    if isinstance(command_level[arg], dict):
                        command_level = command_level[arg]
                    else:
                        if isinstance(command_level[arg], (list, tuple)):
                            self.to_execute = list(command_level[arg])
                        else:
                            self.to_execute = command_level[arg]
                        command_level = dict()
                else:
                    self.params.append(arg)
        while isinstance(command_level.get('', None), dict):
            command_level = command_level['']
        if '' in command_level:
            if isinstance(command_level[''], (list, tuple)):
                self.to_execute = list(command_level[''])
            else:
                self.to_execute = command_level['']
