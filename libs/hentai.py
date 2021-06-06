from __future__ import annotations

from typing import List
from urllib.parse import urljoin, unquote
from dataclasses import dataclass
from enum import Enum, unique
import requests
from datetime import datetime, timezone

from requests.api import get

@unique
class Extensions(Enum):
    JPG = 'j'
    PNG = 'p'
    GIF = 'g'

@unique
class TagOption(Enum):
    Raw = "raw"
    Lang = "language"
    Char = "characters"
    Tags = "tag"
    Artist = "artist"
    Parody = "parody"
    Group = "group"

    all: List[TagOption] = lambda: [option for option in TagOption if option.value != "raw"]

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
    def getTags(cls, tags: List[Tag], property_: str) -> str:
        try:
            return ", ".join([tag.name for tag in tags if tag.type == property_])
        except Exception:
            return " "

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
        self.character = Tag.getTags(self.rawTag, "characters")
        self.tags = Tag.getTags(self.rawTag, "tag")

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
        self.APIurl = "https://nhentai.net/api/"
        self.HOMEurl = "https://nhentai.net/"

    def __getUrl(self, endpoint, params={}) -> dict:
        return self.session.get(
            url=urljoin(self.APIurl, endpoint),
            params=params
        ).json()

    def search(self, query: str, page: int=1, sort_by: str="date") -> List[Book]:
        res = self.__getUrl("galleries/search",
            params={
                "query": query,
                "page": page,
                "sort": sort_by
            })["result"]
        return [Book(data) for data in res]
    
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
    
    def search(self, query: str, page: int=1, sort_by: str="date") -> List[Book]:
        books = self.__getUrl('galleries/search', {
            "query": query,
            "page": page,
            "sort": sort_by
        })['result']
        return [Book(res) for res in books]

    def related(self, id: int):
        books = self.__getUrl(f"gallery/{id}/related")["result"]
        return [Book(relate) for relate in books]