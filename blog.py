#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os,sys,time,shutil,re,json,math,threading
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse,unquote,quote
from multiprocessing import Process
import cmd,mistune,md_math
def chkDependences():
    try:import yaml,Crypto,jinja2,flask,pypinyin,requests,htmlmin
    except:os.system('pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple')
chkDependences()

from jinja2 import Environment,FileSystemLoader,Template
from funcs import lyml,dyml,cp,del_none,str2date,rd,toPinyin,MP
from encrypt import encrypt

def op(path,data):
    if DEBUG:print(path)
    path=Dest/path
    if not path.suffix=='.html':path=path/'index.html'
    path.parent.mkdir(parents=1,exist_ok=1)
    path.open('w',encoding='utf-8').write(data)

config=MP(lyml(rd('config.yml')))
dest=config.dest
Dest=Path(dest)
DEBUG=config.debug
rt=config.site.rt=urlparse(config.site.url).path
t_config=MP(lyml(rd('theme/%s/config.yml'%config.theme)))
t_setting=MP(lyml(rd('theme/%s/setting.yml'%config.theme)))

posts,pages=[],[]
tags,categories=MP(),MP()
index,tags_index,categories_index=[],[],[],
urls=[]
env,tpls=False,MP()
last_build_time=datetime.now().replace(microsecond=0)
def genitem(file,is_post=0,is_page=0):
    data=rd(file).split('---\n')
    meta=MP(lyml(data[1]))
    if isinstance(meta.date,str):meta.date=str2date(meta.date)
    content=''.join(data[2:])
    preview=content[0:min(len(content),config.index.preview)]
    if '<!-- more -->' in content:
        preview=content.split('<!-- more -->',1)[0]
    name=file.stem
    x=MP(
        filename=name,
        assets=file.parent/file.stem,
        addr=name+'/',link=rt+name+'/',
        title=name,
        date=datetime.fromtimestamp(int(os.stat(file).st_mtime)),
        author=config.author,
        tags=[],categories=[],
        top=0,
        content=content,preview=preview,
        meta=meta
    )
    x.update(t_setting.defaut_front);x.update(meta)
    if is_post:
        if config.post_addr=='pinyin':x.addr='posts/%s/'%toPinyin(name)
        elif config.post_addr=='origin':x.addr='posts/%s/'%name

        if x.permalink:x.addr='posts/%s/'%x.permalink
        x.link=rt+x.addr

        if not x.layout:x.layout='post'
    if is_page and not x.layout:x.layout='page'
    return x

def gen_index(path,a,ext={}):
    num=config.index.per_page
    tot=len(a);TOT=math.ceil(tot/num)
    res=[]
    for now,i in enumerate(range(0,tot,num),1):
        nodes=a[i:i+num]
        addr=path if now==1 else path+'page/%d/'%now
        res.append(MP(
            id=now,
            addr=addr,link=rt+addr,
            path=path,
            title=path,
            nodes=nodes,
            total=tot,TOTAL=TOT,
        **ext))
    for id,x in enumerate(res):
        x.pre=res[id-1];x.nxt=res[(id+1)%TOT]
    return res
def read(path,is_post=0,is_page=0):
    return [genitem(i,is_post,is_page) for i in Path(path).glob('*.md')]
def read_all():
    global posts,pages
    posts=read('source/_posts',is_post=1)
    pages=read('source/_pages',is_page=1)
def sort_posts():
    global posts
    posts.sort(key=lambda x:str(x.date),reverse=True) # 日期排序
    tot=len(posts)
    for id,x in enumerate(posts): # 获取前后信息
        x.id=tot-id
        if config.post_addr=='number':
            x.addr='posts/%d/'%x.id;x.link=rt+x.addr
        x.pre=posts[id-1];x.nxt=posts[(id+1)%tot]
    posts.sort(key=lambda x:(x.top,str(x.date)),reverse=True)
    for pos,x in enumerate(posts):x.pos=pos
def gen_categories_index(path,cates):
    if cates.sub:
        for cate in cates.sub:
            gen_categories_index(path+cate+'/',cates['sub'][cate])
    if cates.nodes:
        categories_index.extend(gen_index(path,cates['nodes'],{'layout':'categories_index','sub':cates.sub}))
    elif cates.sub:
        categories_index.append(MP(addr=path,link=rt+path,path=path,title=path,sub=cates.sub,layout='categories_index'))
