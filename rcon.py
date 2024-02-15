#!/home/mjtak/.pyenv/shims/python

import mcrcon
import sys
import os
from dotenv import load_dotenv

load_dotenv()

server_address = os.getenv("SERVER_HOST")
server_pass = os.getenv("SERVER_PASSWORD")
server_port = int(os.getenv("SERVER_PORT"))

args = sys.argv

if len(args) <= 1:
    print("usage: ./rcon.py [command]")

with mcrcon.MCRcon(server_address, server_pass, server_port) as mcr:
    print(mcr.command(args[1]))
