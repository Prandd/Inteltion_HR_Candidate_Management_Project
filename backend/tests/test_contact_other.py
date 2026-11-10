import sqlalchemy as sa


def test_other_contact_persists_and_is_audited(client, auth, new_candidate):
    candidate = new_candidate()
    cid = candidate['candidate_id']
    endpoint = f'/api/candidates/{cid}'
    other = 'LINE: candidate.line\nLinkedIn: https://www.linkedin.com/in/candidate'
    response = client.put(endpoint, headers=auth, json={'contact_other': other})
    assert response.status_code == 200, response.text
    after = client.get(endpoint, headers=auth).json()['data']
    assert after['contact_other'] == other
    assert after['email'] == candidate['email']
    assert after['phone'] == candidate['phone']
    assert after['education'] == candidate['education']
    changes = client.get(endpoint + '/changes', headers=auth).json()['data']
    assert any(change['field'] == 'contact_other' and change['new_value'] == other for change in changes)
    assert client.put(endpoint, headers=auth, json={'contact_other': ''}).status_code == 200
    assert client.get(endpoint, headers=auth).json()['data']['contact_other'] == ''


def test_cv_replacement_keeps_manually_entered_other_contact(client, auth, fixed_extraction):
    from conftest import upload
    fixed_extraction('other-contact-before', email='other-contact-test@example.com')
    fixed_extraction('other-contact-after', email='other-contact-test@example.com')
    first = upload(client, auth, ('before.pdf', 'other-contact-before')).json()['data']['created'][0]
    cid = first['candidate_id']
    client.put(f'/api/candidates/{cid}', headers=auth, json={'contact_other': 'LINE: keep-this'})
    review = upload(client, auth, ('after.pdf', 'other-contact-after')).json()['data']['needs_review'][0]
    response = client.post(f"/api/pending-uploads/{review['pending_upload_id']}/update", headers=auth)
    assert response.status_code == 200, response.text
    assert response.json()['data']['candidate']['contact_other'] == 'LINE: keep-this'


def test_other_contact_upgrade_backfills_existing_rows_and_is_repeatable(monkeypatch):
    from app import main
    engine = sa.create_engine('sqlite:///:memory:')
    try:
        with engine.begin() as connection:
            connection.execute(sa.text('CREATE TABLE candidates (candidate_id VARCHAR(7) PRIMARY KEY)'))
            connection.execute(sa.text("INSERT INTO candidates (candidate_id) VALUES ('0000001')"))
        monkeypatch.setattr(main, 'engine', engine)
        main._ensure_contact_other_column()
        main._ensure_contact_other_column()
        with engine.connect() as connection:
            assert connection.execute(sa.text('SELECT contact_other FROM candidates')).scalar_one() == ''
    finally:
        engine.dispose()
