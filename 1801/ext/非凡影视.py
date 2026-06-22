#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 非凡影视 - 无加密·去广告正常版
import re
import sys
import requests
from urllib import parse
sys.path.append('..')
from base.spider import Spider

class Spider(Spider):
    def getName(self):
        return '非凡资源'

    def init(self, extend=""):
        self.name = '非凡资源'
        self.home_url = 'https://api.ffzyapi.com'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        }

    def getDependence(self):
        return []

    def isVideoFormat(self, url):
        return 1

    def manualVideoCheck(self):
        return 0

    def homeContent(self, filter):
        return {
            'class': [
                {'type_id': '1', 'type_name': '电影片'},
                {'type_id': '2', 'type_name': '连续剧'},
                {'type_id': '3', 'type_name': '综艺片'},
                {'type_id': '4', 'type_name': '动漫片'}
            ],
            'filters': {
                '1': {'key':'cid','name':'分类','value':[
                    {'n':'动作片','v':'6'},{'n':'喜剧片','v':'7'},{'n':'爱情片','v':'8'},
                    {'n':'科幻片','v':'9'},{'n':'恐怖片','v':'10'},{'n':'剧情片','v':'11'},
                    {'n':'战争片','v':'12'},{'n':'记录片','v':'20'},{'n':'伦理片','v':'34'}]},
                '2': {'key':'cid','name':'分类','value':[
                    {'n':'国产剧','v':'13'},{'n':'香港剧','v':'14'},{'n':'韩国剧','v':'15'},
                    {'n':'欧美剧','v':'16'},{'n':'台湾剧','v':'21'},{'n':'日本剧','v':'22'},
                    {'n':'海外剧','v':'23'},{'n':'泰国剧','v':'24'},{'n':'短剧','v':'36'}]},
                '3': {'key':'cid','name':'分类','value':[
                    {'n':'大陆综艺','v':'25'},{'n':'港台综艺','v':'26'},
                    {'n':'日韩综艺','v':'27'},{'n':'欧美综艺','v':'28'}]},
                '4': {'key':'cid','name':'分类','value':[
                    {'n':'国产动漫','v':'29'},{'n':'日韩动漫','v':'30'},
                    {'n':'欧美动漫','v':'31'},{'n':'港台动漫','v':'32'},{'n':'海外动漫','v':'33'}]}
            }
        }

    def homeVideoContent(self):
        result_list = []
        try:
            resp = requests.get(f'{self.home_url}/index.php/ajax/data?mid=1', headers=self.headers)
            data = resp.json().get('list', [])
            for item in data:
                result_list.append({
                    'vod_id': item.get('vod_id',''),
                    'vod_name': item.get('vod_name',''),
                    'vod_pic': item.get('vod_pic',''),
                    'vod_remarks': item.get('vod_remarks','')
                })
        except:
            return {'list':[],'parse':0,'jx':0}
        return {'list':result_list,'parse':0,'jx':0}

    def categoryContent(self, cid, page, filter, ext):
        tid = ext.get('cid', cid)
        url = f'{self.home_url}/index.php/ajax/data?mid=1&tid={tid}&page={page}&limit=20'
        result_list = []
        try:
            resp = requests.get(url, headers=self.headers)
            data = resp.json().get('list', [])
            for item in data:
                result_list.append({
                    'vod_id': item.get('vod_id',''),
                    'vod_name': item.get('vod_name',''),
                    'vod_pic': item.get('vod_pic',''),
                    'vod_remarks': item.get('vod_remarks','')
                })
        except:
            return {'list':[],'msg':'请求失败'}
        return {'list':result_list,'parse':0,'jx':0}

    def detailContent(self, did):
        vod_id = did[0] if isinstance(did, list) else did
        result_list = []
        try:
            url = f'{self.home_url}/api.php/provide/vod?ac=detail&ids={vod_id}'
            resp = requests.get(url, headers=self.headers)
            res = resp.json()
            vod = res.get('list', [{}])[0]
            play_url = vod.get('vod_play_url', '')
            if '$$$' in play_url:
                play_url = play_url.split('$$$')[-1]

            result_list.append({
                'type_name': vod.get('type_name',''),
                'vod_id': vod.get('vod_id',''),
                'vod_name': vod.get('vod_name',''),
                'vod_remarks': vod.get('vod_remarks',''),
                'vod_year': vod.get('vod_year',''),
                'vod_area': vod.get('vod_area',''),
                'vod_actor': vod.get('vod_actor',''),
                'vod_director': vod.get('vod_director',''),
                'vod_content': vod.get('vod_content',''),
                'vod_play_from': '非凡资源',
                'vod_play_url': play_url
            })
        except Exception as e:
            return {'list':[],'msg':str(e)}
        return {'list':result_list,'parse':0,'jx':0}

    def searchContent(self, key, quick, page='1'):
        result_list = []
        if page != '1':
            return {'list':result_list,'parse':0,'jx':0}
        try:
            url = f'{self.home_url}/api.php/provide/vod?ac=detail&wd={key}'
            resp = requests.get(url, headers=self.headers)
            data = resp.json().get('list', [])
            for item in data:
                result_list.append({
                    'vod_id': item.get('vod_id',''),
                    'vod_name': item.get('vod_name',''),
                    'vod_pic': item.get('vod_pic',''),
                    'vod_remarks': item.get('vod_remarks','')
                })
        except:
            return {'list':[],'msg':'搜索失败'}
        return {'list':result_list,'parse':0,'jx':0}

    # 核心：无加密 + 走本地代理去广告
    def playerContent(self, flag, pid, vipFlags):
        return {
            'url': self.getProxyUrl() + '&url=' + pid,
            'header': self.headers,
            'parse': 0,
            'jx': 0
        }

    # 本地代理只做去广告，不做加密解密
    def localProxy(self, params):
        try:
            url = params['url']
            content = self.del_ads(url)
            return [200, 'application/vnd.apple.mpegurl', content]
        except:
            return [200, 'text/plain', '']

    def destroy(self):
        return 'ok'

    # m3u8去广告（原版逻辑，保留）
    def del_ads(self, url):
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code != 200:
                return ''
            base_path = url.rsplit('/', 1)[0] + '/'
            purl = parse.urlparse(url)
            domain = f'{purl.scheme}://{purl.netloc}'
            lines = resp.text.splitlines()

            if lines[0] == '#EXTM3U' and len(lines) > 2 and 'mixed' in lines[2]:
                u = lines[2]
                if u.startswith('/'):
                    u = domain + u
                elif not u.startswith('http'):
                    u = base_path + u
                return self.del_ads(u)

            new_lines = []
            disc_pos = []
            for idx, line in enumerate(lines):
                if '.ts' in line:
                    if line.startswith('/'):
                        new_lines.append(domain + line)
                    elif not line.startswith('http'):
                        new_lines.append(base_path + line)
                    else:
                        new_lines.append(line)
                elif line == '#EXT-X-DISCONTINUITY':
                    new_lines.append(line)
                    disc_pos.append(idx)
                else:
                    new_lines.append(line)

            skip = []
            if len(disc_pos) >= 1: skip.append((disc_pos[0], disc_pos[0]))
            if len(disc_pos) >= 3: skip.append((disc_pos[1], disc_pos[2]))
            if len(disc_pos) >= 5: skip.append((disc_pos[3], disc_pos[4]))
            final = [ln for i, ln in enumerate(new_lines) if not any(s <= i <= e for s,e in skip)]
            return '\n'.join(final)
        except:
            return ''

if __name__ == '__main__':
    pass
