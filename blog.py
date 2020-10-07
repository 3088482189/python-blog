#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os,sys,time,shutil,re,json,math,socket,threading
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse,unquote,quote
from multiprocessing import Process
import cmd,mistune,md_math

install=lambda *args:os.system('pip3 install %s -i https://pypi.tuna.tsinghua.edu.cn/simple'%' '.join(args))
try:import yaml;from jinja2 import Environment,FileSystemLoader,Template;from encrypt import encrypt
except:install('pyyaml','jinja2','pycryptodome');import yaml;from jinja2 import Environment,FileSystemLoader,Template

lyml=lambda s:yaml.load(s,Loader=yaml.CLoader if yaml.CLoader else yaml.SafeLoader)
dyml=lambda x:yaml.dump(x,allow_unicode=True)
def cp(src,dst):
    if DEBUG:print('copy',src,dst)
    if src.is_dir():
        if dst.exists():shutil.rmtree(dst)
        shutil.copytree(src,dst)
    else:shutil.copyfile(src,dst)
def op(path,data):
    if DEBUG:print(path)
    path=Dest/path
    if not path.suffix=='.html':path=path/'index.html'
    path.parent.mkdir(parents=1,exist_ok=1)
    path.open('w',encoding='utf-8').write(data)
def del_none(a):
    if not isinstance(a,dict):return {}
    for x in list(a.keys()):
        if a.get(x)==None:a.pop(x)
    return a
def str2date(s):
    a=re.split(r'[- :]',s.strip())
    a.extend(['0']*6)
    return datetime(int(a[0]),int(a[1]),int(a[2]),int(a[3]),int(a[4]),int(a[5]))

config=lyml(open('config.yml',encoding='utf-8').read())
dest=config['dest']
Dest=Path(dest)
rt=config['site_rt']=urlparse(config['site_url']).path
if config['article_address']=='pinyin':
    try:import pypinyin
    except:install('pypinyin');import pypinyin
t_config=lyml(open('theme/%s/config.yml'%config['theme'],encoding='utf-8').read())
t_setting=lyml(open('theme/%s/setting.yml'%config['theme'],encoding='utf-8').read())

posts,pages=[],[]
tags,categories={},{}
index,tags_index,categories_index=[],[],[],
urls=[]
env,tpls=False,{}
last_build_time=datetime.now().replace(microsecond=0)
def genitem(file,is_post=0,is_page=0):
    data=file.open(encoding='utf-8').read().split('---\n')
    meta=del_none(lyml(data[1]))
    if isinstance(meta['date'],str):meta['date']=str2date(meta['date'])
    content=''.join(data[2:])
    preview=content[0:min(len(content),config['preview_len'])]
    if '<!-- more -->' in content:
        preview=content.split('<!-- more -->',1)[0]
    name=file.stem
    x={**{
        'filename':name,
        'assets':file.parent/file.stem,
        'addr':name+'/','link':rt+name+'/',
        'title':name,
        'date':datetime.fromtimestamp(int(os.stat(file).st_mtime)),
        'author':config['author'],
        'tags':[],'categories':[],
        'top':0,
        'content':content,'preview':preview,
        'meta':meta,
    },**t_setting['defaut_front'],**meta}
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
    return [genitem(i,is_post,is_page) for i in Path(path).glob('*.md')]
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
    posts.sort(key=lambda x:(x['top'],str(x['date'])),reverse=True)
    for pos,x in enumerate(posts):x['pos']=pos
def gen_categories_index(path,cates):
    if 'sub' in cates:
        for cate in cates['sub']:
            gen_categories_index(path+cate+'/',cates['sub'][cate])
    if 'nodes' in cates:
        categories_index.extend(gen_index(path,cates['nodes'],{'layout':'categories_index','sub':cates['sub'] if 'sub' in cates else None}))
    elif 'sub' in cates:
        categories_index.append({'addr':path,'link':rt+path,'path':path,'title':path,'sub':cates['sub'],'layout':'categories_index'})
def generate():
    global posts,pages,tags,categories,index,tags_index,categories_index
    tags,categories={},{}
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
    tags_index,categories_index=[],[]
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
    try:import requests
    except:install('requests');import requests
    r=requests.post(config['baidu_push']['url'],files={'file': oldfile.open('rb')})
    print('推送结果:\n%s\n'%r.text)
    oldfile.open('w',encoding='utf-8').write(oldurls+newurls)

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
    env=Environment(loader=FileSystemLoader('theme/%s/layout/'%config['theme']),trim_blocks=1)
    env.globals.update(**{
        'config':config,
        't_config':t_config,
        't_setting':t_setting,
        'data':{
            'posts':posts,'pages':pages,
            'tags':tags,'categories':categories,
            'index':index,'tags_index':tags_index,'categories_index':categories_index
        },
        'last_build_time': last_build_time
    })
    env.filters['markdown']=mistune.Markdown()
    env.filters['markdown_math']=md_math.parse
    env.filters['encrypt']=encrypt
    
    for i in t_setting['layout']:
        tpls[i]=env.get_template(t_setting['layout'][i])
