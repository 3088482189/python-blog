# 请先安装gunicorn
# 使用方法
# gunicorn wsgi:app

import blog
app=blog.serve()