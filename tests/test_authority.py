import pytest
from app.registry.catalog import load_register
from app.registry.rules import check_authority


def test_refuses_ambiguous_legacy_identifier():
    authority=load_register()['authority']
    authority['journals'][1]['previous']=['0412-2023']
    with pytest.raises(ValueError,match='0412-2023'):
        check_authority(authority)


def test_refuses_missing_quota_pool():
    authority=load_register()['authority']
    authority['terms'][0]['pool']='UNKNOWN'
    with pytest.raises(ValueError,match='OPEN-1'):
        check_authority(authority)
