import json
from collections import namedtuple

import requests
from decouple import config

CACHET_API_KEY = config('CACHET_API_KEY')
CACHET_URL = config('CACHET_URL')

CachetComponent = namedtuple('Component', ['id', 'name', 'status'])


class Cachet():
    UPDATE_URL = CACHET_URL + '/api/v1/components'  # noqa
    OPERATIONAL = 1
    PERFORMANCE_ISSUES = 2
    PARTIAL_OUTAGE = 3
    MAJOR_OUTAGE = 4

    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
            'X-Cachet-Token': CACHET_API_KEY,
            'Content-type': 'application/json'
        }

    def update(self, data, component_id=None):
        json_data = json.dumps(data)
        if component_id:
            url = self.UPDATE_URL + '/{}'.format(component_id)
            response = self.session.put(url, data=json_data)
        else:
            response = self.session.post(self.UPDATE_URL, data=json_data)
        response.raise_for_status()
        return response

    @property
    def components(self):
        components = []
        url = self.UPDATE_URL
        while url:
            response = self.session.get(url)
            data = response.json()
            try:
                url = data['meta']['next_page']
            except KeyError:
                url = None

            for entry in data['data']:
                components.append({
                    'id': entry.get('id'),
                    'name': entry.get('name'),
                    'tags': entry.get('tags', dict()).keys(),
                })

        return components

cachet = Cachet()


def update_cachet(function):
    def _update_cachet():
        updates = function()

        for update in updates:


            for cc in cachet.components:
                if update.id in cc.get('tags', []):
                    cachet.update({'status': update.status}, component_id=cc['id'])
                    break
            else:
                cachet.update({
                    'name': update.name,
                    'status': update.status,
                    'tags': update.id
                })

    return _update_cachet
