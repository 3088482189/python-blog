#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os,sys,time,shutil,re,json,math,socket,threading
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse,unquote
from multiprocessing import Process
import cmd,mistune,md_math

def install_dependencies():
    print('未安装依赖,正在安装')
    requirements=['pyyaml','jinja2','pycryptodome','pypinyin','requests']
    os.system('pip3 install %s -i https://pypi.tuna.tsinghua.edu.cn/simple'%' '.join(requirements))
try:
    import yaml,pypinyin,requests
    from jinja2 import Environment,FileSystemLoader,Template
    from encrypt import encrypt
except:
    install_dependencies()
    import yaml,pypinyin,requests
    from jinja2 import Environment,FileSystemLoader,Template
    from encrypt import encrypt

def del_none(a):
    if not isinstance(a,dict):return {}
    for x in list(a.keys()):
        if a.get(x)==None:a.pop(x)
    return a
def str2date(s):
    a=re.split(r'[- :]',s.strip())
    a.extend(['0']*6)
    return datetime(int(a[0]),int(a[1]),int(a[2]),int(a[3]),int(a[4]),int(a[5]))
def geninfo(file,is_post=0,is_page=0):
    data=file.open(encoding='utf-8').read().split('---\n')
    meta=yaml.load(data[1],Loader=yamloader)
    content=''.join(data[2:])
    preview=content[0:min(len(content),config['preview_len'])]
    if '<!-- more -->' in content:
        preview=content.split('<!-- more -->',1)[0]
    name=file.stem
    x={**{
        'id':None,
        'assets':file.parent/file.stem,
        'addr':name+'/','link':rt+name+'/',
        'title':name,
        'date':datetime.fromtimestamp(int(os.stat(file).st_mtime)),
        'author':config['author'],
        'tags':[],'categories':[],
        'top':0,
        'content':content,'preview':preview,
        'pre':None,'nxt':None,
    },**t_setting['defaut_front'],**del_none(meta)}
    if isinstance(x['date'],str):x['date']=str2date(x['date'])
    if is_post:
        if config['article_address']=='pinyin':x['addr']='posts/%s/'%topinyin(name)
        elif config['article_address']=='origin':x['addr']='posts/%s/'%name

        if 'permalink' in x:x['addr']='posts/%s/'%x['permalink']
        x['link']=rt+x['addr']

        if not 'layout' in x:x['layout']='post'
    if is_page and not 'layout' in x:x['layout']='page'
    return x
def topinyin(word):
    res=''
    for i in pypinyin.pinyin(word,style=pypinyin.NORMAL):
        res+=''.join(i)+'-'
    return res[0:len(res)-1].replace(' ','-')
def gen_index(path,a,ext={}):
    num=config['page_articles']
    tot=len(a)
    TOT=math.ceil(tot/num)
    res=[]
    for now,i in enumerate(range(0,tot,num),1):
        nodes=a[i:i+num]
        addr=path if now==1 else path+'page/%d/'%now
        res.append({**{
            'id':now,
            'addr':addr,'link':rt+addr,
            'path':path,
            'title':path,
            'nodes':nodes,
            'total':tot,'TOTAL':TOT,
            'pre':None,'nxt':None,
        },**ext})
    for id,x in enumerate(res):
        x['pre']=res[id-1]
        x['nxt']=res[(id+1)%TOT]
    return res
def read(path,is_post=0,is_page=0):
    return [geninfo(i,is_post,is_page) for i in Path(path).glob('*.md')]
def read_all():
    global posts,pages
    posts=read('source/_posts',is_post=1)
    pages=read('source/_pages',is_page=1)
def sort_posts():
    global posts
    posts.sort(key=lambda x:str(x['date']),reverse=True) # 日期排序
    tot=len(posts)
    for id,x in enumerate(posts): # 获取前后信息
        x['id']=tot-id
        if config['article_address']=='number':
            x['addr']='posts/%d/'%x['id']
            x['link']=rt+x['addr']
        x['pre']=posts[id-1]
        x['nxt']=posts[(id+1)%tot]
    posts.sort(key=lambda x: '23333-12-31 '+str(x['top']) if x['top'] else str(x['date']),reverse=True)
def gen_categories_index(path,cates):
    if 'sub' in cates:
        for cate in cates['sub']:
            gen_categories_index(path+cate+'/',cates['sub'][cate])
    if 'nodes' in cates:
        categories_index.extend(gen_index(path,cates['nodes'],{'layout':'categories_index','sub':cates['sub'] if 'sub' in cates else None}))
    elif 'sub' in cates:
        categories_index.append({'addr':path,'link':rt+path,'path':path,'title':path,'sub':cates['sub'],'layout':'categories_index'})