def render():
    for i in posts+pages+index+tags_index+categories_index+t_setting['extra_render']:
        op(i['addr'],tpls[i['layout']].render(**i))
        urls.append([config['site_url']+i['addr'],i['date'] if 'date' in i else last_build_time])

    def render_rss(typ):
        (Dest/(typ+'.xml')).open('w',encoding='utf-8').write(env.from_string(open('tpl/%s.j2'%typ,encoding='utf-8').read()).render())
    def render_sitemap():
        (Dest/'sitemap.xml').open('w',encoding='utf-8').write(env.from_string(open('tpl/sitemap.j2',encoding='utf-8').read()).render(urls=urls))
        (Dest/'sitemap.txt').open('w',encoding='utf-8').write('\n'.join([i[0] for i in urls]))

    render_pure_data()
    if config['rss']:render_rss(config['rss'])
    if config['sitemap']:render_sitemap()
def calcTime(opt,f):
    st_time=time.time()
    f(),print('%s in %.3fs'%(opt,time.time()-st_time))
def main():
    if not Dest.exists():Dest.mkdir()
    calcTime('read',read_all)
    calcTime('sort',sort_posts)
    calcTime('generate',generate)
    calcTime('copy assets',CpAssets)
    calcTime('compile templates',init_env)
    calcTime('render',render)
    if config['baidu_push']['enable']:baidu_push()

# server ======================================================

mp={}
tpls_admin,mp_admin={},{}
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
def admin():
    env_admin=Environment(loader=FileSystemLoader('admin/layout/'),trim_blocks=1)
    env_admin.globals.update(**{
        'config':config,
        't_config':t_config,
        't_setting':t_setting,
        'data':{
            'posts':posts,'pages':pages,
            'tags':tags,'categories':categories,
            'index':index,'tags_index':tags_index,'categories_index':categories_index
        }
    })
    env_admin.filters=env.filters
    env_admin.filters['toyaml']=dyml
    env_admin.filters['rejectkey']=lambda x,*args: dict(i for i in x.items() if i[0] not in args)
    tpls_admin['index']=env_admin.get_template('index.html')
    tpls_admin['editPost']=env_admin.get_template('editPost.html')
    tpls_admin['listPost']=env_admin.get_template('listPost.html')
def apiLogin(data):
    if data['password']==config['server']['password']:
        return {'secret':config['server']['secret'],'status':'success'}
    return {'secret':False,'status':'fail'}
rmPost=lambda x:os.remove('source/_posts/%s.md'%x['filename'])    
def postsUpd():
    sort_posts()
    generate()
    for i in index+tags_index+categories_index:mp[rt+i['addr']]=i
def apiEditPost(data):
    data['meta']=del_none(lyml(data['meta']))
    if 'date' not in data['meta']:data['meta']['date']=datetime.now().replace(microsecond=0)
    elif isinstance(data['meta']['date'],str):data['meta']['date']=str2date(data['meta']['date'])    
    data['meta'].update({
        'title':data['title'],'top':data['top'],
        'tags':data['tags'],'categories':data['categories']
    })    
    
    file=Path('source/_posts/%s.md'%data['filename'])
    file.open('w',encoding='utf-8').write(
        '---\n'+
        dyml(data['meta'])+
        '\n---\n'+
        data['content']
    )
    x=genitem(file,is_post=1)
    if 'pos' in data:
        post=posts[data['pos']]
        if post['filename']!=data['filename']:rmPost(post)
        posts[data['pos']]=x
    else:posts.append(x)
    postsUpd()
    mp[rt+x['addr']]=x
    return {'pos':x['pos'],'status':'success','redirect':data.get('pos')!=x['pos']}
def apiRmPost(data):
    if 'pos' not in data:return {'status':'failed'}
    rmPost(posts[data['pos']])
    posts.pop(data['pos']),mp.pop(rt+posts[data['pos']]['addr'])
    postsUpd()
    return {'status':'success'}
