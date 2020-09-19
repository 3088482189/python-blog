function search(file){
    document.getElementById('loading-progress').hidden=0;
    var text=document.getElementById("search_input").value.toLowerCase(),
        res=document.getElementById("search_result"),
        xhr=new XMLHttpRequest();
    res.innerHTML='';
    xhr.open('GET',file,true);
    xhr.onreadystatechange=function(){
        mdui.mutation();
        if(xhr.readyState==4){
            document.getElementById('loading-progress').hidden=1;
            data=JSON.parse(this.responseText);
            for(i in data){
                var f=0;
                if(data[i].title.toLowerCase().indexOf(text)!=-1)f=1;
                else for(j in data[i].tags)
                    if(data[i].tags[j].toLowerCase().indexOf(text)!=-1){
                        f=1;break;
                    }
                else for(j in data[i].categories)
                    for(k in data[i].categories[j])
                    if(data[i].categories[j][k].toLowerCase().indexOf(text)!=-1){
                        f=1;break;
                    }
                else if(data[i].content.toLowerCase().indexOf(text)!=-1)f=1;
                if(f){
                    var a=document.createElement('a'),
                        content=document.createElement('div'),
                        Title=document.createElement('div'),
                        Text=document.createElement('div');
                    
                    a.classList.add('mdui-list-item');
                    Title.classList.add('mdui-list-item-title');
                    Text.classList.add('mdui-list-item-text');
                    content.classList.add('mdui-list-item-content');

                    a.href=data[i].link;
                    Title.innerText=data[i].title;
                    Text.innerText=data[i].content.substr(0,50).replace(/[\r\n]/g," ");
                    
                    content.appendChild(Title),content.appendChild(Text);
                    a.appendChild(content);
                    
                    res.appendChild(a);
                }                
            }
            search_dialog.handleUpdate();
        }
    }
    xhr.send();
}