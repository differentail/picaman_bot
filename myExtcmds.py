import os
import discord
import time
from dotenv import load_dotenv
from random import randint, shuffle

def choose(content):
    return content[randint(0,len(content)-1)]


def isAdmin(messageSender):
    isAdminbool = False
    if(hasattr(messageSender, 'roles')):
       for role in messageSender.roles:
          if(str(role) == 'สิทธิ์แอดมินละกัน'):
              isAdminbool = True
              break
    return isAdminbool

