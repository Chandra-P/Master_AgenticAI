"""Comparison datasets and adjacent insights derived from the validated factual packet."""
from collections import defaultdict


def value_label(value,unit):
    if unit=='percent':
        return f'{value:.2%}'
    if unit=='USD':
        return f'${value:,.2f}'
    return f'{value:,.0f}'


def share(value,total):
    return f'{value/total:.1%}' if total else 'undefined (zero total)'


def comparison_panels(packet):
    f=packet['facts']; cid=packet['campaign_id']; source=f'{cid}-performance_report'
    panels=[]
    def add(key,family,title,labels,values,unit,insight,citations,highlights=None,note=''):
        panels.append(dict(key=key,family=family,title=title,labels=labels,values=values,unit=unit,
            insight=insight,citations=citations,highlights=highlights or [len(values)-1],note=note))
    add('activation_goal','Progress Toward Goals','Activation goal versus actual',
        ['Goal','Actual'],[f['target'],f['actual']],'accounts',
        f"The campaign delivered {f['actual']:,} activations against {f['target']:,} planned ({f['actual']/f['target']:.1%} attainment), "
        f"a difference of {f['actual']-f['target']:+,}. Spend was ${f['spend']:,.0f} against a ${f['budget']:,.0f} ceiling. "
        f"Acquisition cost was ${f['spend']/f['actual']:.2f} versus the planned ${f['budget']/f['target']:.2f} ceiling.",
        [source,f'{cid}-success_plan'])
    add('balance_goal','Progress Toward Goals','Opening balance goal versus actual',
        ['Goal','Actual'],[f['balance_target_cents']/100,f['balance_cents']/100],'USD',
        f"Opening account balances totaled ${f['balance_cents']/100:,.2f}; goal attainment: {share(f['balance_cents'],f['balance_target_cents'])}. "
        f"The difference was ${(f['balance_cents']-f['balance_target_cents'])/100:+,.2f}. These are balances at account opening, not revenue or current deposits.",
        [source,f'{cid}-success_plan'])
    channels=f['channel_results']; names=['Direct mail','Display']; keys=['direct_mail','display']
    counts=[channels[k]['activations'] for k in keys]
    add('channel_accounts','Channel performance','Attributed accounts by channel',names,counts,'accounts',
        f"Direct mail supplied {counts[0]:,} accounts ({counts[0]/f['actual']:.1%} of attributed accounts); display supplied {counts[1]:,} ({counts[1]/f['actual']:.1%}). "
        'This describes volume composition, not incremental channel lift.',[source],highlights=[0,1],
        note='Direct mail: 60 days from mail/drop. Display: 30 days from exposure.')
    defined=[k for k in keys if channels[k]['activations']>0]
    if defined:
        costs=[channels[k]['spend']/channels[k]['activations'] for k in defined]
        lowest=defined[costs.index(min(costs))]
        finding=(f"{lowest.replace('_',' ').title()} had the lower observed acquisition cost at ${min(costs):.2f}. " if len(costs)>1 and min(costs)!=max(costs)
            else f"Both channels had the same acquisition cost of ${costs[0]:.2f}. " if len(costs)>1
            else f"{lowest.replace('_',' ').title()} had a defined acquisition cost of ${costs[0]:.2f}. ")
        add('channel_cost','Channel performance','Attributed cost per activation',
            [k.replace('_',' ').title() for k in defined],costs,'USD',
            finding+
            'Channel cohorts and exposure definitions differ. This is an attributed efficiency comparison, not evidence of causal superiority or ROI.'+
            (' Zero-activation channels have undefined acquisition cost and are excluded.' if len(defined)<2 else ''),[source],
            highlights=[costs.index(min(costs))],note='Lower acquisition cost is better; financial return was not measured.')
    for result in f['history']:
        if result['status']!='ok':
            continue
        for metric,m in result['metrics'].items():
            rate=metric=='activation_rate'; channel=result['channel'].replace('_',' ').title()
            labels=list(m['peer_values'])+['Current campaign']
            values=list(m['peer_values'].values())+[m['current']]
            add(f"{result['channel']}:{metric}",'Same-client historical standing',
                f"{channel}: {'activation rate' if rate else 'acquisition cost'}",labels,values,'percent' if rate else 'USD',
                f"Current {value_label(m['current'],'percent' if rate else 'USD')} versus a same-client historical median of "
                f"{value_label(m['peer_median'],'percent' if rate else 'USD')}: {m['position']}. "
                f"Rank {m['rank']} of {m['total']} including this campaign, using {m['peer_count']} comparable prior campaigns. "+
                ('Small cohort: descriptive only; no statistical significance claim.' if m['small_sample'] else 'Descriptive comparison; no statistical significance claim.')+
                (f" Excludes {m['excluded_undefined_cost_peers']} zero-activation prior campaigns with undefined acquisition cost." if m['excluded_undefined_cost_peers'] else ''),
                [source]+[f'{peer}-performance_report' for peer in m['peer_values']],
                note='Same client, product and channel; earlier periods and mature matching attribution. '+('Higher is better.' if rate else 'Lower is better.'))
    geo=defaultdict(lambda:{'accounts':0,'balance_cents':0})
    for row in f['geography']:
        geo[row['location']]['accounts']+=row['accounts'];geo[row['location']]['balance_cents']+=row['balance_cents']
    for metric,unit,total,title in [('accounts','accounts',f['actual'],'Attributed accounts by location'),
        ('balance_cents','USD',f['balance_cents'],'Opening balances by location')]:
        ordered=sorted(geo,key=lambda name:(-geo[name][metric],name))
        top=ordered[0]; amount=geo[top][metric]
        add('geographic_accounts' if metric=='accounts' else 'geographic_balances','Geographic performance',title,
            ordered,[geo[name][metric]/(100 if metric=='balance_cents' else 1) for name in ordered],unit,
            f"{top} contributed the largest share: {value_label(amount/(100 if metric=='balance_cents' else 1),unit)} "
            f"({share(amount,total)} of the campaign total). Location totals combine the two mutually assigned channels. "
            'This shows concentration of outcomes, not geographic lift or market potential.',[source],highlights=[0],
            note='Fictional city aggregates; all location totals reconcile to the campaign results.')
    return panels