def generate():
    global posts,pages,tags,categories,index,tags_index,categories_index
    tags,categories=MP(),MP()
    for x in posts+pages:
        for tag in x.tags:
            if tag in tags:tags[tag].append(x)
            else: tags.update({tag:[x]})
        for node in x.categories:
            now=categories
            for categorie in node:
                if not 'sub' in now:now.sub=MP()
                if not categorie in now.sub: now.sub[categorie]=MP()
                now=now.sub[categorie]
            if 'nodes' not in now:now.nodes=[x]
            else: now.nodes.append(x)
    index=gen_index('',posts,{'layout':'index'})
    tags_index,categories_index=[],[]
    for tag in tags:tags_index.extend(gen_index('tags/%s/'%tag,tags[tag],{'tag':tag,'layout':'tags_index'}))
    gen_categories_index('categories/',categories)
def CpAssets():
    for i in Path('theme/%s/source'%config.theme).iterdir():cp(i,Dest/i.stem)
    for i in Path('source').glob('[!_]*'):cp(i,Dest/i.name)
    for x in posts+pages:
        if x.assets.exists():cp(x.assets,Path(Dest/x.addr))
def seo_push():
    import requests
    urls=rd(Dest/'sitemap.txt').split('\n')
    def baidu_push():
        print('百度推送中……')
        oldfile=Path('baidu_push_last.txt')
        oldurls=rd(oldfile).split('\n') if oldfile.exists() else []
        newurls=list(set(urls)-set(oldurls))[:3000]
        data='\n'.join(newurls)
        if not data:print('everything up to date');return
        print("推送列表: \n%s\n"%data)
        r=requests.post(
            config.seo_push.baidu,
            headers={'Content-Type':'text/plain'},
            data=data.encode('utf-8'),
            timeout=5
        )
        print('推送结果:\n%s\n'%r.text)
        oldfile.open('w',encoding='utf-8').write('\n'.join(oldurls+newurls))
    def bing_push():
        print('bing推送中……')
        oldfile=Path('bing_push_last.txt')
        oldurls=rd(oldfile).split('\n') if oldfile.exists() else []
        newurls=list(set(urls)-set(oldurls))[:10]
        data='\n'.join(newurls)
        if not data:print('everything up to date');return
        print("推送列表: \n%s\n"%data)
        r=requests.post(
            config.seo_push.bing,
            headers={'Content-Type':'application/json'},
            json={"siteUrl":config.site.url,"urlList":newurls},
            timeout=10
        )
        print('推送结果:\n%s\n'%r.text)
        if 'Error' not in r.text:
            oldfile.open('w',encoding='utf-8').write('\n'.join(oldurls+newurls))
    if config.seo_push.baidu:baidu_push()
    if config.seo_push.bing:bing_push()

def render_pure_data():
    (Dest/'pure_data.json').open('w',encoding='utf-8').write(json.dumps([{
        'title':x.title,
        'content':x.content,
        'link':x.link,
        'tags':x.tags,
        'categories':x.categories
    } for x in posts+pages]))
def init_env():
    global env,tpls
    env=Environment(loader=FileSystemLoader('theme/%s/layout/'%config.theme),trim_blocks=1,extensions=['jinja2htmlcompress.HTMLCompress'])
    env.globals.update(
        config=config,
        t_config=t_config,
        t_setting=t_setting,
        data={
            'posts':posts,'pages':pages,
            'tags':tags,'categories':categories,
            'index':index,'tags_index':tags_index,'categories_index':categories_index
        },
        last_build_time=last_build_time
    )
    env.filters.update(
        markdown=mistune.Markdown(),
        markdown_math=md_math.parse,
        encrypt=encrypt
    )

    for i in t_setting.layout:
        tpls[i]=env.get_template(t_setting.layout[i])
def render():
    for i in posts+pages+index+tags_index+categories_index+t_setting.extra_render:
        op(i.addr,tpls[i.layout].render(**i))
        urls.append([config.site.url+i.addr,i.date or last_build_time])

    def render_rss():
        (Dest/('atom.xml')).open('w',encoding='utf-8').write(env.from_string(rd('tpl/atom.j2')).render())
        (Dest/('rss.xml')).open('w',encoding='utf-8').write(env.from_string(rd('tpl/rss.j2')).render())
    def render_sitemap():
        (Dest/'sitemap.xml').open('w',encoding='utf-8').write(env.from_string(rd('tpl/sitemap.j2')).render(urls=urls))
        (Dest/'sitemap.txt').open('w',encoding='utf-8').write('\n'.join([i[0] for i in urls]))

    render_pure_data()
    if config.rss:render_rss()
    if config.sitemap:render_sitemap()
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

