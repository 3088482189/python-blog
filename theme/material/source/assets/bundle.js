window.addEventListener('load',(e)=>{first_load();});
function first_load(){
    theme('chk');
    document.getElementById('loading-progress').hidden=1;
    page_typ=document.getElementById('page_typ').innerText;
    if(page_typ=='index'){
        document.getElementById('toc_button').hidden=1;
        document.getElementById('toc_drawer').hidden=1;
    }
    else if(page_typ=='article'){
        if(document.getElementById('md-body'))gentoc('md-body');
        document.getElementById('toc_button').hidden=0;
        document.getElementById('toc_drawer').hidden=0;
    }
    var x=document.querySelector('body .mdui-container');
    x.style.minHeight=window.innerHeight-document.body.clientHeight+x.clientHeight+'px';
    katex_();
    highlight();

    lazyload();
    window.addEventListener('scroll',lazyload);
}
function pjax_load(){
    katex_();
    highlight();
    page_typ=document.getElementById('page_typ').innerText;
    if(page_typ=='index'){
        document.getElementById('toc_button').hidden=1;
        document.getElementById('toc_drawer').hidden=1;
    }
    else if(page_typ=='article'){
        if(document.getElementById('md-body'))gentoc('md-body');
        document.getElementById('toc_button').hidden=0;
        document.getElementById('toc_drawer').hidden=0;
    }
    var x=document.querySelector('body .mdui-container');
    x.style.minHeight=window.innerHeight-document.body.clientHeight+x.clientHeight+'px';
}
var timeOut,speed=0;
window.onscroll=function(){
    if(document.documentElement.scrollTop>=300)document.getElementById('totop').classList.remove('mdui-fab-hide');
    else document.getElementById('totop').classList.add('mdui-fab-hide');
}
function totop(){
    if(document.body.scrollTop||document.documentElement.scrollTop)
        window.scrollBy(0,-(speed+=20)),timeOut=setTimeout('totop()',20);
    else clearTimeout(timeOut),document.getElementById('totop').classList.add('mdui-fab-hide'),speed=0;
}
function getCookie(cname){
    var name=cname+'=',decodedCookie=decodeURIComponent(document.cookie),ca=decodedCookie.split(';'),c;
    for(var i in ca){
        c=ca[i];
        while(c.charAt(0)==' ')c=c.substring(1);
        if(c.indexOf(name)==0)return c.substring(name.length, c.length);
    }return '';
}
function setCookie(cname,cval,exdays=0.5){
    if(getCookie(cname)==cval)return;
    var d=new Date();
    d.setTime(d.getTime()+(exdays*24*60*60*1000));
    var expires='expires='+d.toUTCString();
    document.cookie=cname+'='+cval+';'+expires+';path=/';
}
function addCss(url){
    var x=document.createElement('link');
    x.href=url;x.type='text/css';x.rel='stylesheet';
    document.getElementById('theme_css').appendChild(x);
}
function theme_night(){
    setCookie('theme','night');
    document.body.classList.add('mdui-theme-layout-dark');
    addCss('https://cdn.jsdelivr.net/gh/highlightjs/cdn-release/build/styles/nord.min.css');
    addCss('/assets/theme/night.css');
}
function theme_pink(){
    setCookie('theme','pink');
    addCss('/assets/theme/pink.css');
}
function theme_blue(){
    setCookie('theme','blue');
    addCss('/assets/theme/blue.css');
}
function theme_clr(){
    setCookie('theme','day');
    document.getElementById('theme_css').innerHTML='';
    document.body.classList.remove('mdui-theme-layout-dark');
}
function theme(typ){
    if(typ=='chk')typ=getCookie('theme');
    
    if(typ=='day')theme_clr();
    else if(typ=='pink')theme_clr(),theme_pink();
    else if(typ=='blue')theme_clr(),theme_blue();
    else if(typ=='night')theme_clr(),theme_night();
}
function copy(text){
    var x=document.createElement('textarea');
    x.textContent=text;document.body.appendChild(x);
    x.select();document.execCommand('copy');
    x.remove();
}
async function katex_(){
    if(typeof(katex)=='undefined')return;
    document.querySelectorAll('code latex').forEach((x)=>{
        var y=document.createElement('span');
        katex.render(x.innerText,y,{throwOnError: false});
        x.parentElement.replaceWith(y.children[0]);
    });
    document.querySelectorAll('code latex_display').forEach((x)=>{
        var y=document.createElement('span');
        katex.render(x.innerText,y,{displayMode:true,throwOnError: false});
        x.parentElement.replaceWith(y.children[0]);
    });
}
async function highlight(){
    if(typeof(hljs)=='undefined')return;
    document.querySelectorAll('pre code').forEach((x)=>{
        if(x.classList.contains('hljs-nb')){x.remove();return;}
        x.innerHTML=x.innerHTML.replace(/\s+$/g,'');
        var lang=x.classList[0],len=x.innerText.length;
        if(lang&&lang.indexOf('-')!=-1)lang=lang.split('-'),lang=lang[lang.length-1];
        else lang='text';
        hljs.highlightBlock(x);
        var nb=document.createElement('code'),str='',tot=x.innerText.split('\n').length;
        for(var i=1;i<=tot;++i)str+=i+'\n';
        nb.classList.add('hljs','hljs-nb');
        nb.style.float='left';
        nb.innerText=str;
        x.parentElement.insertBefore(nb,x);

        var bar=document.createElement('div'),
            cb=document.createElement('div'),
            fd=document.createElement('div');
        cb.classList.add('hljs-cb');
        cb.setAttribute('data-title','复制');
        cb.addEventListener('click',function(){
            copy(this.parentElement.parentElement.innerText);
            this.setAttribute('data-title','复制成功');
            setTimeout(function(it){it.setAttribute('data-title','复制');},1000,this);
            mdui.snackbar({message: '复制成功!',position: 'top'});
        });

        fd.classList.add('hljs-fd');
        fd.setAttribute('data-title','折叠');
        fd.addEventListener('click',function(){
            this.parentElement.parentElement.parentElement.hidden=1;
            this.parentElement.parentElement.parentElement.previousElementSibling.hidden=0;
        });
        var hl=document.createElement('div');
        hl.classList.add('hljs-lang');
        hl.setAttribute('data-title',lang);
        bar.classList.add('hljs-bar');
        bar.append(hl),bar.append(fd),bar.append(cb);
        x.append(bar);
        var fd_=document.createElement('div'),
            fd_ufd=document.createElement('div'),
            fd_hl=document.createElement('div'),
            fd_hle=document.createElement('div');
        fd_.hidden=1;
        fd_.addEventListener('click',function(){
            this.hidden=1;
            this.nextElementSibling.hidden=0;
        });
 
        fd_ufd.classList.add('hljs-fd');
        fd_ufd.setAttribute('data-title','展开');
        fd_ufd.classList.add('hljs-fd');
        fd_hl.classList.add('hljs-lang');
        fd_hl.setAttribute('data-title',lang);
        fd_hle.classList.add('hljs-len');
        fd_hle.setAttribute('data-title',len);
        fd_.append(fd_hl),fd_.append(fd_hle),fd_.append(fd_ufd);
        x.parentElement.parentElement.insertBefore(fd_,x.parentElement);
    });
    var sty=document.createElement('style');
    sty.innerHTML=[
        '.hljs{position:relative;}',
        '.hljs-bar{display:none;width:fit-content;position:absolute;top:0;right:0;}',
        '.hljs:hover .hljs-bar{display:block;}',
        '.hljs-cb,.hljs-fd,.hljs-lang,.hljs-len{',
            'display: inline-block;',
            'width: fit-content;',
            'color: #fff;',
            'padding: 2px 5px;',
            'cursor: pointer;',
        '}', 
        '.hljs-cb{','background-color: #f7a4b9;','}',
        '.hljs-fd{','background-color: #66ccff;','}',
        '.hljs-lang{','background-color: #6f87ff;','}',
        '.hljs-len{','background-color: #f7a4b9;','}',
        '.hljs-fd:after,.hljs-cb:after,.hljs-lang:after,.hljs-len:after{','content: attr(data-title)','}',
        '.hljs-nb{color: #bbb !important;}'
    ].join('');
    document.getElementsByTagName('head')[0].appendChild(sty);
}
function gentoc(id){
    var toc=document.getElementById('toc'),
        content=document.getElementById(id),
        item=content.firstElementChild,
        secondtoc,thirdtoc;
    toc.innerHTML='';
    while(item){
        if(item.tagName=='H1'){
            item.setAttribute('id',item.textContent);
            var catalogA = document.createElement('a');
            catalogA.textContent=item.textContent;
            catalogA.href='#'+item.id;
            secondtoc=document.createElement('ul');
            var catalogLi=document.createElement('li');
            catalogLi.classList.add('mdui-text-truncate');
            catalogLi.style.marginBottom = '16px';
            catalogLi.appendChild(catalogA);
            catalogLi.appendChild(secondtoc);
            toc.appendChild(catalogLi);
        }
        else if(item.tagName=='H2'){
            item.setAttribute('id',item.textContent);
            if(!secondtoc){
                secondtoc=document.createElement('ul');
                toc.appendChild(secondtoc);
            }
            var catalogA=document.createElement('a');
            catalogA.textContent=item.textContent;
            catalogA.href='#'+item.id;
            thirdtoc=document.createElement('ul');
            var catalogLi=document.createElement('li');
            catalogLi.classList.add('mdui-text-truncate');
            catalogLi.appendChild(catalogA);
            catalogLi.appendChild(thirdtoc);
            secondtoc.appendChild(catalogLi);
        }
        else if(item.tagName=='H3'){
            item.setAttribute('id',item.textContent);
            if(!thirdtoc){
                thirdtoc=document.createElement('ul');
                toc.appendChild(thirdtoc);
            }
            var catalogA=document.createElement('a');
            catalogA.textContent=item.textContent;
            catalogA.href='#'+item.id;
            var catalogLi=document.createElement('li');
            catalogLi.classList.add('mdui-text-truncate');
            catalogLi.appendChild(catalogA);
            thirdtoc.appendChild(catalogLi);
        }
        item=item.nextElementSibling;
        if(!item)break;
    };
}
function copylink(){
    copy(window.location.href);
    mdui.snackbar({message: '复制成功!',position: 'top'});
}
function lazyload(){
    var images=document.getElementsByTagName('img'),
        len=images.length,
        seeHeight=document.documentElement.clientHeight,
        scrollTop=document.documentElement.scrollTop||document.body.scrollTop;
    for(let i=0;i<len;++i)
        if(images[i].offsetTop<seeHeight+scrollTop){
            var datasrc=images[i].getAttribute('data-src');
            if(datasrc!=null&&images[i].src!=datasrc)
                images[i].src=images[i].getAttribute('data-src');
        }
        else break;
}