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

bot = commands.Bot(
    command_prefix="$",
    case_insensitive=True,
    intents=intents
)

RCON_PATH = os.getenv("RCON_PATH")
DISCORD_POLLING_INTERVAL = int(os.getenv("DISCORD_POLLING_INTERVAL"))

SERVER_STATUS_RUNNING = "running"
SERVER_STATUS_PENDING = "pending"
SERVER_STATUS_STOPPED = "stopped"

def get_server_status():
    proc = subprocess.run("python " + RCON_PATH + " info", shell=True, stdout=PIPE, stderr=PIPE, text=True)

    if proc.returncode == 0:
        return SERVER_STATUS_RUNNING

    proc = subprocess.run("pgrep -f -l -c PalServer-Linux", shell=True, stdout=PIPE, stderr=PIPE, text=True)

    if int(proc.stdout.strip()) >= 2:
        return SERVER_STATUS_PENDING

    return SERVER_STATUS_STOPPED

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

async def sleep(n):
    await asyncio.sleep(n)

async def update_status(discord_text = None, discord_status = None):

    status = get_server_status()

    if discord_text == None:
        if status == SERVER_STATUS_RUNNING:
            discord_text = "稼働中"
        elif status == SERVER_STATUS_PENDING:
            discord_text = "起動中"
        else:
            discord_text = "停止中"
    
    if discord_status == None:
        if status == SERVER_STATUS_RUNNING:
            discord_status = discord.Status.online
        elif status == SERVER_STATUS_PENDING:
            discord_status = discord.Status.idle
        else:
            discord_status = discord.Status.dnd
    
    discord_text += "/swap使用量: " + get_swap_usage() 

    await bot.change_presence(status=discord_status, activity=discord.CustomActivity(name=discord_text))

@bot.event
async def on_ready():
    print("on_ready")

    while True:
        await update_status()
        await sleep(DISCORD_POLLING_INTERVAL)

@bot.event
async def on_message(message: discord.Message):
    print("on_message: " + message.content)

    if message.author.bot:
        return

    if message.channel.name != os.getenv("DISCORD_CHANNEL_NAME"):
        return

    command = message.content.strip()
    match command:
        case "!free":
            proc = free()
            await message.reply(proc.stdout + proc.stderr)

        case "!status":
            status = get_server_status()
            if status == SERVER_STATUS_RUNNING:
                await message.reply("server is running")
            elif status == SERVER_STATUS_PENDING:
                await message.reply("server is pending")
            else:
                await message.reply("server is stopping")

        case "!start":
            if get_server_status() != SERVER_STATUS_STOPPED:
                await message.reply("server is running")
            else:
                proc = start()
                if proc.returncode == 0:
                    await message.reply("startup signal sent")
                    while get_server_status() != SERVER_STATUS_RUNNING:
                        await sleep(5)
                    await message.reply("startup successfully")
                else:
                    await message.reply("start failure: " + proc.stdout + " " + proc.stderr)

        case "!stop":
            if get_server_status() != SERVER_STATUS_RUNNING:
                await message.reply("server is stopped")
            else:
                proc = stop()
                await message.reply(proc.stdout + proc.stderr)

                if proc.returncode == 0:
                    while get_server_status() != SERVER_STATUS_STOPPED:
                        await sleep(5)
                    await message.reply("shutdown completed")
                
        case "!update":
            if get_server_status() != SERVER_STATUS_STOPPED:
                await message.reply("server is running")
            else:
                proc = update()
                await message.reply(proc.stdout + proc.stderr)

        case "!players":
            if get_server_status() != SERVER_STATUS_RUNNING:
                await message.reply("server is stopped")
            else:
                proc = show_players()
                await message.reply(proc.stdout + proc.stderr)

        case "!help":
            await message.reply("Usage: !{free|status|start|stop|players|help|update}")
            
        case _:
            if command[0] == "!":
                await message.reply("unknown command: " + command)
            

bot.run(os.getenv("DISCORD_TOKEN"))