def generate():
    global posts,pages,index,tags_index
    for x in posts+pages:
        for tag in x['tags']:
            if tag in tags:tags[tag].append(x)
            else: tags.update({tag:[x]})
        for node in x['categories']:
            now=categories
            for categorie in node:
                if not 'sub' in now:now.update({'sub':{}})
                if not categorie in now['sub']: now['sub'].update({categorie:{}})
                now=now['sub'][categorie]
            if 'nodes' not in now:now.update({'nodes':[x]})
            else: now['nodes'].append(x)
    index=gen_index('',posts,{'layout': 'index'})
    for tag in tags:tags_index.extend(gen_index('tags/%s/'%tag,tags[tag],{'tag':tag,'layout':'tags_index'}))
    gen_categories_index('categories/',categories)
def CpAssets():
    for i in Path('theme/%s/source'%config['theme']).iterdir():cp(i,Dest/i.stem)
    for i in Path('source').glob('[!_]*'):cp(i,Dest/i.name)
    for x in posts+pages:
        if x['assets'].exists():cp(x['assets'],Path(Dest/x['addr']))
def baidu_push():
    print('是否百度推送?y|N')
    if input()!='y': return
    print('百度推送中……')
    oldfile=Path('baidu_push_last.txt')
    oldurls=oldfile.open('r',encoding='utf-8').read() if oldfile.exists() else ''
    newurls=''
    for i in urls:
       if not i[0] in oldurls:
           newurls+=i[0]+'\n'
    oldfile.open('w',encoding='utf-8').write(newurls)
    r=requests.post(config['baidu_push']['url'],files={'file': oldfile.open('rb')})
    print('推送结果:\n%s\n'%r.text)
    oldfile.open('w',encoding='utf-8').write(oldurls+newurls)
def cp(src,dst):
    if DEBUG:print('copy',src,dst)
    if src.is_dir():
        if dst.exists():shutil.rmtree(dst)
        shutil.copytree(src,dst)
    else:
        shutil.copyfile(src,dst)
def op(path,data):
    if DEBUG:print(path)
    path=Dest/path
    if not path.suffix=='.html':path=path/'index.html'
    path.parent.mkdir(parents=1,exist_ok=1)
    path.open('w',encoding='utf-8').write(data)

####################################################################################

try:yamloader=yaml.CLoader
except:yamloader=yaml.SafeLoader

config=yaml.load(open('config.yml',encoding='utf-8').read(),Loader=yamloader)
dest=config['dest']
Dest=Path(dest)
rt=config['site_rt']=urlparse(config['site_url']).path
if config['article_address']=='pinyin':import pypinyin
t_config=yaml.load(open('theme/%s/config.yml'%config['theme'],encoding='utf-8').read(),Loader=yamloader)
t_setting=yaml.load(open('theme/%s/setting.yml'%config['theme'],encoding='utf-8').read(),Loader=yamloader)
posts,pages=[],[]
tags,categories={},{}
index,tags_index,categories_index=[],[],[]
urls=[]
env,tpls=False,{}
last_build_time=datetime.now().isoformat()
DEBUG=0
def debug(status=True):
    global DEBUG
    DEBUG=status

def render_pure_data():
    (Dest/'pure_data.json').open('w',encoding='utf-8').write(json.dumps([{
        'title':x['title'],
        'content':x['content'],
        'link':x['link'],
        'tags':x['tags'],
        'categories':x['categories']
    } for x in posts+pages]))
def init_env():
    global env,tpls
    env=Environment(loader=FileSystemLoader('theme/%s/layout/'%config['theme']))
    env.trim_blocks=True
    env.lstrip_blocks=True
    env.globals.update(**{
        'config':config,
        't_config':t_config,
        'data':{
            'posts':posts,
            'pages':pages,
            'tags':tags,
            'categories':categories
        },
        'last_build_time': last_build_time
    })
    env.filters['markdown']=mistune.Markdown()
    env.filters['markdown_math']=md_math.parse
    env.filters['encrypt']=encrypt
    for i in t_setting['layout']:
        tpls[i]=env.get_template(t_setting['layout'][i])
def render():
    init_env()
    for i in posts+pages+index+tags_index+categories_index+t_setting['extra_render']:
        op(i['addr'],tpls[i['layout']].render(**i))
        urls.append([config['site_url']+i['addr'],i['date'].isoformat() if 'date' in i else last_build_time])

    env.loader=FileSystemLoader('tpl')
    def render_rss(typ):
        (Dest/(typ+'.xml')).open('w',encoding='utf-8').write(env.get_template(typ+'.j2').render())
    def render_sitemap():
        (Dest/'sitemap.xml').open('w',encoding='utf-8').write(env.get_template('sitemap.j2').render(urls=urls))
        (Dest/'sitemap.txt').open('w',encoding='utf-8').write('\n'.join([i[0] for i in urls]))

    render_pure_data()
    if config['rss']:render_rss(config['rss'])
    if config['sitemap']:render_sitemap()
def calcTime(opt,f):
    st_time=time.time()
    f(),print('%s in %.3fs'%(opt,time.time()-st_time))
def main():
    if not Dest.exists():Dest.mkdir()
    calcTime("read",read_all)
    calcTime("sort",sort_posts)
    calcTime("generate",generate)
    calcTime("copy assets",CpAssets)
    calcTime("render",render)
    if config['baidu_push']['enable']:baidu_push()

# server ======================================================

