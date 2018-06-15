#!/usr/bin/python3
import gevent.monkey
gevent.monkey.patch_all()
import requests
import json
import re
import pickle
import Proxy
import os.path
from multiprocessing import Pool
from datetime import date, datetime
from bs4 import BeautifulSoup
from random import choice
from random import uniform
from time import sleep
import insert_data
import grequests


class Parser(object):
    reqs = []
    def __init__(self):
        print('Сбор доступных прокси')
        proxy = Proxy.Proxy()
        self.proxy_list = proxy.get_proxy()
        self.PROXY_LEN = len(self.proxy_list)
        self.user_agents = open('user-agent-list.txt').read().split('\n')
        d = date.today()
        date_file_name = str(d.year) + '-' + str(d.month) + '-' + str(d.day)
        self.proxy_f_name = 'proxies_' + date_file_name + '.txt'

    ''' Получение прокси '''
    def get_proxy(self):
        current_proxy = choice(self.proxy_list)
        self.current_proxy = {}
        self.current_proxy['http'] = current_proxy
        self.current_proxy['https'] = current_proxy

    ''' Счетчик прокси 
    def proxy_counter(self):
        self.pc += 1
        if self.pc == self.PROXY_LEN:
            self.pc = 0
            # sleep_time = uniform(30, 35)
            # print('Отдыхаем ' + str(sleep_time))
            # sleep(sleep_time)
    '''

    ''' Получение случайного юзер агента '''
    def get_user_agent(self):
        self.user_agent = {'User-Agent': choice(self.user_agents)}

    ''' добавить урл для обработки '''
    def add_url(self, url, use_proxy=True, params=None):
        self.get_proxy()
        self.get_user_agent()
        self.reqs.append(grequests.get(
            url, 
            timeout=30,
            proxies=self.current_proxy,
            headers=self.user_agent,
            params=params))            

    ''' Получение html файла '''
    def execute(self):
        result = []
        try:            
            responses = grequests.map(self.reqs)
            result = [resp for resp in responses if (resp is not None) and (resp.status_code == 200)]
            if len(result) == 1:
                return result[0]
            else:
                return result
        except (requests.exceptions.Timeout, requests.exceptions.ProxyError, requests.exceptions.ConnectionError):
                self.proxy_error()
        self.reqs = []

    ''' Отработка при проблемме прокси '''
    def proxy_error(self):
        self.proxy_list.remove(self.current_proxy['http'])
        self.PROXY_LEN = len(self.proxy_list)
        with open(self.proxy_f_name,'wb') as f:
            pickle.dump(self.proxy_list, f)    


