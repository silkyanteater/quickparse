from pprint import pformat

from quickparse import QuickParse


def do_show_help():
    print('Executing \'do_show_help\'...')

def do_commit():
    print('Executing \'do_commit\'...')

def do_log(quickparse):
    print('Executing \'do_log\'...')

def do_stash():
    print('Executing \'do_stash\'...')

def do_stash_list():
    print('Executing \'do_stash_list\'...')

commands_config = {
    '': do_show_help,
    'commit': do_commit,
    'log': do_log,
    'stash': {
        '': do_stash,
        'list': do_stash_list,
    }
}

options_config = [
    ('-m', '--message', str),
    ('-p', '--patch'),
]


parsed = QuickParse(commands_config, options_config)


print(f'Commands:\n{pformat(parsed.commands)}')
print(f'Parameters:\n{pformat(parsed.parameters)}')
print(f'Options:\n{pformat(parsed.options)}')
print(f'\'-\' numeric argument:\n{pformat(parsed.numeric)}')
print(f'\'+\' numeric argument:\n{pformat(parsed.plusnumeric)}')
print(f'Functions to call:\n{pformat(parsed.to_execute)}')

parsed.execute()
