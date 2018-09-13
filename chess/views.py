# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

# Create your views here.

from django.shortcuts import get_object_or_404, render                          
from django.http import HttpResponseRedirect, HttpResponse                      
from django.template import loader                                              
from django.urls import reverse                                                
from django import forms

from genshi import XML, Markup                                                  
from genshi.template import MarkupTemplate
import time
import uuid
import os
import json
import glob
import PChess
import datetime
import re

# GAME PREFERENCES - min,max,default                                            
PREF={}                                                                         
PREF["max_ply"]=(0,25,25)            # search depth                             
PREF["max_search"]=(0,200000,100000) # n positions to search  

def set_preferences(cg, param):                                                 
    for pname in PREF:                                                          
        pmin,pmax,pdefault=PREF[pname]                                          
        if pname in param:                                                      
            val=param[pname]                                                    
        else:                                                                   
            val=pdefault                                                        
            val=int(val)                                                            
        if val>=pmin and val<=pmax:                                             
            setattr(cg, pname, val)                                             
            #set_cookie(pname, val)                                              

def sq_is_black(i):                                                             
    x=7-i/8                                                                     
    y=i % 8                                                                     
    flag=(x % 2==y % 2)                                                         
    return flag                                                                 
                                                                                                
def xy2src(x,y,board):                                                          
    i=(7-x)*8+y                                                                 
    #src="bitmaps/"                                                              
    src="/chess/static/chess/bitmaps/"                                                              
    if sq_is_black(i):                                                          
        src+="b-"                                                               
    else:                                                                       
        src+="w-"                                                               
    if board[i]!='.':
        if board[i].isupper():
            src+='w'
        else:
            src+='b'
    return src+board[i]+".gif"  

def index(request):                                                             
    m=request.session.get('game_id')
    if m==None:
        status="Fancy a nice game of chess?"                                    
        board="."*64                                                            
        l=[]                                                                    
    else:
        uid=request.session.get('user_id')
        gid=request.session.get('game_id')
        fname="GAMES/{}_{}.txt".format(uid,gid)
        cg,info=read_game(fname)
        status=cg.get_status()                                                   
        board=cg.to_string()                                                    
        l=[[frm,to] for (frm,to,kill) in cg.get_possible()]  

    gdir=os.path.dirname(os.path.realpath(__file__))
    tmpl=MarkupTemplate(open("{}/Genshi/main.html".format(gdir), 'r').read())                   
    #tmpl=MarkupTemplate(open("chess/Genshi/main.html", 'r').read())                   
    stream=tmpl.generate( legal=str(l), board=board, status=status, xy2src=xy2src)             
    return HttpResponse(stream.render(doctype='xhtml-transitional'))

def get_game_parameters(data):
    keys=data.keys()
    keys.sort()
    l=[]
    for key in keys:
        if key in ["User", "Moves", "REMOTE_HOST", "REMOTE_ADDR", "Start"]:
            continue
        if key=="remote_host":
            flag=host2flag(data[key])
            if flag!="":
                l+=[("player h", flag)]
        else:
            l+=[(key, data[key])]
    return l

def review(request, gid):
    cg=None
    if gid!='':
        fname="GAMES/%s.txt"%(gid,)
        if os.path.exists(fname): cg,info=read_game(fname)
    if cg==None:
        uid=request.session.get('user_id')
        gid=request.session.get('game_id')
        fname="GAMES/{}_{}.txt".format(uid,gid)
        cg,info=read_game(fname)

    moves=cg.log
    cg=PChess.PChess()
    boards=[]
    board=cg.to_string()
    for i, tup in enumerate(moves):
        cg.make_move(tup[0],tup[1])
        boards+=[(cg.to_string(),cg.get_status())]

    gdir=os.path.dirname(os.path.realpath(__file__))
    tmpl=MarkupTemplate(open("{}/Genshi/review.html".format(gdir), 'r').read())                   
    #tmpl=MarkupTemplate(open("chess/Genshi/review.html", 'r').read())
    ifo={}
    flag=host2flag(info["remote_host"])
    if flag!="":ifo["player h"]=flag

    print(info['stat'])

    moves=[]
    for frm,to,is_kill,t,score,nsearched,depth in info['stat']:
        t=float(t)
        value = datetime.datetime.fromtimestamp(t)
        t=value.strftime('%Y-%m-%d %H:%M:%S')
        moves+=[(frm,to,is_kill,t,score,nsearched,depth)] 

    stream=tmpl.generate(moves=moves, board=board, status="White's turn", boards=boards, info=ifo, xy2src=xy2src)
    return HttpResponse(stream.render(doctype='xhtml-transitional'))


