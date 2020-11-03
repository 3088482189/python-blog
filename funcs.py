class Map(dict):
    __setattr__=dict.__setitem__
    __getattr__=dict.get
    __delattr__=dict.__delitem__
    def has(self,k):
        return self.k!=None

def turn(x):
    if type(x)==dict:
        res=Map()
        for k,v in x.items():
            if v!=None:res[k]=turn(v)
        return res
    elif isinstance(x,list):
        return [turn(i) for i in x]
    else:return x

def MP(*args,**kwargs):
    res=Map()
    for d in args:
        if type(d)==dict:
            for k,v in d.items():
                if v!=None:res[k]=turn(v)
    if kwargs:
        for k,v in kwargs.items():
            if v!=None:res[k]=turn(v)
    return res

from datetime import datetime
from pathlib import Path
import shutil,re,yaml,pypinyin

try:ymloader=yaml.CLoader
except:ymloader=yaml.SafeLoader
lyml=lambda s:yaml.load(s,Loader=ymloader)
dyml=lambda x:yaml.dump(x,allow_unicode=True)
def rd(path):
    if isinstance(path,str):return open(path,encoding='utf-8').read()
    else:return Path(path).open(encoding='utf-8').read()
def cp(src,dst):
    if src.is_dir():
        if dst.exists():shutil.rmtree(dst)
        shutil.copytree(src,dst)
    else:shutil.copyfile(src,dst)
def del_none(a):
    if not isinstance(a,dict):return {}
    for x in list(a.keys()):
        if a.get(x)==None:a.pop(x)
    return a
def str2date(s):
    a=re.split(r'[- :]',s.strip())
    a.extend(['0']*6)
    return datetime(int(a[0]),int(a[1]),int(a[2]),int(a[3]),int(a[4]),int(a[5]))

def toPinyin(word):
    res=''
    for i in pypinyin.pinyin(word,style=pypinyin.NORMAL):
        res+=''.join(i)+'-'
    return res[0:len(res)-1].replace(' ','-')