[Usage]:
from wework import WeApp


app = WeApp('the_app_name')
#app.init_db()
app.send_msg('Hello world!', touser='yaochenzhi')
app.close()