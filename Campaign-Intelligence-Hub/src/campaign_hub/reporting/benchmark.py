"""Transparent comparisons within compatible, earlier historical cohorts."""
from statistics import median
from campaign_hub.reporting.attribution import CHANNEL_RULES,matured


def parse_channel_results(text):
    results={}
    for line in text.splitlines():
        values=[x.strip() for x in line.strip('|').split('|')]
        if len(values)!=10 or values[0] not in CHANNEL_RULES:
            continue
        channel,activations,exposures,spend,days,anchor,anchor_date,as_of,unit,mature=values
        try:
            rule=CHANNEL_RULES[channel]
            if int(days)!=rule['window_days'] or anchor!=rule['anchor'] or unit!=rule['exposure_unit']:
                continue
            stats={'activations':int(activations),'exposures':int(exposures),'spend':float(spend),
                   'window_days':int(days),'anchor':anchor,'anchor_date':anchor_date,'as_of':as_of,
                   'exposure_unit':unit,'mature':mature=='true' and matured(channel,anchor_date,as_of)}
            if stats['activations']<0 or stats['exposures']<=0 or stats['spend']<0:
                continue
            results[channel]=stats
        except (ValueError,TypeError):
            continue
    return results


def percentile(value,peers,higher_is_better=True):
    if not peers:
        return None
    worse=sum(p<value if higher_is_better else p>value for p in peers)
    ties=sum(p==value for p in peers)
    return 100*(worse+ties/2)/len(peers)


def compare_campaign(current,candidates,channel):
    current_stats=current.get('channel_results',{}).get(channel)
    if not current_stats or not current_stats.get('mature'):
        return {'status':'incomplete_attribution','peer_ids':[],'metrics':{},'channel':channel}
    peers=[]
    for c in candidates:
        stats=c.get('channel_results',{}).get(channel)
        if (not stats or c['campaign_id']==current['campaign_id'] or c['period']>=current['period']
                or c['campaign_type']!=current['campaign_type'] or not stats.get('mature')):
            continue
        if any(stats.get(k)!=current_stats.get(k) for k in ['window_days','anchor','exposure_unit']):
            continue
        if stats.get('exposures',0)<=0 or stats.get('activations',0)<0:
            continue
        peers.append(c)
    peers.sort(key=lambda c:(c['period'],c['campaign_id']))
    if not peers:
        return {'status':'insufficient_peers','peer_ids':[],'metrics':{},'channel':channel}
    metrics={}
    for name,higher,calculate in [('activation_rate',True,lambda x:x['activations']/x['exposures']),
                                   ('cost_per_activation',False,lambda x:x['spend']/x['activations'])]:
        denominator=current_stats.get('exposures' if name=='activation_rate' else 'activations',0)
        if denominator<=0:
            continue
        metric_peers=[p for p in peers if name=='activation_rate' or p['channel_results'][channel]['activations']>0]
        if not metric_peers:
            continue
        value=calculate(current_stats)
        values=[calculate(p['channel_results'][channel]) for p in metric_peers]
        rank=1+sum(p>value if higher else p<value for p in values)
        metrics[name]={'current':value,'peer_median':median(values),'rank':rank,'total':len(metric_peers)+1,
                       'peer_values':{p['campaign_id']:v for p,v in zip(metric_peers,values)},
                       'peer_count':len(metric_peers),'excluded_undefined_cost_peers':len(peers)-len(metric_peers),
                       'small_sample':len(metric_peers)<5,
                       'percentile':percentile(value,values,higher),'higher_is_better':higher,
                       'position':'outperforming peer median' if (value>median(values) if higher else value<median(values)) else
                                  'at peer median' if value==median(values) else 'underperforming peer median'}
    return {'status':'ok','channel':channel,'peer_ids':[p['campaign_id'] for p in peers],
            'peer_count':len(peers),'metrics':metrics,'small_sample':len(peers)<5,
            'cohort_rule':'Earlier reporting periods, same campaign type and channel, identical window/anchor/exposure unit, fully matured.'}
