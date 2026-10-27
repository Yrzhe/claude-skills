"""Long left-input inspector PTY smoke; stdlib only, isolated config and mock services."""
import fcntl,json,os,pty,re,select,shlex,signal,struct,subprocess,sys,tempfile,termios,threading,time
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer

plugin=Path(__file__).resolve().parents[1]
root=Path(tempfile.mkdtemp(prefix='pr2-author-fixes-pty-'))
print('Artifacts:',root,flush=True)
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):
        """Suppress HTTP access logs for the local translation fixture."""
        pass
    def do_POST(self):
        """Return a deterministic translation for the incoming mock chat request."""
        body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        text=body['messages'][1]['content'].replace('文','T') if 'English' in body['messages'][0]['content'] else '完成。'
        self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers()
        self.wfile.write(json.dumps({'choices':[{'message':{'content':text},'finish_reason':'stop'}]}).encode())
server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
threading.Thread(target=server.serve_forever,daemon=True).start()
config=root/'config.json'
config.write_text(json.dumps(dict(enabled=True,baseUrl=f'http://127.0.0.1:{server.server_port}/v1',model='fixture',apiKey='fixture-only',detection='script',inputTranslation='left',inputLeft='both',inputRight='off')))
fixture=root/'fixture';(fixture/'.claude-plugin').mkdir(parents=True);(fixture/'hooks').mkdir()
(fixture/'.claude-plugin/plugin.json').write_text('{"name":"author-fixes-fixture","version":"0.0.1"}')
(fixture/'hooks/hooks.json').write_text('{"modules":["./register.ts"]}')
fixture_code='''export const register = on => {
  on('ui.render', {component:'UserMessage'}, async ($,e,next) => {
    if(e.props.origin.kind==='composer' && e.props.text.length>50000) {
      const state=await $.state.get({plugin:'translate-view',key:'originals'});
      const display=await $.state.get({plugin:'translate-view',key:'inputDisplay'});
      if(state.value?.[e.requestId]) await $.fs.write(ID_FILE,JSON.stringify({id:e.requestId,length:e.props.text.length,originalLength:state.value[e.requestId].length,originalKeys:Object.keys(state.value??{}),display:display.value}));
    }
    return next(e);
  });
  on('session.append', {door:'prompt'}, async ($,e,next) => {
    const blocks=e.message.type==='user'?e.message.content:[];
    const text=Array.isArray(blocks)?blocks.filter(b=>b.type==='text').map(b=>b.text).join(''):String(blocks);
    await $.fs.write(APPEND_FILE,JSON.stringify({agentId:e.agentId,type:e.message.type,uuid:e.uuid,length:text.length,head:text.slice(0,30),tail:text.slice(-30),keys:Object.keys(e)}));
    return next(e);
  });
  on('state.set', {plugin:'translate-view',key:'originals'},async($,e,next)=>{await $.fs.write(STATE_FILE,JSON.stringify({keys:Object.keys(e.value),lengths:Object.values(e.value).map(v=>String(v).length)}));return next(e)});
  on('ui.render', {component:'Pane'}, async ($,e,next) => {
    if(e.requestId==='translate-view') await $.fs.write(PANE_FILE,JSON.stringify(e.props));
    return next(e);
  });
  on('ui.press', async($,e,next)=>{const result=await next(e);await $.fs.write(PRESS_FILE,JSON.stringify({event:e,result}));return result});
  on('turn.start', async($,e,next)=>{await $.fs.write(RECEIVED_FILE,JSON.stringify({length:e.text.length}));return next(e)});
  on('turn.step', async function*($,e){yield {kind:'text',index:0,text:'Finished.'};return {turnId:e.turnId,index:e.index,answer:'Finished.',toolUses:[],stopReason:'end_turn',usage:null}});
}'''
for name,file in [('ID_FILE','id.json'),('PANE_FILE','pane.json'),('PRESS_FILE','press.json'),('RECEIVED_FILE','received.json'),('APPEND_FILE','append.json'),('STATE_FILE','state.json')]:fixture_code=fixture_code.replace(name,json.dumps(str(root/file)))
(fixture/'hooks/register.ts').write_text(fixture_code)
home=root/'claude-home';home.mkdir()
(home/'.claude.json').write_text(json.dumps({'hasCompletedOnboarding':True,'theme':'dark','projects':{str(plugin):{'hasTrustDialogAccepted':True}},'customApiKeyResponses':{'approved':['fixture-only'],'rejected':[]}}))
env=dict(os.environ,TERM='xterm-256color',FORCE_COLOR='1',CLAUDE_CODE_NO_FLICKER='1',TRANSLATE_VIEW_CONFIG=str(config),CLAUDE_CONFIG_DIR=str(home),ANTHROPIC_BASE_URL='http://127.0.0.1:1',ANTHROPIC_API_KEY='fixture-only',ANTHROPIC_AUTH_TOKEN='',DISABLE_TELEMETRY='1')
for key in list(env):
    if key in ('NO_COLOR','CLAUDE_CODE_CHILD_SESSION','CLAUDECODE','CLAUDE_CODE_ENTRYPOINT','CLAUDE_PID','CLAUDE_PLUGIN_DATA','CLAUDE_CODE_EXECPATH') or key.startswith(('CLAUDE_CODE_SESSION_','CLAUDE_CODE_BRIDGE_','CLAUDE_CODE_MESSAGING_')):env.pop(key,None)
