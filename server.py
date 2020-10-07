from urllib.parse import urlparse,unquote,quote
import socket,threading
class REQ:
    def __init__(self,s):
        self.content=s
        self.method=s.split()[0]
        self.url=unquote(s.split()[1],'utf-8')
        self.body=s.split('\r\n\r\n',1)[1]
    def parse_url(self):
        x=urlparse(self.url)
        if not x.query:return x.path,{}
        qry={}
        for i in x.query.split('&'):
            if '=' not in i:continue
            k,v=i.split('=')
            if v.isdigit():v=int(v)
            qry[k]=v
        return x.path,qry
    def _headers(self):
        res={}
        for i in self.content.split('\r\n\r\n',1)[0].split('\r\n')[1:]:
            k,v=i.split(': ',1)
            res[k]=v
        return res
    @property
    def headers(self):
        return self._headers()
    @property
    def cookies(self):
        headers=self._headers()
        if 'Cookie' not in headers:return {}
        return dict([i.split('=',1) for i in headers['Cookie'].split('; ')])
status_code={
    200:'HTTP/1.1 200 OK',
    404:'HTTP/1.1 404'
}
class RES:
    def __init__(self,client,status=200,header='',body=''):
        self.client=client
        self.status=status
        self.header={
            'content-type':'text/html; charset=utf-8'
        }
        self.body=False
    def send(self):
        self.client.send(
            (
                status_code[self.status]+'\r\n'+
                '\r\n'.join(['%s: %s'%(k,v) for k,v in self.header.items()])+'\r\n'+
                '\r\n'
            ).encode()+
            self.body
        )
        self.client.close()

def server(res,port):
    svr=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    svr.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,True)
    svr.bind(('',port))
    svr.listen(128)
    print('Serving on http://localhost:%d'%port)
    while True:
        client,addr=svr.accept()
        t=threading.Thread(target=res,args=(REQ(client.recv(1048576).decode()),RES(client)),daemon=True)
        t.start()
mime_type={'.*':'application/octet-stream','.aac':'audio/aac','.abw':'application/x-abiword','.arc':'application/x-freearc','.avi':'video/x-msvideo','.azw':'application/vnd.amazon.ebook','.bin':'application/octet-stream','.bmp':'image/bmp','.bz':'application/x-bzip','.bz2':'application/x-bzip2','.csh':'application/x-csh','.css':'text/css','.csv':'text/csv','.doc':'application/msword','.docx':'application/vnd.openxmlformats-officedocument.wordprocessingml.document','.eot':'application/vnd.ms-fontobject','.epub':'application/epub+zip','.gif':'image/gif','.htm':'text/html','.html':'text/html','.ico':'image/vnd.microsoft.icon','.ics':'text/calendar','.jar':'application/java-archive','.jpeg':'image/jpeg','.jpg':'image/jpeg','.js':'text/javascript','.json':'application/json','.jsonld':'application/ld+json','.mid':'audio/midi','.midi':'audio/midi','.mjs':'text/javascript','.mp3':'audio/mpeg','.mpeg':'video/mpeg','.mpkg':'application/vnd.apple.installer+xml','.odp':'application/vnd.oasis.opendocument.presentation','.ods':'application/vnd.oasis.opendocument.spreadsheet','.odt':'application/vnd.oasis.opendocument.text','.oga':'audio/ogg','.ogv':'video/ogg','.ogx':'application/ogg','.otf':'font/otf','.png':'image/png','.pdf':'application/pdf','.ppt':'application/vnd.ms-powerpoint','.pptx':'application/vnd.openxmlformats-officedocument.presentationml.presentation','.rar':'application/x-rar-compressed','.rtf':'application/rtf','.sh':'application/x-sh','.svg':'image/svg+xml','.swf':'application/x-shockwave-flash','.tar':'application/x-tar','.tif':'image/tiff','.tiff':'image/tiff','.ttf':'font/ttf','.txt':'text/plain','.vsd':'application/vnd.visio','.wav':'audio/wav','.weba':'audio/webm','.webm':'video/webm','.webp':'image/webp','.woff':'font/woff','.woff2':'font/woff2','.xhtml':'application/xhtml+xml','.xls':'application/vnd.ms-excel','.xlsx':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','.xml':'application/xml','.xul':'application/vnd.mozilla.xul+xml','.zip':'application/zip','.3gp':'video/3gpp','.3g2':'video/3gpp2','.7z':'application/x-7z-compressed'}
if __name__=='__main__':
    def resp(req:REQ,res:RES):
        res.header
        res.body='test'.encode()
        res.send()
    server(resp,3333)