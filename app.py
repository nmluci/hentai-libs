from libs.hentai import Hentai

nh = Hentai()
book = nh.random()
print(f"{book.title.pretty=}\n{book.tags=}\n{book.character=}\n{book.num_pages=}")