def get_status(filename):                                                       
    cg, d=read_game(filename)
    if cg.game_over():                                                          
        msg=cg.post_mortem()                                                    
    else:                                                                       
        msg="Unfinished"                                                        
    host="unk"
    if "remote_host" in d:
        host=d["remote_host"]
    return msg, len(cg.log), host

def get_game_info(fname):                                                       
    try:                                                                        
        msg,nmoves,rhost=get_status(fname)                               
    except:                                                                     
        raise
        return None                                                             
    if rhost=="": rhost='unk'
    if nmoves==0:                                                               
        return None                                                             
    name, ext=os.path.splitext(fname)                                           
    gid=name[6:]                                                                
    t=os.path.getmtime(fname)                                                   
    date=time.strftime("%Y-%b-%d (%A) %H:%M:%S (GMT)", time.gmtime(t))          
    label=date+"; %s (%d half moves)"%(msg,nmoves)                              
    url="/chess/review/"+gid                                               
    return label, url, rhost, nmoves

def lookup_games():                                                             
    fnames=glob.glob("GAMES/*.txt")                                            
    fnames.sort(None, os.path.getmtime, True)                                   
    return fnames 

def get_games(offset, N, l=None):                                               
    if l==None:                                                                 
        l=lookup_games()                                                        
    l2=[]                                                                       
    i=0                                                                         
    for fname in l[offset:]:                                                    
        print(fname)
        if i>=N:                                                                
            break                                                               
        tup=get_game_info(fname)                                                
        if tup==None: continue                                                  
        l2+=[tup]                                                               
        i+=1                                                                    
    return l2   

def host2country(rhost):                                                        
    country=""                                                                  
    if rhost=="": return country

    words=rhost.split(".")                                                  
    if len(words)>0 and len(words[-1])==2:                                  
        country=words[-1]                                                   
    if country=="uk":                                                           
        country="gb"                                                            
    return country                                                              

def host2flag(rhost):                                                           
    ext=host2country(rhost)                                                     
    if ext=="": return ""                                                       
    oponent="http://flagspot.net/images/%s/%s.gif"%(ext[0],ext)                 
    return oponent  

def recent(request, offset):                                                             
    offset=int(offset)
    N=20                                                                        
    l=lookup_games()                                                            
    prev=None                                                                   
    nxt=None                                                                   
    if offset>0:                                                                
        prev="/chess/recent/{}".format(offset-N)                         
    if offset+N<len(l):                                                         
        nxt="/chess/recent/{}".format(offset+N)                         
    
    games=[]                                                                    
    for i, (label, url, rhost, nmoves) in enumerate(get_games(offset, N, l)):
        flag=None                                                               
        if rhost!="":                                                           
            flag=host2flag(rhost)                                               
            #games+=[(i+offset+1, url, label, flag)]                                 
            games+=[{'n':i+offset+1, 'url':url, 'label':label, 'flag':flag}]
    tmpl=loader.get_template('chess/list.html')
    context={'next':nxt, 'prev':prev, 'games':games}
    return HttpResponse(tmpl.render(context,request))

class SettingsForm(forms.Form):
    max_ply=forms.IntegerField(min_value=0,max_value=25)
    max_search=forms.IntegerField(min_value=0,max_value=200000)

def settings(request):                                                             
    if request.method=='POST':
        form = SettingsForm(request.POST)
        if form.is_valid():
            request.session['max_ply']=form.cleaned_data['max_ply']
            request.session['max_search']=form.cleaned_data['max_search']
    else:
        form = SettingsForm()

    pref=[]                                                                     
    for pname in ['max_ply', 'max_search']:
        pmin,pmax,pdefault=PREF[pname]                                          
        pval=request.session.get(pname)
        if pval==None: pval=pdefault
        pref+=[{'pname':pname, 'pmin': pmin, 'pmax':pmax, 'pval':pval}]

    tmpl=loader.get_template('chess/settings.html')
    context={'pref':pref, 'form': form}
    return HttpResponse(tmpl.render(context,request))

