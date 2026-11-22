def test_three_column_folio_has_evidence(client):
    data=client.get('/').get_data(as_text=True)
    assert '58 = 32 + 18 + 8' in data and '签发印版' in data
    page=client.get('/folio/pages').get_data(as_text=True)
    assert '复本页段凭据' in page and 'R01 · 6 页' in page
