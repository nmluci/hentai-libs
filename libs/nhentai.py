from urllib.parse import urljoin
from typing import List
import requests

from .models.Book import Book

class Nhentai:
    def __init__(self):
        self.module = "NH"
        self.session = requests.Session()
        self.baseAddress = "https://nhentai.net/api/"

    def __getData(self, endpoints, params={}) -> dict:
        return self.session.get(
            urljoin(self.baseAddress, endpoints),
            params=params
            ).json()
    
    def search(self, query: str, page: int=1, sort_by: str="date") -> List[Book]:
        galleries = self.__getData("galleries/search", 
            params= {
                "query": query,
                "page": page,
                "sort": sort_by
            })['result']
        return [Book(data) for data in galleries]

    def getDoujin(self, id: int) -> Book:
        try:
            return Book(self.__getData(f"gallery/{id}"))
        except KeyError:
            raise ValueError("Invalid Nuke Code!")

    def random(self) -> Book:
        nukeid = int(self.session.head("https://nhentai.net/random/").headers["Location"][3:-1])
        print(nukeid)
        return Book(self.__getData(f"gallery/{nukeid}"))

    def search(self, query: str, page: int=1, sort_by: str="date") -> List[Book]:
        galleries = self.__getData('galleries/search', {
            "query": query,
            "page": page,
            "sort": sort_by
        })["result"]
        return [Book(res) for res in galleries]
    
    def searchTagged(self, tag_id: int, page: int=1, sort_by: str="date") -> List[Book]:
        try:
            galleries = self.__getData("galleries/tagged", {
                "tag_id": tag_id,
                "page": page,
                "sort": sort_by
            })['result']
        except KeyError:
            raise ValueError("No tag available for given tag_id!")
        return [Book(res) for res in galleries]

    