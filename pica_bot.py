from asyncio.tasks import sleep
import asyncio
import os
import time
import discord
import sys
import aioconsole
import dotenv
import youtube_dl
import discord_together
from discord.errors import ClientException, Forbidden
from dotenv import load_dotenv
from random import randint, shuffle, choice


def is_admin(messageSender, fromChannel):
    return messageSender.permissions_in(fromChannel).administrator


def has_role(member, role_name):
    for role in member.roles:
        if role.name == role_name:
            return True
    return False


def list_diff(a, b):
    return list(set(a) - (set(b)))


def do_reboot():
    os.execv(sys.executable, ["python"] + sys.argv)


load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
MY_ID = int(os.getenv("MY_ID"))
TEST_CHANNEL_ID = int(os.getenv("TEST_CHANNEL_ID"))
BOT_ID = int(os.getenv("BOT_ID"))
YT_KEY = os.getenv("YT_KEY")
_volume = float(os.getenv("VOLUME"))

dirpath = os.path.dirname(__file__)
lobby = []
lobbyCreated = False
lobbyCreator = ""
isGuessnumPlaying = False
guessnumNumber = randint(1, 1024)
guessnumPlayer = ""
guessnumPlayerID = ""
guessnumCount = 0
guessnumPlayCount = 0
ydl_opts = {
    "outtmpl": "%(id)s.%(ext)s",
    "format": "bestaudio",
    "default_search": "ytsearch",
}
ydl = youtube_dl.YoutubeDL(ydl_opts)
my_server_id = 703264756986937415
self_role_channel_id = 859078452346880040
selfRoleMsgID = 859079003691548712

self_role_emojis = ["valo", "petCrew", "zhongliRed"]
self_role_ids = {
    "valo": 857645813128101898,
    "petCrew": 857645382543867926,
    "zhongliRed": 878277681488224296,
}


class Song:
    def __init__(self, player, file_name, song_title):
        self.player = player
        self.file_name = file_name
        self.song_title = song_title

    def copy(self, volume):
        return Song(
            discord.FFmpegOpusAudio(self.file_name), self.file_name, self.song_title
        )

    @property
    def song_id(self):
        return self.file_name[: self.file_name.rfind(".")]


