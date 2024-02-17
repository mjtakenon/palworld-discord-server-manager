from discord.ext import commands
import discord

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
PALWORLD_INSTALL_DIR = os.getenv("PALWORLD_INSTALL_DIR")
SERVER_PUBLIC_IP = os.getenv("SERVER_PUBLIC_IP")
SERVER_PUBLIC_PORT = os.getenv("SERVER_PUBLIC_PORT")
DISCORD_CHANNEL_NAME = os.getenv("DISCORD_CHANNEL_NAME")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
STEAMCMD_PATH = os.getenv("STEAMCMD_PATH")

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
    return subprocess.run("screen -AmdS palworld /bin/bash " + PALWORLD_INSTALL_DIR + "/PalServer.sh -useperfthreads -NoAsyncLoadingThread -UseMultithreadForDS EpicApp=PalServer -publicip=" + SERVER_PUBLIC_IP + " -publicport=" + SERVER_PUBLIC_PORT, shell=True, stdout=PIPE, stderr=PIPE, text=True)
    
def stop():
    return subprocess.run("python " + RCON_PATH + " shutdown", shell=True, stdout=PIPE, stderr=PIPE, text=True)

def show_players():
    return subprocess.run("python " + RCON_PATH + " showplayers", shell=True, stdout=PIPE, stderr=PIPE, text=True)
    
def update():
    return subprocess.run(STEAMCMD_PATH + " +login anonymous +force_install_dir " + PALWORLD_INSTALL_DIR + " +app_update 2394010 validate +quit", shell=True, stdout=PIPE, stderr=PIPE, text=True)

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

    if message.channel.name != DISCORD_CHANNEL_NAME:
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
                        await update_status()
                        await sleep(10)
                    await message.reply("startup successfully")
                    await update_status()
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
                        await update_status(discord_text="停止準備中", discord_status=discord.Status.idle)
                        await sleep(10)
                    await message.reply("shutdown completed")
                    await update_status()
                
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
            

bot.run(DISCORD_TOKEN)
