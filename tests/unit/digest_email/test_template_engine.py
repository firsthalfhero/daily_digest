import os
import pytest
from src.digest_email.template_engine import EmailTemplateEngine

@pytest.fixture
def engine():
    template_dir = os.path.join(os.path.dirname(__file__), '../../../src/digest_email/templates')
    return EmailTemplateEngine(template_dir=template_dir)

def test_render_html_digest(engine):
    context = {
        'greeting_time': 'morning',
        'user_name': 'Alice',
        'calendar_events': [
            {'time': '09:00', 'title': 'Standup', 'location': 'Zoom'},
            {'time': '11:00', 'title': '1:1', 'location': 'Cafe'}
        ],
        'weather': {'summary': 'Sunny', 'high': 22, 'low': 14},
        'daily_summary': 'All is well.',
        'unsubscribe_url': 'http://unsubscribe',
        'preferences_url': 'http://prefs'
    }
    html = engine.render('daily_digest', context)
    assert 'Good morning, Alice!' in html
    assert 'Standup' in html and '1:1' in html
    assert 'Sunny' in html
    assert 'All is well.' in html
    assert 'Unsubscribe' in html
    assert 'Cheerio!' in html

def test_render_plain_digest(engine):
    context = {
        'greeting_time': 'afternoon',
        'user_name': 'Bob',
        'calendar_events': [],
        'weather': None,
        'daily_summary': 'Nothing much.',
        'unsubscribe_url': 'http://unsubscribe',
        'preferences_url': 'http://prefs'
    }
    txt = engine.render('daily_digest', context, plain=True)
    assert 'Good afternoon, Bob!' in txt
    assert 'No events today' in txt
    assert 'Weather' in txt
    assert 'Nothing much.' in txt
    assert 'Unsubscribe' in txt
    assert 'Cheerio!' in txt

def test_render_missing_template_raises(engine):
    with pytest.raises(ValueError):
        engine.render('not_a_real_template', {}, plain=False)

def test_partial_greeting_formal(engine):
    context = {'greeting_time': 'evening', 'user_name': 'Charlie', 'personality': 'formal'}
    html = engine.env.get_template('partials/greeting.html').render(**context)
    assert 'I trust you are well' in html
    txt = engine.env.get_template('partials/greeting.txt').render(**context)
    assert 'I trust you are well' in txt

def test_partial_greeting_informal(engine):
    context = {'greeting_time': 'evening', 'user_name': 'Charlie', 'personality': 'informal'}
    html = engine.env.get_template('partials/greeting.html').render(**context)
    assert "Alright, Charlie?" in html
    txt = engine.env.get_template('partials/greeting.txt').render(**context)
    assert "Alright, Charlie?" in txt 