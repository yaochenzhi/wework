[Usage]:
from wework import WeApp


app = WeApp('the_app_name')
app.send_app_msg('Hello world from app!', touser='yaochenzhi')
# app.send_app_msg('Hello world from app!', test=True)
# app.send_app_msg('Hello world from app!', testor='userid')
app.send_room_msg('Hello world!')
app.close()