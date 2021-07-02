from helper_functions import load_cfpage, load_page, get_site_domain
from helper_functions import add_to_novels_list, load_novels_list
from helper_functions import load_site_data
from helper_functions import clean_up_title, clean_filename, clean_text
from helper_functions import realtive_to_absloute, is_absloute_url

import novel_exceptions

import cfscrape
import jinja2
from bs4 import BeautifulSoup

import os
import json
from shutil import copy, copytree, rmtree

from weasyprint import HTML, CSS


class Novel():
    """
    Novel Class - Has all the data and methods to deal with novels\n
    params:\n
        name: Novel's name\n
        optional named params:
            str link: link to novel
            bool load: load novel from local folder or not
            (ignored if link not provided)
    """
    def __init__(self, name, **kwrgs):
        # main variables
        self.name = name
        self.path = os.path.join(os.getcwd(), 'Novels', self.name)
        self.initialized = False

        self.link = None
        # get link if in kwrgs
        if 'link' in list(kwrgs.keys()):
            self.link = kwrgs['link']

        self.load = False
        # get load if in kwrgs and set it to true if no link provided
        if self.link is None:
            self.load = True
        elif 'load' in list(kwrgs.keys()):
            self.load = kwrgs['load']

        if self.name not in load_novels_list().keys():
            add_to_novels_list(self.name, self.link)

    def __repr__(self):
        return self.name

    def initialize(self, debug=False) -> None:
        """ initializes novel object """
        # Create a folder for novel if it doesn't exist
        if not os.path.exists(self.path):
            os.mkdir(self.path)

        if self.link is None or self.load:
            try:
                self.data = self.load_novel_data()
                self.link = self.data['link']

                self.site_domain = self.data['domain']
                self.cf = self.data['cf']

                self.initialized = True
                self.chapters_data = self.load_chapters_data()
                self.chapters = self.load_chapters()
            except FileNotFoundError as e:
                if self.data is None:
                    print(e)
                    raise novel_exceptions.NoNovelData
                elif self.chapters_data is None:
                    print(e)
                    raise novel_exceptions.NoChapterData
            except KeyError as e:
                print(e)
                raise novel_exceptions.MissingNovelData
            except Exception as e:
                print(e)

        self.site_domain = get_site_domain(self.link)
        self.site_data = load_site_data(self.site_domain)
        self.cf = True if self.site_data['cloudflare'] == "1" else False
        self.scraper = cfscrape.create_scraper() if self.cf else None

        if self.load is False:
            self.data, self.chapters_data = self.get_novel_data()
            self.chapters = self.get_chapters(5 if debug else 0)

        self.initialized = True

    # fetching methods

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
                      "description": description,
                      "cf": self.cf, "domain": self.site_domain,
                      }
        return novel_data, chapters_data

    def get_chapters(self, num=0):
        """
        creates a list of chapter objects\n
        each object is a chapter in the novel\n
        params:
            int num: number of chapters to load
                default: 0 => to get all chapters
        return:
            list chapters: [class Chapter]
        """
        # make sure novel object initialized
        assert(self.initialized is False)

        text_selector = self.site_data["chapter_selector"]
        # create chapter object for each chapter
        chapters = []
        chapters_titles = list(self.chapters_data.keys())
        if self.site_data['reverse'] == "1":
            chapters_titles = list(reversed(chapters_titles))

        n = 1
        for chapter_title in chapters_titles[0:num-1]:
            # create chapter object
            chapter = Chapter(self, chapter_title,
                              self.chapters_data[chapter_title], self.cf)
            # fetch chapter content
            chapter.content = chapter.get_content(text_selector, self.scraper)
            chapter.save()
            # add to chapters list
            chapters.append(chapter)
            print(n)
            n += 1
        return chapters

    def update(self):
        # make sure novel object initialized
        assert(self.initialized is True)

        text_selector = self.site_data["chapter_selector"]
        # update chapters data
        self.data, self.chapters_data = self.get_novel_data()

        new_chapters = []
        existing_chapters_titles = []

        # save existing chapters and get their titles
        for chapter in self.chapters:
            existing_chapters_titles.append(chapter.title)
            new_chapters.append(chapter)

        # reverse chapters sorting if needed
        chapters_titles = list(self.chapters_data.keys())
        if self.site_data['reverse'] == "1":
            chapters_titles = list(reversed(chapters_titles))

        # get new chapters
        for chapter_title in chapters_titles:
            # ignore existing chapters
            if chapter_title in existing_chapters_titles:
                continue
            # create chapter object
            print("New chapter: {}".format(chapter_title))
            chapter = Chapter(self, chapter_title,
                              self.chapters_data[chapter_title], self.cf)
            # fetch chapter content
            chapter.content = chapter.get_content(text_selector, self.scraper)
            chapter.save()
            # add to new chapters list
            new_chapters.append(chapter)

        # update novel chapters
        self.chapters = new_chapters

    # loading methods

    def load_novel_data(self):
        """
            loads novel data\n
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
            loads chapters data\n
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
        # make sure novel object initialized
        assert(self.initialized is True)

        chapters_paths = {}
        with open(os.path.join(self.path, 'chapters_path.json')) as f:
            chapters_paths = json.loads(f.read())
            f.close()

        chapters_links = {}
        with open(os.path.join(self.path, 'chapters_data.json')) as f:
            chapters_links = json.loads(f.read())
            f.close()

        chapters = []
        for chapter_title, path in chapters_paths.items():
            with open(path, 'r') as f:
                content = f.read()
                f.close()
            chapter = Chapter(self, chapter_title,
                              chapters_links[chapter_title],
                              self.cf, content)
            chapters.append(chapter)
        return chapters

    # saving methods

    def save_novel_data(self):
        """ saves novel data as json file in novel folder """
        # make sure novel object initialized
        assert(self.initialized is True)
        file_path = os.path.join(self.path, "novel_data.json")
        with open(file_path, "w") as f:
            f.write(json.dumps(self.data))
            f.close()

    def save_chapters_data(self):
        """ saves chapters data {name:link} as json file in novel folder """
        # make sure novel object initialized
        assert(self.initialized is True)
        file_path = os.path.join(self.path, "chapters_data.json")
        with open(file_path, "w") as f:
            f.write(json.dumps(self.chapters_data))
            f.close()

    def save_chapters(self):
        """ saves each chapter and saves a json with their paths"""
        # make sure novel object initialized
        assert(self.initialized is True)
        chapter_paths = {}
        # store path and save chapter
        for chapter in self.chapters:
            chapter_paths[chapter.title] = chapter.path
            chapter.save()

        # store paths as a json
        with open(os.path.join(self.path, 'chapters_path.json'), 'w') as f:
            f.write(json.dumps(chapter_paths))
            f.close()

    def save(self):
        """ saves chapters, novel data and chapters data in novel's folder """
        # make sure novel object initialized
        assert(self.initialized is True)

        self.save_novel_data()
        self.save_chapters_data()
        self.save_chapters()

    # Exporting methods
    # HTML

    def write_html(self):
        """
        Generates HTML from Template
        return:
            str HTML: Generated HTML
        """
        # make sure novel object initialized
        assert(self.initialized is True)

        current_path = os.getcwd()
        templates_folder = os.path.join(current_path, 'templates')
        # set jinja2 enviroment
        template_loader = jinja2.FileSystemLoader(searchpath=templates_folder)
        template_env = jinja2.Environment(loader=template_loader,
                                          autoescape=True)
        TEMPLATE_FILE = "novel.html"
        template = template_env.get_template(TEMPLATE_FILE)
        output_text = template.render(novel=self)

        return output_text

    def export_as_html(self):
        """ Exports Novel as HTML File """
        # make sure novel object initialized
        assert(self.initialized is True)

        # Creates novel folder if it doesn't exist
        if not os.path.exists(self.path):
            os.mkdir(self.path)

        current_path = os.getcwd()
        templates_folder = os.path.join(current_path, 'templates')

        # save output_text to html file
        html = self.write_html()
        file_path = os.path.join(self.path, self.name)+'.html'
        with open(file_path, 'w') as f:
            f.write(html)
            f.close()

        # create assets folder with javascript and css files
        if not os.path.exists(os.path.join(self.path, 'assets')):
            os.mkdir(os.path.join(self.path, 'assets'))

        css_path = os.path.join(templates_folder, 'style.css')
        css_dst = os.path.join(self.path, 'assets', 'style.css')
        if os.path.isfile(css_dst):
            os.remove(css_dst)
        copy(css_path, css_dst)

        js_path = os.path.join(templates_folder, 'scripts')
        js_dst = os.path.join(self.path, 'assets', 'scripts')
        if os.path.isdir(js_dst):
            rmtree(js_dst)
        copytree(js_path, js_dst)

        fonts_path = os.path.join(templates_folder, 'fonts')
        fonts_dst = os.path.join(self.path, 'assets', 'fonts')
        if os.path.isdir(fonts_dst):
            rmtree(fonts_dst)
        copytree(fonts_path, fonts_dst)

    # PDF
    def write_pdf_as_html(self, dark_mode=False):
        """
        Generates PDF Content as HTML from Template
        return:
            str HTML: Generated HTML
        """
        # make sure novel object initialized
        assert(self.initialized is True)

        current_path = os.getcwd()
        templates_folder = os.path.join(current_path, 'templates')

        # set jinja2 enviroment
        template_loader = jinja2.FileSystemLoader(searchpath=templates_folder)
        template_env = jinja2.Environment(loader=template_loader,
                                          autoescape=True)
        TEMPLATE_FILE = "pdf_novel.html"

        template = template_env.get_template(TEMPLATE_FILE)
        output_text = template.render(novel=self, dark_mode=dark_mode)

        return output_text

    def export_as_pdf(self, dark_mode=False):
        """ Exports Novel as PDF File """
        # make sure novel object initialized
        assert(self.initialized is True)

        # Creates novel folder if it doesn't exist
        if not os.path.exists(self.path):
            os.mkdir(self.path)
        # important Paths
        templates_folder = os.path.join(os.getcwd(), 'templates')
        css_file_suffix = '_dark' if dark_mode else '_light'
        css_filename = 'pdf_style{}.css'.format((css_file_suffix))
        css_path = os.path.join(templates_folder, css_filename)
        pdf_dst = os.path.join(self.path, self.name+'.pdf')
        if dark_mode:
            pdf_dst = os.path.join(self.path, self.name+' Dark'+'.pdf')

        html = self.write_pdf_as_html(dark_mode)
        # delete older pdf if exists
        if os.path.isfile(pdf_dst):
            os.remove(pdf_dst)
        # write pdf file
        HTML(string=html).write_pdf(pdf_dst, stylesheets=[CSS(css_path)])


class Chapter():
    def __init__(self, novel, title, link, cf=False, content=""):
        # main variables
        self.novel = novel
        self.title = title
        self.link = link
        self.content = content
        self.path = os.path.join(self.novel.path, clean_filename(self.title))
        # technical variables
        self.cf = cf

    def __repr__(self):
        return self.novel.name + "-" + self.title

    def get_content(self, css_selector, scraper):
        """
            gets chapter content
            params:
                str css_selector: css selector for content html elements
            return:
                content: str
        """
        # get chapter page html source
        if self.cf:
            html = load_cfpage(self.link, scraper)
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

    def save(self):
        """ saves chapter as txt file """
        # ignore chapter if already exists, if not save it
        if os.path.isfile(self.path):
            with open(self.path) as f:
                # and same content
                if f.read() == self.content:
                    pass
                else:
                    f.write(self.content)
                f.close()
        else:
            with open(self.path, 'x') as f:
                f.write(self.content)
                f.close()
