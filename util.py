# Утилитарные функции
import yt_dlp, asyncio, requests
from bs4 import BeautifulSoup

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
                 'prefix': '~',
                 'sgchannel': '1160699169531494512',
                 'rr': []}
        writef(prefs)
    return prefs

def get_data(url):
    return yt_dlp.YoutubeDL({'format': 'bestaudio/best'}).extract_info(url, download=False)

#WIP
def get_yt_url(search):
    return search

async def success(ctx):
    await ctx.message.add_reaction('👍')
    await asyncio.sleep(2)
    await ctx.message.clear_reaction('👍')

print(readf())
