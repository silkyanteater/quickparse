# QuickParse
Simple command line argument parser for Python

list_things.py:
```python
from quickparse import QuickParse

def list_things(a_list, quickparse):
    print(', '.join(map(str, a_list[:quickparse.numeric])))

commands_config = {
    'ls': list_things,
    '': lambda: print(f"Unknown command"),
}

mylist = list(range(1, 12))

QuickParse(commands_config).execute(mylist)
```

Run it:
```sh
$ python list_things.py ls -5
1, 2, 3, 4, 5
```

# Supported argument setups
[command] [subcommand]  $ git log
[command] [single-char flag]  $ ps -e
[command] [single-char flag stack]  $ ps -ef
[command] [single-char plus flag] [parameter]  $ chmod +x myfile
[command] [double-dash flag]  $ git --version
[command] [numeric flag]  $ ps -123
[command] [subcommand] [numeric flag]  $ git log -42
[command] [parameter]  $ ls /home
[command] [double-dash key-value]  $ git log --diff-filter=M
[command] [single-dash key-nodelimiter-value]  $ git log -Smytext

subcommand vs parameter: subcommands are validated against an enumerate

# How to define flags
('-v', ) : single-char flag without equivalent double-dash flag
('--version', ) : double-dash flag without equivalent single-char flag
('-u', '--utc') : single-char flag and the equivalent double-dash flag
('-u', '--utc', '--universal') : single-char flag and multiple equivalent double-dash flag

set up valueless flags - that means the next value is a parameter
curl -O http://www.gnu.org/software/gettext/manual/gettext.html

make sure right argument order:
chmod +x myfile

value can be '-'
curl -C - -O http://www.gnu.org/software/gettext/manual/gettext.html

trailing parameter list delimiter:
git checkout -- myfile

# Not supported argument setups
[command] [single-dash long flag]  $ find -version
[command] [single-dash long key-value]  $ find -name x
[command] [single-dash long key-equal-value]  $ mycommand -name=x
[command] [double-dash single-char flag]  $ mycommand --v
[command] [single-dash key-equal-value]  $ mycommand -H=myvalue
