# Утилитарные функции
import yt_dlp, asyncio
from youtubesearchpython import VideosSearch

def writef(prefs):
    with open('prefs.txt', 'w') as f:
        f.write(','.join(prefs['servers'])+'\n')
        f.write(prefs['prefix']+'\n')
        f.write(prefs['sgchannel']+'\n')
        f.write('\n'.join(','.join(map(str, i)) for i in prefs['rr']))

def readf():
    prefs = dict()
    try:
        with open('prefs.txt') as f:
            t = f.read().split('\n')
            prefs['servers'] = t[0].split(',')
            prefs['prefix'] = t[1]
            prefs['sgchannel'] = t[2]
            prefs['rr'] = [i.split(',') for i in t[3:]]
    except FileNotFoundError:
        prefs = {'servers': ['1160681427227127949'],
                 'prefix': 'ы',
                 'sgchannel': '1160699169531494512',
                 'rr': []}
        writef(prefs)
    return prefs

def get_data(url):
    return yt_dlp.YoutubeDL({'format': 'bestaudio/best'}).extract_info(url, download=False)

async def success(ctx):
    await ctx.message.add_reaction('👍')
    await asyncio.sleep(2)
    await ctx.message.clear_reaction('👍')

def get_yt_url(search):
    videosSearch = VideosSearch(search, limit = 1)
    return videosSearch.result()['result'][0]['link']

# Работа с алиасами
def get_aliases(filename):
    aliases = dict()
    for line in open(filename).read().split('\n'):
        aliases[line.split(';')[0]] = line.split(';')[1]
    return aliases

def write_aliases(aliases, filename):
    with open(filename, 'w') as f:
        f.write('\n'.join([k+';'+aliases[k] for k in aliases.keys()]))

def add_alias(alias1, alias2):
    aliases = get_aliases('aliases.txt')
    aliases[alias1] = alias2
    write_aliases(aliases, 'aliases.txt')

def remove_alias(alias1):
    aliases = get_aliases('aliases.txt')
    del aliases[alias1]
    write_aliases(aliases, 'aliases.txt')
    
print(readf())
