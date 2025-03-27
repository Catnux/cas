'''
cas, the catnux assembler.
Copyright (C) 2025  Avalyn Baldyga

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, see
<https://www.gnu.org/licenses/>.
'''
import sys
import config
import math

file = open(sys.argv[1], 'r')
lines = file.read().replace('\n','').split(';')
out = ""
constants = {}
addrpoints = {}
if lines[0] == 'NOHEADERS':
    lines = lines[1:]
else:
    lines = config.headers + lines
for index, line in enumerate(lines):
    line = line.strip()
    if not line.startswith('+'):
        break
    else:
        line = line[1:]
        print(f"Added headerfile {line + '.c86'}")
        plusfile = open(line + '.c86', 'r')
        lines = plusfile.read().replace('\n','').split(';') + lines
for index, line in enumerate(lines):
    lineout = ""
    try:
        line = line.strip()
        if line.startswith('+'):
            continue
        elif line.startswith('.'):
            name = line.split(' ')[0][1:]
            val = line.split(' ')[1]
            assert val.isnumeric() or val.startswith('.')
            if val.startswith('.'):
                try:
                    val = constants[val[1:]]
                except KeyError:
                    raise Exception(f"Assembler constant {val[1:]} not found.")
            constants[name] = val
        elif line.startswith('#'):
            name = line.split('=')[0][1:].strip()
            addrpoints[name] = "{:010}".format((len(out))//12)
            val: str = ''.join(line.split('=')[1:]).strip()
            if val.isnumeric():
                lineout += "{:012}".format(int(val))
            elif val.startswith('.'):
                try:
                    val = constants[val[1:]]
                except KeyError:
                    raise Exception(f"Assembler constant {val[1:]} not found.")
                lineout += "{:012}".format(int(val))
            elif val.startswith('{'):
                bites = val[1:-1].replace(' ','').split(',')
                for bite in bites:
                   if bite:
                       if bite.startswith('.'):
                            try:
                                bite = constants[bite[1:]]
                            except KeyError:
                                raise Exception(f"Assembler constant {bite[1:]} not found.")
                       lineout += "{:012}".format(int(bite))
            elif val.startswith('"'):
                val = val[1:-1]
                val = val.replace('\\n','\n')
                val = val.replace('@', 'at')
                val += '@'
                constants['L'+name] = math.ceil(len(val)/6)
                bite = ''
                for char in val:
                    if len(bite) == 12:
                        lineout += bite
                        bite = ''
                    bite += "{:02}".format(config.charset.index(char))
                lineout += "{:012}".format(int(bite))
            elif val.startswith('\''):
                val = val[1:-1]
                val = val.replace('\\n','\n')
                val = val.replace('@', 'at')
                val += '@'
                constants['L'+name] = len(val)
                for char in val:
                    lineout += "{:012}".format(config.charset.index(char))
            elif 'x' in val:
                bite = val.split('x')[0].strip()
                constants['L'+name] = val.split('x')[1].strip()
                lineout += "{:012}".format(int(bite))*int(val.split('x')[1].strip())
        elif line.startswith(':'):
            addrpoints[line[1:]] = "{:010}".format(len(out)//12)
        elif line.split(' ')[0].isalpha():
            ictn = config.itable[line.split(' ')[0].upper()]
            inpt: str = line.split(' ')[1]
            if inpt.startswith('.'):
                try:
                    inpt = "{:010}".format(int(constants[inpt[1:]]))
                except KeyError:
                    raise Exception(f"Assembler constant {inpt[1:]} not found.")
            elif inpt.startswith('#'):
                inpt = f"{{addrpoints['{inpt[1:]}']}}"
            elif inpt.isalpha():
                if ictn == '00':
                    raise Exception(f"Registers may not be passed to a NOOP.")
                ictn= f"{int(ictn) + max([int(x) for x in config.itable.values()])}"
                inpt = config.regs.index(inpt.lower())
            elif not inpt.startswith('{'):
                inpt = "{:010}".format(int(inpt))
            if isinstance(inpt, int):
                inpt = "{:010}".format(int(inpt))
            lineout += f"{ictn}{inpt}"
            assert (len(lineout) % 12 == 0) or '{' in lineout
        out += lineout
    except Exception as e:
        print(f"Failed to assemble line {index} \"{line}\" with error: {e}.")
        raise e
        quit()
try:
    out = eval(f'f"{out}"')
except KeyError as e:
    print(f"Pointer not found: {e}")
    quit()
assert len(out) % 12 == 0
open((sys.argv[1][:-4] if sys.argv[1].endswith('.c86') else sys.argv[1])+'.mco', 'w').write(out)
