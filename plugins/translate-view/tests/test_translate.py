import importlib.util
import io
import json
import os
import stat
import tempfile
import threading
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
                self.send_header('Content-Type','text/event-stream' if body['stream'] else 'application/json')
                self.end_headers()
                if body['stream']:
                    for part in ['这是','译文。']:
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
            self.assertEqual(captured[0][0],'/v1/chat/completions');self.assertEqual(captured[0][1],'Bearer test-key')
        finally: server.shutdown();server.server_close();thread.join()
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
