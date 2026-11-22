import json

import pytest

from app.registry.catalog import compile_register, load_register
from app.source import bundle
from app.workflow import steps

HEADER = 'entry,action,received,institution,issn,pages,target\n'


def register_with(previous):
    authority = json.loads(json.dumps(load_register()['authority']))
    authority['journals'][1]['previous'] = previous
    return compile_register(authority, 'test')


def csv_bytes(*rows):
    return (HEADER + '\n'.join(rows) + '\n').encode()


def copy(entry, received, issn='0412-2023', pages='3-4', org='00123'):
    return f'{entry},copy,{received},{org},{issn},{pages},'


def records(report):
    return {row['entry']: row for row in report['registry']['records']}


def test_receipt_date_selects_registration():
    # 样例目录：0412-2023 在 2027-01-01 前归海岬文献，之后归馆藏辑刊
    report = steps(csv_bytes(copy('A1', '2026-12-31'), copy('A2', '2027-01-01')))
    rows = records(report)
    assert rows['A1']['journal']['issn'] == '2049-3630'
    assert rows['A2']['journal']['issn'] == '1980-3412'
    assert rows['A1']['basis']['window'] == {'from': '2001-01-01', 'until': '2027-01-01'}
    assert rows['A2']['basis']['window'] == {'from': '2027-01-01', 'until': None}


def test_overlap_pends_only_orders_in_window():
    # 补录后两段登记在 2026-11-01 起交叠
    register = register_with([{'key': '0412-2023', 'from': '2026-11-01'}])
    report = steps(csv_bytes(copy('B1', '2026-10-15'), copy('B2', '2026-11-15'),
                             copy('B3', '2027-02-01'), copy('B4', '2026-11-15', issn='2049-3630')),
                   register=register)
    rows = records(report)
    assert rows['B1']['journal']['issn'] == '2049-3630'  # 交叠期前仍归海岬文献
    assert rows['B2']['journal'] is None                 # 交叠期待证
    assert rows['B2']['reasons'][0]['code'] == 'ISSN_OVERLAP'
    assert rows['B2']['basis']['candidates'] == ['1980-3412', '2049-3630']
    assert rows['B3']['journal']['issn'] == '1980-3412'  # 海岬文献登记已止
    assert rows['B4']['journal']['issn'] == '2049-3630'  # 现行刊号不受交叠影响
    copies = {row['entry']: row for row in report['pages']['copies']}
    assert (copies['B2']['licensed'], copies['B2']['pending']) == (0, 2)
    assert copies['B1']['licensed'] == copies['B4']['licensed'] == 2
    assert report['balance']['balanced']


def test_overlap_reported_as_register_conflict():
    register = register_with([{'key': '0412-2023', 'from': '2026-11-01'}])
    report = steps(csv_bytes(copy('C1', '2026-11-15')), register=register)
    conflict = next(item for item in report['registry']['conflicts'] if item['key'] == '0412-2023')
    assert {entry['journal'] for entry in conflict['claims']} == {'2049-3630', '1980-3412'}
    assert report['registry']['issn_overlap'] == 1


def test_shipped_catalog_has_no_conflict():
    report = steps(bundle('dirty'))
    assert report['registry']['conflicts'] == [] and report['registry']['issn_overlap'] == 0


def test_window_must_be_left_closed():
    with pytest.raises(ValueError, match='0412-2023'):
        register_with([{'key': '0412-2023', 'from': '2027-01-01', 'until': '2026-01-01'}])


def test_window_dates_must_be_iso_days():
    with pytest.raises(ValueError, match='0412-2023'):
        register_with([{'key': '0412-2023', 'from': '2027-1-1'}])


def test_dated_and_undated_mix_loads_with_conflict():
    register = register_with(['0412-2023'])  # 馆藏辑刊无期限，海岬文献有期限
    assert any(item['key'] == '0412-2023' for item in register['conflicts'])
    report = steps(csv_bytes(copy('D1', '2026-06-01'), copy('D2', '2028-06-01')), register=register)
    rows = records(report)
    assert rows['D1']['reasons'][0]['code'] == 'ISSN_OVERLAP'   # 海岬文献窗口内两说
    assert rows['D2']['journal']['issn'] == '1980-3412'         # 窗口外归无期限登记


def test_signed_certificate_keeps_recognition_basis(client):
    run = client.post('/api/volumes', json={'sample': 'dirty'}).json['run_id']
    client.post(f'/api/volumes/{run}/stamp', json={})
    document = client.get(f'/api/volumes/{run}/export').json['document']
    c01 = next(row for row in document['resolutions'] if row['entry'] == 'C01')
    assert c01['basis'] == {'key': '0412-2023', 'journal': '2049-3630', 'via': 'legacy',
                            'window': {'from': '2001-01-01', 'until': '2027-01-01'}}


def test_catalog_update_recomputes_unsigned_and_keeps_signed(client, tmp_path, monkeypatch):
    first = client.post('/api/volumes', json={'sample': 'dirty'}).json
    signed = client.post(f"/api/volumes/{first['run_id']}/stamp", json={}).json
    # 目录补录：馆藏辑刊的旧刊号登记提前，与海岬文献的登记交叠
    catalog = tmp_path / 'catalog'
    catalog.mkdir()
    authority = json.loads(json.dumps(load_register()['authority']))
    authority['journals'][1]['previous'] = [{'key': '0412-2023', 'from': '2026-11-01'}]
    (catalog / 'authority.json').write_text(json.dumps(authority), encoding='utf-8')
    monkeypatch.setattr('app.registry.catalog.CATALOG', catalog)
    # 同一卷宗按新目录重算，未签申请的许可页随之变化
    second = client.post('/api/volumes', json={'csv': bundle('dirty').decode()}).json
    assert second['run_id'] != first['run_id']
    assert (second['totals']['licensed'], second['totals']['pending'], second['totals']['restored']) == (26, 16, 0)
    # 已签凭证仍可查当时的认刊依据
    kept = client.get(f"/api/volumes/{first['run_id']}/export").json
    assert kept['verified'] and kept['imprint'] == signed['imprint']
    c01 = next(row for row in kept['document']['resolutions'] if row['entry'] == 'C01')
    assert c01['journal']['issn'] == '2049-3630' and c01['basis']['via'] == 'legacy'
    # 重跑同一次复核不重复签发
    again = client.post(f"/api/volumes/{first['run_id']}/stamp", json={}).json
    assert again == {'run_id': first['run_id'], 'imprint': signed['imprint'], 'reused': True}
    # 新复核里 C01 待证，认刊依据记录交叠候选
    renewed = client.post(f"/api/volumes/{second['run_id']}/stamp", json={}).json
    assert renewed['imprint'] != signed['imprint'] and not renewed['reused']
    document = client.get(f"/api/volumes/{second['run_id']}/export").json['document']
    c01_new = next(row for row in document['resolutions'] if row['entry'] == 'C01')
    assert c01_new['ruling'] == 'ISSN_OVERLAP'
    assert c01_new['basis']['candidates'] == ['1980-3412', '2049-3630']
    assert next(row for row in document['requests'] if row['entry'] == 'C01')['pending'] == 8


def test_stamp_page_lists_pending_entries(client):
    run = client.post('/api/volumes', json={'sample': 'dirty'}).json['run_id']
    page = client.get(f'/folio/stamp?run={run}').get_data(as_text=True)
    assert '本卷待证申请' in page and 'C04' in page and '待证 8 页' in page


def test_registry_page_shows_recognition_basis(client):
    page = client.get('/folio/registry').get_data(as_text=True)
    assert '认刊依据' in page and '沿革 2001-01-01–2027-01-01' in page
