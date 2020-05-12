import sys

from .lib import validate_commands_config, validate_params_config, humblecall, get_arg_type, get_params_equivalency_from_config


class QuickParse(object):

    raw_args = None
    commands_config = None
    params_config = None
    commands = list()
    params = dict()
    numeric = None
    plusnumeric = None
    to_execute = None

    _params_equivalency = dict()

    def __init__(self, *, commands = None, params = None, cli_args = None):
        if cli_args is None:
            self.raw_args = sys.argv[:]
        else:
            if not (isinstance(cli_args, (list, tuple)) and all(isinstance(element, str) for element in cli_args)):
                raise ValueError(f"cli_args must be a list of strings")
            self.raw_args = cli_args[:]
        self.commands_config = commands or dict()
        self.params_config = params or tuple()
        try:
            validate_commands_config(self.commands_config)
            validate_params_config(self.params_config)
        except AssertionError as ae:
            raise ValueError(ae)
        self._params_equivalency = get_params_equivalency_from_config(self.params_config)
        self._process_args()

    def execute(self, *args, **kwargs):
        return_values = list()
        if isinstance(self._to_execute, list):
            for try_to_call in self._to_execute:
                return_values.append(humblecall(try_to_call, *args, **kwargs))
        else:
            return_values = humblecall(self._to_execute, args, kwargs)
        return return_values

    def _process_args(self):
        command_level = self.commands_config
        arg_index = 0
        while arg_index < len(self.raw_args):
            arg = self.raw_args[arg_index]
            arg_index += 1
            arg_type = get_arg_type(arg)
            if arg_type in ('minus letter block', 'plus letter block') and arg not in self._params_equivalency:
                for letter in arg[1:]:
                    flag = f"{arg[0]}{letter}"
                    if flag in self._params_equivalency:
                        if self._params_equivalency[flag]['type'] != bool:
                            raise RuntimeError(f"{flag} found in block parameter while expecting {self._params_equivalency[flag]['type']} value")
                        for eq_param in self._params_equivalency[flag]['equivalents']:
                            self.params[eq_param] = True
                    else:
                        self.params[flag] = True
            if arg_type in ('minus char', 'plus char', 'minus string', 'doubleminus string'):
                # TODO: check params_config if it expects value and process it
                pass
            if arg_type == 'minus numeric':
                pass
            if arg_type == 'plus numeric':
                pass
            if arg_type == 'param or command':
                if arg in command_level:
                    self.commands.append(arg)
                    if isinstance(command_level[arg], dict):
                        command_level = command_level[arg]
                    else:
                        if isinstance(command_level[arg], (list, tuple)):
                            self._to_execute = list(command_level[arg])
                        else:
                            self._to_execute = command_level[arg]
                        command_level = dict()
                else:
                    self.params.append(arg)
