#!/usr/bin/env python3
"""Cache non-CORS sources (NHC, NDBC) into data/*.json for the dashboard."""
import json, re, urllib.request, datetime
UA={'User-Agent':'sd-storm-dashboard (github.com/Shap-Code/sd-storm-dashboard)'}
def get(u):
    return urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=30).read().decode('utf-8','replace')
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
out={'fetched':now,'storms':[]}
try:
    d=json.loads(get('https://www.nhc.noaa.gov/CurrentStorms.json'))
    for s in d.get('activeStorms',[]):
        b=s['binNumber'].lower(); imgs={}
        try:
            html=get(f'https://www.nhc.noaa.gov/graphics_{b}.shtml')
            for k,pat in {'cone':r'_5day_cone_sm\+png/[^"]+','wind':r'_current_wind_sm\+png/[^"]+','toa':r'_earliest_reasonable_toa_no_wsp_34_sm\+png/[^"]+','keymsg':r'_key_messages_sm\+png/[^"]+','ero':r'WPCERO_sm1\+gif/[^"]+'}.items():
                m=re.search(r'/storm_graphics/[A-Z0-9]+/refresh/[A-Z0-9]+'+pat,html)
                if m: imgs[k]='https://www.nhc.noaa.gov'+(m.group(0).replace('_sm+png','+png').replace('_sm.png','.png') if k!='ero' else m.group(0))
        except Exception as e: imgs['error']=str(e)
        s['images']=imgs; s['graphicsPage']=f'https://www.nhc.noaa.gov/graphics_{b}.shtml'
        out['storms'].append(s)
except Exception as e: out['error']=str(e)
json.dump(out,open('data/nhc.json','w'),indent=1)
buoys={'fetched':now}
for bid,name in [('46232','Point Loma South'),('46254','SCRIPPS Nearshore')]:
    try:
        rows=[l.split() for l in get(f'https://www.ndbc.noaa.gov/data/realtime2/{bid}.txt').splitlines() if not l.startswith('#')]
        obs=[]
        for r in rows[:96]:
            t=f'{r[0]}-{r[1]}-{r[2]}T{r[3]}:{r[4]}:00Z'
            f=lambda i:None if r[i]=='MM' else float(r[i])
            obs.append({'t':t,'wvht_m':f(8),'dpd_s':f(9),'mwd':f(11),'wtmp_c':f(14)})
        buoys[bid]={'name':name,'obs':obs}
    except Exception as e: buoys[bid]={'name':name,'error':str(e)}
json.dump(buoys,open('data/buoys.json','w'),indent=1)
print('ok',len(out['storms']),'storms')
# Record reachability of hot-linked imagery so the page/ops can see it
chk={'fetched':now}
for k,u in {'goes':'https://cdn.star.nesdis.gov/GOES18/ABI/SECTOR/psw/GEOCOLOR/GOES18-PSW-GEOCOLOR-600x600.gif'}.items():
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers=UA,method='HEAD'),timeout=20); chk[k]={'status':r.status,'type':r.headers.get('Content-Type'),'len':r.headers.get('Content-Length')}
    except Exception as e: chk[k]={'error':str(e)}
try:
    ts=json.loads(get('https://slider.cira.colostate.edu/data/json/goes-18/conus/geocolor/latest_times.json'))['timestamps_int'][:12]
    chk['goes_frames']=[f"https://slider.cira.colostate.edu/data/imagery/{str(t)[:4]}/{str(t)[4:6]}/{str(t)[6:8]}/goes-18---conus/geocolor/{t}/00/000_000.png" for t in reversed(ts)]
except Exception as e: chk['goes_frames_error']=str(e)
json.dump(chk,open('data/check.json','w'),indent=1)
