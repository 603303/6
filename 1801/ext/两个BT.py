# coding=utf-8
# !/usr/bin/python
import sys
sys.path.append('..')
from base.spider import Spider
import json
import time
import urllib.parse
import re
import base64
import os
import sqlite3

class Spider(Spider):
    
    def getName(self):
        return "两个BT"

    def init(self, extend=""):
        self.host = "https://www.bttwoo.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Referer': self.host
        }
        # 初始化本地搜索数据库
        self._init_local_search_db()
        self.log(f"两个BT爬虫初始化完成，主站: {self.host}")

    def isVideoFormat(self, url):
        pass

    def manualVideoCheck(self):
        pass

    # ========== 本地搜索核心（新增） ==========
    def _init_local_search_db(self):
        """初始化本地搜索SQLite数据库"""
        try:
            db_dir = os.path.join(os.path.expanduser("~"), ".tvbox_cache")
            if not os.path.exists(db_dir):
                os.makedirs(db_dir)
            self.db_path = os.path.join(db_dir, "lianggebt_search.db")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS videos (
                    vod_id TEXT PRIMARY KEY,
                    vod_name TEXT NOT NULL,
                    vod_pic TEXT,
                    vod_remarks TEXT,
                    vod_year TEXT,
                    update_time INTEGER DEFAULT 0
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            self.log(f"本地搜索DB初始化失败: {str(e)}")

    def _save_to_local_search(self, video_list):
        """批量保存视频到本地搜索库"""
        try:
            if not video_list:
                return
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            now_ts = int(time.time())
            
            for v in video_list:
                if not v.get("vod_id") or not v.get("vod_name"):
                    continue
                cursor.execute('''
                    INSERT OR REPLACE INTO videos 
                    (vod_id, vod_name, vod_pic, vod_remarks, vod_year, update_time)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    v["vod_id"],
                    v["vod_name"],
                    v.get("vod_pic", ""),
                    v.get("vod_remarks", ""),
                    v.get("vod_year", ""),
                    now_ts
                ))
            conn.commit()
            conn.close()
        except Exception as e:
            self.log(f"保存本地搜索失败: {str(e)}")

    def _local_search(self, key, pg="1", limit=20):
        """本地离线搜索"""
        try:
            page = int(pg)
            offset = (page - 1) * limit
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # 模糊匹配标题
            keyword = f"%{key}%"
            cursor.execute('''
                SELECT vod_id, vod_name, vod_pic, vod_remarks, vod_year
                FROM videos 
                WHERE vod_name LIKE ? 
                ORDER BY update_time DESC
                LIMIT ? OFFSET ?
            ''', (keyword, limit, offset))
            
            rows = cursor.fetchall()
            conn.close()
            
            result = []
            for row in rows:
                result.append({
                    "vod_id": row[0],
                    "vod_name": row[1],
                    "vod_pic": row[2],
                    "vod_remarks": row[3],
                    "vod_year": row[4]
                })
            return result
        except Exception as e:
            self.log(f"本地搜索出错: {str(e)}")
            return []

    # ========== 原有方法增强（自动入库） ==========
    def homeContent(self, filter):
        result = {}
        classes = [
            {'type_id': 'movie_bt_tags/xiju', 'type_name': '喜剧'},
            {'type_id': 'movie_bt_tags/aiqing', 'type_name': '爱情'},
            {'type_id': 'movie_bt_tags/adt', 'type_name': '冒险'},
            {'type_id': 'movie_bt_tags/at', 'type_name': '动作'},
            {'type_id': 'movie_bt_tags/donghua', 'type_name': '动画'},
            {'type_id': 'movie_bt_tags/qihuan', 'type_name': '奇幻'},
            {'type_id': 'movie_bt_tags/xuanni', 'type_name': '悬疑'},
            {'type_id': 'movie_bt_tags/kehuan', 'type_name': '科幻'},
            {'type_id': 'movie_bt_tags/juqing', 'type_name': '剧情'},
            {'type_id': 'movie_bt_tags/kongbu', 'type_name': '恐怖'},
            {'type_id': 'meiju', 'type_name': '美剧'},
            {'type_id': 'gf', 'type_name': '高分电影'}
        ]
        result['class'] = classes
        result['filters'] = self._get_filters()
        
        try:
            rsp = self.fetch(self.host, headers=self.headers)
            doc = self.html(rsp.text)
            videos = self._get_videos(doc, limit=50)
            # 自动存入本地搜索
            self._save_to_local_search(videos)
            result['list'] = videos
        except Exception as e:
            self.log(f"首页获取出错: {str(e)}")
            result['list'] = []
        
        return result

    def homeVideoContent(self):
        return {
            'class': [
                {'type_id': 'movie_bt_tags/xiju', 'type_name': '喜剧'},
                {'type_id': 'movie_bt_tags/aiqing', 'type_name': '爱情'},
                {'type_id': 'movie_bt_tags/adt', 'type_name': '冒险'},
                {'type_id': 'movie_bt_tags/at', 'type_name': '动作'},
                {'type_id': 'movie_bt_tags/donghua', 'type_name': '动画'},
                {'type_id': 'movie_bt_tags/qihuan', 'type_name': '奇幻'},
                {'type_id': 'movie_bt_tags/xuanni', 'type_name': '悬疑'},
                {'type_id': 'movie_bt_tags/kehuan', 'type_name': '科幻'},
                {'type_id': 'movie_bt_tags/juqing', 'type_name': '剧情'},
                {'type_id': 'movie_bt_tags/kongbu', 'type_name': '恐怖'},
                {'type_id': 'meiju', 'type_name': '美剧'},
                {'type_id': 'gf', 'type_name': '高分电影'}
            ],
            'filters': self._get_filters()
        }

    def categoryContent(self, tid, pg, filter, extend):
        try:
            if filter and isinstance(filter, dict):
                if not extend:
                    extend = {}
                extend.update(filter)
            
            self.log(f"分类请求: tid={tid}, pg={pg}, extend={extend}")
            url = self._build_url(tid, pg, extend)
            if not url:
                return {'list': []}
            
            rsp = self.fetch(url, headers=self.headers)
            doc = self.html(rsp.text)
            videos = self._get_videos(doc, limit=20)
            # 分类内容也入库
            self._save_to_local_search(videos)
            
            return {
                'list': videos,
                'page': int(pg),
                'pagecount': 999,
                'limit': 20,
                'total': 19980
            }
        except Exception as e:
            self.log(f"分类内容获取出错: {str(e)}")
            return {'list': []}

    # ========== 搜索：优先本地 + 兜底网络（新增） ==========
    def searchContent(self, key, quick, pg="1"):
        """增强搜索：本地优先 + 网络兜底"""
        try:
            # 1. 先本地搜索（速度极快）
            local_videos = self._local_search(key, pg)
            if local_videos:
                self.log(f"本地搜索命中 {len(local_videos)} 条")
                return {'list': local_videos}
            
            # 2. 本地无结果，走网络搜索
            self.log(f"本地无结果，执行网络搜索")
            search_url = f"{self.host}/xssssearch?q={urllib.parse.quote(key)}"
            if pg and pg != "1":
                search_url += f"&p={pg}"
            
            rsp = self.fetch(search_url, headers=self.headers)
            doc = self.html(rsp.text)
            
            videos = []
            seen_ids = set()
            elements = doc.xpath('//li[contains(@class,"") and .//a[contains(@href,"/movie/")]]')
            
            for elem in elements:
                video = self._extract_video_info(elem, is_search=True)
                if video and video['vod_id'] not in seen_ids:
                    if self._is_relevant_search_result(video['vod_name'], key):
                        videos.append(video)
                        seen_ids.add(video['vod_id'])
            
            # 网络结果自动入库
            self._save_to_local_search(videos)
            self.log(f"网络搜索结果: {len(videos)} 个")
            return {'list': videos}
        
        except Exception as e:
            self.log(f"搜索出错: {str(e)}")
            return {'list': []}

    def detailContent(self, ids):
        try:
            vid = ids[0]
            detail_url = f"{self.host}/movie/{vid}.html"
            rsp = self.fetch(detail_url, headers=self.headers)
            doc = self.html(rsp.text)
            video_info = self._get_detail(doc, vid)
            
            # 详情也更新本地
            if video_info:
                self._save_to_local_search([video_info])
            
            return {'list': [video_info]} if video_info else {'list': []}
        except Exception as e:
            self.log(f"详情获取出错: {str(e)}")
            return {'list': []}

    def playerContent(self, flag, id, vipFlags):
        try:
            self.log(f"获取播放链接: flag={flag}, id={id}")
            try:
                decoded_id = base64.b64decode(id).decode('utf-8')
                self.log(f"解码播放ID: {decoded_id}")
            except:
                decoded_id = id
            
            play_url = f"{self.host}/v_play/{id}.html"
            return {'parse': 1, 'playUrl': '', 'url': play_url}
        except Exception as e:
            self.log(f"播放链接获取出错: {str(e)}")
            return {'parse': 1, 'playUrl': '', 'url': f"{self.host}/v_play/{id}.html"}

    # ========== 以下为原有辅助方法（不变） ==========
    def _get_filters(self):
        base_filters = [
            {
                'key': 'area',
                'name': '地区',
                'value': [
                    {'n': '全部', 'v': ''},
                    {'n': '中国大陆', 'v': '中国大陆'},
                    {'n': '美国', 'v': '美国'},
                    {'n': '韩国', 'v': '韩国'},
                    {'n': '日本', 'v': '日本'},
                    {'n': '英国', 'v': '英国'},
                    {'n': '法国', 'v': '法国'},
                    {'n': '德国', 'v': '德国'},
                    {'n': '其他', 'v': '其他'}
                ]
            },
            {
                'key': 'year',
                'name': '年份',
                'value': [
                    {'n': '全部', 'v': ''},
                    {'n': '2026', 'v': '2026'},
                    {'n': '2025', 'v': '2025'},
                    {'n': '2024', 'v': '2024'},
                    {'n': '2023', 'v': '2023'},
                    {'n': '2022', 'v': '2022'},
                    {'n': '2021', 'v': '2021'},
                    {'n': '2020', 'v': '2020'},
                    {'n': '2019', 'v': '2019'},
                    {'n': '2018', 'v': '2018'}
                ]
            }
        ]
        filters = {}
        category_ids = [
            'movie_bt_tags/xiju', 'movie_bt_tags/aiqing', 'movie_bt_tags/adt',
            'movie_bt_tags/at', 'movie_bt_tags/donghua', 'movie_bt_tags/qihuan',
            'movie_bt_tags/xuanni', 'movie_bt_tags/kehuan', 'movie_bt_tags/juqing',
            'movie_bt_tags/kongbu', 'meiju', 'gf'
        ]
        for cid in category_ids:
            filters[cid] = base_filters
        return filters

    def _build_url(self, tid, pg, extend):
        try:
            if tid.startswith('movie_bt_tags/'):
                url = f"{self.host}/{tid}"
            elif tid == 'meiju':
                url = f"{self.host}/meiju"
            elif tid == 'gf':
                url = f"{self.host}/gf"
            else:
                url = f"{self.host}/{tid}"
            if pg and pg != '1':
                if '?' in url:
                    url += f"&paged={pg}"
                else:
                    url += f"?paged={pg}"
            return url
        except Exception as e:
            self.log(f"构建URL出错: {str(e)}")
            return f"{self.host}/movie_bt_tags/xiju"

    def _get_videos(self, doc, limit=None):
        try:
            videos = []
            seen_ids = set()
            selectors = [
                '//li[.//a[contains(@href,"/movie/")]]',
                '//div[contains(@class,"item")]//li[.//a[contains(@href,"/movie/")]]'
            ]
            for selector in selectors:
                elements = doc.xpath(selector)
                if elements:
                    for elem in elements:
                        video = self._extract_video_info(elem)
                        if video and video['vod_id'] not in seen_ids:
                            videos.append(video)
                            seen_ids.add(video['vod_id'])
                    break
            return videos[:limit] if limit and videos else videos
        except Exception as e:
            self.log(f"获取视频列表出错: {str(e)}")
            return []

    def _extract_video_info(self, element, is_search=False):
        try:
            links = element.xpath('.//a[contains(@href,"/movie/")]/@href')
            if not links:
                return None
            link = links[0]
            if link.startswith('/'):
                link = self.host + link
            vod_id = self.regStr(r'/movie/(\d+)\.html', link)
            if not vod_id:
                return None
            title = ''
            title_selectors = ['.//h3/a/text()', './/h3/text()', './/a/@title', './/a/text()']
            for s in title_selectors:
                ts = element.xpath(s)
                for t in ts:
                    if t and t.strip() and len(t.strip())>1:
                        title = t.strip()
                        break
                if title: break
            if not title: return None
            pic = self._extract_image(element, is_search, vod_id)
            remarks = self._extract_remarks(element)
            return {
                'vod_id': vod_id,
                'vod_name': title,
                'vod_pic': pic,
                'vod_remarks': remarks,
                'vod_year': ''
            }
        except Exception as e:
            self.log(f"提取视频信息出错: {str(e)}")
            return None

    def _extract_image(self, element, is_search=False, vod_id=None):
        pic_selectors = ['.//img/@data-original', './/img/@data-src', './/img/@src']
        for s in pic_selectors:
            ps = element.xpath(s)
            for p in ps:
                if p and not p.endswith('blank.gif') and 'data:image/' not in p:
                    if p.startswith('//'): return 'https:'+p
                    elif p.startswith('/'): return self.host+p
                    elif p.startswith('http'): return p
        if is_search and vod_id:
            return self._get_image_from_detail(vod_id)
        return ''

    def _extract_remarks(self, element):
        rs = [
            './/span[contains(@class,"rating")]/text()',
            './/div[contains(@class,"rating")]/text()',
            './/span[contains(@class,"status")]/text()',
            './/div[contains(@class,"status")]/text()',
            './/span[contains(text(),"集")]/text()',
            './/span[contains(text(),"1080p")]/text()',
            './/span[contains(text(),"HD")]/text()'
        ]
        for s in rs:
            rl = element.xpath(s)
            for r in rl:
                if r and r.strip():
                    return r.strip()
        return ''

    def _get_image_from_detail(self, vod_id):
        try:
            u = f"{self.host}/movie/{vod_id}.html"
            r = self.fetch(u, headers=self.headers)
            d = self.html(r.text)
            ps = ['//img[contains(@class,"poster")]/@src','//div[contains(@class,"poster")]//img/@src','//img/@src']
            for s in ps:
                imgs = d.xpath(s)
                for img in imgs:
                    if img and not img.endswith('blank.gif'):
                        if img.startswith('//'): return 'https:'+img
                        elif img.startswith('/'): return self.host+img
                        elif img.startswith('http'): return img
        except: pass
        return ''

    def _is_relevant_search_result(self, title, key):
        if not title or not key: return False
        tl = title.lower()
        kl = key.lower()
        if kl in tl: return True
        sc = set(kl.replace(' ',''))
        tc = set(tl.replace(' ',''))
        if len(sc)>0 and len(sc & tc)/len(sc)>=0.6:
            return True
        if len(kl)<=2:
            return kl in tl
        return False

    def _get_detail(self, doc, vod_id):
        try:
            title = ''
            for s in ['//h1/text()','//h2/text()','//title/text()']:
                ts = doc.xpath(s)
                for t in ts:
                    if t and t.strip():
                        title = t.strip()
                        break
                if title: break
            
            pic = ''
            for s in ['//img[contains(@class,"poster")]/@src','//div[contains(@class,"poster")]//img/@src','//img/@src']:
                imgs = doc.xpath(s)
                for img in imgs:
                    if img and not img.endswith('blank.gif'):
                        if img.startswith('//'): pic='https:'+img
                        elif img.startswith('/'): pic=self.host+img
                        elif img.startswith('http'): pic=img
                        break
                if pic: break
            
            desc = ''
            for s in ['//div[contains(@class,"intro")]//text()','//div[contains(@class,"description")]//text()','//p[contains(@class,"desc")]//text()']:
                parts = [p.strip() for p in doc.xpath(s) if p.strip()]
                if parts:
                    desc = ' '.join(parts)
                    break
            
            actor = ''
            for s in ['//li[contains(text(),"主演")]/text()','//span[contains(text(),"主演")]/following-sibling::text()','//div[contains(@class,"actor")]//text()']:
                for a in doc.xpath(s):
                    if a and '主演' in a:
                        actor = a.strip().replace('主演：','').replace('主演','')
                        break
                if actor: break
            
            director = ''
            for s in ['//li[contains(text(),"导演")]/text()','//span[contains(text(),"导演")]/following-sibling::text()','//div[contains(@class,"director")]//text()']:
                for d in doc.xpath(s):
                    if d and '导演' in d:
                        director = d.strip().replace('导演：','').replace('导演','')
                        break
                if director: break
            
            plays = self._parse_play_sources(doc, vod_id)
            return {
                'vod_id': vod_id,
                'vod_name': title,
                'vod_pic': pic,
                'type_name': '',
                'vod_year': '',
                'vod_area': '',
                'vod_remarks': '',
                'vod_actor': actor,
                'vod_director': director,
                'vod_content': desc,
                'vod_play_from': '$$$'.join([p['name'] for p in plays]),
                'vod_play_url': '$$$'.join([p['episodes'] for p in plays])
            }
        except Exception as e:
            self.log(f"获取详情出错: {str(e)}")
            return None

    def _parse_play_sources(self, doc, vod_id):
        try:
            ps = []
            eps = []
            for s in ['//a[contains(@href,"/v_play/")]','//div[contains(@class,"play")]//a']:
                es = doc.xpath(s)
                if es:
                    for e in es:
                        t = e.xpath('./text()')[0] if e.xpath('./text()') else ''
                        u = e.xpath('./@href')[0] if e.xpath('./@href') else ''
                        if t and u:
                            pid = self.regStr(r'/v_play/([^.]+)\.html', u)
                            if pid:
                                eps.append(f"{t.strip()}${pid}")
                    break
            if eps:
                ps.append({'name':'默认播放','episodes':'#'.join(eps)})
            else:
                ps.append({'name':'默认播放','episodes':'第1集$bXZfMTM0NTY4LW5tXzE='})
            return ps
        except Exception as e:
            self.log(f"解析播放源出错: {str(e)}")
            return [{'name':'默认播放','episodes':'第1集$bXZfMTM0NTY4LW5tXzE='}]
