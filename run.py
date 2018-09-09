from bottle import route, run, template, request, redirect, static_file
import subprocess
import tempfile
import os
import hls
global streaming_downloader
global temp_dir
global m3u8_path
global m3u8_url
global pool
streaming_downloader = None
pool = {}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_PATH = os.path.join(BASE_DIR, 'static')
log = '-loglevel panic'

def to_static_url(path):
    global m3u8_path, BASE_DIR
    static_url = os.path.join('/static', os.path.relpath(path, STATIC_PATH))
    return static_url

@route('/')
def index():
    global streaming_downloader
    if streaming_downloader:
        return redirect ('/main')
    else:
        return template(open('templates/index.html').read())

@route('/start', method='POST')
def start():
    global m3u8_path, temp_dir, m3u8_url, streaming_downloader, STATIC_PATH
    m3u8_url = request.forms.get('m3u8_url')
    temp_dir = tempfile.mkdtemp(dir=STATIC_PATH)
    m3u8_path = os.path.join(temp_dir, 'index.m3u8')
    cmd = 'ffmpeg -loglevel panic -i {} -start_number 0 -hls_time 10 -hls_list_size 0 -vcodec copy -f hls {}'.format(m3u8_url, m3u8_path).split()
    streaming_downloader = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    return redirect('main')

@route('/main')
def main():
    return template(open('templates/main.html').read(), m3u8_url=to_static_url(m3u8_path))


@route('/slince', method='POST')
def slince():
    global pool
    start = float(request.forms.get('start'))
    end = float(request.forms.get('end'))

    m3u8 = hls.M3U8.from_path(m3u8_path).slince(start, end)
    name = os.path.join(temp_dir, '{}_{}'.format(start, end))
    m3u8_dir = name + '.m3u8'
    mp4_dir = name + '.mp4'
    with open(m3u8_dir, 'w+') as f:
        f.write(m3u8.render())

    cmd = 'ffmpeg -loglevel panic -i {} -vcodec copy {}'.format(m3u8_dir, mp4_dir).split()
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    info = {}
    info['mp4'] = mp4_dir
    info['proc'] = proc

    pool[proc.pid] = info
    return redirect('/wait/{}'.format(proc.pid))

@route('/wait/<pid:re:\d+>')
def wait(pid):
    global pool
    info = pool[int(pid)]
    # success
    code = info['proc'].poll()
    if code == 0:
        return redirect(to_static_url(info['mp4']))
    else:
        return '<meta http-equiv="refresh" content="3" /> code:{}'.format(code)


@route('/static/<path:path>')
def static(path):
    return static_file(path, root=STATIC_PATH)
    
run(host='localhost', port=8080)

