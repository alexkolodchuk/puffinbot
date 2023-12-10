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
    
    def hasPlayer(self, guild):
        if guild.id not in self.players.keys():
            return False
        return True
    
    def process_suggestions(self):
        #WIP
        while True:
            pass
    
bot = Puffinbot()

# 2. Описать все события, обрабатываемые ботом
@bot.event
async def on_ready():
    print("Тупикbot ожил")
    #bot.loop.create_task(bot.process_suggestions())

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

@bot.command(name='help', aliases=['помощь'])
async def help(ctx, *args):
    await ctx.send('''
**Параметры**
    `преф`
**Модерация**
    `рр`, `пред`
**Музыка**
    `вкл`, `выкл`, `скип`, `ряд`, `громкость`, `повтор`, `алиас`
    
**Settings**
    `pref`
**Moderation**
    `rr`, `sugg`
**Music**
    `play`, `stop`, `skip`, `queue`, `volume`, `repeat`, `alias`''')
    
    
@bot.command(name='преф', aliases=['pref'])
async def pref(ctx, *args):
    if len(args)==0:
        await ctx.send('`'+prefs['prefix']+'`')
    else:
        prefs['prefix'] = ' '.join(args)

@bot.command(name='рр', aliases=['rr'])
async def rr(ctx, *args):
    if len(args) not in [0, 4]: return
    if len(args)==0:
        msg = '\n'.join(['https://discord.com/channels/'+'/'.join(i[:3])+' - <:'+i[3]+':'+i[4]+'> <@&'+i[5]+'>' for i in prefs['rr']])
        if msg=='': await ctx.send('Нет реакционных ролей')
        else: await ctx.send(msg)
        return
    if len(args)!=4: return
    new = [args[1].split('/')[4], args[1].split('/')[5],
           args[1].split('/')[6], args[2].split(":")[1], args[2].split(":")[2][:-1], 
           args[3][3:-1]]
    if args[0]=='+':
        prefs['rr'].append(new)
        writef(prefs)
    elif args[0]=='-':
        if new in prefs['rr']:
            prefs['rr'].remove(new)
        writef(prefs)
    print(args, prefs)

@bot.command(name='пред', aliases=['sugg'])
async def sg(ctx, *args):
    if len(args)!=1:
        await ctx.send('''Использование:
`'''+prefs['prefix']+'''пред айдиКанала` - установить айди канала предложений
# WIP''')
    try:
        prefs['sgchannel'] = str(int(args[0]))
        writef(prefs)
        await ctx.message.add_reaction('white_check_mark')
    except: return


@bot.command(name='вкл', aliases=['play'])
async def on(ctx, *args):
    url = ' '.join(args)
        
    aliases = get_aliases('aliases.txt')
    
    if url=='':
        await ctx.send('''
Использование команды:
`'''+prefs['prefix']+'''вкл ссылка-на-ютуб-видео` - добавить видео/стрим в очередь
`'''+prefs['prefix']+'''вкл алиас` - добавить ссылку под алиасом
`'''+prefs['prefix']+'''вкл ссылка-на-файл` - добавить файл/аудиострим в очередь
`'''+prefs['prefix']+'''вкл всё-остальное` - добавить первое ютуб-видео по поиску всё-остальное''')
        return
        
    player = bot.getPlayer(ctx.guild, ctx.author.voice.channel)

    if url in aliases.keys():
        url = aliases[url]
    elif not url.startswith('http'):
        url = get_yt_url(url)
    await player.add(url)
    await success(ctx)

@bot.command(name='выкл', aliases=['stop'])
async def off(ctx):
    player = bot.getPlayer(ctx.guild, ctx.author.voice.channel)
    await player.kill()
    await success(ctx)
    
@bot.command(name='скип', aliases=['skip'])
async def skip(ctx, *args):
    if len(args)==0:
        cnt = 1
    else:
        cnt = int(args[0])
    player = bot.getPlayer(ctx.guild, ctx.author.voice.channel)
    for i in range(0, cnt):
        await player.skip()
    await success(ctx)
    
@bot.command(name='ряд', aliases=['queue'])
async def queue(ctx):
    if not bot.hasPlayer(ctx.guild):
        return
    player = bot.getPlayer(ctx.guild, ctx.author.voice.channel)
    await ctx.send('**Сейчас играет: [`'+player.rn['title']+'`]('+player.rn['url']+')**\nДалее:\n'+'\n'.join(['**'+str(i+1)+'**: [`'+player.queue[i]['title']+'`]('+player.queue[i]['url']+')' for i in range(0, len(player.queue))]))
    await success(ctx)

@bot.command(name='громкость', aliases=['volume'])
async def queue(ctx, *volume):
    if len(volume)==0:
        await ctx.send('''Использование:
`'''+prefs['prefix']+'''громкость n` - установить громкость n% от максимальной''')
        return
    player = bot.getPlayer(ctx.guild, ctx.author.voice.channel)
    player.vc.source.volume = int(volume[0])/100

@bot.command(name='повтор', aliases=['repeat'])
async def repeat(ctx):
    player = bot.getPlayer(ctx.guild, ctx.author.voice.channel)
    player.repeat = not player.repeat
    await ctx.send('Повтор в'+'ы'*(not player.repeat)+'ключен')

@bot.command(name='алиас', aliases=['alias'])
async def alias(ctx, *args):
    if len(args)==0:
        await ctx.send('''Использование:
`'''+prefs['prefix']+'''алиас вывод` - вывести все алиасы
`'''+prefs['prefix']+'''алиас + выражение1;выражение2` - создать новый алиас "выражение1"
`'''+prefs['prefix']+'''алиас - выражение1` - убрать алиас "выражение1"''')
        return
    al = ' '.join(args[1:])
    if args[0]=='+':
        add_alias(al.split(';')[0], al.split(';')[1])
    elif args[0]=='-':
        remove_alias(al.split(';')[0])
    elif args[0]=='вывод':
        aliases = get_aliases('aliases.txt')
        await ctx.send(', '.join(['[`'+k+'`]('+aliases[k]+')' for k in aliases.keys()]))
    await success(ctx)

@bot.command(name='дебаг', aliases=['debug'])
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
        self.repflag = False
        
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
            if self.repeat and not self.vc.is_playing():
                print('repeating')
                await self.add(self.rn['url'])
            song_data = await self.qget()
            self.play(song_data)
            self.rn = song_data
            await self.next.wait()

    async def kill(self):
        await self.vc.disconnect()
        del bot.players[self.vc.guild.id]
        
    async def move(self, channel):
        await self.vc.move_to(channel)
    
    async def add(self, url, offset=0):
        self.queue.append(get_data(url))
        
    async def skip(self):
        self.vc.stop()
        bot.loop.call_soon_threadsafe(self.next.set)
    
    def play(self, data, offset=0):
        self.vc.play(discord.FFmpegOpusAudio(data["url"], options='-vn', before_options='-reconnect 1 -ss '+str(offset)), after=lambda _: bot.loop.call_soon_threadsafe(self.next.set))

# 3. Запустить бота
bot.run(open('token.txt').read())