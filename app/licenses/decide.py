from .terms import eligible, rank


def decide(mapped, terms):
    verdicts = []
    for row in mapped:
        valid = []
        chosen = None
        if row['action'] == 'cancel':
            reason = row['reasons'][0]['code'] if row['reasons'] else None
        elif row['reasons']:
            reason = row['reasons'][0]['code']
        else:
            valid = sorted((item for item in terms if eligible(item,row)),key=lambda x:x['id'])
            if not valid:
                reason = 'NO_LICENSE'
            else:
                strongest = max(map(rank,valid))
                best = [item for item in valid if rank(item)==strongest]
                chosen = best[0] if len(best)==1 else None
                reason = None if chosen else 'VERSION_TIE'
        verdicts.append(dict(row, license=chosen, candidates=[term['id'] for term in valid], ruling=reason))
    return {'verdicts':verdicts,'selected':sum(bool(r['license']) for r in verdicts),
            'overlaps':sum(len(r['candidates'])>1 for r in verdicts),
            'ties':sum(r['ruling']=='VERSION_TIE' for r in verdicts)}
