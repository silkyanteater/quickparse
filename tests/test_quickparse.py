
'''
commands and subcommand (command tree) + command aliases
binary flags short/long (either or)
named parameters (like '--name Steve') with type
minus numeric flags
plus numeric flags
-- (only parameters after that)
'''

parameters = {
    'all': ('-a', '--all'),
    'long': (('-l', '-long', '--long'), bool),  # same as without type 'bool'
    'name': (('-n', '-name', '--name'), str),
}


onNoCommand = onClear = onUser = onUserList = onUserAdd = onUserDel = onLoad = onStageList = onStageDrop = onTree = lambda: None

command_map = {
    '': onNoCommand,
    'clear': onClear,
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
