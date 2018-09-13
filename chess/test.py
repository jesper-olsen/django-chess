import os
import re
import glob

p = re.compile(r'(?P<word>\b\w+\b)')
p = re.compile(r'[0-9a-z\-]+_(?P<gid>[0-9]+).txt$')
p = re.compile(r'_(?P<gid>[0-9]+).txt$')
s='http://127.0.0.1:8000/chess/recent/review/331e4fee-a864-4ee7-bc20-098b8f0c8a9b_0.txt'

def get_gid(gdir,uid):
    p = re.compile(r'_(?P<gid>[0-9]+).txt$')
    g=glob.glob("{}/{}_*.txt".format(gdir,uid))
    l=(p.search(s) for s in g)
    l=(m.group('gid') for m in l if m!=None)
    l=(int(m) for m in l)
    return max(l)

def get_gids():
    g=glob.glob("../GAMES/*.txt")
    for s in g:
        m=p.search(s)

        print(m.group('gid'))
        yield int( m.group('gid') )

print(max(get_gids()))

print("max",get_gid("../GAMES/","331e4fee-a864-4ee7-bc20-098b8f0c8a9b"))
