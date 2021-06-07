from __future__ import annotations

import os
import sys
import requests
import time
import json
import re
from bs4 import BeautifulSoup
from typing import List
from urllib.parse import urljoin, unquote
from dataclasses import dataclass
from enum import Enum, unique
from fake_useragent import UserAgent
from datetime import datetime

@unique
class Extensions(Enum):
    JPG = 'j'
    PNG = 'p'
    GIF = 'g'

@unique
class TagOption(Enum):
    Lang = "language"
    Char = "character"
    Tags = "tag"
    Artist = "artist"
    Parody = "parody"
    Group = "group"

@unique
class Sort(Enum):
    Popular = 'popular'
    PopularYear = 'popular-year'
    PopularMonth = 'popular-month'
    PopularWeek = 'popular-week'
    PopularToday = 'popular-today'
    Date = 'date'

@dataclass(frozen=True)
class Title:
    eng: str
    jp: str
    pretty: str

@dataclass(frozen=True)
class Tag:
    id: int
    type: str
    name: str
    url: str
    count: int

    @classmethod
    def getTags(cls, tags: List[Tag], opt: TagOption) -> str:            
        try:
            return ", ".join([tag.name for tag in tags if tag.type == opt.value])
        except Exception:
            return None

@dataclass(frozen=True)
class Page:
    url: str
    width: int
    height: int

    @classmethod
    def getUrls(cls, pages: List[Page]) -> List[str]:
        return [page.url for page in pages]

class Book:
    def __init__(self, data):
        self.id = int(data["id"])
        self.media_id = int(data["media_id"])
        self.title = self.__parseTitle__(data["title"])
        self.favorites = int(data["num_favorites"])
        images = data["images"]

        thumb_ext = Extensions(images["thumbnail"]["t"]).name.lower()
        self.thumbnail = f"https://t.nhentai.net/galleries/{self.media_id}/thumb.{thumb_ext}"

        cover_ext = Extensions(images["cover"]["t"]).name.lower()
        self.cover = f"https://t.nhentai.net/galleries/{self.media_id}/cover.{cover_ext}"

        self.scanlator = data["scanlator"]
        self.uploaded = datetime.fromtimestamp(data["upload_date"]).strftime('%Y-%m-%d %H:%M:%S')
        self.epoch = data["upload_date"]

        self.rawTag = [self.__parseTags__(tag) for tag in data["tags"]] 
        self.character = Tag.getTags(self.rawTag, TagOption.Char)
        self.tags = Tag.getTags(self.rawTag, TagOption.Tags)

        self.pages = [
            self.__parsePage__(self.media_id, num, **_) for num, _ in enumerate(images["pages"], start=1)
        ]
        self.num_pages = data["num_pages"]
        
    def __parseTitle__(self, titles: dict) -> Title:
        return Title(
            titles["english"],
            titles["japanese"],
            titles["pretty"]
        )
    
    def __parsePage__(self, media_id: int, num: int, t: str, w: int, h: int) -> Page:
        return Page(
            url = f"https://i.nhentai.net/galleries/{media_id}/{num}.{Extensions(t).name.lower()}",
            width = int(w),
            height = int(h)
        )

    def __parseTags__(self, tag) -> Tag:
        return Tag(
            id = int(tag["id"]),
            type = tag["type"],
            name = tag["name"],
            url = tag["url"],
            count = tag["count"] 
        )

class Hentai:
    def __init__(self):
        self.module = "nh"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": UserAgent().chrome
        })
        self.APIurl = "https://nhentai.net/api/"
        self.HOMEurl = "https://nhentai.net/"

    def __getUrl(self, endpoint, params={}) -> dict:
        return self.session.get(
            url=urljoin(self.APIurl, endpoint),
            params=params
        ).json()

    def search(self, query: str, page: int=1, sort_by: Sort = Sort.Date) -> List[Book]:
        res = self.__getUrl("galleries/search",
            params={
                "query": query,
                "page": page,
                "sort": sort_by
            })
        return [Book(data) for data in res['result']]
    
    def searchFallback(self, query, page: int=1, sort_by: Sort = Sort.Date) -> List[Book]:
        res = self.session.get(urljoin(self.HOMEurl, "search/"), 
            params={
                "q": query,
                "page": page
            })
        
        book = []
        soup = BeautifulSoup(res.content.decode("UTF-8"), "html.parser")
        soup = soup.find_all("a", href=True)
        
        for link in soup:
            regex = re.findall("\/g\/\d+\/", str(link))
            if regex: book.append(self.getDoujin(int(regex[0].split("/")[2])))
        return book

    def getDoujin(self, id: int) -> Book:
        try: 
            return Book(self.__getUrl(f"gallery/{id}"))
        except KeyError:
            raise ValueError("NukeCode Nuked!")

    def random(self):
        nukeid = self.session.head(
            urljoin(self.HOMEurl, "random/")
        ).headers["Location"][3:-1]
        return self.getDoujin(int(nukeid))
    

    def related(self, id: int):
        books = self.__getUrl(f"gallery/{id}/related")["result"]
        return [Book(relate) for relate in books]

    def searchAllQuery(self, query: str, sort: Sort= Sort.Date) -> List[Book]:
        data = []
        payload = {'query': query, 'page': 1, "sort": sort.value}
        res = self.__getUrl('galleries/search', params=payload)

        for page in range(1, int(res["num_pages"])):
            try:
                buff = self.search(query, page, sort)
                data.extend(buff)
            except KeyError:
                try:
                    buff = self.searchFallback(query, page, sort)
                    data.extend(buff)
                except Exception as e:
                    print(f"{page=} {e=}")
                    continue

            with open("zasauce.schdata", "a+", encoding="UTF-8") as nuke:
                for doujin in buff:
                    nuke.write(f"{doujin.id} => {doujin.title.pretty}\n")
            time.sleep(.1)
        return data

    def download(self, doujin: Book):
        urls = Page.getUrls(doujin.pages)
        baseFolder = "Doujin"
        for url in urls:
            try:
                response = self.session.head(url)

                if response.status_code == 200:
                    fSize = int(response.headers.get("Content-Length"))
                    if fSize == None: fSize = 1
                    response = self.session.get(url, stream=True)
                    filename = os.path.join(url.split("/")[len(url.split("/"))-1])
                    dlPath = os.path.join(baseFolder, str(doujin.id))
                    if not os.path.isdir(dlPath):
                        os.makedirs(dlPath)

                    filename = os.path.join(dlPath, filename)

                    if os.path.isfile(filename) and os.stat(dlPath).st_size == fSize:
                        pass
                    else:
                        with open(filename, "wb") as file:
                            for chunk in response.iter_content(1024):
                                file.write(chunk)
            except Exception as e:
                print(f"Error {e}")