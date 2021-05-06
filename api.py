from flask import Flask
from flask_restful import Resource, Api, reqparse
from api_helpers import load_site_data, load_sites_data

app = Flask(__name__)
api = Api(app)
parser = reqparse.RequestParser()


# for specific site data
class Site(Resource):
    def get(self, site_domain):
        site_data = load_site_data(site_domain)
        if site_data == 404:
            return "Site not supported", 404
        return site_data, 200


# for all sites data
class SitesData(Resource):
    def get(self):
        return load_sites_data()


api.add_resource(Site, '/sitesdata/<site_domain>/')
api.add_resource(SitesData, '/sitesdata/')
if __name__ == "__main__":
    app.run(debug=True)
