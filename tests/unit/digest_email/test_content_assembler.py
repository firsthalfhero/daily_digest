import pytest
from src.digest_email.content_assembler import ContentAssembler

def test_assemble_minimal():
    assembler = ContentAssembler(personality='formal')
    user = {'name': 'Alice', 'unsubscribe_url': 'u', 'preferences_url': 'p'}
    calendar = [{'time': '09:00', 'title': 'Standup', 'location': 'Zoom'}]
    weather = {'summary': 'Sunny', 'high': 20, 'low': 10}
    summary = 'All is well.'
    context = assembler.assemble(user, calendar, weather, summary)
    assert context['user_name'] == 'Alice'
    assert context['calendar_events'][0]['title'] == 'Standup'
    assert context['weather']['summary'] == 'Sunny'
    assert context['daily_summary'] == 'All is well.'
    assert context['personality'] == 'formal'
    assert context['unsubscribe_url'] == 'u'
    assert context['preferences_url'] == 'p'

def test_assemble_handles_missing_weather():
    assembler = ContentAssembler()
    user = {'name': 'Bob'}
    calendar = []
    summary = 'Nothing much.'
    context = assembler.assemble(user, calendar, None, summary)
    assert context['weather'] is None
    assert context['calendar_events'] == []
    assert context['daily_summary'] == 'Nothing much.'

def test_weather_unit_conversion():
    assembler = ContentAssembler(preferences={'weather_units': 'fahrenheit'})
    user = {'name': 'Cathy'}
    calendar = []
    weather = {'summary': 'Cloudy', 'high': 20, 'low': 10}
    summary = 'Cloudy day.'
    context = assembler.assemble(user, calendar, weather, summary)
    assert context['weather']['high'] == 68
    assert context['weather']['low'] == 50

def test_validation_missing_required():
    assembler = ContentAssembler()
    user = {}
    calendar = None
    weather = None
    summary = ''
    with pytest.raises(ValueError):
        assembler.assemble(user, calendar, weather, summary)

def test_personality_variable():
    assembler = ContentAssembler(personality='casual')
    user = {'name': 'Dave'}
    calendar = []
    weather = None
    summary = 'Chill.'
    context = assembler.assemble(user, calendar, weather, summary)
    assert context['personality'] == 'casual' 