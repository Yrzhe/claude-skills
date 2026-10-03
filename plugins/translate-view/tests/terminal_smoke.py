#!/usr/bin/env python3
"""Real Claude-work PTY smoke test. Needs pyte; never calls a real agent model.

Run: PYTHONPATH=/path/to/pyte python3 tests/terminal_smoke.py
Only synthetic test prompts and a local translation endpoint are used.
"""
import codecs
import fcntl
import json
import os
import pty
import select
import struct
import subprocess
import tempfile
import termios
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import pyte

PLUGIN = Path(__file__).resolve().parents[1]
ANSWER = 'This is a live response. The original reply remains visible on the left.'

class Harness:
    def __init__(self, root):
        self.root = root
        self.requests = []
        owner = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                owner.requests.append(body)
                self.send_response(200)
                stream = body.get('stream')
                self.send_header('Content-Type', 'text/event-stream' if stream else 'application/json')
                self.end_headers()
                if not stream:
                    self.wfile.write(json.dumps({'choices':[{'message':{'content':'Please explain this feature.'},'finish_reason':'stop'}]}).encode())
                    return
                for part in ['这是译文。', '原回复仍在左侧。']:
                    self.wfile.write(('data: '+json.dumps({'choices':[{'index':0,'delta':{'content':part}}]},ensure_ascii=False)+'\n\n').encode())
                    self.wfile.flush(); time.sleep(.15)
                self.wfile.write(b'data: [DONE]\n\n')
        class Server(ThreadingHTTPServer):
            def handle_error(self, request, client_address):
                import sys
                if not isinstance(sys.exc_info()[1], (BrokenPipeError, ConnectionResetError)):
                    super().handle_error(request, client_address)
        self.server = Server(('127.0.0.1',0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        config = root/'config.json'
        config.write_text(json.dumps({'enabled':True,'baseUrl':f'http://127.0.0.1:{self.server.server_port}/v1','model':'fixture','apiKeyEnv':'','baseUrlEnv':'','modelEnv':''}))
        fixture = root/'fixture'; (fixture/'.claude-plugin').mkdir(parents=True); (fixture/'hooks').mkdir()
        (fixture/'.claude-plugin/plugin.json').write_text('{"name":"translate-fixture","version":"0.0.1"}')
        (fixture/'hooks/hooks.json').write_text('{"modules":["./register.ts"]}')
        (fixture/'hooks/register.ts').write_text('''export const register = on => {
  on('ui.press', async ($,e,next) => { await $.fs.write('''+json.dumps(str(root/'press.json'))+''',JSON.stringify(e)); return next(e); });
  on('turn.start', async ($,e,next) => {
    await $.fs.write('''+json.dumps(str(root/'received.json'))+''', JSON.stringify({text:e.text}));
    return next(e);
  });
  on('turn.step', async function* ($,e) {
    const answer = '''+json.dumps(ANSWER)+''';
    yield {kind:'text',index:0,text:answer};
    return {turnId:e.turnId,index:e.index,answer,toolUses:[],stopReason:'end_turn',usage:null};
  });
}
''')
        self.master, slave = pty.openpty()
        fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',40,160,0,0))
        env = dict(os.environ, TERM='xterm-256color', CLAUDE_CODE_NO_FLICKER='1', TRANSLATE_VIEW_CONFIG=str(config),
                   ANTHROPIC_BASE_URL='http://127.0.0.1:1', ANTHROPIC_API_KEY='fixture-only', ANTHROPIC_AUTH_TOKEN='', DISABLE_TELEMETRY='1')
        command = ['claude-work','--setting-sources','','--settings','{"enabledPlugins":{},"remoteControlAtStartup":false}',
                   '--plugin-dir',str(fixture),'--plugin-dir',str(PLUGIN),'--strict-mcp-config','--mcp-config','{"mcpServers":{}}','--tools','']
        self.process = subprocess.Popen(command,stdin=slave,stdout=slave,stderr=slave,cwd=PLUGIN,env=env)
        os.close(slave)
        self.screen = pyte.Screen(160,40); self.stream = pyte.Stream(self.screen)
        self.decoder = codecs.getincrementaldecoder('utf8')('replace')
        self.log = (root/'terminal.bin').open('wb')
    def send(self, text): os.write(self.master,text.encode())
    def read(self, seconds=.1):
        if not select.select([self.master],[],[],seconds)[0]: return
        raw=os.read(self.master,65536);self.log.write(raw);self.log.flush()
        self.stream.feed(self.decoder.decode(raw))
        if b'\x1b[6n' in raw: self.send(f'\x1b[{self.screen.cursor.y+1};{self.screen.cursor.x+1}R')
        if b'\x1b[c' in raw: self.send('\x1b[?1;2c')
    def view(self): return '\n'.join(self.screen.display)
    def wait(self, condition, label, timeout=25):
        end=time.monotonic()+timeout
        approved_trust = approved_key = False
        while time.monotonic()<end:
            self.read()
            if not approved_trust and 'Yes, I trust this folder' in self.view():
                self.send('\x1b[B'); time.sleep(.25); self.read(); self.send('\r'); approved_trust = True; continue
            if not approved_key and 'Do you want to use this API key?' in self.view():
                self.send('\x1b[A'); time.sleep(.25); self.read(); self.send('\r'); approved_key = True; continue
            if condition():
                (self.root/'screen.txt').write_text(self.view())
                print('PASS:',label,flush=True); return
        (self.root/'screen.txt').write_text(self.view())
        if (self.root/'press.json').exists(): print('Last press:',(self.root/'press.json').read_text(),flush=True)
        raise AssertionError(label+' timed out; see '+str(self.root/'screen.txt'))
    def click(self, text):
        time.sleep(.3); self.read()
        for row in range(40):
            for column in range(160):
                chunk=''.join(self.screen.buffer[row][col].data for col in range(column,min(160,column+len(text)*2)))
                if chunk.startswith(text):
                    print('Click',text,'at',column+1,row+1,flush=True); self.send(f'\x1b[<0;{column+1};{row+1}M'); time.sleep(.08); self.send(f'\x1b[<0;{column+1};{row+1}m'); return
        raise AssertionError('No clickable '+text)
    def close(self):
        try:
            self.send('\x1b');self.read(.2);self.send('/exit\r')
            end=time.monotonic()+3
            while self.process.poll() is None and time.monotonic()<end: self.read()
        except OSError: pass
        if self.process.poll() is None: self.process.terminate()
        try: self.process.wait(timeout=5)
        except subprocess.TimeoutExpired: self.process.kill(); self.process.wait()
        self.log.close();os.close(self.master)
        self.server.shutdown();self.server.server_close()

def main():
    root=Path(tempfile.mkdtemp(prefix='translate-view-smoke-'))
    print('Artifacts:',root,flush=True)
    h=Harness(root)
    try:
        h.wait(lambda:'等待 Agent 回复' in h.view(),'full-height translation dock')
        first='请解释第一个功能。';second='请说明第二个功能。'
        h.send(first+'\r')
        h.wait(lambda:'这是译文。' in h.view() and first in h.view(),'first translated reply with original prompt')
        received=json.loads((root/'received.json').read_text())
        assert received['text']=='Please explain this feature.'
        h.send(second+'\r')
        h.wait(lambda:first in h.view() and second in h.view() and len(h.requests)>=4 and '翻译中' not in h.view() and '这是译文。' in h.view(),'identical translations retain distinct original prompts')
        assert 'Please explain this feature.' not in h.view()
        assert ANSWER in h.view()
        h.click('设置')
        h.wait(lambda:'翻译设置' in h.view(),'settings button opens settings')
        h.click('Prompt')
        h.wait(lambda:'发送前:' in h.view() and '回复:' in h.view(),'independent custom prompts')
        h.click('取消')
        h.wait(lambda:'Translation' in h.view() and '翻译设置' not in h.view(),'closing settings restores translation pane')
        # A real drop must not erase the user's prompt. Make the local provider
        # unreachable, then verify the message remains available in the composer.
        p=root/'config.json';cfg=json.loads(p.read_text());cfg['baseUrl']='http://127.0.0.1:1';p.write_text(json.dumps(cfg))
        failed='这个输入应该保留下来。'
        h.send(failed+'\r')
        h.wait(lambda:'发送前翻译失败' in h.view(),'failed translation blocks agent submission')
        assert failed in h.view(), 'failed prompt was lost'
        assert json.loads((root/'received.json').read_text())==received, 'failure reached agent'
        print('Terminal smoke completed.',flush=True)
    finally: h.close()

if __name__=='__main__': main()
