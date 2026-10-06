#!/usr/bin/env python3
"""Real Claude Code PTY smoke test. Needs pyte; never calls a real agent model.

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
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import pyte

PLUGIN = Path(__file__).resolve().parents[1]
ANSWER = '# Overview\n\nThis is a **live response**. The original reply remains visible on the left.\n\n- **Bold item**\n- Inline `const answer = 42`\n\n```python\nprint(42)\n```'
LONG_ANSWER = '\n\n'.join(f'- **Item {i:03d}**: A detailed explanation in English.' for i in range(80))
TABLE_ANSWER = '''# Comparison

| Option | Speed | Description |
| --- | --- | --- |
| Local | Fast | Detects language on this computer without making a network request. |
| LLM | Varies | Uses your configured model to identify the language before translating. |

End of comparison.'''

class Harness:
    def __init__(self, root, columns=160, rows=40):
        self.root = root
        self.columns, self.rows = columns, rows
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
                    self.wfile.write(json.dumps({'choices':[{'message':{'content':'Please show a long reply.' if '长文' in body['messages'][-1]['content'] else 'Please explain this feature.'},'finish_reason':'stop'}]}).encode())
                    return
                translated = body['messages'][-1]['content']
                for english, chinese in [('Overview','概览'),('This is a **live response**.','这是**译文**。'),('The original reply remains visible on the left.','原回复仍在左侧。'),('Bold item','加粗条目'),('Inline','内联代码'),('Item','项目'),('A detailed explanation in English.','这是一段详细说明。')]:
                    translated = translated.replace(english, chinese)
                for english, chinese in [('Comparison','对比'),('Option','项目'),('Speed','速度'),('Description','说明'),('Local','本地脚本'),('Fast','快'),('LLM','模型'),('Varies','不固定'),('Detects language on this computer without making a network request.','在这台电脑上判断语言，不需要发送网络请求。'),('Uses your configured model to identify the language before translating.','使用配置的模型判断语言，再把回复翻译成目标语言。'),('End of comparison.','表格结束。')]:
                    translated = translated.replace(english, chinese)
                for part in [translated[:len(translated)//2], translated[len(translated)//2:]]:
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
        config.write_text(json.dumps({'enabled':True,'baseUrl':f'http://127.0.0.1:{self.server.server_port}/v1','model':'fixture','apiKey':'fixture-secret-A123','jevKey':'fixture-secret-J456','apiKeyEnv':'','baseUrlEnv':'','modelEnv':''}))
        fixture = root/'fixture'; (fixture/'.claude-plugin').mkdir(parents=True); (fixture/'hooks').mkdir()
        (fixture/'.claude-plugin/plugin.json').write_text('{"name":"translate-fixture","version":"0.0.1"}')
        (fixture/'hooks/hooks.json').write_text('{"modules":["./register.ts"]}')
        (fixture/'hooks/register.ts').write_text('''export const register = on => {
  let input = '';
  on('ui.press', async ($,e,next) => { await $.fs.write('''+json.dumps(str(root/'press.json'))+''',JSON.stringify(e)); return next(e); });
  on('turn.start', async ($,e,next) => {
    input = e.text;
    await $.fs.write('''+json.dumps(str(root/'received.json'))+''', JSON.stringify({text:e.text}));
    return next(e);
  });
  on('turn.step', async function* ($,e) {
    const answer = input.includes('long reply') ? '''+json.dumps(LONG_ANSWER)+''' : '''+json.dumps(ANSWER)+''';
    yield {kind:'text',index:0,text:answer};
    return {turnId:e.turnId,index:e.index,answer,toolUses:[],stopReason:'end_turn',usage:null};
  });
}
''')
        self.master, slave = pty.openpty()
        fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',rows,columns,0,0))
        env = dict(os.environ, TERM='xterm-256color', CLAUDE_CODE_NO_FLICKER='1', TRANSLATE_VIEW_CONFIG=str(config),
                   ANTHROPIC_BASE_URL='http://127.0.0.1:1', ANTHROPIC_API_KEY='fixture-only', ANTHROPIC_AUTH_TOKEN='', DISABLE_TELEMETRY='1')
        env.pop('NO_COLOR', None)
        env['FORCE_COLOR'] = '1'
        command = [os.environ.get('CLAUDE_BIN', 'claude'),'--setting-sources','','--settings','{"enabledPlugins":{},"remoteControlAtStartup":false}',
                   '--plugin-dir',str(fixture),'--plugin-dir',str(PLUGIN),'--strict-mcp-config','--mcp-config','{"mcpServers":{}}','--tools','']
        self.process = subprocess.Popen(command,stdin=slave,stdout=slave,stderr=slave,cwd=PLUGIN,env=env)
        os.close(slave)
        self.screen = pyte.Screen(columns,rows); self.stream = pyte.Stream(self.screen)
        self.decoder = codecs.getincrementaldecoder('utf8')('replace')
        self.log = (root/'terminal.bin').open('wb')
    def send(self, text): os.write(self.master,text.encode())
    def read(self, seconds=.1):
        if not select.select([self.master],[],[],seconds)[0]: return
        raw=os.read(self.master,65536);self.log.write(raw);self.log.flush()
        self.stream.feed(self.decoder.decode(raw))
        if b'\x1b[6n' in raw: self.send(f'\x1b[{self.screen.cursor.y+1};{self.screen.cursor.x+1}R')
        if b'\x1b[c' in raw: self.send('\x1b[?1;2c')
    def view(self):
        # Native redraws can temporarily leave a wide-character continuation
        # cell without its lead cell; pyte.display crashes on those frames.
        return '\n'.join(''.join(self.screen.buffer[row][col].data for col in range(self.columns)) for row in range(self.rows))
    def pane(self):
        divider = next(col for col in range(self.columns) if self.screen.buffer[0][col].data == '│')
        return [''.join(self.screen.buffer[row][col].data for col in range(divider+1,self.columns)).rstrip() for row in range(self.rows)]
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
        time.sleep(.5)
        end=time.monotonic()+1
        while time.monotonic()<end and select.select([self.master],[],[],.05)[0]: self.read(.01)
        for row in range(self.rows):
            for column in range(self.columns):
                chunk=''.join(self.screen.buffer[row][col].data for col in range(column,min(self.columns,column+len(text)*2)))
                if chunk.startswith(text):
                    print('Click',text,'at',column+1,row+1,flush=True); self.send(f'\x1b[<0;{column+1};{row+1}M'); time.sleep(.08); self.send(f'\x1b[<0;{column+1};{row+1}m'); return
        raise AssertionError('No clickable '+text)
    def resize_pane(self, columns=90):
        self.read(.2)
        divider = next(col for col in range(self.columns) if self.screen.buffer[0][col].data == '│')
        target=self.columns-columns
        self.send(f'\x1b[<0;{divider+1};8M'); time.sleep(.15)
        self.send(f'\x1b[<32;{target};8M'); time.sleep(.15)
        self.send(f'\x1b[<0;{target};8m')
        self.wait(lambda:any(self.screen.buffer[0][col].data=='│' for col in range(max(1,target-3),min(self.columns,target+3))), f'pane resized to about {columns} columns')
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

def settings_check(h):
    h.click('设置')
    h.wait(lambda:'模型接口' in h.view() and '语言检测:' in h.view(),'settings opens language detection overview')
    if '--settings-wide' in sys.argv:
        assert any(all(name in row for name in ['语言检测','模型接口','环境变量','Jev 接口','翻译 Prompt']) for row in h.view().splitlines()[:4]), 'wide tabs are not on one row'
    h.click('语言检测:')
    h.send('\x1b[B\r')
    h.wait(lambda:'检测模型:' in h.view(),'LLM detection exposes an independent model field')
    for section, fields in [('模型接口',['接口 Base URL:', '翻译模型名:', '新的 API Key:', '完整 POST URL（可选）:']), ('环境变量',['地址变量名:', '密钥变量名:', '模型变量名:']), ('Jev 接口',['Jev POST URL:', 'Jev 模型名:', '新的 Jev API Key:']), ('翻译 Prompt',['发送前:', '回复:'])]:
        h.click(section)
        title = {'模型接口':'翻译模型', '环境变量':'环境变量绑定', 'Jev 接口':'Jev ·', '翻译 Prompt':'分别设置两个方向'}[section]
        h.wait(lambda:title in h.view(), 'settings section rendered: '+section)
        if '--settings-wide' in sys.argv and section in ('模型接口','Jev 接口'):
            suffix='****A123' if section=='模型接口' else '****J456'
            h.wait(lambda:suffix in h.view() and '本机配置' in h.view(), 'masked key source visible: '+section)
            assert 'fixture-secret' not in h.view(), 'raw saved key exposed'
        for field in fields:
            end=time.monotonic()+5
            while field not in h.view() and time.monotonic()<end:
                h.send(f'\x1b[<65;{h.columns-5};{h.rows-9}M'); h.read(.08)
            assert field in h.view(), 'unreachable setting: '+field
    h.click('取消')
    h.wait(lambda:'Translation' in h.view() and '翻译设置' not in h.view(),'closing settings restores translation pane')
    h.click('设置')
    h.wait(lambda:'语言检测:' in h.view(),'reopening settings resets to language overview')
    h.click('取消')
    h.wait(lambda:'Translation' in h.view() and '翻译设置' not in h.view(),'return to reply')

def table_check(h):
    h.resize_pane(110)
    h.send('请解释表格。\r')
    h.wait(lambda:'表格结束。' in '\n'.join(h.pane()) and '翻译中' not in h.view(), 'translated table completed')
    request_count = len(h.requests)
    for size in (110,40,22,110):
        h.resize_pane(size)
        def correct():
            pane = h.pane()
            compact=''.join(''.join(pane).split())
            complete = '表格结束。' in compact and '在这台电脑上判断语言，不需要发送网络请求。' in compact and '使用配置的模型判断语言，再把回复翻译成目标语言。' in compact
            if size == 110:
                return any('┌' in row and '┐' in row for row in pane) and any('本地脚本' in row and '快' in row and '网络请求' in row for row in pane)
            return complete and '项目: 本地脚本' in pane and '速度: 快' in pane and '项目: 模型' in pane and '速度: 不固定' in pane and not any(any(c in row for c in '┌┬└┴') for row in pane)
        h.wait(correct, f'table layout fits {size}-column pane')
        pane=h.pane()
        (h.root/f'table-{size}.txt').write_text('\n'.join(pane))
        if size != 110:
            first=pane.index('项目: 本地脚本');second=pane.index('项目: 模型')
            assert any(row and set(row)=={'─'} for row in pane[first+1:second]), 'records have no separator'
            compact=''.join(''.join(pane).split())
            assert '在这台电脑上判断语言，不需要发送网络请求。' in compact, 'first cell was truncated'
            assert '使用配置的模型判断语言，再把回复翻译成目标语言。' in compact, 'second cell was truncated'
    assert len(h.requests)==request_count, 'resizing called the translation provider again'
    print('Table smoke completed.',flush=True)

def main():
    global ANSWER
    tables = '--tables' in sys.argv
    if tables: ANSWER = TABLE_ANSWER
    root=Path(tempfile.mkdtemp(prefix='translate-view-smoke-'))
    print('Artifacts:',root,flush=True)
    narrow = '--settings-only' in sys.argv
    wide = '--settings-wide' in sys.argv
    h=Harness(root,220 if wide or tables else 120 if narrow else 160,45 if tables else 40 if wide else 28 if narrow else 40)
    try:
        h.wait(lambda:'等待 Agent 回复' in h.view(),'full-height translation dock')
        if tables:
            table_check(h);return
        if wide: h.resize_pane()
        elif narrow: h.resize_pane(22)
        if narrow or wide:
            settings_check(h)
            print('Settings smoke completed.',flush=True); return
        first='请解释第一个功能。';second='请说明第二个功能。'
        h.send(first+'\r')
        h.wait(lambda:'这是译文。' in h.view() and first in h.view(),'first translated reply with original prompt')
        received=json.loads((root/'received.json').read_text())
        assert received['text']=='Please explain this feature.'
        h.send(second+'\r')
        h.wait(lambda:first in h.view() and second in h.view() and len(h.requests)>=4 and '翻译中' not in h.view() and '这是译文。' in h.view(),'identical translations retain distinct original prompts')
        assert 'Please explain this feature.' not in h.view()
        assert 'live response' in h.view()
        right = '\n'.join(line.split('│',1)[-1] for line in h.view().splitlines() if '│' in line)
        assert '加粗条目' in right and '**' not in right and '```' not in right, right
        assert 'constanswer=42' in ''.join(right.split()) and 'print(42)' in right
        assert any(cell.bold and cell.data == '加' for row in h.screen.buffer.values() for cell in row.values()), 'bold Markdown was not styled'
        settings_check(h)
        outgoing_before = sum(bool(r.get('stream')) for r in h.requests)
        h.send('请给我长文。\r')
        h.wait(lambda:'项目 079' in h.view() and '翻译中' not in h.view(),'long Markdown follows the last paragraph',timeout=55)
        assert sum(bool(r.get('stream')) for r in h.requests) - outgoing_before == 1, 'finished reply was translated paragraph by paragraph'
        received=json.loads((root/'received.json').read_text())
        for _ in range(50):
            h.send('\x1b[<64;140;15M'); h.read(.03)
        h.wait(lambda:'项目 000' in h.view(),'native Markdown scroll reaches first paragraph')
        assert 'Translation' in '\n'.join(h.view().splitlines()[:3]) and 'Agent 接收' in '\n'.join(h.view().splitlines()[:4]), 'header scrolled away'
        h.click('回到底部')
        h.wait(lambda:'项目 079' in h.view(),'back to bottom restores follow')
        # A real drop must not erase the user's prompt. Make the local provider
        # unreachable, then verify the message remains available in the composer.
        p=root/'config.json';cfg=json.loads(p.read_text());cfg['baseUrl']='http://127.0.0.1:1';p.write_text(json.dumps(cfg))
        h.send('\x1b'); h.read(.3)  # Return keyboard focus from the pane to the composer.
        composer_row = next(row for row in reversed(range(h.rows)) if h.screen.buffer[row][0].data == '❯') + 1
        h.send(f'\x1b[<0;3;{composer_row}M\x1b[<0;3;{composer_row}m');h.read(.3)
        failed='这个输入应该保留下来。'
        h.send(failed+'\r')
        h.wait(lambda:'Prompt dropped by a hook:' in h.view() and '连接翻译接口失败' in h.view(),'failed translation blocks agent submission')
        assert failed in h.view(), 'failed prompt was lost'
        assert json.loads((root/'received.json').read_text())==received, 'failure reached agent'
        print('Terminal smoke completed.',flush=True)
    finally: h.close()

if __name__=='__main__': main()
