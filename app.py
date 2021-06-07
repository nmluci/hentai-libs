from libs.hentai import Book, Hentai, Tag, TagOption

nh = Hentai()
book = nh.getDoujin(178348)
nh.download(book)
