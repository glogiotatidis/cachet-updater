# Mozilla Marketing Engineering Status Page

You can reach Mozilla Marketing Engineering Status Page at
https://status.mozmar.org. The page is powered by Cachet and this worker,
responsible to update the status of the different Cachet Components.

The worker fetches information from [NewRelic](http://newrelic.com/) Synthenics
and App monitoring and from [DeadMansSnitch](http://deadmanssnitch.com/).


## Status Codes

This section describes how status from the different monitored services is
matched to Cachet status codes.

### Dead Man's Snitch

Snitch status is directly read from DMS API. DMS health status is matched to
Cachet status as following:

 - healthy -> OPERATIONAL
 - pending -> OPERATIONAL
 - failed  -> MAJOR_OUTAGE


### NewRelic App Monitoring

App status is directly read from NewRelic API. NR Color codes are matched to
Cachet status as following:

 - red -> MAJOR_OUTAGE
 - yellow -> PARTIAL_OUTAGE
 - green -> OPERATIONAL
 - gray -> PARTIAL_OUTAGE


### NewRelic Synthetics

NewRelic Synthetics status cannot be directly read from the API. We do fetch the
checks from the last 15 minutes from NewRelic Insights API and we match the
check results to Cachet status as following:

 - All checks successful -> OPERATIONAL
 - Most of the checks successful -> PERFORMANCE_ISSUES
 - Most of the checks failed -> PARTIAL_OUTAGE
 - All checks failed -> MAJOR_OUTAGE
