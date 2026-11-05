"""Bounded Keenable web discovery. Source snippets are not verified place facts."""
import ipaddress
import os
import re
import socket
import time
from urllib.parse import urlsplit, urlunsplit
import httpx
from fastapi import Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Literal
from .core import fail, register


def safe_source_url(raw):
    if not isinstance(raw,str) or len(raw)>2048 or any(c.isspace() or ord(c)<32 for c in raw): return None
    try:
        url=urlsplit(raw);host=(url.hostname or '').rstrip('.').lower()
        if url.scheme not in ('http','https') or not host or url.username is not None or url.password is not None or url.port not in (None,80,443): return None
        if host=='localhost' or host.endswith(('.local','.internal','.localhost')): return None
        try:
            if not ipaddress.ip_address(host).is_global: return None
        except ValueError:
            if '.' not in host or all(c in '0123456789.' for c in host): return None
            try:
                if not ipaddress.ip_address(socket.inet_aton(host)).is_global:return None
            except OSError:pass
            labels=host.encode('idna').decode('ascii').split('.')
            if any(not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?',label) for label in labels):return None
        return urlunsplit((url.scheme,url.netloc,url.path or '/',url.query,''))
    except ValueError: return None


class KeenableSearch:
    def __init__(self,transport=None): self.transport=transport

    def search(self,query,location,category):
        key=os.getenv('KEENABLE_API_KEY')
        headers={'Accept':'application/json','X-Keenable-Title':'Tagalong'}
        if key:headers['X-API-Key']=key
        try:
            with httpx.Client(timeout=12,trust_env=False,follow_redirects=False,transport=self.transport) as client:
                result=client.post('https://api.keenable.ai/v1/search'+('' if key else '/public'),headers=headers,json={'query':f'{category} in {location}: {query}', 'max_results':5})
                result.raise_for_status()
                if len(result.content)>2_000_000: raise ValueError('Oversized response')
                rows=result.json()['results']
                if not isinstance(rows,list): raise ValueError('Invalid results')
                output=[];seen=set()
                for row in rows[:20]:
                    if not isinstance(row,dict): continue
                    url=safe_source_url(row.get('url'))
                    if not url or url in seen: continue
                    seen.add(url)
                    title=row.get('title');snippet=row.get('snippet',row.get('description',''))
                    output.append({'title':title[:200] if isinstance(title,str) and title.strip() else urlsplit(url).hostname,'url':url,'snippet':snippet[:1500] if isinstance(snippet,str) else ''})
                    if len(output)==5:break
                return output
        except (httpx.HTTPError,ValueError,TypeError,KeyError):
            fail(502,'Place search is temporarily unavailable or rate limited. Please try again later.')


class SearchRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    query:str=Field(min_length=2,max_length=250)
    location:str=Field(min_length=2,max_length=150)
    category:Literal['restaurants','attractions','places']='places'

    @field_validator('query','location',mode='before')
    @classmethod
    def trimmed(cls,value):return ' '.join(value.split()) if isinstance(value,str) else value


def install_places(app,repo,actor,provider):
    @app.post('/v1/places/search')
    def search(b:SearchRequest,a=Depends(actor)):
        def reserve(s):
            register(s,a);bucket=int(time.time()//60);limits=s.setdefault('places_limits',{})
            for key in list(limits):
                if limits[key]['bucket']!=bucket:del limits[key]
            record=limits.get(a.id,{'bucket':bucket,'count':0})
            if record['count']>=10:fail(429,'Search limit reached. Please retry next minute.')
            record['count']+=1;limits[a.id]=record
        repo.transact(reserve)
        results=provider.search(b.query,b.location,b.category)
        repo.transact(lambda s:register(s,a))
        return JSONResponse({'provider':'Keenable','results':results,'notice':'Web search results. Check the source for current details; hours, prices and availability are not verified.'},headers={'Cache-Control':'no-store'})
