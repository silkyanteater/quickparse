import pytest

from quickparse import QuickParse

'''
commands and subcommand (command tree) + command aliases
binary flags short/long (either or)
named parameters (like '--name Steve') with type
minus numeric flags
plus numeric flags
-- (only parameters after that)

add validator object and a way to direct those invalid calls to an error handler of that command
'''

params = [
    ('-a', '--all'),
    ('-l', '-long', '--long', bool),  # same as without 'bool'
    ('-n', '-name', '--name', str),
]

func_names1 = \
    ['onNoCommand', 'onClear', 'onUser', 'onUserList', 'onUserAdd', 'onUserDel', 'onLoad', 'onStageList', 'onStageDrop', 'onTree', 'onBranch'] + \
    ['validateNoCommand']
for item in func_names1:
    globals()[item] = (lambda s: lambda: s)(item)

commands1 = {
    '': (validateNoCommand, onNoCommand),
    'user': (onUser, {
        ('list', 'ls'): onUserList,
        'add': onUserAdd,
        'del': onUserDel,
    }),
    'load': onLoad,
    'stage': {
        ('', 'ls', 'list'): onStageList,
        'drop': onStageDrop,
    },
    'tree': onTree,
    ('branch', 'br'): onBranch,
}


func_names2 = \
    ['show_help', 'user_list', 'user_add', 'user_del', 'user_select', 'stage_show', 'stage_drop', 'branch_getall', 'branch_add'] + \
    ['branch_move', 'branch_remove', 'import_space', 'export_all', 'export_trees', 'export_gems']
for item in func_names2:
    globals()[item] = (lambda s: lambda(*args): s)(item)

commands2 = {
    'h': show_help,
    'user': {
        '': user_select,
        'ls': user_list,
        'add': user_add,
        'del': user_del,
    },
    'st': {
        '': stage_show,
        'drop': stage_drop,
    },
    'br': {
        '': branch_getall,
        'add': branch_add,
        'mv': branch_move,
        'del': branch_remove,
    },
    'im': import_space,
    'ex': {
        '': export_all,
        'tr': export_trees,
        'gm': export_gems,
    },
}

def test_basics():
    with pytest.raises(ValueError):
        cli_args = [()]
        parsed = QuickParse(commands=commands1, params=params, cli_args=cli_args)
    cli_args = []
    parsed = QuickParse(commands=commands1, params=params, cli_args=cli_args)
    assert isinstance(getattr(parsed, 'raw_args', None), list)
    assert isinstance(getattr(parsed, 'commands', None), list)
    assert isinstance(getattr(parsed, 'params', None), dict)
    assert callable(getattr(parsed, 'execute', None))

def test_commands_config():
    cli_args = ['h']
    parsed = QuickParse(commands=commands2, cli_args=cli_args)
    assert parsed.execute() == 'show_help'
