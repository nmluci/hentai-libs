from collections import namedtuple
from enum import Enum, unique

@unique
class Extensions(Enum):
    JPG = 'j'
    PNG = 'p'
    GIF = 'g'

class Book:
    Tag = namedtuple("Tag", ["id", "type", "name", "url", "count"])
    Pages = namedtuple("Page", ["url", "width", "height"])
    Title = namedtuple("Title", ["eng", "jp", "pretty"])

    def __init__(self, data):
        self.id = int(data["id"])
        self.media_id = int(data["media_id"])
        self.title = Book.__maketitle__(data["title"])
        self.favorites = int(data["num_favorites"])
        self.url = f"https://nhentai.net/g/{self.id}"
        images = data["images"]

        self.pages = [
            Book.__makepage__(self.media_id, num, **_) for num, _ in enumerate(images["pages"], start=1)
        ]
        self.tags = [
            Book.__maketag__(tag) for tag in data["tags"]
        ]

        thumb_ext = Extensions(images["thumbnail"]["t"]).name.lower()
        self.thumbnail = f"https://t.nhentai.net/galleries/{self.media_id}/thumb.{thumb_ext}"

        cover_ext = Extensions(images["cover"]["t"]).name.lower()
        self.cover = f"https://t.nhentai.net/galleries/{self.media_id}/cover.{cover_ext}"

    def __maketag__(tag: dict) -> Tag:
        return Book.Tag(
            id = int(tag['id']),
            type = tag["type"],
            name = tag["name"],
            url = tag["url"],
            cunt = int(tag['count'])
        )
    
    def __makepage__(media_id: int, num: int, t:str, w: int, h: int) -> Pages:
        return Book.Pages(
            url = f"https://i.nhentai.net/galleries/{media_id}/{num}.{Extensions(t).name.lower()}",
            height = int(w),
            width = int(h)
        )

    def __maketitle__(titles: dict) -> Title:
        return Book.Title(
            eng = titles["english"],
            jp = titles["japanese"],
            pretty = titles["pretty"]
        )