import inspect
import re

minus_numeric_re = re.compile('^-\\d+$')
plus_numeric_re = re.compile('^\\+\\d+$')
minus_letter_re = re.compile('^-\\w$')
plus_letter_re = re.compile('^\\+\\w$')
minus_letter_block_re = re.compile('^-\\w+$')
plus_letter_block_re = re.compile('^\\+\\w+$')
minus_string_re = re.compile('^-[^-].*$')
doubleminus_string_re = re.compile('^--[^-].*$')


def validate_commands_config(commands_config):
    assert isinstance(commands_config, dict), f"Dict expedted as params config"
    # TODO: validate commands - one command occurs only once at a level / no ambiguous command

def validate_params_config(params_config):
    params = list()
    assert isinstance(params_config, (list, tuple)), f"List expedted as params config, got this: {params}"
    for equivalents in params_config:
        assert isinstance(equivalents, (list, tuple)), f"List expedted as params config item, got this {equivalents}"
        type_count = 0
        for equivalent in equivalents:
            if isinstance(equivalent, str):
                assert equivalent.startswith('-') or equivalent.startswith('+'), f"Parameters must start with '-' or '+', got this: {equivalent}"
                assert equivalent not in params, f"Parameter found multiple times in params config: {equivalent}"
                params.append(equivalent)
            elif equivalent not in (bool, int, float, str):
                raise AssertionError(f"Strings or types (bool, int, float, str) are accepted in a params config item, got this: {equivalent}")
            else:
                type_count += 1
                assert type_count <= 1, f"More than one type found here: {equivalents}"

def humblecall(func, args, kwargs):
    if not callable(func):
        return func
    args = list(args)
    positional_only_args, positional_or_keyword_args, has_positional_var, keyword_only_args, has_keyword_var = _get_func_signature_data(func)
    missing_args = list()
    if len(positional_only_args) > len(args):
        for extra_poso_arg in positional_only_args[len(args):]:
            if not extra_poso_arg['has_default']:
                missing_args.append(extra_poso_arg['name'])
    matched_args = args[:len(positional_only_args)]
    args = args[len(positional_only_args):]
    for pork_arg in positional_or_keyword_args:
        name = pork_arg['name']
        if name in kwargs:
            matched_args.append(kwargs[name])
            del kwargs[name]
        else:
            if len(args) > 0:
                matched_args.append(args.pop(0))
            elif not pork_arg['has_default']:
                missing_args.append(name)
    keyword_only_arg_names = list()
    for kwo_arg in keyword_only_args:
        name = kwo_arg['name']
        if not kwo_arg['has_default'] and name not in kwargs:
            missing_args.append(name)
        keyword_only_arg_names.append(name)
    if len(missing_args) > 0:
        raise TypeError(f"Arguments for calling {func.__name__}() are missing: {', '.join(missing_args)}")
    if has_positional_var:
        matched_args += args
    if not has_keyword_var:
        kwargs = {key: value for key, value in kwargs.items() if key in keyword_only_arg_names}
    return func(*matched_args, **kwargs)

def _get_func_signature_data(func):
    positional_only_args = list()
    positional_or_keyword_args = list()
    has_positional_var = False
    keyword_only_args = list()
    has_keyword_var = False
    for name, param in inspect.signature(func).parameters.items():
        param_data = {
            'name': name,
            'has_default': param.default is not inspect._empty
        }
        if param.kind == param.POSITIONAL_ONLY:
            positional_only_args.append(param_data)
        elif param.kind == param.POSITIONAL_OR_KEYWORD:
            positional_or_keyword_args.append(param_data)
        elif param.kind == param.VAR_POSITIONAL:
            has_positional_var = True
        elif param.kind == param.KEYWORD_ONLY:
            keyword_only_args.append(param_data)
        elif param.kind == param.VAR_KEYWORD:
            has_keyword_var = True
    return positional_only_args, positional_or_keyword_args, has_positional_var, keyword_only_args, has_keyword_var

def get_arg_type(arg):
    if minus_numeric_re.match(arg):
        return 'minus numeric'
    if plus_numeric_re.match(arg):
        return 'plus numeric'
    if minus_letter_re.match(arg):
        return 'minus letter'
    if plus_letter_re.match(arg):
        return 'plus letter'
    if minus_letter_block_re.match(arg):
        return 'minus letter block'
    if plus_letter_block_re.match(arg):
        return 'plus letter block'
    if minus_string_re.match(arg):
        return 'minus string'
    if doubleminus_string_re.match(arg):
        return 'doubleminus string'
    return 'param or command'

def get_params_equivalency_from_config(params_config):
    params_equivalency = dict()
    for equivalents in params_config:
        param_type = ([eq for eq in equivalents if isinstance(eq, type)] or [bool])[0]
        equivalent_params = tuple(eq for eq in equivalents if isinstance(eq, str))
        equivalency = {'type': param_type, 'equivalents': equivalent_params}
        for eq_param in equivalent_params:
            params_equivalency[eq_param] = equivalency
    return params_equivalency
