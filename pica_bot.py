from myExtcmds import *

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
MY_ID = os.getenv('MY_ID')


lobby = []
lobbyCreated = False
lobbyCreator = ''
client = discord.Client()
isGuessnumPlaying = False
guessnumNumber = randint(1,1024)
guessnumPlayer = ''
guessnumPlayerID = ''
guessnumCount = 0


class myClient(discord.Client):
    async def on_ready(self):
        await self.change_presence(status=discord.Status.online,activity=discord.Game(name='with @Differential'))
        print(f'Logged in as {self.user}  ------\nReady!')
        return


    async def on_member_join(self, member):
        joinedGuild = member.guild
        if joinedGuild.system_channel is not None:
            await joinedGuild.system_channel.send('สวัสดีเจ้า ' + member.mention + ' น้าาาาาาา')
        return


    async def on_member_remove(self, member):
        joinedGuild = member.guild
        if joinedGuild.system_channel is not None:
            await joinedGuild.system_channel.send('บะบายน้า ' + member.mention + ' ;w;')
        return


    async def on_message(self, message):
        fromChannel=self.get_channel(message.channel.id)
        if(not message.content.startswith('!') or message.author.id==self.user.id):
            return
        if(message.content.startswith('!help')):
            em = discord.Embed(title = 'สิ่งที่เราทำได้ตอนนี้อ่ะนะ :thinking:',description='มีเท่านี้แหละ\nไปสั่งคนทำมาเพิ่มฟีเจอร์เราสิ ;w;',author='Pica, pica!',colour=0xffe770)
            em.add_field(name = '!help',value='ก็อันนี้นี่แหละ')
            em.add_field(name = '!ดีมั้ย {คำถาม}/!ดีไหม {คำถาม}',value='เอาไว้ช่วยตัดสินใจอ่ะนะ')
            em.add_field(name = '!role',value='ช่วยตัดสินใจว่าเล่นตำแหน่งไรดี \(RoV\)')
            await fromChannel.send(content=None,embed=em)
        elif(message.content.startswith('!ดีมั้ย') or message.content.startswith('!ดีไหม')):
            if(message.content == '!ดีมั้ย' or message.content==('!ดีไหม')):
                await fromChannel.send(message.author.mention + ' อะไรเล่า!?')
                return
            responses=['เอาดิ','จัดไปอย่าให้เสีย','เรื่องนี้มันก็แน่อยู่แล้วปะวะ',\
                       'จะถามอย่างงั้นจริงๆ หรอ','ไม่แน่ใจเท่าไหร่ว่ะ','ห้ะ?',\
                       'ไม่ดีกว่า','อย่าเลยเพื่อน','ถ้าอยากมีความสุขก็อย่าเถอะ']
            await fromChannel.send(message.author.mention + ' ' + choose(responses))
        elif(message.content.startswith('!hi')):
            responses = ['สวัสดี! ','สวัสดีจ้า ','ฮ้ายฮายย~ ','เห็นโล่วเจ้า ','ว่างาย ','Bonjour! ','안녕 ']
            await fromChannel.send(choose(responses) + ":wave: " + message.author.mention)
        elif(message.content.startswith('!role')):
            responses=['แครี่ดิวะ','คนไทยหัวใจแครี่สิดี','แครี่ที่ดีต้องเป็นคุณ','ทีมต้องการแครี่!',\
                       'โรมมิ่งวิ่งแก้งไปสิ','โรมไปนะเพื่อน','ไปซัพแครี่ซะนะ','ทีมต้องการโรม!',\
                       'เมจเก่งไม่ใช่หรอเราอ่ะ','ไปโยนสกิลใส่เลนกลางเล้ยยยยย','อย่างงี้ต้องเดินทางสายกลาง','ทีมต้องการเมจ!',\
                       'ไปเก็บตังในป่าซะ','ป่าน่าจะเหมาะสุดนะจังหวะนี้','ทีมมันกาก ต้องเล่นป่าไปแบกสิ','ทีมต้องการป่า!',\
                       'ไปเฝ้าป้อมเล่นด้าคให้หน่อยสิ','จงไปเลนดาร์คซะ','เป็นแท้งให้ทีมสิดี','ทีมต้องการแท้ง!']
            await fromChannel.send(message.author.mention + ' ' + choose(responses))
        elif(message.content.startswith('!lobby')):
            global lobby, lobbyCreated, lobbyCreator
            if(message.content[7:]=='help'):
                em = discord.Embed(title = '!lobby',description='วิธีใช้ !lobby นะครับทุกทั่น :100:\n:rainbow: คำสั่งต่อไปนี้พิมต่อจาก !lobby เว้นด้วย 1 เว้นวรรคนะ :rainbow:',author='Pica, pica!',colour=0xf5ad42)
                em.add_field(name='help',value='ก็อันนี้นี่แหละ')
                em.add_field(name='create random',value='สร้างตี้แบบสุ่มตำแหน่งให้ คือบอทจะสุ่มตำแหน่งให้แต่ละคนอ่ะ สร้างได้ทีละห้องนะ!!')
                em.add_field(name='join',value='เข้าห้องที่สร้างอยู่ตอนนี้ ถ้ามีอ่ะนะ')
                await fromChannel.send(content=None,embed=em)
            elif(message.content[7:]=='create random'):
                if(lobbyCreated):
                    await fromChannel.send(message.author.mention + f' {lobbyCreator} สร้างล็อบบี้ไปแล้วน้า')
                else:
                    lobbyCreator = message.author.name
                    lobby.append(message.author.id)
                    lobbyCreated=True
                    await fromChannel.send('ล็อบบี้ถูกสร้างโดย ' + message.author.mention + ' เรียบร้อยแน้ว!')
            elif(message.content[7:]=='join'):
                if(lobbyCreated):
                    if(message.author.id in lobby):
                        await fromChannel.send(message.author.mention + ' พี่อยู่ในล็อบบี้อยู่แล้วง่าาา')
                        return;
                    lobby.append(message.author.id)
                    msg = ''
                    for peopleInd in range(len(lobby)):
                        msg+=f'{peopleInd+1} - {discord.Client.get_user(self,lobby[peopleInd]).mention}\n'
                    await fromChannel.send('เพิ่ม ' + message.author.mention + ' เข้าล็อบบี้แบ้วฮับ!\nตอนนี้สมาชิกตี้มี:\n' + msg)
                    if(len(lobby)==5):
                        random.shuffle(lobby)
                        await fromChannel.send('ล็อบบี้เต็มละน้าา ผลสุ่มก็คื๊ออออ:\n'\
                            + discord.Client.get_user(self,lobby[0]).mention + ' ไปเลนดาร์คน้า\n'\
                            + discord.Client.get_user(self,lobby[1]).mention + ' ฟามป่าเลยจ้า\n'\
                            + discord.Client.get_user(self,lobby[2]).mention + ' ไปโยนสกิลในเลนกลางน้า\n'\
                            + discord.Client.get_user(self,lobby[3]).mention + ' แบกทีมด้วยแครี่ในเลนมังกรไปเลยยยย\n'\
                            + discord.Client.get_user(self,lobby[4]).mention + ' นายจะได้เป็นโรมที่ดีที่สุดในทีม!\nEnjoy~')
                        lobby.clear();
                        lobbyCreated=False;
                else:
                    await fromChannel.send(message.author.mention + ' ล็อบบี้ยังเคยไม่เคยสร้างง่า ลอง !lobby create random ดูเสะ')
            else:
                await fromChannel.send(message.author.mention + ' ถ้าใช้ยังไม่เป็น ลอง !lobby help น้า')
        elif(message.content.startswith('!ping')):
            await fromChannel.send(message.author.mention + ' ป๊อง! ' + str(round(self.latency*1000)) + ' ms')
        elif(message.content.startswith('!bye')):
            responses = ['บ้ายบายยยย ','ลาก่อยยยย ','แจปืนนนน ','ไว้เจอกันค้าบบ ','โชคดีน้าาา ']
            await fromChannel.send(choose(responses) + ":wave: " + message.author.mention)
        elif(message.content.startswith('!guessnum')):
            global isGuessnumPlaying, guessnumPlayer, guessnumPlayerID, guessnumNumber
            if(message.content[9:]==' reset'):
                if(not isAdmin(message.author)):
                    await fromChannel.send(f'{message.author.mention} อันนี้แอดมินใช้เท่านั้นน้าา')
                    return
                else:
                    isGuessnumPlaying = False
                    guessnumPlayer = ''
                    guessnumPlayerID = ''
                    guessnumNumber = randint(1,1024)
                    await fromChannel.send(f'รีเซ็ตเกมทายเลขละจ้า')
                    return
            elif(isGuessnumPlaying):
                if(message.author.id != guessnumPlayerID):
                    await fromChannel.send(f"{message.author.mention} กำลังเล่นกับ {guessnumPlayer} อยู่ง่าาาาา")
                else:
                    await fromChannel.send(f"{message.author.mention} ทายมาสิครับ รออะไร!?")
            elif(not isGuessnumPlaying):
                isGuessnumPlaying = True
                guessnumPlayer = message.author.name
                guessnumPlayerID = message.author.id
                await fromChannel.send(f"**ก็มาดิครับ** {message.author.mention} :exclamation:\n\
:question: **วิธีเล่น** :question:\n\
เราจะให้นายทายเลขที่เราคิดไว้ มีค่า `1` ถึง `1024`\n\
พิมพ์ว่า `!? <ตัวเลข>` - ทายว่าใช่เลขนี้มั้ย\n\
แล้วเราจะบอกว่าใช่ น้อยกว่าหรือมากกว่าเลขของเรา")
        elif(message.content.startswith('!?')):
            if(not isGuessnumPlaying or message.author.id != guessnumPlayerID):
                await fromChannel.send(f'อยากเล่นหรอครับคุณ {message.author.mention} พิม `!guessnum` ก่อนนะครับ ไม่ก็รอคนอื่นเล่นจบก่อนน้า')
            else:
                if(message.content == '!?'):
                    await fromChannel.send(f'ทายมาสิครับ รออยู่นะ! {message.author.mention}')
                elif(message.content[2:] == ' <ตัวเลข>'):
                    await fromChannel.send(f'{message.author.mention} ตวงติงนักน้าาาาาา')
                else:
                    try:
                        thisnum = int(message.content[2:])
                        if(thisnum == guessnumNumber):
                            responses = ['เก่งสุด ๆ ไปเลยนะ','ว้าวซ่า','โห้ เก่งนี่หว่า']
                            isGuessnumPlaying = False
                            guessnumNumber = randint(1,1024)
                            await fromChannel.send(f'{message.author.mention} {choose(responses)} เลขของผมคือ **{str(thisnum)}** ถูกต้องนะครับ')
                        elif(thisnum > guessnumNumber):
                            responses = ['เยอะเกิน ไอหนู','เยอะไปนะครับ','มากไปนะ','เยอะเกินครับ ลองใหม่ครับ']
                            await fromChannel.send(f'{message.author.mention} {thisnum} {choose(responses)}')
                        elif(thisnum < guessnumNumber):
                            responses = ['น้อยไป ไอหนู','น้อยไปนะครับ','น้อยไปนะ','น้อยเกินครับ ลองใหม่ครับ']
                            await fromChannel.send(f'{message.author.mention} {thisnum} {choose(responses)}')
                    except Exception:
                        await fromChannel.send(f'{message.author.mention} ขอจำนวนเต็มสิครับพรี่')
        elif(message.content.startswith('!rps')):
            if(message.content == '!rps'):
                await fromChannel.send(f'อ้าวววว {message.author.mention} เจอได้นะครับบบบ :hammer: :scissors: :roll_of_paper:\n\
พิม `!rps <ค้อน/กรรไกร/กระดาษ>` มาเป่ายิ้งฉุบกับเราได้เลย!\n\
เราไม่โกงแน่นอน สาบานได้นะ!')
            else:
                realStuff = {
                    0 : ':hammer:',
                    1 : ':scissors:',
                    2 : ':roll_of_paper:'
                }
                playerState = -1
                if(message.content[4:]==' ค้อน'):
                    playerState = 0
                elif(message.content[4:]==' กรรไกร'):
                    playerState = 1
                elif(message.content[4:]==' กระดาษ'):
                    playerState = 2
                if(playerState == -1):
                    await fromChannel.send(f'{message.author.mention} เอาซักอย่างครับ!! `ค้อน`, `กรรไกร` ไม่ก็ `กระดาษ`')
                    return
                botState=randint(0,2)
                text = f'{message.author.mention}\n{realStuff[playerState]}  :vs:  {realStuff[botState]} :exclamation:\n'
                if(playerState == botState):
                    responses = ['เสมอครับ! เอาใหม่ซักตามั้ยล่าาา','ฮึ่ยย่ะ! เสมอครับ','ว่าว เรียกได้ว่าเราเก่งเท่ากันได้มั้ยน้า']
                    text += choose(responses)
                elif(playerState == botState+1 or (playerState==0 and botState==2)):
                    responses = ['ตานี้ชั้นขอละกัน! ฮ่าๆๆ','เย่ เลาชนะน้า','เย่ เลาชนะ ไม่เป็นไรน้าา']
                    text += choose(responses)
                elif(playerState+1 == botState or (playerState==2 and botState==0)):
                    responses = ['โถ่เอ้ย! ฝากไว้ก่อนเถอะ...','ว้าว เก่งจัด ๆ เลยนะนายน่ะ','ง่าาา เก่งไป รับมั่ยดั้ย']
                    text += choose(responses)
                await fromChannel.send(text)
        return

    
    async def on_member_update(self, memBef, memAft):
        if(str(memBef.id) == MY_ID):
            if(memAft.status==discord.Status.idle):
                await self.change_presence(status=discord.Status.idle,activity=discord.Activity(name='@Differential sleep',type=discord.ActivityType.watching))
            elif(memAft.status==discord.Status.dnd):
                await self.change_presence(status=discord.Status.dnd,activity=discord.Activity(name='@Differential being busy',type=discord.ActivityType.watching))
            else:
                await self.change_presence(status=discord.Status.online,activity=discord.Game(name='with @Differential'))


client = myClient()
client.run(TOKEN)
