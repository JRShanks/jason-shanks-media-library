#!/usr/bin/env python3
"""Shared local lease and completed-period receipts; never silently steal a lease."""
import argparse
import fcntl
import json
import os
import subprocess
import time
import uuid
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parent.parent

def transition(state, action, mode, period, token, now):
    key=mode+':'+period
    lease=state.get('lease')
    if action=='begin':
        if lease: raise ValueError('another run holds the shared lease; investigate if expired, do not steal')
        if key in state.get('completed',{}): return {'status':'already-completed','key':key}
        state['lease']={'token':uuid.uuid4().hex,'key':key,'expires_at':now+7200}
        return {'status':'acquired',**state['lease']}
    if not lease or lease['token']!=token: raise ValueError('lease ownership mismatch')
    if action=='renew':lease['expires_at']=now+7200
    else:
        if action=='complete':state.setdefault('completed',{})[lease['key']]={'finished_at':now}
        state['lease']=None
    return {'status':action}

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['begin','renew','complete','fail','status']);p.add_argument('--mode',choices=['weekly','monthly'],default='weekly');p.add_argument('--period');p.add_argument('--token');a=p.parse_args()
    gitdir=subprocess.check_output(['git','rev-parse','--absolute-git-dir'],cwd=ROOT,text=True).strip()
    folder=Path(gitdir)/'clive-media';folder.mkdir(exist_ok=True)
    with (folder/'mutex').open('a') as mutex:
        fcntl.flock(mutex,fcntl.LOCK_EX)
        path=folder/'state.json';state=json.loads(path.read_text()) if path.exists() else {}
        if a.action=='status':print(json.dumps(state));return
        today=datetime.now(ZoneInfo('America/Indiana/Indianapolis'))
        period=a.period or (today.strftime('%Y-%m') if a.mode=='monthly' else today.strftime('%G-W%V'))
        result=transition(state,a.action,a.mode,period,a.token,time.time())
        temp=folder/'state.tmp';temp.write_text(json.dumps(state,indent=2));os.replace(temp,path)
        print(json.dumps(result))
if __name__=='__main__':main()
