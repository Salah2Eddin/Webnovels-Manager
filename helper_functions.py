from urllib.parse import urlparse
import re
import requests
import os
import json
import time


def load_page(link):
    """
    loads normal webpages\n
    params:\n
        str link: page's link\n
    return:
        page html: string"""
    no_tries = 0
    while no_tries < 3:
        try:
            page = requests.get(link)
            return page.text
        except Exception:
            no_tries += 1
            time.sleep(3)


def load_cfpage(link, cfscraper):
    """
    loads cloudflare protected webpages\n
    scrapper object not created inside function to avoid cache loss\n
    params:
        str link: page's link
        CloudflareScrapper cfscrapper: scraper object
    return:
        page html: str
    """
    no_tries = 0
    while no_tries < 3:
        try:
            page = cfscraper.get(link)
            return str(page.content)
        except Exception:
            no_tries += 1
            time.sleep(3)


def load_novels_list():
    """
    reads novels_list.json and returns dict with all novels
    return:
        novels_list: dict{name: str link}
    """
    file = 'novels_list.json'
    # check if json file exists, if not adds it
    if not os.path.exists(file):
        with open(file, 'w') as f:
            f.write('{}')
            f.close
        return {}
    # reads json and returns novels list
    else:
        with open(file, 'r') as f:
            novels_list = json.load(f)
            f.close()
        return novels_list


def load_site_data(sd):
    """
    gets needed data for the novel's host from sites_data.json\n
    params:
        str sd: site_domain
    return:\n
        site_data: dict
    """
    # try sending api request for site data
    request_url = f"https://novels-reader-api.herokuapp.com/sitesdata/{sd}"
    request = requests.get(request_url)
    return json.loads(request.text)


def add_to_novels_list(name, link):
    """
    adds novel to novels_list.json\n
    paramas:\n
        str name: novel's name
        str link: novel's link
    """
    # Remove copying mistakes
    name = clean_up_title(name)

    novels_list = load_novels_list()
    novels_list[name] = link
    with open('novels_list.json', 'w') as f:
        f.write(json.dumps(novels_list))
        f.close()


def get_site_domain(url):
    """
    gets the domain from url
    params:
        str url: site url
    return:
        domain: str
    """
    return urlparse(url).netloc


def clean_up_title(title):
    """
    cleans up title from extra spaces
    params:
        str title
    return:
        clean_title: str
    """
    clean_title = title.replace('\n', '')
    clean_title = clean_title.replace('/n', '')
    clean_title = clean_title.strip()
    return clean_title


def clean_text(text):
    """
    cleans text from wierd stuff
    params:
        str text
    return:
        clean_text: str
    """
    # remove all escape characters
    escape_chars = ['\n', '\t', '\r']
    for char in escape_chars:
        clean_text = text.replace(char, '')
    # remove spaces at start and end
    clean_text = clean_text.strip()

    # add space after each double quote if there isn't one
    # and removes edge spaces inside them
    double_quotes_no_space = re.findall(r'".*"\b', clean_text)
    for i in double_quotes_no_space:
        double_quotes_text = i[1:-2].strip()
        clean_text = clean_text.replace(i, '"{}" '.format(double_quotes_text))
    return clean_text


def clean_filename(name):
    """
    cleans and creates a suitable text file name from title
    params:
        str name: title
    return:
        file_name: str
    """
    file_name = name.replace(':', '')
    file_name = file_name.replace('–', '')
    file_name = file_name.replace('-', '')
    file_name = file_name.replace('?', '')
    file_name = file_name.replace('\"', '')
    file_name = file_name.replace('\\', '')
    file_name = file_name.replace(':', '')
    file_name = file_name.strip()
    file_name += '.txt'
    return file_name


def clean_foldername(name):
    """
    cleans title to make it suitable as a folder name
    params:
        str name: title
    return:
        folder_name: str
    """
    folder_name = name.replace(':', '')
    folder_name = folder_name.replace('–', '')
    folder_name = folder_name.replace('-', '')
    folder_name = folder_name.replace('?', '')
    folder_name = folder_name.replace('\"', '')
    folder_name = folder_name.replace('\\', '')
    folder_name = folder_name.replace(':', '')
    folder_name = folder_name.strip()
    return folder_name


def is_absloute_url(url):
    """
    checks if url is absloute
    params:
        str url
    return:
        bool: is_absloute
    """
    if url.startswith("http://"):
        return True
    elif url.startswith("https://"):
        return True
    else:
        return False


def realtive_to_absloute(url, site_domain=""):
    """
    turns relative url to absloute
    params:
        str url : relative url
        str site_domain: in case it needs starting point, can be empty
    return:
        absloute url: str
    """
    parser = urlparse(url)
    if parser.netloc and not parser.scheme:
        return "https://"+url
    elif not parser.netloc and parser.path:
        return "https://"+site_domain+url


def get_novel_path(novelName):
    return os.path.join(os.getcwd(), 'Novels', clean_foldername(novelName))
