async function search(api){
    document.getElementById('loading-progress').hidden=0;
    var text=document.getElementById("search_input").value.toLowerCase(),
        res=document.getElementById("search_result");
    res.innerHTML='';
    var data=await fetch(api+'/?keyword='+text).then((r)=>r.json());
    document.getElementById('loading-progress').hidden=1;
    for(var i of data){
        var a=document.createElement('a'),
            content=document.createElement('div'),
            Title=document.createElement('div'),
            Text=document.createElement('div');
        
        a.classList.add('mdui-list-item');
        Title.classList.add('mdui-list-item-title');
        Text.classList.add('mdui-list-item-text');
        content.classList.add('mdui-list-item-content');
        a.href=i[0];
        Title.innerText=i[1];
        Text.innerText=i[2].replace(/[\r\n]/g," ");
        
        content.appendChild(Title),content.appendChild(Text);
        a.appendChild(content);

        res.appendChild(a);
    }
}