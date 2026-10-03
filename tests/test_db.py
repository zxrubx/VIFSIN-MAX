from bot import db


def test_create_and_get():
    rid = db.create_report(42, db.CATEGORIES[0], 'текст', '@user')
    assert len(rid) == 8
    r = db.get_report(rid.lower())  # регистр не важен
    assert r['user_id'] == 42 and r['status'] == 'pending' and r['reviewed_at'] is None


def test_anonymous_has_no_user():
    rid = db.create_report(None, db.CATEGORIES[1], 'x', None)
    r = db.get_report(rid)
    assert r['user_id'] is None and r['contact_info'] is None


def test_update_status_and_counts():
    a = db.create_report(1, 'c', 'a', None)
    db.create_report(2, 'c', 'b', None)
    assert db.update_status(a, 'resolved')
    assert db.get_report(a)['reviewed_at']
    assert not db.update_status(a, 'bogus')
    assert not db.update_status('NOPE0000', 'resolved')
    assert db.count_by_status() == {'pending': 1, 'approved': 0, 'rejected': 0, 'resolved': 1}
    assert [r['id'] for r in db.list_reports('resolved')] == [a]