class Beletag(object):
    BASE_URL = "http://shop.beletag.com/"           # базовый урл
    elements = []                                   # Все элементы каталога
    pages = []                                      # all pages
    main_catalog_link = 'https://shop.beletag.com/catalog/?pagecount=90&mode=ajax'
    # урл корневого элементв каталога
    element_count = 0                               # Счетчик спарсенных товаров

    """docstring for Beletag"""

    def __init__(self):
        self.parser = Parser()
        d = date.today()
        date_file_name = str(d.year) + '-' + str(d.month) + '-' + str(d.day)
        self.elements_list_name = 'elements-' + date_file_name + '.pkl'
        self.pages_list_name = 'pages-' + date_file_name + '.pkl'

        if os.path.exists(self.elements_list_name):
            with open(self.elements_list_name, 'rb') as afile:
                self.elements = pickle.load(afile)
        if os.path.exists(self.pages_list_name):
            with open(self.pages_list_name, 'rb') as afile:
                self.pages = pickle.load(afile)

    # Получение всех ссылок из меню
    def get_menu_links(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        li = soup.find(id='bx_1847241719_472')
        all_a = li.find('ul').find_all('a')

        result = []
        for a in all_a:
            result.append(self.BASE_URL + a['href'][1:])
        return result

    # Получение количества страниц c элемента меню
    def get_pages(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        div_pages = soup.find("div", class_='pages')
        if isinstance(div_pages, type(None)):
            self.pages_count = 0
        count = div_pages.find_all('a')
        self.pages_count = int(count[-1].text)

    # Получение всех страниц корневого каталога
    def get_all_pages(self):
        # parse menu_lik
        print('Собираются все страницы каталога')
        html = self.parser.add_url(self.main_catalog_link)
        html = self.parser.execute()
        soup = BeautifulSoup(html.content, 'html.parser')
        div_pages = soup.find("div", class_='pages')
        if isinstance(div_pages, type(None)):
            self.pages_count = 0
        count = div_pages.find_all('a')
        pages_count = int(count[-1].text)
        if pages_count < 1:
            pages_count = 1
        print('Количество страниц в каталоге: ' + str(pages_count))
        self.pages_count = pages_count
        for x in range(1, pages_count + 1):
            self.pages.append(self.main_catalog_link + "&PAGEN_1=" + str(x))
        self.save('page')

    # Сохранение картинки
    def save_image(self, img_url, name):
        if os.path.exists("images/" + name):
            return
        url = self.BASE_URL + img_url
        img = requests.get(url, stream=True)
        with open("images/" + name, "bw") as f:
            for chunk in img.iter_content(8192):
                f.write(chunk)

    # Получение всех элементов каталога со страницы
    def get_elements(self, html):
        result = []
        soup = BeautifulSoup(html.content, 'html.parser')
        content = soup.find(class_='catalog-section')
        photos = content.find_all(class_='photo')
        for photo in photos:
            ra = self.BASE_URL + photo.find(class_="base-photo")["href"][1:]
            result.append(ra)
        self.elements.extend(result)
        return len(result)

    # Сбор всей информации о товаре и занесение в массив с результатом
    def parse(self, html, url):
        result = {'url': url}
        soup = BeautifulSoup(html, 'html.parser')
        catalog_element = soup.find(class_="catalog-element")
        if catalog_element is None:
            return 0

        cn = catalog_element.find("span", itemprop="category")["content"]
        cn = cn.split(" > ")[-1:]
        category_name = "".join(cn)
        good_id = catalog_element["data-id"]
        category_id = catalog_element["data-categoryid"]

        try:
            img = catalog_element.find(class_="photo-zoom").find('img')['src']
        except Exception:
            img = None

        self.save_image(img, good_id + '.' + "".join(img.split('.')[-1:]))

        scripts = soup.find_all("script")
        stocks = None
        for script in scripts:
            data = script.string
            if data is None:
                continue
            stock = re.search('offersQuantity\[[0-9]+\]=(.*?);', data)
            if stock is None:
                continue
            else:
                stocks = json.loads(stock.groups()[0])
                break

        try:
            info = soup.find(id="item-full-zoom")
        except Exception:
            info = ''

        try:
            name = info.find(class_="title").find(attrs={"itemprop": "name"})
            name = name.text
        except Exception:
            name = ''

        try:
            articul = info.find(class_="article").span["content"]
        except Exception:
            articul = ''

        try:
            compositions = info.find_all(class_="composition")
            complecte = ''
            season = ''
            for composition in compositions:
                if "Состав" in composition.text:
                    complecte = " ".join(composition.text.split()[1:])
                elif "Сезон" in composition.text:
                    season = " ".join(composition.text.split()[1:])
        except Exception:
            complecte = ''
            season = ''

        try:
            description = info.find(class_="description").text
            description = description.replace(u'\xa0', u' ')
            description = description.strip()
        except Exception:
            description = ''

        try:
            price = info.find_all(class_="price").pop().text.split()[:-1]
            price = "".join(price)
        except Exception:
            price = ''

        colors = []

        try:
            colors_container = info.find(class_="colors").find_all("div")
            for color in colors_container:
                colors.append({"name": color.text, "id": color["data-id"]})

            sizes = []
            sizes_container = info.find(class_="sizes").find_all("div")
            for size in sizes_container:
                sizes.append({"name": size.text[1:], "id": size["data-id"]})
        except Exception:
            pass

        result = {
            "category":
            {
                "name": category_name,
                "id": category_id
            },
            "item":
            {
                "name": name,
                "id": good_id
            },
            "articul": articul,
            "season": season,
            "complecte": complecte,
            "description": description,
            "price": price,
            "colors": []
        }

        for color in colors:
            tmp_color = {
                "id": color["id"],
                "name": color["name"],
                "size": []
            }
            for size in sizes:
                # size count
                c = 0
                if (color["id"] in stocks) and (size["id"] in stocks[color["id"]]):
                    c = stocks[color["id"]][size["id"]]
                tmp_color["size"].append({
                    "id": size["id"],
                    "name": size["name"],
                    "count": c
                })
            result["colors"].append(tmp_color)
        insert_data.Beletag(result)
        self.scrapped('element', url)
        return 1

    # получение всех элементов со всех страниц
    def get_all_elements(self):
        result = []
        i = 0
        for x in self.pages:            
            self.parser.add_url(x)
            i += 1
            self.scrapped('page',x)
            if(i == 20):
                i = 0
                result.extend(self.parser.execute())
        for page_html in result:
            self.get_elements(page_html)
        self.save('element')

    def scrapped(self, type, url):
        if type == 'element':
            #if os.path.exists(self.elements_list_name):
            #    with open(self.elements_list_name, 'rb') as afile:
            #        self.elements = pickle.load(afile)
            if url in self.elements:
                with open(self.elements_list_name, 'wb') as file:
                    self.elements.remove(url)
                    pickle.dump(self.elements, file)
        else:
            #if os.path.exists(self.pages_list_name):
            #    with open(self.pages_list_name, 'rb') as afile:
            #        self.pages = pickle.load(afile)
            with open(self.pages_list_name, 'wb') as file:
                self.pages.remove(url)
                pickle.dump(self.pages, file)

    def save(self, type):
        if type == 'element':
            with open(self.elements_list_name, 'wb') as file:
                pickle.dump(self.elements, file)
        else:
            with open(self.pages_list_name, 'wb') as file:
                pickle.dump(self.pages, file)

    # Обработка элемента каталога
    def parse_element(self):
        counter_start = 0
        counter_end = 20
        while counter_start < len(self.elements):
            current_dict = self.elements[counter_start:counter_end]
            for element in current_dict:
                self.parser.add_url(element)
            responses = self.parser.execute()
            for resp in responses:
                res = self.parse(resp.content, element)
                if res == 1:
                    self.scrapped('element',resp.url)
            counter_start += 20
            counter_end += 20


def main():
    start = datetime.now()
    print('Старт')
    b = Beletag()
    print('Всего ' + str(b.parser.PROXY_LEN) + 'проксей')
    if len(b.pages) < 1:
        print('Получаем список страниц')
        b.get_all_pages()
    if len(b.elements) < 1:
        print('Получаем список элементов')
        while len(b.pages) > 1:
            b.get_all_elements()
    print('Обрабатываем элементы в 40 процессов')
    while len(b.elements) > 0:
        b.parse_element()
    end = datetime.now()
    print('Завершено за ' + str(end-start))


if __name__ == '__main__':
    main()
