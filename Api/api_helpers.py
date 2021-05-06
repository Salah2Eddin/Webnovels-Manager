import json


def load_sites_data():
    """
    reads sites_data.json and returns dict with all sites data
    return:
        site_data: dict
    """
    file = 'sites_data.json'
    # reads json and returns site data
    with open(file, 'r') as f:
        sites_data = json.load(f)
        f.close()
    return sites_data


def load_site_data(sd):
    """
    reads sites_data.json and returns dict with specified site data
    params:
        str sd: site domain
    return:
        site_data: dict
    """
    sites_data = load_sites_data()
    # puts site domain in right format (www. at start)
    site = 'www.' + sd if 'www.' not in sd[0:4] else sd
    # checks if site exists
    if site not in sites_data.keys():
        return 404
    return sites_data[site]