master,slave=pty.openpty();fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',40,160,0,0))
command=[*shlex.split(os.environ.get('CLAUDE_BIN','claude')),'--debug-file',str(root/'debug.log'),'--setting-sources','','--settings','{"enabledPlugins":{},"remoteControlAtStartup":false,"tui":"fullscreen"}','--plugin-dir',str(fixture),'--plugin-dir',str(plugin),'--strict-mcp-config','--mcp-config','{"mcpServers":{}}','--tools','']
process=subprocess.Popen(command,stdin=slave,stdout=slave,stderr=slave,cwd=plugin,env=env);os.close(slave)
raw=bytearray();log=(root/'terminal.bin').open('wb')
trust_answered=False
screen=None
if '--short-window' in sys.argv:
    import pyte
    screen=pyte.Screen(160,40);terminal_stream=pyte.ByteStream(screen)
def send(text):
    """Write UTF-8 input or terminal control sequences to the Claude PTY."""
    os.write(master,text.encode())
def read(seconds=.05):
    """Capture available PTY output and answer terminal capability queries."""
    if select.select([master],[],[],seconds)[0]:
        chunk=os.read(master,65536);raw.extend(chunk);log.write(chunk);log.flush()
        if screen is not None:terminal_stream.feed(chunk)
        if b'\x1b[6n' in chunk:send('\x1b[1;1R')
        if b'\x1b[c' in chunk:send('\x1b[?1;2c')
def clean(start=0):
    """Decode captured output and strip ANSI sequences for text assertions."""
    text=bytes(raw[start:]).decode('utf-8','replace')
    return re.sub(r'\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))','',text)
def wait(check,label,timeout=35):
    """Read until a condition passes, preserving diagnostic output on timeout."""
    global trust_answered
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        read()
        if not trust_answered and 'Yes,Itrustthisfolder' in ''.join(clean().split()):
            # A custom account launcher may override our temporary config directory.
            # Accept only this test checkout, after the prompt finishes mounting.
            time.sleep(1)
            if '❯No,exit' in ''.join(clean().split()):send('\x1b[B');time.sleep(.5)
            send('\r');trust_answered=True
        if check():print('PASS:',label,flush=True);return
        if process.poll() is not None:raise AssertionError('Claude exited: '+str(process.returncode))
    (root/'screen-raw-text.txt').write_text(clean())
    raise AssertionError(label+' timed out')
def press(x,y,key):
    """Click a settled pointer target and verify its completed ui.press event."""
    # Wait for the native frame and its pointer targets to settle after a redraw.
    until=time.monotonic()+.5
    while time.monotonic()<until:read(.05)
    file=root/'press.json'
    if file.exists():file.unlink()
    send(f'\x1b[<0;{x};{y}M');time.sleep(.08);send(f'\x1b[<0;{x};{y}m')
    wait(lambda:file.exists() and key in file.read_text(),key,timeout=8)