def save_game(cg, request, fname, info):
    with open(fname, 'w') as f:
        info["http_host"]=request.META['HTTP_HOST']
        info["remote_host"]=request.META['REMOTE_HOST']
        f.write(cg.to_json()+'\n')
        f.write(json.dumps(info))

def read_game(fname, max_move=None):
    cg=PChess.PChess()
    d={"stat":[]}
    if os.path.exists(fname):
        with open(fname, 'r') as f:
            cg.from_json(f.readline(), max_move)
            d=json.loads(f.readline())
    return cg, d

def change(request):                                                             
    uid=request.session.get('user_id')
    gid=request.session.get('game_id')
    fname="GAMES/{}_{}.txt".format(uid,gid)

    cg,info=read_game(fname)
    if not cg.game_over():                                                  
        (frm, to, kill, val, count, depth)=cg.compute_move()                
        is_kill=cg.make_move(frm,to) 
        info["stat"]+=[(frm,to,kill,time.time(), val,count,depth)]
        save_game(cg, request, fname, info)
    return HttpResponse(xml_response(cg), content_type='text/xml')


def new_gid(gdir,uid):
    #max old gid + 1
    p = re.compile(r'_(?P<gid>[0-9]+).txt$')
    g=glob.glob("{}/{}_*.txt".format(gdir,uid))
    l=(p.search(s) for s in g)
    l=(m.group('gid') for m in l if m!=None)
    l=(int(m) for m in l)
    return str(max(l)+1)

def new(request):                                                             
    uid=request.session.get('user_id')
    if uid==None: uid=str(uuid.uuid4())
    request.session['user_id']=uid

    gdir="GAMES"
    if not os.path.exists(gdir):
        os.mkdir(gdir)
    #gid=str(len(glob.glob("{}/{}_*.txt".format(gdir,uid))))
    gid=new_gid(gdir,uid)
    request.session['game_id']=gid

    fname="GAMES/{}_{}.txt".format(uid,gid)
    cg=PChess.PChess()
    info={"stat":[]}
    save_game(cg, request, fname, info)


    return HttpResponse(xml_response(cg), content_type='text/xml')


def xml_response(cg):                                                           
    legal=[[frm,to] for (frm,to,kill) in cg.get_possible()]                     
    if len(cg.log)==0:                                                          
        lastFrom,lastTo=-1,-1                                                   
    else:                                                                       
        t=cg.log[-1]                                                            
        lastFrom,lastTo=t[0],t[1]                                               
        
    s="""<?xml version="1.0" encoding="utf-8" standalone="yes"?>
    <chessgame>
        <board>{board}</board>
        <status>{status}</status>
        <color>{color}</color>
        <lastFrom>{lastFrom}</lastFrom>
        <lastTo>{lastTo}</lastTo>
        <legal>{legal}</legal>
        <nmoves>nmoves</nmoves>
    </chessgame>""".format(board=cg.to_string(), \
                         status=cg.get_status(), \
                         color=cg.get_turn(), \
                         lastFrom=lastFrom, \
                         lastTo=lastTo, \
                         legal=str(legal), \
                         nmoves=len(cg.log)/2+1)                               
    return s

def move(request, frm, to):
    uid=request.session.get('user_id')
    gid=request.session.get('game_id')
    fname="GAMES/{}_{}.txt".format(uid,gid)
    cg,info=read_game(fname)

    move=(int(frm),int(to))
    is_kill=cg.make_move(move[0], move[1])                                  
    info["stat"]+=[(move[0],move[1],is_kill,time.time(), None,None,None)]

    if not cg.game_over():                                                  
        (frm, to, kill, val, count, depth)=cg.compute_move()                
        is_kill=cg.make_move(frm,to)                                        
        info["stat"]+=[(frm,to,kill,time.time(), val,count,depth)]
    save_game(cg, request, fname, info)

    s=xml_response(cg)
    return HttpResponse(s, content_type='text/xml')

