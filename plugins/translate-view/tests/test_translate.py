import importlib.util
import io
import json
import os
import stat
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('translate',Path(__file__).parents[1]/'scripts/translate.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.env=patch.dict(os.environ, {'TRANSLATE_VIEW_CONFIG':self.tmp.name+'/private/config.json'}, clear=True)
        self.env.start()
    def tearDown(self):
        self.env.stop();self.tmp.cleanup()
    def config(self,**kw):
        return dict(m.DEFAULTS,enabled=True,baseUrl='http://localhost:4321/v1',model='translator',**kw)
    def test_input_display_defaults_and_old_config(self):
        self.assertEqual(m.load_config().get('inputTranslation'),'off')
        self.assertEqual(m.load_config().get('inputLeft'),'translation')
        self.assertEqual(m.load_config().get('inputRight'),'both')
        m.config_path().parent.mkdir(parents=True)
        m.config_path().write_text(json.dumps({'enabled':True,'model':'old'}))
        cfg=m.load_config()
        self.assertEqual(cfg.get('inputTranslation'),'off')
        self.assertEqual(cfg.get('inputLeft'),'translation')
        self.assertEqual(cfg.get('inputRight'),'both')
        self.assertTrue(cfg['enabled'])
    def test_input_display_modes_round_trip(self):
        for position in ('off','left','right','both'):
            for left in ('off','original','translation','both'):
                for right in ('off','original','translation','both'):
                    with self.subTest(position=position,left=left,right=right):
                        pub=m.save_config({'inputTranslation':position,'inputLeft':left,'inputRight':right})
                        self.assertEqual(pub.get('inputTranslation'),position)
                        self.assertEqual(pub.get('inputLeft'),left)
                        self.assertEqual(pub.get('inputRight'),right)
                        self.assertEqual(m.load_config().get('inputRight'),right)
    def test_input_display_rejects_invalid_values(self):
        m.save_config({'model':'keep'})
        before=m.config_path().read_text()
        for key,values in [('inputTranslation',['unknown','LEFT',True,None]),('inputLeft',['unknown','BOTH',False,None]),('inputRight',['unknown','BOTH',False,None])]:
            for value in values:
                with self.subTest(key=key,value=value):
                    with self.assertRaises(m.TranslationError): m.save_config({key:value})
                    self.assertEqual(m.config_path().read_text(),before)
    def test_config_private_atomic_and_never_echoes_keys(self):
        pub=m.save_config({'apiKey':'SECRET','jevKey':'JEV_SECRET','model':'custom'})
        self.assertTrue(pub['hasApiKey']);self.assertNotIn('SECRET',json.dumps(pub))
        self.assertEqual(stat.S_IMODE(m.config_path().stat().st_mode),0o600)
        m.save_config({'apiKey':''});self.assertEqual(m.load_config()['apiKey'],'SECRET')
        m.save_config({'clearApiKey':True});self.assertEqual(m.load_config()['apiKey'],'')
    def test_environment_and_exact_endpoint(self):
        cfg=dict(m.DEFAULTS)
        with patch.dict(os.environ,{'OPENAI_BASE_URL':'https://local.example/v1','OPENAI_MODEL':'my-model','OPENAI_API_KEY':'env-secret'}):
            self.assertEqual(m.endpoint(cfg),'https://local.example/v1/chat/completions')
            self.assertEqual(m.chat_body(cfg,[])['model'],'my-model')
            self.assertNotIn('env-secret',json.dumps(m.public_config(cfg)))
            cfg['postUrl']='http://127.0.0.1:8000/custom?route=a'
            self.assertEqual(m.endpoint(cfg),cfg['postUrl'])
            cfg['apiKey']='direct';self.assertEqual(m.value(cfg,'apiKey','apiKeyEnv'),'direct')
    def test_disabled_helper_passes_through_without_calling_provider(self):
        m.save_config({'enabled':False,'baseUrl':'http://127.0.0.1:1','model':'fake'})
        for action in ('translate','stream'):
            result=subprocess.run([sys.executable,str(Path(m.__file__))],input=json.dumps(dict(action=action,direction='incoming',text='保留原文')),capture_output=True,text=True,timeout=5)
            self.assertEqual(result.returncode,0)
            self.assertEqual(json.loads(result.stdout),dict(type='done',text='保留原文',skipped=True,disabled=True))

    def test_network_errors_identify_failure_without_exposing_private_details(self):
        for error,expected in [(TimeoutError('PRIVATE_HOST'),'90 秒'),(socket.gaierror('PRIVATE_HOST'),'DNS'),(ssl.SSLCertVerificationError('PRIVATE_HOST'),'证书'),(ssl.SSLError('PRIVATE_HOST'),'TLS'),(ConnectionRefusedError('PRIVATE_HOST'),'拒绝连接'),(ConnectionResetError('PRIVATE_HOST'),'重置')]:
            with self.subTest(kind=type(error).__name__):
                with patch.object(m.urllib.request.OpenerDirector,'open',side_effect=m.urllib.error.URLError(error)):
                    with self.assertRaises(m.TranslationError) as raised:
                        m.request('https://example.com/v1','PRIVATE_KEY',{})
                self.assertIn(expected,str(raised.exception))
                self.assertNotIn('PRIVATE',str(raised.exception))
        with patch.object(m,'translate_content',side_effect=TimeoutError('PRIVATE_HOST')):
            with self.assertRaisesRegex(m.TranslationError,'90 秒'):
                m.translate(self.config(),'Please translate this message.','outgoing',lambda _:None)

    def test_script_ignores_code_and_detects_prose_conservatively(self):
        self.assertEqual(m.script_language('你好，请帮我修改这个文件。\n```py\nprint("hello")\n```'),'zh')
        self.assertEqual(m.script_language('Please fix the code and explain why.'),'en')
        self.assertEqual(m.script_language('```py\nx = 1\n```'),'none')
        self.assertEqual(m.script_language('これは日本語です。'),'ja')
        self.assertEqual(m.script_language('안녕하세요'),'ko')
        self.assertEqual(m.script_language('bonjour tout le monde'),'unknown')
        self.assertEqual(m.script_language('https://example.com/a.py'),'none')
    def test_target_language_skips_network_and_preserves_whitespace(self):
        cfg=self.config()
        with patch.object(m,'request',side_effect=AssertionError('no network')):
            got=m.translate(cfg,'  已经是中文回复。\n\n','outgoing')
            self.assertTrue(got['skipped']);self.assertEqual(got['text'],'  已经是中文回复。\n\n')
    def test_protected_literals_and_custom_prompt(self):
        text='请看 [Image #1] [link](https://example.com/a?b=1) 和 `rm -rf /tmp/a`。\n```py\nx="中文"\n```\n'
        seen=[]
        def request(url,key,body):
            seen.append(body)
            content=body['messages'][1]['content'].replace('请看','Please see').replace(' 和 ',' and ')
            return FakeResponse({'choices':[{'message':{'content':content}}]})
        cfg=self.config(incomingPrompt='Be concise. Translate to {target_language}. Source: {source_language}.')
        with patch.object(m,'request',request): result=m.translate(cfg,text,'incoming')
        self.assertIn('Be concise. Translate to English.',seen[0]['messages'][0]['content'])
        for exact in ['[Image #1]','https://example.com/a?b=1','`rm -rf /tmp/a`','```py\nx="中文"\n```']:
            self.assertIn(exact,result['text'])
        self.assertTrue(result['text'].endswith('\n'))
    def test_corrupted_protection_is_rejected(self):
        with patch.object(m,'request',return_value=FakeResponse({'choices':[{'message':{'content':'Code changed'}}]})):
            with self.assertRaises(m.TranslationError): m.translate(self.config(),'请修改 `hello()`','incoming')
    def test_jev_payload_and_confidence(self):
        seen=[]
        def request(url,key,body):
            seen.append((url,body));return FakeResponse({'answers':{'language':{'choice':'en','confidence':.95}}})
        with patch.object(m,'request',request):
            self.assertEqual(m.detect(self.config(detection='jev'),'Hello there'),'en')
        self.assertEqual(seen[0][1]['questions']['language']['type'],'choice')
        self.assertEqual(seen[0][0],'https://api.typesafe.ai/v1/systemone')
        with patch.object(m,'request',return_value=FakeResponse({'answers':{'language':{'choice':'en','confidence':.1}}})):
            self.assertEqual(m.detect(self.config(detection='jev'),'Hello there'),'unknown')
    def test_llm_detection_uses_configured_chat_model(self):
        cfg=self.config(detection='llm')
        with patch.object(m,'request',return_value=FakeResponse({'choices':[{'message':{'content':'en'}}]})):
            self.assertEqual(m.detect(cfg,'Hello there'),'en')
    def test_environment_only_mode_ignores_literals_without_deleting_them(self):
        cfg=self.config(apiKey='PRIVATE',postUrl='http://localhost:4321/override',llmConfigSource='env')
        with patch.dict(os.environ, {'OPENAI_BASE_URL':'http://localhost:8765/v1','OPENAI_API_KEY':'ENV_SECRET','OPENAI_MODEL':'env-model'}):
            self.assertEqual(m.endpoint(cfg),'http://localhost:8765/v1/chat/completions')
            self.assertEqual(m.value(cfg,'apiKey','apiKeyEnv'),'ENV_SECRET')
            public=m.public_config(cfg)
            self.assertEqual(public['effectiveModel'],'env-model')
            self.assertNotIn('ENV_SECRET',json.dumps(public))
            self.assertNotIn('PRIVATE',json.dumps(public))
            self.assertEqual(cfg['apiKey'],'PRIVATE')
        self.assertFalse(m.public_config(cfg)['ready'])

    def test_detector_can_use_a_different_compatible_model(self):
        cfg=self.config(detection='llm',detectionModel='gemini-example')
        seen=[]
        def request(url,key,body):
            seen.append(body['model']);return FakeResponse({'choices':[{'message':{'content':'en'}}]})
        with patch.object(m,'request',request):self.assertEqual(m.detect(cfg,'Hello there'),'en')
        self.assertEqual(seen,['gemini-example'])
        self.assertEqual(cfg['model'],'translator')

    def test_sources_and_environment_status_never_reveal_secrets(self):
        cfg=self.config(apiKey='LOCAL_SECRET',apiKeyEnv='CUSTOM_TRANSLATION_KEY',jevConfigSource='env')
        with patch.dict(os.environ, {'CUSTOM_TRANSLATION_KEY':'ENV_SECRET','TYPESAFE_API_KEY':'JEV_SECRET','TYPESAFE_MODEL':'jev-custom','TYPESAFE_POST_URL':'http://localhost:4444/decisions'}):
            public=m.public_config(cfg)
            self.assertEqual(public['sources']['apiKey'],'manual')
            self.assertTrue(public['envStatus']['apiKeyEnv'])
            self.assertEqual(m.value(cfg,'jevModel','jevModelEnv'),'jev-custom')
            self.assertEqual(m.value(cfg,'jevUrl','jevUrlEnv'),'http://localhost:4444/decisions')
            self.assertEqual(public['sources']['jevKey'],'env')
            for secret in ('LOCAL_SECRET','ENV_SECRET','JEV_SECRET'):self.assertNotIn(secret,json.dumps(public))
            cfg['llmConfigSource']='env'
            self.assertEqual(m.public_config(cfg)['sources']['apiKey'],'env')
        self.assertEqual(m.public_config(cfg)['sources']['apiKey'],'missing')

    def test_masked_key_identifies_effective_key_and_separate_saved_key(self):
        cfg=self.config(apiKey='local-secret-A123',jevKey='local-jev-J456')
        with patch.dict(os.environ, {'OPENAI_API_KEY':'environment-secret-E789','TYPESAFE_API_KEY':'environment-jev-Z012'}):
            pub=m.public_config(cfg)
            self.assertEqual(pub['keyInfo']['apiKey'],dict(active='****A123',saved='****A123'))
            self.assertEqual(pub['configPath'],str(m.config_path()))
            cfg.update(llmConfigSource='env',jevConfigSource='env')
            pub=m.public_config(cfg)
            self.assertEqual(pub['keyInfo']['apiKey'],dict(active='****E789',saved='****A123'))
            self.assertEqual(pub['keyInfo']['jevKey'],dict(active='****Z012',saved='****J456'))
            for secret in ('local-secret-A123','local-jev-J456','environment-secret-E789','environment-jev-Z012'):
                self.assertNotIn(secret,json.dumps(pub))
            m.save_config(cfg)
            pub=m.save_config({'apiKey':'','jevKey':''})
            self.assertEqual(pub['keyInfo']['apiKey']['saved'],'****A123')
            pub=m.save_config({'clearApiKey':True,'llmConfigSource':'manual'})
            self.assertEqual(pub['keyInfo']['apiKey'],dict(active='****E789',saved=''))
        pub=m.public_config(cfg)
        self.assertEqual(pub['keyInfo']['apiKey'],dict(active='',saved='****A123'))
        self.assertEqual(pub['sources']['apiKey'],'missing')

    def test_short_or_control_character_keys_are_fully_masked(self):
        for key in ('abc','12345678901','long-secret-\x1b[0m'):
            self.assertEqual(m.masked_key(key),'****')
        self.assertEqual(m.masked_key('  '),'')

    def test_incomplete_response_rejected(self):
        with self.assertRaises(m.TranslationError): m.chat_text({'choices':[{'message':{'content':'partial'},'finish_reason':'length'}]})
        response=FakeResponse(raw=b'data: {"choices":[{"delta":{"content":"partial"}}]}\n\n',sse=True)
        with patch.object(m,'request',return_value=response):
            with self.assertRaises(m.TranslationError): m.translate(self.config(),'Please explain the code.','outgoing',lambda _:None)
    def test_placeholder_stream_does_not_flash_partial_tokens(self):
        self.assertEqual(m.visible_partial('look TVKEEPabcX',{'TVKEEPabcX0Z':'`x`'},'TVKEEPabcX'),'look ')
        self.assertEqual(m.visible_partial('look TVKEEPabcX0Z',{'TVKEEPabcX0Z':'`x`'},'TVKEEPabcX'),'look `x`')
    def test_actual_http_sse_and_json_fallback(self):
        captured=[]
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args): pass
            def do_POST(self):
                body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                captured.append((self.path,self.headers.get('Authorization'),body))
                self.send_response(200)
                stream='JSON' not in body['messages'][-1]['content']
                self.send_header('Content-Type','text/event-stream' if stream else 'application/json')
                self.end_headers()
                if stream:
                    parts=['Translated','.'] if 'English' in body['messages'][0]['content'] else ['这是','译文。']
                    for part in parts:
                        self.wfile.write(('data: '+json.dumps({'choices':[{'index':0,'delta':{'content':part}}]})+'\n\n').encode());self.wfile.flush()
                    self.wfile.write(b'data: [DONE]\n\n')
                else: self.wfile.write(json.dumps({'choices':[{'message':{'content':'Translated.'}}]}).encode())
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        cfg=self.config(apiKey='test-key');cfg['baseUrl']=f'http://127.0.0.1:{server.server_port}/v1'
        partials=[]
        try:
            got=m.translate(cfg,'Please explain the code.\n\n','outgoing',partials.append)
            self.assertEqual(got['text'],'这是译文。\n\n');self.assertEqual(len(partials),2)
            got=m.translate(cfg,'请解释代码。','incoming');self.assertEqual(got['text'],'Translated.')
            got=m.translate(cfg,'请返回 JSON。','incoming');self.assertEqual(got['text'],'Translated.')
            self.assertTrue(all(item[2]['stream'] for item in captured))
            self.assertEqual(captured[0][0],'/v1/chat/completions');self.assertEqual(captured[0][1],'Bearer test-key')
        finally: server.shutdown();server.server_close();thread.join()

    def test_long_input_chunk_boundaries_preserve_every_character_and_protected_span(self):
        code='```python\n'+('print("中文")\n'*10000)+'```\n'
        source=('请翻译这一段。\n\n'*300)+code+('中文 '*2000)+'[Image #1] [链接](https://example.com/path) `keep_this()`'+('文'*8000)
        chunks=list(m.input_chunks(source))
        self.assertEqual(''.join(chunks),source)
        boundaries=set();offset=0
        for chunk in chunks:
            self.assertTrue(chunk)
            offset+=len(chunk);boundaries.add(offset)
            if len(chunk)>m.INPUT_CHUNK:self.assertEqual(chunk,code)
        for match in m.PROTECTED.finditer(source):
            self.assertFalse(any(match.start()<cut<match.end() for cut in boundaries))
        with patch.object(m,'request',side_effect=AssertionError('code needs no translation')):
            self.assertEqual(m.translate(self.config(),code,'incoming')['text'],code)

    def test_over_100k_input_translates_in_order_without_losing_spacing_or_literals(self):
        source=('  请翻译 `x()`。\n\n'*8000)+'结束。\n'
        calls=[]
        def request(url,key,body):
            calls.append(body)
            content=body['messages'][-1]['content'].replace('请翻译','Please translate').replace('结束','End')
            return FakeResponse({'choices':[{'message':{'content':content},'finish_reason':'stop'}]})
        self.assertGreater(len(source),100000)
        with patch.object(m,'request',request):got=m.translate(self.config(),source,'incoming')
        self.assertEqual(got['text'],source.replace('请翻译','Please translate').replace('结束','End'))
        self.assertGreater(len(calls),1)
        self.assertTrue(all(body['stream'] for body in calls))

    def test_later_chunk_failure_never_emits_a_partial_incoming_prompt(self):
        calls=[]
        def request(url,key,body):
            calls.append(body)
            if len(calls)==2:raise TimeoutError('PRIVATE_HOST')
            return FakeResponse({'choices':[{'message':{'content':'First translated paragraph.'},'finish_reason':'stop'}]})
        source=('请翻译这一段。\n\n'*1000)
        with patch.object(m,'request',request):
            with self.assertRaisesRegex(m.TranslationError,'90 秒'):
                m.translate(self.config(),source,'incoming')
        self.assertEqual(len(calls),2)

    def test_input_and_output_limits_fail_explicitly(self):
        with self.assertRaisesRegex(m.TranslationError,'500000'):
            m.translate(self.config(),'文'*(m.MAX_TEXT+1),'incoming')
        with patch.object(m,'MAX_OUTPUT',4),patch.object(m,'request',return_value=FakeResponse({'choices':[{'message':{'content':'Too long'}}]})):
            with self.assertRaisesRegex(m.TranslationError,'译文过长'):
                m.translate(self.config(),'请翻译','incoming')

    def test_translated_chunks_without_source_whitespace_do_not_glue_words(self):
        source='文'*(m.INPUT_CHUNK+2)
        replies=[FakeResponse({'choices':[{'message':{'content':part}}]}) for part in ('First sentence.','Next sentence.')]
        with patch.object(m,'request',side_effect=replies):
            self.assertEqual(m.translate(self.config(),source,'incoming')['text'],'First sentence.\nNext sentence.')
        with patch.object(m,'request',side_effect=AssertionError('already target language')):
            self.assertEqual(m.translate(self.config(incomingLanguage='zh'),source,'incoming')['text'],source)

    @unittest.skipUnless(os.environ.get('TRANSLATE_SLOW_TEST')=='1','opt-in real 27-second response delay')
    def test_cli_waits_past_old_25s_deadline_and_emits_only_complete_long_prompt(self):
        captured=[]
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                captured.append(body)
                if len(captured)==1:time.sleep(27)
                self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
                translated=body['messages'][-1]['content'].replace('请翻译','Please translate')
                for part in (translated[:len(translated)//2],translated[len(translated)//2:]):
                    self.wfile.write(('data: '+json.dumps({'choices':[{'delta':{'content':part}}]})+'\n\n').encode());self.wfile.flush()
                self.wfile.write(b'data: [DONE]\n\n')
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        m.save_config({'enabled':True,'baseUrl':f'http://127.0.0.1:{server.server_port}/v1','model':'fixture'})
        source='请翻译这段文字。\n\n'*11000
        try:
            started=time.monotonic()
            result=subprocess.run([sys.executable,m.__file__],input=json.dumps(dict(action='translate',direction='incoming',text=source)),capture_output=True,text=True,timeout=60)
            self.assertGreaterEqual(time.monotonic()-started,27)
            self.assertEqual(result.returncode,0,result.stdout)
            self.assertEqual(len(result.stdout.splitlines()),1)
            self.assertEqual(json.loads(result.stdout)['text'],source.replace('请翻译','Please translate'))
            self.assertGreater(len(captured),1)
            self.assertTrue(all(body['stream'] for body in captured))
        finally:server.shutdown();server.server_close();thread.join()
    def test_redirect_does_not_forward_key(self):
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args): pass
            def do_POST(self):
                self.send_response(302);self.send_header('Location','http://127.0.0.1:1/steal');self.end_headers()
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            with self.assertRaisesRegex(m.TranslationError,'重定向'):
                m.request(f'http://127.0.0.1:{server.server_port}/','test-key',{})
        finally: server.shutdown();server.server_close();thread.join()

class FakeResponse(io.BytesIO):
    def __init__(self,data=None,raw=None,sse=False):
        super().__init__(raw if raw is not None else json.dumps(data).encode())
        self.headers={'Content-Type':'text/event-stream' if sse else 'application/json'}

if __name__=='__main__': unittest.main()
