import requests
import re
import os
from lxml import etree


class Searchpubmed:
    def __init__(self, term):
        self.__term = term
        # UA伪装
        self.__headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
              (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"
        }
        self.url = "https://pubmed.ncbi.nlm.nih.gov/"
        self.__size, self.__page = 200, 1
        self.__param = {}
        self.param = {
            "term": self.__term,
            "size": self.__size,
            "page": self.__page
        }
        self.__doi, self.__doi_list, self.__down_url = [], [], []
        self.__response, self.__page_text, self.__step_num, self.__results_amount, \
        self.__tree, self.__snippet, self.__citation, self.__title = [None]*8

    def get_text(self, url, param):
        self.__response = requests.get(url=url, params=param, headers=self.__headers)
        self.__page_text = self.__response.text
        return self.__page_text

    @staticmethod
    def __format_text(xpathelement):
        xpathelement = "".join(xpathelement.xpath(".//text()")).replace("<b>", "").replace("</b>", "").lower()
        return xpathelement

    def get_doi(self, page_text):
        self.__tree = etree.HTML(page_text)
        self.__title = self.__tree.xpath("//div[@class='docsum-content']/a")
        self.__snippet = self.__tree.xpath("//div[@class='full-view-snippet']")
        self.__citation = self.__tree.xpath("//span[@class='docsum-journal-citation full-journal-citation']")
        for title, snippet, citation in zip(self.__title, self.__snippet, self.__citation):
            title = self.__format_text(title)
            snipper = self.__format_text(snippet)
            searchtext = title + snipper
            self.__doi = re.search(r"""(doi: (10\..*?)\. )|(doi: (10\.\S+)\.$)""", citation.xpath("./text()")[0])
            self.__doi = [self.__doi.group(2) if self.__doi.group(2) else self.__doi.group(4)] if self.__doi else []
            for kw in self.__term:
                if kw.lower() in searchtext:
                    continue
                else:
                    self.__doi = []
                    break
            self.__doi_list += self.__doi
        return self.__doi_list

    def get_allpagedoi(self, page_text):
        print("Processing Page1")
        self.__results_amount = int(re.search(r"""<span class="value">(\d+(?:,?\d+)?)</span>.*?results""", page_text,
                                            re.DOTALL).group(1).replace(",", ""))
        self.get_doi(page_text)
        if self.__results_amount % 200 == 0:
            self.__step_num = self.__results_amount / 200 - 1
        else:
            self.__step_num = self.__results_amount // 200
        if self.__step_num:
            for page in range(2, self.__step_num + 2):
                print(f"Processing Page{page}")
                self.__size = 200
                self.__page = page
                self.__param = {
                    "term": self.__term,
                    "size": self.__size,
                    "page": self.__page
                }
                self.__page_text = self.get_text(url=self.url, param=self.__param)
                self.get_doi(self.__page_text)
        return self.__doi_list

    def scihuburl(self, doi_list):
        for doi in doi_list:
            self.__down_url.append(r"https://sci.bban.top/pdf/"+doi+".pdf")
        return self.__down_url

    @staticmethod
    def getpdf(down_url, path="./", direct=False):
        downloadpath = os.path.join(path, "download_url.txt")
        if os.path.isfile(downloadpath) and not direct:
            os.remove(downloadpath)
        for doiurl in down_url:
            if direct:
                r = requests.get(url=down_url)
                with open(os.path.join(path, os.path.basename(doiurl)), "wb") as f:
                     f.write(r.content)
            else:
                with open(downloadpath, "a") as u:
                    u.write(doiurl + "\n")


if __name__ == "__main__":
    term = input("Please input your keywords: ")
    if '"' in term:
        term = [i for i in term.split('"') if i not in ("", " ")]
    else:
        term = term.split(" ")
    downloaddir= input("Please specify the directory for downloading: ")
    direct = input("Do you want to download the pdf directly?[y/n]")
    while direct not in ["y", "n"]:
        print("You only can input y or n!")
        direct = input("Do you want to download the pdf directly?[y/n]")
    direct = True if direct == "y" else False
    getpub = Searchpubmed(term)
    page_text = getpub.get_text(getpub.url, getpub.param)
    doi_list = getpub.get_allpagedoi(page_text)
    down_url = getpub.scihuburl(doi_list)
    getpub.getpdf(down_url, downloaddir, direct)


