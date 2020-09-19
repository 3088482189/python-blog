function search(api){
    document.getElementById('loading-progress').hidden=0;
    var text=document.getElementById("search_input").value.toLowerCase(),
        res=document.getElementById("search_result"),
        xhr=new XMLHttpRequest();
    res.innerHTML='';
    xhr.open('GET',api+'/?keyword='+text,true);
    xhr.onreadystatechange=function(){
        if(xhr.readyState==4){
            document.getElementById('loading-progress').hidden=1;
            var data=JSON.parse(this.responseText);
            for(i in data){
                var a=document.createElement('a'),
                    content=document.createElement('div'),
                    Title=document.createElement('div'),
                    Text=document.createElement('div');
                
                a.classList.add('mdui-list-item');
                Title.classList.add('mdui-list-item-title');
                Text.classList.add('mdui-list-item-text');
                content.classList.add('mdui-list-item-content');
                a.href=data[i][0];
                Title.innerText=data[i][1];
                Text.innerText=data[i][2].replace(/[\r\n]/g," ");
                
                content.appendChild(Title),content.appendChild(Text);
                a.appendChild(content);
                
                res.appendChild(a);
            }
            search_dialog.handleUpdate();
        }
    }
    xhr.send();
}