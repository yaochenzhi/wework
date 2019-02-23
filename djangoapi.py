import json
import datetime

def HttpResponse(data):
    print(data)

def djangoapi(request, jstr=None, touser=None):

    app, room, touser = "container", False, None

    error_code, error_msg = 0, "ok"

    if not jstr:
        jstr = request.body
    try:
        data = json.loads(jstr)
    except Exception:
        error_code, error_msg = 1, "data error"
    else:
        if not 'title' in data:
            error_code, error_msg = 2, "title missing"
        else:
            if 'meta' in data:
                meta = data.pop("meta")
                if not isinstance(meta, dict):
                    error_code, error_msg = 3, "meta data error"
                else:
                    if 'app' in meta:
                        app = meta['app']
                    if 'room' in meta:
                        room = meta['room']
                    if 'touser' in meta:
                        touser = meta['touser']

            from wework import WeApp
            app = WeApp(app)

            app_valid, room_valid = app.app_info
            if not app_valid:
                error_code, error_msg = 4, "app invalid"
            else:
                # app valid
                time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                title = data.pop("title")
                title = "{}\n告警时间:{}\n\n".format(title, time)

                keys_sorted = sorted(data.keys(), key=lambda x: x.lower())
                msg_lines = [ "{} : {}".format(k, data[k]) for k in keys_sorted]
                msg = title + ",\n".join(msg_lines)

                if room:
                    if not room_valid:
                        error_code, error_msg = 5, "room invalid"
                    else:
                        app.send_room_msg(msg)
                else:
                    app.send_app_msg(msg, touser=touser)
            app.close()
    finally:
        resp_data = {
            "error_code": error_code,
            "error_msg": error_msg
        }

    return HttpResponse(resp_data)


djangoapi("hello", jstr="""{"h": "hello world", "title": "test", "meta": {"app": "filesystem", "room": "1"}}""", touser="yaochenzhi")