try:
    wait(lambda:'等待Agent回复' in ''.join(clean().split()),'initial translation pane',timeout=90)
    payload='\x1b[200~'+'文'*60000+'\x1b[201~'
    def paste():
        """Write the bracketed-paste payload in chunks while output is drained."""
        encoded=payload.encode()
        for at in range(0,len(encoded),4096):os.write(master,encoded[at:at+4096])
    writer=threading.Thread(target=paste);writer.start()
    wait(lambda:not writer.is_alive(),'large input pasted')
    for _ in range(10):read(.05)
    send('\r')
    wait(lambda:(root/'received.json').exists(),'long input accepted by fixture agent')
    wait(lambda:(root/'id.json').exists(),'long input message identity available')
    message=json.loads((root/'id.json').read_text())
    mark=len(raw);send('/translate input '+message['id']+'\r')
    wait(lambda:'1/4页' in ''.join(clean(mark).split()),'full input inspector opened from actual command')
    wait(lambda:json.loads((root/'pane.json').read_text())['scroll']['offset']==0,'full input starts at the top')
    props=json.loads((root/'pane.json').read_text());columns=props['bodyColumns']
    start_x=160-columns+1
    if columns<42:press(start_x+2,5,'input-full-next')
    else:press(start_x+9,4,'input-full-next')
    for _ in range(10):read(.05)
    wait(lambda:json.loads((root/'pane.json').read_text())['scroll']['offset']==0,'new full-content page starts at the top')
    divider=160-columns
    send(f'\x1b[<0;{divider};8M');time.sleep(.1);send('\x1b[<32;138;8M');time.sleep(.1);send('\x1b[<0;138;8m')
    wait(lambda:(root/'pane.json').exists() and json.loads((root/'pane.json').read_text())['bodyColumns']<30,'narrow inspector pane')
    columns=json.loads((root/'pane.json').read_text())['bodyColumns'];start_x=160-columns+1
    press(start_x+2,6,'input-full-next')
    for _ in range(10):read(.05)
    press(start_x+2,7,'input-full-close')
    assert json.loads(config.read_text())['inputRight']=='off'
    print('PASS: persistent right-side display remains off',flush=True)
    print('Received length:',json.loads((root/'received.json').read_text())['length'],flush=True)

    if screen is not None:
        def visible():
            """Read the current terminal frame, preserving wide-character cells."""
            return [''.join(screen.buffer[y][x].data for x in range(screen.columns)) for y in range(screen.lines)]
        def control_row():
            """Find the compact inspector toolbar rather than transcript command text."""
            return next((y for y,line in enumerate(visible()) if '返回' in line and re.search(r'\d+/\d+',line)),None)
        def click_compact(label,key):
            """Click a compact toolbar action at its actual terminal coordinates."""
            # A resize can move the toolbar after the first frame arrives.
            until=time.monotonic()+.5
            while time.monotonic()<until:read(.05)
            row=control_row()
            assert row is not None, 'compact toolbar is not visible'
            line=visible()[row]
            press(line.index(label)+1,row+1,key)
        mark=len(raw);send('/translate input '+message['id']+'\r')
        wait(lambda:'1/4页' in ''.join(clean(mark).split()),'reopen full input for short-window checks')
        for height in (12,10):
            screen.resize(lines=height,columns=64)
            fcntl.ioctl(master,termios.TIOCSWINSZ,struct.pack('HHHH',height,64,0,0))
            os.kill(process.pid,signal.SIGWINCH)
            wait(lambda:control_row() is not None and json.loads((root/'pane.json').read_text())['bodyColumns']==60
                 and json.loads((root/'pane.json').read_text())['scroll']['bodyRows'] <= (2 if height==12 else 1),
                 f'compact controls visible at 64x{height}')
            assert '>' in visible()[control_row()], 'next-page control is clipped'
            (root/f'compact-64x{height}.txt').write_text('\n'.join(visible()))
            click_compact('>','input-full-next')
            wait(lambda:control_row() is not None and '2/4' in visible()[control_row()], 'compact next page')
            click_compact('<','input-full-prev')
            wait(lambda:control_row() is not None and '1/4' in visible()[control_row()], 'compact previous page')
        click_compact('返回','input-full-close')
        wait(lambda:control_row() is None,'compact return closes full input')
        print('PASS: short-window navigation at 64x12 and 64x10',flush=True)

finally:
    process.terminate()
    try:process.wait(timeout=5)
    except subprocess.TimeoutExpired:process.kill();process.wait()
    os.close(master);log.close();server.shutdown();server.server_close()
