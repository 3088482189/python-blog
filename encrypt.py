# -*- coding:utf-8 -*-
import base64
from Crypto.Cipher import AES

def pad(data):
    tot=len(data.encode('utf-8'))
    add=16-(tot%16)
    return data+(chr(add)*add)
def unpad(data):
    return data[0:-ord(data[-1])]
def encrypt(data,passwd):
    while len(passwd)%16:passwd+='\0'
    res=AES.new(passwd.encode("utf8"),AES.MODE_ECB).encrypt(pad(data).encode("utf8"))
    msg=str(base64.b64encode(res),encoding="utf8")
    return msg