def serve():
    import string,random
    # config['server']['secret']=''.join(random.sample(string.ascii_letters + string.digits,8))
    global rt,env,tpls
    rt='/'
    upd()
    mp[rt+'sitemap.xml']={'layout':'sitemap'}
    mp[rt+'atom.xml']={'layout':'atom'}
    mp[rt+'rss.xml']={'layout':'rss'}
    init_env()
    admin()
    # watch=set_interval(upd,config['server']['watch_interval'])

    try:from flask import Flask,request,make_response,abort,Response,send_from_directory
    except:install('flask');from flask import Flask,request,make_response,abort,Response,send_from_directory

    app=Flask(__name__)
    @app.route('/admin/api/login',methods=['POST'])
    def postLogin():
        if request.get_json()['password']==config['server']['password']:
            res=make_response({'secret':config['server']['secret'],'status':'success'})
            res.set_cookie('secret',config['server']['secret'])
            return res
        else: return {'status':'failed'},500
    @app.route('/admin/api/editPost/',methods=['POST'])
    def postEditPost():
        return apiEditPost(request.get_json())
    @app.route('/admin/api/rmPost/',methods=['POST'])
    def PostRmPost():
        return apiRmPost(request.get_json())
    @app.route('/admin/assets/<path:path>',methods=['GET'])
    def getAdminAssets(path):
        return send_from_directory('admin/assets/',path)
    @app.route('/admin/',methods=['GET'])
    def getAdmin():
        return tpls_admin['index'].render(cookies=request.cookies)
    @app.route('/admin/newPost/',methods=['GET'])
    def getAdminNewPost():
        return tpls_admin['editPost'].render(title='新建文章',cookies=request.cookies)
    @app.route('/admin/editPost/<int:pos>',methods=['GET'])
    def getAdminEditPost(pos):
        return tpls_admin['editPost'].render(title='编辑文章',post=posts[pos],cookies=request.cookies)
    @app.route('/admin/listPost/',methods=['GET'])
    def getAdminListPost():
        return tpls_admin['listPost'].render(title='文章列表',posts=posts,cookies=request.cookies)

    @app.route('/sitemap.xml',methods=['GET'])
    def getSitemap():
        return env.from_string(open('tpl/sitemap.j2',encoding='utf-8').read()).render(urls=urls)
    @app.route('/atom.xml',methods=['GET'])
    def getAtom():
        return Response(env.from_string(open('tpl/atom.j2',encoding='utf-8').read()).render(),mimetype='text/xml')
    @app.route('/rss.xml',methods=['GET'])
    def getRss():
        return Response(env.from_string(open('tpl/rss.j2',encoding='utf-8').read()).render(),mimetype='text/xml')

    @app.route('/')
    def getIndex():
        x=mp['/']
        return tpls[x['layout']].render(**x,cookies=request.cookies)

    @app.route('/<path:path>',methods=['GET'])
    def getPath(path):
        x=mp.get(request.path)
        if x:return tpls[x['layout']].render(**x,cookies=request.cookies)
        elif Path('source/'+path).exists():return send_from_directory('source/',path)
        else:return send_from_directory('theme/%s/source/'%config['theme'],path)

    @app.errorhandler(404)
    def page_not_found(e):
        if '/404.html' in mp:return tpls[mp['/404.html']['layout']].render(**mp['/404.html'])
        elif Path('source/404.html').is_file():return send_from_directory('source/','404.html')
        return '404 not found',404
    
    return app
def serve_static():
    try:from flask import Flask
    except:install('flask');from flask import Flask

    app=Flask(__name__,static_folder=config['dest'])
    @app.route('/',defaults={'path': ''})
    @app.route('/<path:path>')
    def statics(path):
        if path.endswith('/'):path+='index.html'
        if '.' not in path.split('/')[-1]:path+='/index.html'
        return app.send_static_file(path)
    app.run()
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
    if not Dest.exists():print('请先渲染博客'),exit()
    Deploy=Path('deploy')
    ff=not Deploy.exists()
    repo=config['repo']
    if ff:os.system('git clone %s deploy'%repo[0])
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
7. [S/Server]: 预览博客(静态,预览渲染后的文件)
''')
    exit()

if __name__=='__main__':
    cmd=sys.argv[1:] if '.py' in sys.argv[0] else sys.argv
    if len(cmd)<1 or cmd[0]=='h' or cmd[0]=='help' or cmd[0]=='-h' or cmd[0]=='--help':show_help()
    elif cmd[0][0]=='g':main()
    elif cmd[0][0:2]=='cl':
        if Dest.exists():shutil.rmtree(Dest)
    elif cmd[0][0]=='s':serve().run(threaded=True)
    elif cmd[0][0]=='S':serve_static()
    elif(cmd[0]=='n' or cmd[0]=='new'):new_post({
        'title':' '.join(cmd[1:]),
        'date':time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
    })
    elif(cmd[0]=='np' or cmd[0]=='newpage'):new_page({
        'title':' '.join(cmd[1:]),
        'date':time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
    })
    elif cmd[0][0]=='d':deploy(len(cmd)>2 and cmd[1]=='-f')
    else:show_help()