# server ======================================================

mp=MP()
admin=MP()
def upd():
    read_all()
    sort_posts()
    generate()
    for i in posts+pages+index+tags_index+categories_index+t_setting.extra_render:mp[i.addr]=i
def set_interval(f,s):
    f()
    t=threading.Timer(s,set_interval,(f,s))
    t.setDaemon(True);t.start()
    return t
def init_admin():
    admin.env=Environment(loader=FileSystemLoader('admin/layout/'),trim_blocks=1)
    admin.env.globals.update(**{
        'config':config,
        't_config':t_config,
        't_setting':t_setting,
        'data':{
            'posts':posts,'pages':pages,
            'tags':tags,'categories':categories,
            'index':index,'tags_index':tags_index,'categories_index':categories_index
        }
    })
    admin.env.filters=env.filters
    admin.env.filters.update(
        toyaml=dyml,
        rejectkey=lambda x,*args: dict(i for i in x.items() if i[0] not in args)
    )
    admin.tpls=MP(
        login=admin.env.get_template('login.html'),
        index=admin.env.get_template('index.html'),
        editPost=admin.env.get_template('editPost.html'),
        listPost=admin.env.get_template('listPost.html')
    )
def apiLogin(data):
    if data['password']==config.server.password:
        return {'secret':config.server.secret,'status':'success'}
    return {'secret':False,'status':'fail'}
rmPost=lambda x:os.remove('source/_posts/%s.md'%x.filename)
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
    mp[rt+x.addr]=x
    return {'pos':x.pos,'status':'success','redirect':data.get('pos')!=x.pos}
def apiRmPost(data):
    if 'pos' not in data:return {'status':'failed'}
    rmPost(posts[data['pos']])
    posts.pop(data['pos']),mp.pop(rt+posts[data['pos']]['addr'])
    postsUpd()
    return {'status':'success'}
def serve():
    import string,random
    config.server.secret=''.join(random.sample(string.ascii_letters + string.digits,8))
    global rt,env,tpls
    rt='/'
    upd();init_env();init_admin()
    # watch=set_interval(upd,config.server.watch_interval)
    from flask import Flask,request,make_response,abort,Response,send_from_directory,redirect
    app=Flask(
        __name__,
        static_url_path='/admin/assets/',static_folder='admin/assets'
    )
    app.config.update(config)

    @app.route('/admin/login',methods=['GET'])
    def getLogin():
        return admin.tpls['login'].render()
    @app.route('/admin/api/login',methods=['POST'])
    def postLogin():
        if request.get_json()['password']==config.server.password:
            res=make_response({'secret':config.server.secret,'status':'success'})
            res.set_cookie('secret',config.server.secret)
            return res
        else: return {'status':'failed','msg':'验证失败'}

    def chkAdmin():
        return request.cookies and request.cookies['secret']==config.server.secret
    def ChkAdmin(fn):
        return fn() if chkAdmin() else redirect('/admin/login')

    @app.route('/admin/api/update',methods=['GET','POST'])
    def postUpdate():
        if chkAdmin():
            upd();return {'stauts':'success'}
        else:return redirect('/admin/login')

    @app.route('/admin/api/editPost/',methods=['POST'])
    def postEditPost():
        if chkAdmin():return apiEditPost(request.get_json())
        else:return redirect('/admin/login')
    @app.route('/admin/api/rmPost/',methods=['POST'])
    def PostRmPost():
        if chkAdmin():return apiRmPost(request.get_json())
        else:return redirect('/admin/login')
    @app.route('/admin/',methods=['GET'])
    def getAdmin():
        return ChkAdmin(lambda:admin.tpls['index'].render())
    @app.route('/admin/newPost/',methods=['GET'])
    def getAdminNewPost():
        return ChkAdmin(lambda:admin.tpls['editPost'].render(title='新建文章'))
    @app.route('/admin/editPost/<int:pos>',methods=['GET'])
    def getAdminEditPost(pos):
        return ChkAdmin(lambda:admin.tpls['editPost'].render(title='编辑文章',post=posts[pos]))
    @app.route('/admin/listPost/',methods=['GET'])
    def getAdminListPost():
        return ChkAdmin(lambda:admin.tpls['listPost'].render(title='文章列表',posts=posts))

    @app.route('/sitemap.xml',methods=['GET'])
    def getSitemap():
        urls=[]
        for k,v in mp.items():
            urls.append([config.site.url+v['addr'],v.get('date') or last_build_time])
        return Response(env.from_string(rd('tpl/sitemap.j2')).render(urls=urls),mimetype='text/xml')
    @app.route('/atom.xml',methods=['GET'])
    def getAtom():
        return Response(env.from_string(rd('tpl/atom.j2')).render(),mimetype='text/xml')
    @app.route('/rss.xml',methods=['GET'])
    def getRss():
        return Response(env.from_string(rd('tpl/rss.j2')).render(),mimetype='text/xml')
    
    def render(x):
        return tpls[x.layout].render(**x,cookies=request.cookies)
    @app.route('/')
    def getIndex():
        return render(mp[''])

    @app.route('/<path:path>',methods=['GET'])
    def getPath(path):
        if path in mp:return render(mp[path])
        if Path('source/'+path).exists():return send_from_directory('source/',path)
        if 'posts/' in path:
            par,file=path.rsplit('/',1);par+='/'
            if par in mp:return send_from_directory(mp[par].assets,file)
        return send_from_directory('theme/%s/source/'%config.theme,path)

    @app.errorhandler(404)
    def page_not_found(e):
        if '/404.html' in mp:return tpls[mp['/404.html']['layout']].render(**mp['/404.html'])
        elif Path('source/404.html').is_file():return send_from_directory('source/','404.html')
        return '404 not found',404

    return app
