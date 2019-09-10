import pytest
from src.kitools import DataTypeTemplate


def test_it_gets_all_templates():
    all = DataTypeTemplate.all()
    assert len(all) == 2
    for template in all:
        assert template.name in ['rally', 'generic']


def test_it_gets_the_default_template():
    expected_template = next(t for t in DataTypeTemplate.all() if t.is_default)
    template = DataTypeTemplate.default()
    assert template == expected_template


def test_it_gets_a_template_by_name():
    name = DataTypeTemplate.all()[-1].name
    template = DataTypeTemplate.get(name)
    assert template.name == name


def test_it_registers_a_template():
    template = DataTypeTemplate('test', 'test', [])
    DataTypeTemplate.register(template)
    assert template in DataTypeTemplate._templates