class MyClient(discord.Client):
    def __init__(self, *, loop=None, **options):
        super().__init__(loop=loop, **options)

        print("Setting private variables...")

        self.temp_roles = dict()
        self.temp_textch = dict()
        self.song_queue = []
        self.volume = _volume
        self.music_channel_id = 887307591062020136
        self.music_channel = self.get_channel(self.music_channel_id)
        self.music_message_id = 887309277604237342
        self.music_message = self.music_channel.get_partial_message(
            self.music_message_id
        )
        self.remove_song = True

        print("creating song directory")
        try:
            os.umask(0)
            os.mkdir(os.path.join(dirpath, "songs"), mode=0o777)
            os.chmod(os.path.join(dirpath, "songs"), mode=0o777)
        except FileExistsError:
            print("song directory already exists")

    async def on_ready(self):
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Game(name="with @Differential"),
        )  # change status
        print(f"Logged in as {self.user}")

        self.discord_together = await discord_together.DiscordTogether(TOKEN)
        await self.update_song_list()
        print("checking for self role changes")
        my_server = self.get_guild(my_server_id)

        # ------------ checking for self role adding ---------------
        self_role_message = await self.get_channel(self_role_channel_id).fetch_message(
            selfRoleMsgID
        )
        for reaction in self_role_message.reactions:
            role_to_add = discord.Object(-1)
            members_have_role = my_server.get_role(
                self_role_ids[reaction.emoji.name]
            ).members
            if reaction.emoji.name in self_role_emojis:
                role_to_add.id = self_role_ids[reaction.emoji.name]
            else:
                await reaction.clear()
                return
            reaction_senders = await reaction.users().flatten()
            for user in list_diff(
                reaction_senders, members_have_role
            ):  # self role adding
                if user.id != BOT_ID:
                    await user.add_roles(role_to_add)  # add the role
                    print(f"added {reaction.emoji.name}'s role to {user.name}")

            for member in list_diff(
                members_have_role, reaction_senders
            ):  # self role remove
                if member.id != BOT_ID:
                    await member.remove_roles(
                        discord.Object(self_role_ids[reaction.emoji.name])
                    )
                    print(f"removed {reaction.emoji.name}'s role to {member.name}")
        # ------------ done checking self role adding --------------

        # ---------- checking for earlier temp chat/role ------------
        for role in my_server.roles:
            if role.name.startswith("ระเบิดเวลา"):
                role_for = role.name[11:]
                voice_ch_id = discord.utils.find(
                    lambda ch: isinstance(ch, discord.VoiceChannel)
                    and ch.name == role_for,
                    my_server.channels,
                ).id
                self.temp_roles[voice_ch_id] = role
        for ch in my_server.channels:
            if ch.name.startswith("ระเบิดเวลา"):
                text_for = ch.name[11:]
                voice_ch_id = discord.utils.find(
                    lambda ch: isinstance(ch, discord.VoiceChannel)
                    and ch.name == role_for,
                    my_server.channels,
                ).id
                self.temp_textch[voice_ch_id] = ch
        # ---------- done checking for earlier temp chat/role ------------
        print("ready!")
        # await self.wait_for_input()
        return

    async def wait_for_input(self):
        while True:
            int_command = await aioconsole.ainput()
            if int_command == "reboot":
                print("Rebooting...")
                await self.close()
                do_reboot()
            elif int_command == "exit":
                await self.close()
            else:
                print("Invalid command")

    async def update_song_list(self):
        text = "__***Queue list:***__\n"
        if len(self.song_queue):
            text += (
                f"1. {self.song_queue[0].song_title} `({self.song_queue[0].song_id})` "
            )
            if self.voice_clients[0].is_paused():
                text += "***(Paused)***\n"
            else:
                text += "***(Playing now)***\n"
            for i, song in enumerate(self.song_queue[1:], start=2):
                text += f"{i}. {song.song_title} `({song.song_id})`\n"
        await self.music_message.edit(content=text)
        return

    def dl_song(self, title: str) -> dict:
        try:
            info = ydl.extract_info(title, download=False)
        except Exception as e:
            print("extract info error!", e)
            return {"download_ok": False, "error_on_search": True, "exception": e}

        if "entries" in info:
            if len(info["entries"]) > 0:
                info = info["entries"][0]
            else:
                print("not found!?")
                return {
                    "download_ok": False,
                    "error_on_search": True,
                    "exception": "Query not found :(",
                }
        try:
            ydl.download(["https://youtu.be/" + info["id"]])
        except youtube_dl.utils.DownloadError as e:
            print("download error!", info["title"], "\n", e)
            return {
                "download_ok": False,
                "error_on_search": False,
                "exception": e,
                "title": info["title"],
                "ext": info["ext"],
                "id": info["id"],
            }
        else:
            return {
                "download_ok": True,
                "title": info["title"],
                "ext": info["ext"],
                "id": info["id"],
            }

    def remove_all_songs(self):
        for song in self.song_queue[1:]:
            song.player = None
            os.remove(song.file_name)
        self.song_queue = self.song_queue[:1]
        if self.voice_clients[0].is_playing() or self.voice_clients[0].is_paused():
            self.voice_clients[0].stop()

    def get_next_song(self, error):
        if error is not None:
            print("Something is wrong...?", error)

        last_song_file_name = None
        if len(self.song_queue):
            last_song_file_name = self.song_queue.pop(0).file_name
        if len(self.song_queue):
            self.voice_clients[0].play(
                self.song_queue[0].player, after=self.get_next_song
            )

        if self.remove_song and last_song_file_name is not None:
            try:
                os.remove(os.path.join(last_song_file_name))
            except Exception as e:
                print("cant remove file", last_song_file_name, "\n", "Error:", e)
        else:
            self.remove_song = True

        asyncio.run_coroutine_threadsafe(self.update_song_list(), self.loop)

    async def on_member_join(self, member):
        joinedGuild = member.guild
        if joinedGuild.system_channel is not None:
            await joinedGuild.system_channel.send(
                "สวัสดีเจ้า " + member.mention + " น้าาาาาาา"
            )
        return

    async def on_message(self, message):
        if not self.is_ready():
            return
        fromChannel = message.channel
        if (
            fromChannel.id == self.music_channel_id
            and message.author.id != self.user.id
        ):
            if message.content.startswith("!"):  # song specific cmds
                args = message.content[1:].split()
                cmd = args[0]
                args = args[1:]

                await message.delete(delay=0.2)

                if cmd == "skip":
                    song_no = int(args[0]) - 1
                    if song_no == 0:
                        self.voice_clients[0].stop()
                    else:
                        try:
                            skipping_song_file_name = self.song_queue.pop(
                                song_no
                            ).file_name
                        except IndexError as e:
                            sent = await fromChannel.send(
                                f"{message.author.mention} มันมีถึง {song_no} ที่ไหนเล่า"
                            )
                            await sent.delete(delay=10)
                        try:
                            os.remove(skipping_song_file_name)
                        except Exception as e:
                            print(
                                "cant remove file",
                                skipping_song_file_name,
                                "\n",
                                "Error:",
                                e,
                            )
                        await self.update_song_list()
                elif cmd == "volume":
                    try:
                        args[0] = float(args[0])
                    except:
                        print("input error")
                        return
                    self.volume = args[0]
                    dotenv.set_key(
                        dotenv_path=os.path.join(dirpath, ".env"),
                        key_to_set="VOLUME",
                        value_to_set=str(args[0]),
                    )
                    print(f"volume set to {self.volume}")

            else:  # user requesting song via name
                song_name = message.content
                sender_voicestate = message.author.voice
                await message.delete(delay=0.2)
                if sender_voicestate is None:
                    sent = await fromChannel.send(
                        f"{message.author.mention} ไม่เข้ามาฟังด้วยกันหรอ ;w;"
                    )
                    await sent.delete(delay=15)
                    return
                elif len(self.voice_clients) == 0:
                    await sender_voicestate.channel.connect()
                elif self.voice_clients[0].channel.id != sender_voicestate.channel.id:
                    sent = await fromChannel.send(
                        f"{message.author.mention} เข้ามาอยู่ด้วยกันก่อนมามะ"
                    )
                    await sent.delete(delay=15)
                    return

                # search music
                download = await self.loop.run_in_executor(
                    None, lambda: self.dl_song(song_name)
                )

                if download["download_ok"]:  # play music
                    downloaded_path = os.path.join(
                        download["id"] + "." + download["ext"]
                    )
                    song = Song(
                        discord.FFmpegOpusAudio(downloaded_path),
                        download["id"] + "." + download["ext"],
                        download["title"],
                    )

                    self.song_queue.append(song)

                    if not self.voice_clients[0].is_playing():
                        self.voice_clients[0].play(
                            song.player, after=self.get_next_song
                        )
                    await self.update_song_list()
                else:  # error
                    if download["error_on_search"]:
                        sent = await fromChannel.send(
                            f"{message.author.mention} ที่ขอมา (`{song_name}`) มันเสิร์ชไม่ได้งะ\n`{download['exception']}`"
                        )
                    else:
                        sent = await fromChannel.send(
                            f"{message.author.mention} ที่ขอมา (`{song_name}`)\nเจอเพลง `{download['title']}`\nแต่มันโหลดไม่ได้งะ`{download['exception']}`"
                        )

                    await sent.delete(delay=15)

        elif message.content.startswith("!") and message.author.id != self.user.id:
            args = message.content[1:].split()
            cmd = args[0]
            args = args[1:]
            if cmd == "help":
                if len(args) == 0:
                    em = discord.Embed(
                        title="สิ่งที่เราทำได้ตอนนี้อ่ะนะ :thinking:",
                        description="มีเท่านี้แหละ\nไปสั่งคนทำมาเพิ่มฟีเจอร์เราสิ ;w;",
                        author="Pica, pica!",
                        colour=0xFFE770,
                    )
                    em.add_field(name="!help", value="ก็อันนี้นี่แหละ")
                    em.add_field(
                        name="!ดีมั้ย <คำถาม>/!ดีไหม <คำถาม>",
                        value="เอาไว้ช่วยตัดสินใจอ่ะนะ",
                    )
                    em.add_field(
                        name="!role", value="ช่วยตัดสินใจว่าเล่นตำแหน่งไรดี (RoV)"
                    )
                    em.add_field(name="!ping", value="เช็คปิงบอทเฉย ๆ น่ะ")
                    em.add_field(name="!guessnum", value="เล่นทายเลขขำ ๆ กับน้อนบอท")
                    em.add_field(name="!rps", value="เล่นเป่ายิ้งฉุบขำ ๆ กับน้อนบอท")
                    em.add_field(
                        name="!coolApostrophe",
                        value="ส่งตัว ` ให้ใช้เฉยๆ ไม่มีไร ส่งในแชทส่วนตัวน่ะ",
                    )
                    em.add_field(
                        name="!lobby",
                        value="ตั้งตี้เล่นเกม ตอนนี้มีแค่ rov มีคำสั่งอีกมากมาย ลอง `!lobby help` ดูนะ",
                    )
                    em.add_field(
                        name="!random <เกม>",
                        value="ไม่รู้จะเล่นไรดี ใช้นี่ได้ (ตอนนี้ซัพพอร์ท Valorant เกมเดียว)",
                    )
                    em.add_field(
                        name="!together <activity>",
                        value="สร้างลิงค์ together <activity> จะมี `youtube`, `poker`, `chess`, `betrayal`, `fishing`, `letter-tile`, `word-snack`, `doodle-crew`, `spellcast`, `awkword`, `checkers`",
                    )
                    # ----------------------- add help here --------------------------
                    await fromChannel.send(content=None, embed=em)
                elif args[0] == "admin":
                    em = discord.Embed(
                        title="คำสั่งสำหรับแอดมินจ้า",
                        author="differtail",
                        colour=0xFFE770,
                    )
                    em.add_field(
                        name="!guessnum reset", value="รีเซตเกมทายเลขถ้ามันพัง"
                    )
                    em.add_field(
                        name="!say <ข้อความ>", value="บอทพูด<ข้อความ>ในช่อง system"
                    )
                    em.add_field(name="!react <channel_id> <reaction_id>")
                    em.add_field(name="!reboot", value="รีสาร์ทบอท")

                    # -------------------------add admin commands help here-----------------------
                    await fromChannel.send(content=None, embed=em)

            elif cmd == "ดีมั้ย" or cmd == "ดีไหม":
                if len(args) == 0:
                    await fromChannel.send(message.author.mention + " อะไรเล่า!?")
                    return
                positive_ans = randint(0, 1)
                if positive_ans:
                    responses = [
                        "เอาดิ",
                        "ลุยเลยๆ",
                        "จัดไปอย่าให้เสีย",
                        "เรื่องนี้มันก็แน่อยู่แล้วปะวะ",
                        "ก็ดี๊",
                    ]
                else:
                    responses = [
                        "ไม่ดีกว่า",
                        "อย่าเลยเพื่อน",
                        "ถ้าอยากมีความสุขก็อย่าเถอะ",
                        "ไม่รุดิแต่ฉันว่าไม่",
                        "ม่ายอะ",
                    ]
                await fromChannel.send(message.author.mention + " " + choice(responses))
            elif cmd == "hi":
                responses = [
                    "สวัสดี! ",
                    "สวัสดีจ้า ",
                    "ฮ้ายฮายย~ ",
                    "เห็นโล่วเจ้า ",
                    "ว่างาย ",
                    "Bonjour! ",
                    "안녕 ",
                ]
                await fromChannel.send(
                    choice(responses) + ":wave: " + message.author.mention
                )
            elif cmd == "role":
                responses = [
                    "แครี่ดิวะ",
                    "คนไทยหัวใจแครี่สิดี",
                    "แครี่ที่ดีต้องเป็นคุณ",
                    "ทีมต้องการแครี่!",
                    "โรมมิ่งวิ่งแก้งไปสิ",
                    "โรมไปนะเพื่อน",
                    "ไปซัพแครี่ซะนะ",
                    "ทีมต้องการโรม!",
                    "เมจเก่งไม่ใช่หรอเราอ่ะ",
                    "ไปโยนสกิลใส่เลนกลางเล้ยยยยย",
                    "อย่างงี้ต้องเดินทางสายกลาง",
                    "ทีมต้องการเมจ!",
                    "ไปเก็บตังในป่าซะ",
                    "ป่าน่าจะเหมาะสุดนะจังหวะนี้",
                    "ทีมมันกาก ต้องเล่นป่าไปแบกสิ",
                    "ทีมต้องการป่า!",
                    "ไปเฝ้าป้อมเล่นด้าคให้หน่อยสิ",
                    "จงไปเลนดาร์คซะ",
                    "เป็นแท้งให้ทีมสิดี",
                    "ทีมต้องการแท้ง!",
                ]
                await fromChannel.send(message.author.mention + " " + choice(responses))
            elif cmd == "lobby":
                global lobby, lobbyCreated, lobbyCreator
                if len(args) == 0:
                    await fromChannel.send(
                        message.author.mention + " ถ้าใช้ยังไม่เป็น ลอง !lobby help น้า"
                    )
                elif args[0] == "reset":
                    if not is_admin(message.author, fromChannel):
                        await fromChannel.send(
                            f"{message.author.mention} อันนี้แอดมินใช้เท่านั้นน้าา"
                        )
                    else:
                        lobbyCreator = ""
                        lobbyCreated = False
                        lobby = []
                        await fromChannel.send(
                            f"รีเซตห้องล็อบบี้ตี้เกมตีป้อมแล้วจ้า\nคำสั่งถูกสั่งโดย {message.auther.mention}"
                        )
                elif args[0] == "help":
                    em = discord.Embed(
                        title="!lobby",
                        description="วิธีใช้ `!lobby` นะครับทุกทั่น  :100:\n:rainbow: คำสั่งต่อไปนี้พิมต่อจาก `!lobby` เว้นด้วย 1 เว้นวรรคนะ :rainbow:",
                        author="Pica, pica!",
                        colour=0xF5AD42,
                    )
                    em.add_field(name="help", value="ก็อันนี้นี่แหละ")
                    em.add_field(
                        name="create random",
                        value="สร้างตี้แบบสุ่มตำแหน่งให้ คือบอทจะสุ่มตำแหน่งให้แต่ละคนอ่ะ สร้างได้ทีละห้องนะ!!",
                    )
                    em.add_field(
                        name="join", value="เข้าห้องที่สร้างอยู่ตอนนี้ ถ้ามีอ่ะนะ"
                    )
                    await fromChannel.send(content=None, embed=em)
                elif args[0] == "create":
                    if args[1] == "random":
                        if lobbyCreated:
                            await fromChannel.send(
                                message.author.mention
                                + f" {lobbyCreator} สร้างล็อบบี้ไปแล้วน้า"
                            )
                        else:
                            lobbyCreator = message.author.name
                            lobby.append(message.author.id)
                            lobbyCreated = True
                            await fromChannel.send(
                                "ล็อบบี้ถูกสร้างโดย "
                                + message.author.mention
                                + " เรียบร้อยแน้ว!"
                            )
                elif args[0] == "join":
                    if lobbyCreated:
                        if message.author.id in lobby:
                            await fromChannel.send(
                                message.author.mention
                                + " พี่อยู่ในล็อบบี้อยู่แล้วง่าาา"
                            )
                            return
                        lobby.append(message.author.id)
                        msg = ""
                        for peopleInd in range(len(lobby)):
                            msg += f"{peopleInd+1} - {discord.Client.get_user(self,lobby[peopleInd]).mention}\n"
                        await fromChannel.send(
                            "เพิ่ม "
                            + message.author.mention
                            + " เข้าล็อบบี้แบ้วฮับ!\nตอนนี้สมาชิกตี้มี:\n"
                            + msg
                        )
                        if len(lobby) == 5:
                            shuffle(lobby)
                            await fromChannel.send(
                                "ล็อบบี้เต็มละน้าา ผลสุ่มก็คื๊ออออ:\n"
                                + discord.Client.get_user(self, lobby[0]).mention
                                + " ไปเลนดาร์คน้า\n"
                                + discord.Client.get_user(self, lobby[1]).mention
                                + " ฟามป่าเลยจ้า\n"
                                + discord.Client.get_user(self, lobby[2]).mention
                                + " ไปโยนสกิลในเลนกลางน้า\n"
                                + discord.Client.get_user(self, lobby[3]).mention
                                + " แบกทีมด้วยแครี่ในเลนมังกรไปเลยยยย\n"
                                + discord.Client.get_user(self, lobby[4]).mention
                                + " นายจะได้เป็นโรมที่ดีที่สุดในทีม!\nEnjoy~"
                            )
                            lobby.clear()
                            lobbyCreated = False
                    else:
                        await fromChannel.send(
                            message.author.mention
                            + " ล็อบบี้ยังเคยไม่เคยสร้างง่า ลอง !lobby create random ดูเสะ"
                        )
                return
            elif cmd == "ping":
                await fromChannel.send(
                    message.author.mention
                    + " ป๊อง! "
                    + str(round(self.latency * 1000))
                    + " ms"
                )
            elif cmd == "bye":
                responses = [
                    "บ้ายบายยยย ",
                    "ลาก่อยยยย ",
                    "แจปืนนนน ",
                    "ไว้เจอกันค้าบบ ",
                    "โชคดีน้าาา ",
                ]
                await fromChannel.send(
                    choice(responses) + ":wave: " + message.author.mention
                )
            elif cmd == "guessnum":
                global isGuessnumPlaying, guessnumPlayer, guessnumPlayerID, guessnumNumber
                if args and args[0] == "reset":
                    if not is_admin(message.author, fromChannel):
                        await fromChannel.send(
                            f"{message.author.mention} อันนี้แอดมินใช้เท่านั้นน้าา"
                        )
                        return
                    else:
                        isGuessnumPlaying = False
                        guessnumPlayer = ""
                        guessnumPlayerID = ""
                        guessnumNumber = randint(1, 1024)
                        await fromChannel.send(f"รีเซ็ตเกมทายเลขละจ้า")
                        return
                elif args and args[0] == "stop":
                    if message.author.id != guessnumPlayerID:
                        await fromChannel.send(
                            f"{message.author.mention} อย่าไปหยุดความสนุกของ {guessnumPlayer} เขาสิแหม่"
                        )
                    else:
                        await fromChannel.send(
                            f"{message.author.mention} เลิกเล่นแล้วอ่อโด่ว เลขเมื่อกี้คือ **{guessnumNumber}** น่ะ\n"
                            + "เดี๋ยวรีเซ็ตเกมให้ละกันนะ"
                        )
                        isGuessnumPlaying = False
                        guessnumPlayer = ""
                        guessnumPlayerID = ""
                        guessnumNumber = randint(1, 1024)
                        return
                elif isGuessnumPlaying:
                    if message.author.id != guessnumPlayerID:
                        await fromChannel.send(
                            f"{message.author.mention} กำลังเล่นกับ {guessnumPlayer} อยู่ง่าาาาา"
                        )
                    else:
                        await fromChannel.send(
                            f"{message.author.mention} ทายมาสิครับ รออะไร!?"
                        )
                elif not isGuessnumPlaying:
                    isGuessnumPlaying = True
                    guessnumPlayer = message.author.name
                    guessnumPlayerID = message.author.id
                    await fromChannel.send(
                        f"**ก็มาดิครับ** {message.author.mention} :exclamation:\n"
                        + ":question: **วิธีเล่น** :question:\n"
                        + "เราจะให้นายทายเลขที่เราคิดไว้ มีค่า `1` ถึง `1024`\n"
                        + "พิมพ์ว่า `!guess <ตัวเลข>` - ทายว่าใช่เลขนี้มั้ย\n"
                        + "แล้วเราจะบอกว่าใช่, น้อยกว่า, หรือมากกว่าเลขของเรา"
                    )
            elif cmd == "guess":
                if not isGuessnumPlaying or message.author.id != guessnumPlayerID:
                    await fromChannel.send(
                        f"อยากเล่นหรอครับคุณ {message.author.mention} พิม `!guessnum` ก่อนนะครับ ไม่ก็รอคนอื่นเล่นจบก่อนน้า"
                    )
                else:
                    if len(args) == 0:
                        await fromChannel.send(
                            f"ทายมาสิครับ รออยู่นะ! {message.author.mention}"
                        )
                    elif args[0] == "<ตัวเลข>":
                        await fromChannel.send(
                            f"{message.author.mention} ตวงติงนักน้าาาาาา"
                        )
                    else:
                        try:
                            thisnum = int(args[0])
                        except ValueError:
                            await fromChannel.send(
                                f"{message.author.mention} ขอเป็นจำนวนเต็มคับพรี่"
                            )
                        else:
                            global guessnumPlayCount
                            guessnumPlayCount += 1
                            if thisnum == guessnumNumber:
                                responses = [
                                    "เก่งสุด ๆ ไปเลยนะ",
                                    "ว้าวซ่า",
                                    "โห้ เก่งนี่หว่า",
                                ]
                                isGuessnumPlaying = False
                                guessnumNumber = randint(1, 1024)
                                await fromChannel.send(
                                    f"{message.author.mention} {choice(responses)} เลขของผมคือ **{thisnum}** ถูกต้องนะครับ\n"
                                    + f"ทายถูกภายใน {guessnumPlayCount} ครั้ง เก่งมากๆ :clap:"
                                )
                            elif thisnum > guessnumNumber:
                                responses = [
                                    "เยอะเกิน ไอหนู",
                                    "เยอะไปนะครับ",
                                    "มากไปนะ",
                                    "เยอะเกินครับ ลองใหม่ครับ",
                                ]
                                await fromChannel.send(
                                    f"{message.author.mention} {thisnum} {choice(responses)}"
                                )
                            elif thisnum < guessnumNumber:
                                responses = [
                                    "น้อยไป ไอหนู",
                                    "น้อยไปนะครับ",
                                    "น้อยไปนะ",
                                    "น้อยเกินครับ ลองใหม่ครับ",
                                ]
                                await fromChannel.send(
                                    f"{message.author.mention} {thisnum} {choice(responses)}"
                                )
            elif cmd == "rps":
                if len(args) == 0:
                    await fromChannel.send(
                        f"อ้าวววว {message.author.mention} เจอได้นะครับบบบ :hammer: :scissors: :roll_of_paper:\n\
                        พิม `!rps <ค้อน/กรรไกร/กระดาษ>` มาเป่ายิ้งฉุบกับเราได้เลย!\n\
                        เราไม่โกงแน่นอน สาบานได้นะ!"
                    )
                else:
                    realStuff = {0: ":hammer:", 1: ":scissors:", 2: ":roll_of_paper:"}
                    playerState = -1
                    if args[0] == "ค้อน":
                        playerState = 0
                    elif args[0] == " กรรไกร":
                        playerState = 1
                    elif args[0] == " กระดาษ":
                        playerState = 2
                    if playerState == -1:
                        await fromChannel.send(
                            f"{message.author.mention} เอาซักอย่างครับ!! `ค้อน`, `กรรไกร` ไม่ก็ `กระดาษ`"
                        )
                        return
                    botState = randint(0, 2)
                    text = f"{message.author.mention}\n{realStuff[playerState]}  :vs:  {realStuff[botState]} :exclamation:\n"
                    if playerState == botState:
                        responses = [
                            "เสมอครับ! เอาใหม่ซักตามั้ยล่าาา",
                            "ฮึ่ยย่ะ! เสมอครับ",
                            "ว่าว เรียกได้ว่าเราเก่งเท่ากันได้มั้ยน้า",
                        ]
                        text += choice(responses)
                    elif playerState == botState + 1 or (
                        playerState == 0 and botState == 2
                    ):
                        responses = [
                            "ตานี้ชั้นขอละกัน! ฮ่าๆๆ",
                            "เย่ เลาชนะน้า",
                            "เย่ เลาชนะ ไม่เป็นไรน้าา",
                        ]
                        text += choice(responses)
                    elif playerState + 1 == botState or (
                        playerState == 2 and botState == 0
                    ):
                        responses = [
                            "โถ่เอ้ย! ฝากไว้ก่อนเถอะ...",
                            "ว้าว เก่งจัด ๆ เลยนะนายน่ะ",
                            "ง่าาา เก่งไป รับมั่ยดั้ย",
                        ]
                        text += choice(responses)
                    await fromChannel.send(text)
            elif cmd == "coolApostrophe":
                await message.author.send(f"รับไปซะ อะโฟสโตฟี่เท่มากๆ `")
            elif cmd == "random" or cmd == "สุ่มตัว":
                all_chars = None
                if args[0].lower() in {
                    "valo",
                    "วาโล",
                    "valorant",
                    "วาโลแร้น",
                    "วาโลแรนท์",
                }:
                    all_chars = [  # set to valorant chars
                        "Brimstone",
                        "Viper",
                        "Omen",
                        "Killjoy",
                        "Cypher",
                        "Sova",
                        "Sage",
                        "Phoenix",
                        "Jett",
                        "Reyna",
                        "Raze",
                        "Breach",
                        "Skye",
                        "Yoru",
                        "Astra",
                        "Kay/O",
                        "Chamber",
                    ]
                if all_chars is not None:
                    await fromChannel.send(
                        f"{message.author.mention} {choice(all_chars)} ไป"
                    )
                else:
                    await fromChannel.send(
                        'f"{message.author.mention} เกมไรอะ ไม่รุจัก'
                    )
            elif cmd == "together":
                if not has_role(message.author, "จุดรวมพล"):
                    await fromChannel.send(
                        f"{message.author.mention} อนุญาตให้ผู้ที่มีโรล `จุดรวมพล` สร้างห้องทูเก้ตเต้อได้เท่านั้นนะจ๊ะ"
                    )
                    return

                if fromChannel.name != "จุดรวมพล":
                    await fromChannel.send(
                        f"{message.author.mention} กรุณาสร้างห้องทูเก้ตเต้อในห้องจุดรวมพลนะจ้ะ"
                    )
                    return

                if message.author.voice:
                    if args and args[0] in [
                        "youtube",
                        "poker",
                        "chess",
                        "betrayal",
                        "fishing",
                        "letter-tile",
                        "word-snack",
                        "doodle-crew",
                        "spellcast",
                        "awkword",
                        "checkers",
                    ]:
                        link = await self.discord_together.create_link(
                            message.author.voice.channel.id,
                            args[0],
                            max_age=3600,
                            max_uses=1,
                        )
                        await fromChannel.send(
                            f"ลิ้งเปิดห้องตรงนี้เลยจ้า คนแรกคลิกที่ลิงค์ก่อนนะ คนอื่นถึงจะกด Play ได้ แต่ก็คลิกลิงค์ได้เหมือนกัน\n{link}"
                        )
                    else:
                        await fromChannel.send(  # send how to use
                            f"{message.author.mention} พิมงี้นะจ๊ะ `!together <activity>` <activity> จะมี\n\
:white_small_square:  `youtube` **->** Youtube watch party :arrow_forward:\n\
:white_small_square:  `poker` **->** Poker night :black_joker:\n\
:white_small_square:  `chess` **->** Chess in the Park\n\
:white_small_square:  `betrayal` **->** Betrayal.io\n\
:white_small_square:  `fishing` **->** Fishington.io\n\
:white_small_square:  `letter-tile` **->** Letter Tile\n\
:white_small_square:  `word-snack` **->** Word Snack\n\
:white_small_square:  `doodle-crew` **->** Doodle Crew\n\
:white_small_square:  `spellcast` **->** SpellCast\n\
:white_small_square:  `awkword` **->** Awkword\n\
:white_small_square:  `checkers` **->** Checkers in the Park\n\
ถ้าจะถามว่านอกจากยูทูปกับโป้กเก้อคือไร บอกเลยว่า ไม่รู้"
                        )
                else:
                    await fromChannel.send(
                        f"{message.author.mention} เข้าห้องเสียงซักห้องก่อนน้า"
                    )
            # ------------------- admin commands --------------------------
            elif cmd == "say":
                args = message.content.split(" ", 2)[1:]
                if (
                    not is_admin(message.author, fromChannel)
                    or message.guild.system_channel is None
                ):
                    return
                channel_to_send = message.guild.get_channel(int(args[0]))
                messageToSend = args[1]
                messageToSend = messageToSend.replace("<!code!>", "```")
                messageToSend = messageToSend.replace("<!strikethrough!>", "~~")
                await channel_to_send.send(messageToSend)
            elif cmd == "react":
                if not is_admin(message.author, fromChannel):
                    return
                channel_to_react = message.guild.get_channel(int(args[0]))
                msg_to_react = channel_to_react.get_partial_message(int(args[1]))
                try:
                    await msg_to_react.add_reaction(args[2])
                except discord.Forbidden:
                    print(f"reaction {args[2]} to guild {message.guild} was forbidden!")
                except:
                    print(
                        f"reaction {args[2]} to guild {message.guild} on channel {channel_to_react} was not successful (maybe emoji not found?)"
                    )
            elif cmd == "reboot":
                if not is_admin(message.author, fromChannel):
                    await fromChannel.send(
                        f"{message.author.mention} อันนี้แอดมินใช้เท่านั้นน้าา"
                    )
                else:
                    do_reboot()

        # --------------------- voice commands ------------------------

        return

    async def on_raw_reaction_add(self, reactionAdded):
        if reactionAdded.user_id == BOT_ID:
            return  # dont do shit if bot itself added that

        if reactionAdded.message_id == selfRoleMsgID:
            role_to_add = discord.Object(-1)  # empty object for now
            if reactionAdded.emoji.name in self_role_emojis:
                role_to_add.id = self_role_ids[reactionAdded.emoji.name]
            if role_to_add.id != -1:
                await reactionAdded.member.add_roles(role_to_add)  # add the role
                print(
                    f"{reactionAdded.member.name} reacted {reactionAdded.emoji.name} for role {role_to_add.id}"
                )
            else:
                this_message = self.get_channel(
                    reactionAdded.channel_id
                ).get_partial_message(selfRoleMsgID)
                await this_message.remove_reaction(
                    reactionAdded.emoji, discord.Object(reactionAdded.user_id)
                )  # not defined emote, remove that reaction

        elif reactionAdded.message_id == self.music_message_id:
            if reactionAdded.emoji.name == "⏮️":
                if len(self.voice_clients) > 0:
                    playing = self.song_queue[0].copy(self.volume)
                    self.song_queue.insert(1, playing)
                    self.remove_song = False
                    self.voice_clients[0].stop()
                else:
                    print("not in a voice channel")
            elif reactionAdded.emoji.name == "⏯️":
                if len(self.voice_clients) == 0:
                    await reactionAdded.member.voice.channel.connect()
                if len(self.voice_clients) > 0:
                    if self.voice_clients[0].is_playing():
                        self.voice_clients[0].pause()
                        await self.update_song_list()
                    elif self.voice_clients[0].is_paused():
                        self.voice_clients[0].resume()
                        await self.update_song_list()
                    else:
                        print("not playing nor paused")
            elif reactionAdded.emoji.name == "⏭️":
                if len(self.voice_clients) > 0:
                    if (
                        self.voice_clients[0].is_playing()
                        or self.voice_clients[0].is_paused()
                    ):
                        print(f"Skipping song {self.song_queue[0].song_title}!")
                        self.voice_clients[0].stop()
                else:
                    print("not in a voice channel")
            elif reactionAdded.emoji.name == "📴":
                print("exit voice ch cmd issued")
                if len(self.voice_clients) > 0:
                    self.remove_all_songs()
                    await self.update_song_list()
                    await self.voice_clients[0].disconnect()

            elif reactionAdded.emoji.name == "💱":
                if self.voice_clients:
                    if reactionAdded.member.voice is not None:
                        await self.voice_clients[0].move_to(
                            reactionAdded.member.voice.channel
                        )
                elif reactionAdded.member.voice is not None:
                    await reactionAdded.member.voice.channel.connect()
            this_message = self.get_channel(
                reactionAdded.channel_id
            ).get_partial_message(reactionAdded.message_id)
            await this_message.remove_reaction(
                reactionAdded.emoji, discord.Object(reactionAdded.user_id)
            )

        return

    async def on_raw_reaction_remove(self, reactionRemoved):
        if reactionRemoved.message_id == selfRoleMsgID:
            role_to_remove = discord.Object(-1)  # empty object for now
            if reactionRemoved.emoji.name in self_role_emojis:
                role_to_remove.id = self_role_ids[reactionRemoved.emoji.name]

            if role_to_remove.id != -1:
                this_member = self.get_guild(my_server_id).get_member(
                    reactionRemoved.user_id
                )
                if this_member is not None:
                    await this_member.remove_roles(role_to_remove)  # remove the role
                    print(
                        f"{this_member.name} un-reacted {reactionRemoved.emoji.name} for role {role_to_remove.id}"
                    )

        return

    async def on_member_update(self, memBef, memAft):
        if memBef.id == MY_ID:
            if memAft.status == discord.Status.idle:
                await self.change_presence(
                    status=discord.Status.idle,
                    activity=discord.Activity(
                        name="@Differential sleep", type=discord.ActivityType.watching
                    ),
                )
            elif memAft.status == discord.Status.dnd:
                await self.change_presence(
                    status=discord.Status.dnd,
                    activity=discord.Activity(
                        name="@Differential being busy",
                        type=discord.ActivityType.watching,
                    ),
                )
            else:
                await self.change_presence(
                    status=discord.Status.online,
                    activity=discord.Game(name="with @Differential"),
                )
        return

    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return

        def bot_count(members):
            count = 0
            for _member in members:
                if _member.bot:
                    count += 1
            return count

        if after.channel and after.channel != before.channel:  # user joins voice
            print(member.name, "joined", after.channel.name)
            if (
                len(after.channel.members) - bot_count(after.channel.members) == 1
            ):  # first person to join voice
                print("first person to join this voice, creating role and text channel")
                self.temp_roles[after.channel.id] = await member.guild.create_role(
                    name=f"ระเบิดเวลา-{after.channel.name}",
                    reason=f"temp role for {after.channel.name}",
                )
                overwrite_perms = {
                    member.guild.default_role: discord.PermissionOverwrite(
                        send_messages=False, read_messages=False
                    ),
                    self.temp_roles[after.channel.id]: discord.PermissionOverwrite(
                        send_messages=True, read_messages=True
                    ),
                }
                self.temp_textch[
                    after.channel.id
                ] = await member.guild.create_text_channel(
                    f"ระเบิดเวลา-{after.channel.name}",
                    overwrites=overwrite_perms,
                    category=after.channel.category,
                    position=0,
                    topic="ห้องแชทชั่วคราวสำหรับคุยเรื่องลับลับลับลับ **แชทไม่เซฟนะจ้ะ**",
                )
            try:
                await member.add_roles(self.temp_roles[after.channel.id])
            except KeyError:
                print(
                    "KeyError when adding role to member\n->",
                    self.temp_roles,
                    after.channel.id,
                )
            except Exception as e:
                print("Error while adding temp role\n-> " + e)

        if before.channel and before.channel != after.channel:  # user leaves voice
            print(member.name, "left", before.channel.name)
            if before.channel.id in self.temp_roles:
                if self.temp_roles[before.channel.id] in member.roles:
                    await member.remove_roles(self.temp_roles[before.channel.id])
                else:
                    print("member dont have role for", before.channel.name, "???")
            if (
                len(before.channel.members) - bot_count(before.channel.members) == 0
            ):  # last person to leave voice
                print("no more ppl in", before.channel.name)
                try:
                    await self.temp_textch.pop(before.channel.id).delete(
                        reason="temp textch delete"
                    )
                    await self.temp_roles.pop(before.channel.id).delete(
                        reason="temp role delete"
                    )
                except KeyError:
                    print(
                        f"{self.temp_textch=}\n{self.temp_roles=}\n{before.channel.id}"
                    )
                except Exception as e:
                    print("Error while deleting temp role/textch\n-> " + e)
            if (
                len(before.channel.members) == bot_count(before.channel.members) == 1
                and self.voice_clients
                and self.voice_clients[0].channel == before.channel
                and not self.voice_clients[0].is_playing()
            ):
                self.remove_all_songs()
                await self.update_song_list()
                await self.voice_clients[0].disconnect()


if os.cpu_count() == 12:
    print("me!")
new_intent = discord.Intents().default()
new_intent.members = True
new_intent.voice_states = True
client = MyClient(intents=new_intent)
client.run(TOKEN)

print("Client stopped running")