mp={}
def upd():
    read_all()
    sort_posts()
    generate()
    for i in posts+pages+index+tags_index+categories_index+t_setting['extra_render']:mp[rt+i['addr']]=i
def set_interval(f,s):
    f()
    t=threading.Timer(s,set_interval,(f,s))
    t.setDaemon(True)
    t.start()
    return t
def response(client,addr):
    req_data=client.recv(4096).decode()
    data=req_data.split(" ")
    method=data[0]
    url=unquote(data[1],'utf-8')
    path=urlparse(url).path
    if not path.endswith('/') and '.' not in path:path+='/'
    print(method,url)

    if method=='POST':
        postData=unquote(req_data.split('\r\n')[-1],'utf-8')
        return
        
    res_line='HTTP/1.1 200 OK\r\n'
    res_header='Server: WTT/1.1\r\n'
    res_body='404'.encode()
    if '/404.html' in mp:
        x=mp['/404.html']
        res_body=tpls[x['layout']].render(**x).encode()
    elif Path('source/404.html').is_file():
        res_body=rd('source/404.html')

    def rd(path):
        try:return open(path,encoding='utf-8').read().encode()
        except:return open(path,'rb').read()
    print(path)
    if path in mp:
        print(path)
        x=mp[path]
        res_body=tpls[x['layout']].render(**x).encode()
    elif Path('source'+path).is_file():
        res_body=rd('source'+path)
    elif Path('theme/%s/source%s'%(config['theme'],path)).is_file():
        res_body=rd('theme/%s/source%s'%(config['theme'],path))
    else:
        path=path.split('/')
        i=3 if path[1]=='posts' else 2
        par,now='/'.join(path[:i])+'/','/'.join(path[i:])
        print(par,'-',now)
        if par in mp:
            x=mp[par]
            if (x['assets']/now).is_file():
                res_body=rd(str(x['assets']/now))

    client.send((res_line+res_header+"\r\n").encode()+res_body)
    client.close()
def serve():
    port=config['server']['port']
    print('Serving on http://localhost:%d'%port)
    init_env()
    watch=set_interval(upd,config['server']['watch_interval'])
    svr=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    svr.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,True)
    svr.bind(('',port))
    svr.listen(128)
    while True:
        client,addr=svr.accept()
        t=threading.Thread(target=response,args=(client,addr),daemon=True)
        t.start()

# cmd =========================================================

def new_post(data):
    file=Path('source/_posts/%s.md'%data['title'].replace('/','-'))
    if file.exists() and input('文件已存在,是否覆盖(yes|no)')!='yes':return
    file.open('w',encoding='utf-8').write(
        Template(open('tpl/scaffolds/post.j2',encoding='utf-8').read()).render(data)
    )
def new_page(data):
    file=Path('source/_pages/%s.md'%data['title'].replace('/','-'))
    if file.exists() and input('文件已存在,是否覆盖(yes|no)')!='yes':return
    file.open('w',encoding='utf-8').write(
        Template(open('tpl/scaffolds/page.j2',encoding='utf-8').read()).render(data)
    )
def deploy(force):
    if not Dest.exists():print('请先渲染博客'),sys.exit()
    Deploy=Path('deploy')
    ff=not Deploy.exists()
    repo=config['repo']
    if ff:os.system("git clone %s deploy"%repo[0])
    for i in Deploy.iterdir():
        if not i.name.startswith('.git'):shutil.rmtree(i) if i.is_dir() else os.remove(i)
    for i in Dest.iterdir():cp(i,Deploy/i.name)
    os.chdir('deploy')
    if ff:
        open('.gitignore','w',encoding='utf-8').write('.git')
        for i in range(1,len(repo)):os.system('git remote set-url --add origin %s'%repo[i])
    os.system('git add -A\ngit commit -m .\n'+'git push' if not force else 'git push -f')
def show_help():
    print('''
1. [g/generate]: 渲染博客,生成的文件在自定义文件夹中
2. [cl/clean]: 清空输出文件夹
3. [s/server]: 预览博客
4. [n/new] + [title]: 新建文章
5. [np/newpage] + [title]: 新建页面
6. [d/deploy]: 部署博客
''')
    sys.exit()

if __name__=='__main__':
    cmd=sys.argv[1:] if '.py' in sys.argv[0] else sys.argv
    if len(cmd)<1 or cmd[0]=="h" or cmd[0]=="help" or cmd[0]=="-h" or cmd[0]=="--help":show_help()
    elif cmd[0][0]=='g':main()
    elif cmd[0][0:2]=='cl':
        if Dest.exists():shutil.rmtree(Dest)
    elif cmd[0][0]=="s":serve()
    elif(cmd[0]=="n" or cmd[0]=="new"):new_post({
        'title':' '.join(cmd[1:]),
        'date':time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
    })
    elif(cmd[0]=="np" or cmd[0]=="newpage"):new_page({
        'title':' '.join(cmd[1:]),
        'date':time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
    })
    elif cmd[0][0]=="d":deploy(len(cmd)>2 and cmd[1]=='-f')
    else:show_help()