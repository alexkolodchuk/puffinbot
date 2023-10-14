import discord, asyncio
from discord.ext import commands
from util import *


# 1. Инициализировать настройки бота и самого бота
prefs = readf()
class Puffinbot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=prefs['prefix'], intents=discord.Intents.all())
        self.players = dict()
        
    def getPlayer(self, guild, channel):
        try:
            player = self.players[guild.id]
            if player.vc.channel.id != channel.id:
                player.move(channel)
        except KeyError:
            player = Player(channel)
            self.players[guild.id] = player
        return player
    
bot = Puffinbot()

# 2. Описать все события, обрабатываемые ботом
@bot.event
async def on_ready():
    print("Тупикbot ожил")

@bot.event
async def on_message(msg):
    if str(msg.guild.id) in prefs['servers']:
        if msg.channel.id == int(prefs['sgchannel']):
            await msg.add_reaction('thumbsup')
            await msg.add_reaction('thumbsdown')
    await bot.process_commands(msg)

@bot.event
async def on_raw_reaction_add(payload):
    for x in prefs['rr']:
        if int(x[2]) == payload.message_id and int(x[4]) == payload.emoji.id:
            await payload.member.add_roles(discord.utils.find(lambda y: y.id == int(x[5]),
                                                              payload.member.guild.roles))

@bot.event
async def on_raw_reaction_remove(payload):
    for x in prefs['rr']:
        if int(x[2]) == payload.message_id and int(x[4]) == payload.emoji.id:
            guild = discord.utils.find(lambda y: y.id == payload.guild_id, bot.guilds)
            member = discord.utils.find(lambda y: y.id == payload.user_id, guild.members)
            await member.remove_roles(discord.utils.find(lambda y: y.id == int(x[5]),
                                                              guild.roles))


# Не музыкальные команды
bot.remove_command('help')

@bot.command(name='help')
async def help(ctx, *args):
    await ctx.send('''
**Модерация**
    `rr`
**Музыка**
    `вкл`, `выкл`, `скип`, `ряд`''')

@bot.command(name='rr')
async def rr(ctx, *args):
    if len(args) not in [1, 4]: return
    if args[0]=='list':
        msg = '\n'.join(['https://discord.com/channels/'+'/'.join(i[:3])+' - <:'+i[3]+':'+i[4]+'> <@&'+i[5]+'>' for i in prefs['rr']])
        if msg=='': await ctx.send('Нет реакционных ролей')
        else: await ctx.send(msg)
        return
    if len(args)!=4: return
    new = [args[1].split('/')[4], args[1].split('/')[5],
           args[1].split('/')[6], args[2].split(":")[1], args[2].split(":")[2][:-1], 
           args[3][3:-1]]
    if args[0]=='add':
        prefs['rr'].append(new)
        writef(prefs)
    elif args[0]=='del':
        if new in prefs['rr']:
            prefs['rr'].remove(new)
        writef(prefs)
    print(args, prefs)

@bot.command(name='sg')
async def sg(ctx, *args):
    if len(args)!=1: return
    try:
        prefs['sgchannel'] = str(int(args[0]))
        writef(prefs)
        await ctx.message.add_reaction('white_check_mark')
    except: return


@bot.command(name='вкл')
async def on(ctx, *args):
    url = ' '.join(args)
    if url=='':
        url = 'https://dj.bronyradio.com/streamhq.mp3'
    player = bot.getPlayer(ctx.guild, ctx.author.voice.channel)
    if not url.startswith('http'): # this is a YT search and needs to be parsed
        url = get_yt_url(url)
    await player.add(url)
    await success(ctx)

@bot.command(name='выкл')
async def off(ctx):
    player = bot.getPlayer(ctx.guild, ctx.author.voice.channel)
    await player.kill()
    await success(ctx)
    
@bot.command(name='скип')
async def skip(ctx):
    player = bot.getPlayer(ctx.guild, ctx.author.voice.channel)
    await player.skip()
    await success(ctx)
    
@bot.command(name='ряд')
async def queue(ctx):
    player = bot.getPlayer(ctx.guild, ctx.author.voice.channel)
    await ctx.send('**Сейчас играет: [`'+player.rn['title']+'`]('+player.rn['url']+')**\nДалее:\n'+'\n'.join(['**'+str(i+1)+'**: [`'+player.queue[i]['title']+'`]('+player.queue[i]['url']+')' for i in range(0, len(player.queue))]))
    open('data.txt', 'w').write('\n'.join(x+'\n'+y+'\n\n' for x, y in zip(player.rn.keys(), map(str, player.rn.values()))))
    await success(ctx)

@bot.command(name='повтор')
async def repeat(ctx):
    player = bot.getPlayer(ctx.guild, ctx.author.voice.channel)
    player.repeat = not player.repeat
    await ctx.send('Повтор в'+'ы'*(not player.repeat)+'ключен')

@bot.command(name='дебаг')
async def debug(ctx):
    print(bot.players)

# Инстанция Player создаётся каждый раз, когда на сервере создаётся голосовой клиент бота 
#
# queue - список песен, проигрываемых Player
# vc - голосовой клиент (бота) сервера
#
# в __init__ создаётся пустой список песен, голосовой клиент, и запускается цикл работы Player
# kill - уничтожить объект Player
# move - переместить бота в другой гк
class Player:
    def __init__(self, channel):
        self.queue = []
        self.next = asyncio.Event()
        self.vc = None
        self.channel = channel
        self.rn = None
        self.repeat = False
        
        bot.loop.create_task(self.player_loop())

    # Queue funcs
    async def qget(self):
        while True:
            try:
                return self.queue.pop(0)
            except IndexError:
                await asyncio.sleep(0.01)

    async def player_loop(self):
        self.vc = await self.channel.connect()
        
        while True:
            song_data = await self.qget()
            if self.repeat:
                self.queue.append(song_data)
            self.play(song_data)
            self.rn = song_data
            await self.next.wait()

    async def kill(self):
        await self.vc.disconnect()
        del bot.players[self.vc.guild.id]
        
    async def move(self, channel):
        await self.vc.move_to(channel)
    
    async def add(self, url):
        self.queue.append(get_data(url))
        
    async def skip(self):
        self.vc.stop()
        bot.loop.call_soon_threadsafe(self.next.set)
    
    def play(self, data):
        self.vc.play(discord.FFmpegPCMAudio(data["url"], options='-vn'),
                     after=lambda _: bot.loop.call_soon_threadsafe(self.next.set))
        self.vc.source.volume = .5

# 3. Запустить бота
bot.run(open('token.txt').read())