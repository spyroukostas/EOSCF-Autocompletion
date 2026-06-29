import pytest
import requests

BASE_URL = "http://0.0.0.0:4559/v1"


@pytest.mark.api
@pytest.mark.catalogue
def test_autocompletion_health():
    # r = requests.get(url=f"{BASE_URL}/health")
    # assert r.status_code == 200
    assert True


@pytest.mark.api
@pytest.mark.catalogue
def test_autocompletion_update():
    r = requests.get(url=f"{BASE_URL}/update")
    assert r.status_code == 200


@pytest.mark.api
@pytest.mark.catalogue
@pytest.mark.usefixtures("onboarded_service")
def test_autocompletion_suggest_status(onboarded_service):
    r = requests.post(url=f"{BASE_URL}/auto_completion/suggest",
                      json=onboarded_service['request'])

    assert r.status_code == 200


@pytest.mark.api
@pytest.mark.catalogue
@pytest.mark.usefixtures("onboarded_service")
def test_autocompletion_suggest_field_names(onboarded_service):
    r = requests.post(url=f"{BASE_URL}/auto_completion/suggest",
                      json=onboarded_service['request'])

    assert r.json()[0]['field_name'] in ['categories', 'scientific_domains']
    assert r.json()[1]['field_name'] in ['categories', 'scientific_domains']


@pytest.mark.api
@pytest.mark.catalogue
@pytest.mark.usefixtures("onboarded_service")
def test_autocompletion_suggest_max_suggestions(onboarded_service):
    onboarded_service['request']['maximum_suggestions'] = 2
    r = requests.post(url=f"{BASE_URL}/auto_completion/suggest",
                      json=onboarded_service['request'])

    assert len(r.json()[0]['suggestions']) <= 2
    assert len(r.json()[1]['suggestions']) <= 2
    assert len(r.json()[2]['suggestions']) <= 2


@pytest.mark.api
@pytest.mark.catalogue
@pytest.mark.usefixtures("onboarded_service")
@pytest.mark.xfail(reason='Fixture is not kept updated')
def test_autocompletion_suggest_categories(onboarded_service):
    r = requests.post(url=f"{BASE_URL}/auto_completion/suggest",
                      json=onboarded_service['request'])

    assert set(r.json()[0]['suggestions']) == set(onboarded_service['expected_response'][0]['suggestions'])


@pytest.mark.api
@pytest.mark.catalogue
@pytest.mark.usefixtures("onboarded_service")
@pytest.mark.xfail(reason='Fixture is not kept updated')
def test_autocompletion_suggest_scientific_domain(onboarded_service):
    r = requests.post(url=f"{BASE_URL}/auto_completion/suggest",
                      json=onboarded_service['request'])

    assert r.json()[2]['suggestions'] == onboarded_service['expected_response'][2]['suggestions']
