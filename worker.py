import logging
from datetime import datetime, timedelta
from collections import defaultdict, Counter

import requests
from decouple import config

from cachet import CachetComponent, cachet, update_cachet

DMS_API_KEY = config('DMS_API_KEY')
NEW_RELIC_API_KEY = config('NEW_RELIC_API_KEY')
NEW_RELIC_QUERY_KEY = config('NEW_RELIC_QUERY_KEY')

DMS_URL = 'https://api.deadmanssnitch.com/v1/snitches'

formt = '[%(asctime)s] %(levelname)s - %(message)s'
LOG_LEVEL = config('LOG_LEVEL', default='INFO')
logging.basicConfig(level=LOG_LEVEL, format=formt)


@update_cachet
def fetch_snitches():
    response = requests.get(DMS_URL, auth=(DMS_API_KEY, ''))
    response.raise_for_status()
    STATUS = {
        'healthy': cachet.OPERATIONAL,
        'pending': cachet.OPERATIONAL,
        'failed': cachet.MAJOR_OUTAGE,
    }

    snitches = []
    for snitch in response.json():
        id = 'dms-{}'.format(snitch['token'])
        status = STATUS[snitch['status']]
        snitches.append(
            CachetComponent(id=id, name=snitch['name'], status=status)
        )

    return snitches


@update_cachet
def fetch_newrelic():
    STATUS = {
        'red': cachet.MAJOR_OUTAGE,
        'yellow': cachet.PARTIAL_OUTAGE,
        'green': cachet.OPERATIONAL,
        'gray': cachet.PARTIAL_OUTAGE,
    }
    apps = []
    response = requests.get('https://api.newrelic.com/v2/applications.json',
                            headers={'X-Api-Key': NEW_RELIC_API_KEY})

    for application in response.json()['applications']:
        id = 'nr-{}'.format(application['id'])
        apps.append(
            CachetComponent(id=id,
                            name=application['name'],
                            status=STATUS[application['health_status']]))

    return apps


@update_cachet
def fetch_synthetics():
    response = requests.get('https://insights-api.newrelic.com/v1/accounts/1299394/query?nrql=SELECT%20monitorId%2C%20monitorName%2C%20result%20%20FROM%20SyntheticCheck%20LIMIT%20200',
                            headers={'X-Query-Key': NEW_RELIC_QUERY_KEY})
    monitor_name = {}
    monitor_status = defaultdict(Counter)
    now = datetime.utcnow()
    for x in response.json()['results'][0]['events']:
        monitor_time = datetime.fromtimestamp(float(str(x['timestamp'])[:-3]))
        if monitor_time + timedelta(minutes=15) < now:
            continue
        monitor_status[x['monitorId']].update([x['result']])
        monitor_name[x['monitorId']] = x['monitorName']

    monitors = []
    for monitor_id, status in monitor_status.items():
        if len(status) > 1:
            first, second = status.most_common(2)
        else:
            first = status.most_common()
            second = first
        first = first[0][0]
        second = second[0][0]

        if first == 'SUCCESS' and second == 'SUCCESS':
            status = cachet.OPERATIONAL
        elif first == 'SUCCESS' and second == 'FAILED':
            status = cachet.PERFORMANCE_ISSUES
        elif first == 'FAILED' and second == 'SUCCESS':
            status = cachet.PARTIAL_OUTAGE
        else:
            status = cachet.MAJOR_OUTAGE

        monitors.append(CachetComponent(id='synthetics-{}'.format(monitor_id),
                                        name=monitor_name[monitor_id],
                                        status=status))
    return monitors


if __name__ == '__main__':
    from apscheduler.schedulers.blocking import BlockingScheduler
    scheduler = BlockingScheduler()

    for job in [fetch_snitches, fetch_newrelic, fetch_synthetics]:
        scheduler.add_job(job, 'interval', minutes=2,
                          max_instances=1, coalesce=True)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
