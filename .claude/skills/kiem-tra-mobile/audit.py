"""Dò tràn ngang trên mobile. Dùng: python audit.py [rộng=375] [base=http://127.0.0.1:8123]"""
import re, sys, urllib.request
from playwright.sync_api import sync_playwright

W = int(sys.argv[1]) if len(sys.argv) > 1 else 375
BASE = (sys.argv[2] if len(sys.argv) > 2 else 'http://127.0.0.1:8123').rstrip('/')
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

xml = urllib.request.urlopen(BASE + '/sitemap.xml').read().decode('utf-8')
paths = sorted({re.sub(r'^https?://[^/]+', '', u) for u in re.findall(r'<loc>([^<]+)</loc>', xml)})
pages = ['/'] + [p for p in paths if p != '/'] + ['/404/']

JS = '''()=>{const W=document.documentElement.clientWidth;const out=[];
for(const e of document.querySelectorAll('body *')){const r=e.getBoundingClientRect();if(r.width==0||r.height==0)continue;
if(getComputedStyle(e).position==='fixed')continue;
if(r.right>W+1||r.left<-1){let p=e.parentElement,clip=false;while(p&&p!==document.body){const o=getComputedStyle(p);if(['hidden','auto','scroll','clip'].includes(o.overflowX)){clip=true;break}p=p.parentElement}
if(!clip)out.push(e.tagName+'.'+String(typeof e.className==='string'?e.className:'').split(' ').join('.').slice(0,60)+' L'+Math.round(r.left)+' R'+Math.round(r.right))}}
return {sw:document.documentElement.scrollWidth,W,over:out.slice(0,6),n:out.length}}'''

bad = 0
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME)
    pg = b.new_context(viewport={'width': W, 'height': 800}, is_mobile=True, has_touch=True).new_page()
    for u in pages:
        try:
            pg.goto(BASE + u, wait_until='load', timeout=30000)
            pg.wait_for_timeout(800)
            r = pg.evaluate(JS)
        except Exception as e:
            print(u, 'LỖI', str(e)[:80]); continue
        if r['sw'] > r['W']:
            bad += 1
            print(u, 'OVERFLOW', r['sw'], '>', r['W'])
            for o in r['over']:
                print('   ', o)
        else:
            print(u, 'ok')
    b.close()
print('Số trang tràn ngang:', bad)
