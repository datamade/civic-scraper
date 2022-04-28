import re

def la_county_committee_parser(name):
    bos_strings = ('BOS', 'Board')
    bos_meeting = any((s in name for s in bos_strings))
    if bos_meeting:
        return 'Board of Supervisors'
    else:
        return name.strip(', ')

def la_usd_committee_parser(name):
    print(name)
    board_strings = ('Board', 'Regular', 'Special')
    bos_meeting = any(s in name for s in board_strings)
    if bos_meeting:
        return 'Board of Education'

    pattern = r'\d{2}-\d{2}-\d{2,4},? [- ]?([,&\w\s]*)[ -]? \d{1,2}:?\d{0,2} (AM|PM|a.m.|p.m.)?'
    match = re.match(pattern, name)

    if match and match.group(1):
        committee = match.group(1).strip(', ')
        committee_str_list = committee.split(' ')
        if committee_str_list[-1] == 'Meeting':
            return ' '.join(committee_str_list[:-1])
        else:
            return committee

    else:
        return name.strip(', ')
