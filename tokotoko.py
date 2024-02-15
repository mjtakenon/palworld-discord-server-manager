#!/home/mjtak/.pyenv/shims/python

from discord.ext import commands
from discord import app_commands
import discord
import time

import subprocess
from subprocess import PIPE

import asyncio

import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot( # Bot
    command_prefix="$",
    case_insensitive=True,
    intents=intents
)

RCON_PATH = os.getenv("RCON_PATH")
POLLING_INTERVAL = os.getenv("DISCORD_POLLING_INTERVAL")

def is_running():
    proc = subprocess.run("pgrep -f -l -c PalServer-Linux", shell=True, stdout=PIPE, stderr=PIPE, text=True)
    return int(proc.stdout.strip()) >= 2

def free():
    return subprocess.run("free -h", shell=True, stdout=PIPE, stderr=PIPE, text=True)

def start():
    return subprocess.run("screen -AmdS palworld /bin/bash /opt/steam/PalWorld/PalServer.sh -useperfthreads -NoAsyncLoadingThread -UseMultithreadForDS EpicApp=PalServer -publicip=116.80.59.136 -publicport=8211", shell=True, stdout=PIPE, stderr=PIPE, text=True)
    
def stop():
    return subprocess.run("python " + RCON_PATH + " shutdown", shell=True, stdout=PIPE, stderr=PIPE, text=True)

def show_players():
    return subprocess.run("python " + RCON_PATH + " showplayers", shell=True, stdout=PIPE, stderr=PIPE, text=True)
    
def update():
    return subprocess.run("/usr/games/steamcmd +login anonymous +force_install_dir /opt/steam/PalWorld +app_update 2394010 validate +quit", shell=True, stdout=PIPE, stderr=PIPE, text=True)

def get_swap_usage():
    proc = subprocess.run("free -h | grep Swap: | awk '{print $3}'", shell=True, stdout=PIPE, stderr=PIPE, text=True)
    return proc.stdout.strip()

async def timer():
    text = "停止中/"
    status = discord.Status.dnd
    if is_running():
        text = "起動中/"
        status = discord.Status.online
    text += "swap使用量: " + get_swap_usage() 
    await bot.change_presence(status=status, activity=discord.CustomActivity(name=text))
    await asyncio.sleep(POLLING_INTERVAL)
    
@bot.event
async def on_ready():
    print("Bot is ready!")
    #await bot.change_presence(activity=discord.CustomActivity(name="!helpで使い方表示"))

    while True:
        await timer()
    #loop = asyncio.get_event_loop()
    #loop.call_later(10, lambda l: l.stop(), loop)
    #loop.call_soon(timer, loop)

    #loop.run_forever()

@bot.event
async def on_message(message: discord.Message):

    if message.author.bot:
        return

    if message.channel.name != "🎮server-controls":
        return

    command = message.content.strip()
    match command:
        case "!free":
            proc = free()
            await message.reply(proc.stdout + proc.stderr)

        case "!status":
            if is_running():
                await message.reply("server is running")
            else:
                await message.reply("server is stopping")

        case "!start":
            if is_running():
                await message.reply("server is running")
            else:
                proc = start()
                print(proc)
                if proc.stdout.strip() == "" and proc.stderr.strip() == "":
                    await message.reply("start successfully")
                else:
                    await message.reply("start failure: " + proc.stderr)
                    
        case "!stop":
            if not is_running():
                await message.reply("server is stopping")
            else:
                proc = stop()
                await message.reply(proc.stdout + proc.stderr)
                # todo: send message after shutdown

                while is_running():
                    time.sleep(5)

                await message.reply("shutdown completed")
                
        case "!update":
            if is_running():
                await message.reply("server is running")
            else:
                proc = update()
                await message.reply(proc.stdout + proc.stderr)
                
        case "!players":
            if not is_running():
                await message.reply("server is stopping")
            else:
                proc = show_players()
                await message.reply(proc.stdout + proc.stderr)
                
        case "!help":
            await message.reply("Usage: !{free|status|start|stop|players|help|update}")
            
        case _:
            await message.reply("unknown command: " + command)

bot.run(os.getenv("DISCORD_TOKEN"))
