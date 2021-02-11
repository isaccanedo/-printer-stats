import requests
import logging
import xmltodict
import graphiteQueue
import os

printer_host = os.getenv('PRINTER_HOST')
graphite = graphiteQueue.graphite(prefix='printer')
r = requests.get('https://{}/DevMgmt/ConsumableConfigDyn.xml'.format(printer_host), verify=False)
inkstatus = xmltodict.parse(r.text)
u = requests.get('https://{}/DevMgmt/ProductUsageDyn.xml'.format(printer_host), verify=False)
usage = xmltodict.parse(u.text)
for cartridge in inkstatus['ccdyn:ConsumableConfigDyn']['ccdyn:ConsumableInfo']:
    graphite.stage('ink-remaining.{}'.format(cartridge['dd:ConsumableLabelCode']), float(cartridge['dd:ConsumablePercentageLevelRemaining']))
    logging.debug("{} cartridge: {}% remaining".format(
      cartridge['dd:ConsumableLabelCode'],
      cartridge['dd:ConsumablePercentageLevelRemaining']
    ))
pagecount = usage['pudyn:ProductUsageDyn']['pudyn:PrinterSubunit']['dd:TotalImpressions']['#text']
colourpages = usage['pudyn:ProductUsageDyn']['pudyn:PrinterSubunit']['dd:ColorImpressions']
graphite.stage('pages.total', float(pagecount))
graphite.stage('pages.colour', float(colourpages))
logging.debug("{} total pages".format(pagecount))
logging.debug("{} colour pages".format(colourpages))
for t in usage['pudyn:ProductUsageDyn']['pudyn:PrinterSubunit']['pudyn:UsageByMedia']:
    if t['dd:TotalImpressions'] != "0":
        logging.debug("{} of type {}".format(t['dd:TotalImpressions']['#text'], t['dd:MediaSizeName']))
        graphite.stage('pages.{}'.format(t['dd:MediaSizeName']), float(t['dd:TotalImpressions']['#text']))
for c in usage['pudyn:ProductUsageDyn']['pudyn:ConsumableSubunit']['pudyn:Consumable']:
    label = c['dd:MarkerColor'].lower()
    if label == "cyanmagentayellow":
        label = 'colour'
    graphite.stage('{}.ink-remaining'.format(label), float(c['dd:ConsumableRawPercentageLevelRemaining']))
    graphite.stage('{}.cumulative-cartridges'.format(label), float(c['dd2:CumulativeConsumableCount']))
    graphite.stage('{}.cumulative-microlitres'.format(label), float(c['dd2:CumulativeMarkingAgentUsed']['dd:ValueFloat']))
    logging.info("{} cartridge: {}% remaining - cumulative {} cartridges, {} microliters".format(
      c['dd:MarkerColor'],
      c['dd:ConsumableRawPercentageLevelRemaining'],
      c['dd2:CumulativeConsumableCount'],
      c['dd2:CumulativeMarkingAgentUsed']['dd:ValueFloat']
    ))
graphite.store()