def serve_static():
    from flask import Flask
    app=Flask(__name__,static_folder=config.dest)
    @app.route('/',defaults={'path': ''})
    @app.route('/<path:path>')
    def statics(path):
        if not path or path.endswith('/'):path+='index.html'
        elif '.' not in path.split('/')[-1]:path+='/index.html'
        return app.send_static_file(path)
    app.run(port=config.server.port)
# cmd =========================================================

def new_post(data):
    file=Path('source/_posts/%s.md'%data['title'].replace('/','-'))
    if file.exists() and input('文件已存在,是否覆盖(yes|no)')!='yes':return
    file.open('w',encoding='utf-8').write(
        Template(rd('tpl/scaffolds/post.j2')).render(data)
    )
def new_page(data):
    file=Path('source/_pages/%s.md'%data['title'].replace('/','-'))
    if file.exists() and input('文件已存在,是否覆盖(yes|no)')!='yes':return
    file.open('w',encoding='utf-8').write(
        Template(rd('tpl/scaffolds/page.j2')).render(data)
    )
def zip():
    import htmlmin
    def work(i):
        print(i)
        html=rd(i)
        i.open('w',encoding='utf-8').write(htmlmin.minify(html,remove_empty_space=True,remove_comments=True))
    from multiprocessing import Process
    for i in Dest.glob('**/*.html'):
        Process(target=work,args=(i,)).start()

def deploy(force):
    if not Dest.exists():print('请先渲染博客'),exit()
    Deploy=Path('deploy')
    ff=not Deploy.exists()
    repo=config.repo
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
3. [s/server]: 预览博客(动态)
4. [n/new] + [title]: 新建文章
5. [np/newpage] + [title]: 新建页面
6. [d/deploy]: 部署博客
7. [S/Server]: 预览博客(静态,预览渲染后的文件)
8. [sp/seopush]: 搜索引擎推送
''')
    exit()

if __name__=='__main__':
    cmd=sys.argv[1:] if '.py' in sys.argv[0] else sys.argv
    if len(cmd)<1 or cmd[0]=='h' or cmd[0]=='help' or cmd[0]=='-h' or cmd[0]=='--help':show_help()
    elif cmd[0] in ['g','generate']:main()
    elif cmd[0] in ['cl','clean']:
        if Dest.exists():shutil.rmtree(Dest)
    elif cmd[0] in ['s','server']:
        serve().run(threaded=True,port=config.server.port)
    elif cmd[0] in ['S','Server']:
        serve_static()
    elif cmd[0] in ['n','new']:new_post({
        'title':' '.join(cmd[1:]),
        'date':time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
    })
    elif cmd[0] in ['np','newpage']:new_page({
        'title':' '.join(cmd[1:]),
        'date':time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
    })
    elif cmd[0] in ['z','zip']:zip()
    elif cmd[0] in ['d','deploy']:
        deploy(len(cmd)>2 and cmd[1]=='-f')
    elif cmd[0] in ['sp','seopush']:
        seo_push()
    else:show_help()