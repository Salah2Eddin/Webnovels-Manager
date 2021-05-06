from helper_functions import load_cfpage, load_page, get_site_domain
from helper_functions import add_to_novels_list, load_novels_list
from helper_functions import load_site_data
from helper_functions import clean_up_title, clean_filename, clean_text
from helper_functions import realtive_to_absloute, is_absloute_url
import requests
import cfscrape
import jinja2
from bs4 import BeautifulSoup

import os
import json


class Novel():
    """
    Novel Class - Has all the data and methods to deal with novels\n
    params:\n
        name: Novel's name\n
        link: Novel's link\n
    """
    def __init__(self, name, link):
        # main variables
        self.name = name
        self.link = link

        # technical variables
        self.path = os.path.join(os.getcwd(), 'Novels', self.name)
        self.site_domain = get_site_domain(link)
        self.site_data = load_site_data(self.site_domain)
        self.cf = True if self.site_data['cloudflare'] == "1" else False
        self.scraper = cfscrape.create_scraper() if self.cf else None
        self.site_domain = get_site_domain(self.link)

        # data variables
        self.data, self.chapters_data = {}, {}
        self.chapters = []

        if self.name not in load_novels_list().keys():
            add_to_novels_list(self.name)

    def __repr__(self):
        return self.name

    # fetching methods

    def initialize(self, debug=False):
        """ gets novel and chapters data than gets chapters themselves """
        self.data, self.chapters_data = self.get_novel_data()
        self.chapters = self.get_chapters(5 if debug else 0)

    def get_chapter_data(self, chapters_elements=[]):
        """
            gets chapters data
            params:
                list chapter_elements: list of chapters html tags
                if not provided it gets them
                    default: [empty list]
            return:
                chapters_data : dict{
                    chapter title: chapter link\n
                    }
        """

        # checks if chapters html tags are provided
        if chapters_elements is []:
            # if not it gets them
            if self.cf:
                html = load_cfpage(self.link, self.scraper)
            else:
                html = load_page(self.link)
            bs4 = BeautifulSoup(html, "html.parser")
            chapters_data_selector = self.site_data['chapter_data_selector']
            chapters_elements = bs4.select(chapters_data_selector)

        # get chapters data
        chapters_data = {}
        for chapter_element in chapters_elements:
            title = clean_up_title(chapter_element.get_text())

            # some url are relative
            if is_absloute_url(chapter_element['href']):
                chapter_link = chapter_element['href']
            else:
                chapter_link = realtive_to_absloute(chapter_element['href'],
                                                    self.site_domain)

            # set the title as a key in the dict with the url as value
            chapters_data[title] = chapter_link
        return chapters_data

    def get_novel_data(self):
        """
        gets novel's data\n
        return:\n
            tuple:
                novel_data: dict{\n
                    cover_link: str\n
                    description: str\n
                    },
                chapters: dict{
                    title: str\n
                    link: str\n
                    }
        """
        # get novel page html content
        if self.cf:
            html = load_cfpage(self.link, self.scraper)
        else:
            html = load_page(self.link)

        # parse html content
        bs4 = BeautifulSoup(html, "html.parser")
        cover_element = bs4.select(self.site_data['cover_selector'])[0]
        desc_element = bs4.select(self.site_data['desc_selector'])[0]
        chapters_elements = bs4.select(self.site_data['chapter_data_selector'])

        # get cover image link
        cover_link = ""
        if is_absloute_url(cover_element['src']):
            cover_link = cover_element['src']
        else:
            cover_link = realtive_to_absloute(cover_element['src'],
                                              self.site_domain)

        # get description
        description = clean_text(desc_element.get_text())

        chapters_data = self.get_chapter_data(chapters_elements)

        novel_data = {"name": self.name, "link": self.link,
                      "cover_link": cover_link,
                      "description": description}
        return novel_data, chapters_data

    def get_chapters(self, num=0):
        """
        creates a list of chapter objects\n
        each object is a chapter in the novel\n
        params:
            int num: number of chapters to load
                default: 0 => to load all chapters
        return:
            list chapters: [class Chapter]
        """
        text_selector = self.site_data["chapter_selector"]
        # create chapter object for each chapter
        chapters = []
        n = 1
        for chapter_title in list(self.chapters_data.keys())[0:num-1]:
            # create chapter object
            chapter = Chapter(self.name, chapter_title,
                              self.chapters_data[chapter_title], self.cf)
            # fetch chapter content
            chapter.content = chapter.get_content(text_selector)
            # add to chapters list
            chapters.append(chapter)
            print(n)
            n += 1
        if self.site_data['reverse'] == "1":
            chapters.reverse()
        return chapters

    # loading methods

    def load_novel_data(self):
        """
            loads novel data if novel was saved
            return:
                novel_data: dict
        """
        file_path = os.path.join(self.path, "novel_data.json")
        with open(file_path, "r") as f:
            data = json.load(f)
            f.close()
        return data

    def load_chapters_data(self):
        """
            loads chapters data if novel was saved
            return:
                chapters_data: dict
        """
        file_path = os.path.join(self.path, "chapters_data.json")
        with open(file_path, "r") as f:
            data = json.load(f)
            f.close()
        return data

    def load_chapters(self):
        """
            loads chapters if they were saved
            return:
                chapters: list
        """
        chapters = []

        files = os.listdir(self.path)
        for file in files:
            if '.txt' not in file:
                continue
            name = file.replace('.txt', '')
            link = self.chapters_data[name]
            with open(os.path.join(self.path, file)) as f:
                chapter_content = f.read()
                f.close()
            chapter = Chapter(name, name, link, content=chapter_content)
            chapters.append(chapter)
        return chapters

    def load(self):
        """
            loads all data about this novel if it was saved
        """
        self.data = self.load_novel_data()
        self.chapters_data = self.load_chapters_data()
        self.chapters = self.load_chapters()

    # saving methods

    def save_novel_data(self):
        """ saves novel data as json file in novel folder """
        file_path = os.path.join(self.path, "novel_data.json")
        with open(file_path, "w") as f:
            f.write(json.dumps(self.data))
            f.close()

    def save_chapters_data(self):
        """ saves chapters data as json file in novel folder """
        file_path = os.path.join(self.path, "chapters_data.json")
        with open(file_path, "w") as f:
            f.write(json.dumps(self.chapters_data))
            f.close()

    def save_chapters(self):
        """ saves each chapter """
        for chapter in self.chapters:
            chapter.save(self.path)

    def save(self):
        """ saves chapters, novel data and chapters data in novel's folder """
        # Create a folder for novel if it doesn't exist
        if not os.path.exists(self.path):
            os.mkdir(self.path)

        self.save_novel_data()
        self.save_chapters_data()
        self.save_chapters()

    # html methods

    def write_html(self):
        """ Create HTML file for novel """
        current_path = os.getcwd()
        templates_folder = os.path.join(current_path, 'templates')
        # set jinja2 enviroment
        template_loader = jinja2.FileSystemLoader(searchpath=templates_folder)
        template_env = jinja2.Environment(loader=template_loader,
                                          autoescape=True)
        TEMPLATE_FILE = "novel.html"
        template = template_env.get_template(TEMPLATE_FILE)
        output_text = template.render(novel=self)
        # save output_text to html file
        file_path = os.path.join(self.path, self.name)+'.html'
        with open(file_path, 'w') as f:
            f.write(output_text)
            f.close()
        # create assets folder with javascript and css files
        if not os.path.exists(os.path.join(self.path, 'assets')):
            os.mkdir(os.path.join(self.path, 'assets'))

        css_path = os.path.join(self.path, 'assets', 'style.css')
        with open(css_path, 'w') as f:
            css = open(os.path.join(templates_folder, 'style.css')).read()
            f.write(css)
            f.close()

        js_path = os.path.join(self.path, 'assets', 'script.js')
        with open(js_path, 'w') as f:
            js = open(os.path.join(templates_folder, 'script.js')).read()
            f.write(js)
            f.close()


class Chapter():
    def __init__(self, novel, title, link, cf=False, content=""):
        # main variables
        self.novel = novel
        self.title = title
        self.link = link
        self.content = content

        # technical variables
        self.cf = cf

    def __repr__(self):
        return self.novel + "-" + self.title

    def get_content(self, css_selector):
        """
            gets chapter content
            params:
                str css_selector: css selector for content html elements
            return:
                content: str
        """
        # get chapter page html source
        if self.cf:
            html = load_cfpage(self.link, self.scraper)
        else:
            html = load_page(self.link)

        # parse html source
        bs4 = BeautifulSoup(html, "html.parser")
        chapter_content = bs4.select(css_selector)

        # get chapter content
        chapter_paragraphs = []
        for p in chapter_content:
            chapter_paragraphs.append(p.get_text())
        content = '\n'.join(chapter_paragraphs)

        # encode than decode to avoid any problems
        content = content.encode("ascii", "ignore").decode()
        content = clean_text(content)
        return content

    def save(self, path):
        """ saves chapter as txt file """
        file_name = clean_filename(self.title)
        with open(os.path.join(path, file_name), 'w') as f:
            f.write(self.content)
            f.close
