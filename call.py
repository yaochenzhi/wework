from wework import WeApp


app = WeApp('ntp')

app.send_msg("Hello world from yaochenzhi!\nThis is a brand new starting!", touser='yaochenzhi')
app.close()