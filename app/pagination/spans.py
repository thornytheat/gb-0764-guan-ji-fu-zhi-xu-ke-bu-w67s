def normalize(text):
    intervals = []
    for expression in text.split(';'):
        numbers = list(map(int, expression.split('-')))
        intervals.append((numbers[0], numbers[-1]+1))
    merged = []
    for start,end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(end,merged[-1][1])
        else:
            merged.append([start,end])
    return merged


def pages_in(spans):
    return sum(end-start for start,end in spans)


def split_limit(intervals, first, last, allowance):
    allowed, out_of_range, exhausted = [], [], []
    for start,end in intervals:
        low,high = max(first,start),min(last+1,end)
        if low >= high:
            out_of_range.append([start,end])
            continue
        if start < low:
            out_of_range.append([start,low])
        if high < end:
            out_of_range.append([high,end])
        taken = min(allowance, high-low)
        if taken:
            allowed.append([low,low+taken])
        if low+taken < high:
            exhausted.append([low+taken,high])
        allowance -= taken
    return allowed, out_of_range, exhausted
