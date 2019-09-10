import pytest
from src.kitools.ki_project_init_params import KiProjectInitParams
from src.kitools.data_type_template import DataTypeTemplate, DataTypeTemplatePath
from src.kitools.data_uri import DataUri


def test_it_sets_the_params(syn_test_helper):
    no_prompt = True
    title = syn_test_helper.uniq_name()
    description = syn_test_helper.uniq_name()
    project_name = syn_test_helper.uniq_name()
    data_type_template = DataTypeTemplate(name=syn_test_helper.uniq_name(),
                                          description='Test',
                                          paths=[
                                              DataTypeTemplatePath('test', 'test')
                                          ],
                                          is_default=False)
    DataTypeTemplate.register(data_type_template)

    init_params = KiProjectInitParams(no_prompt=no_prompt,
                                      title=title,
                                      description=description,
                                      project_name=project_name,
                                      data_type_template=data_type_template)
    assert init_params.no_prompt == no_prompt
    assert init_params.title == title
    assert init_params.description == description
    assert init_params.project_uri is None
    assert init_params.project_name == project_name
    assert init_params.data_type_template == data_type_template


def test_it_sets_the_project_uri():
    data_uri = DataUri('syn', 'syn123')
    init_params = KiProjectInitParams(project_uri=data_uri.uri)
    assert init_params.project_uri == data_uri.uri
    assert init_params.project_name is None


def test_it_sets_the_project_name(syn_test_helper):
    test_name = syn_test_helper.uniq_name()
    init_params = KiProjectInitParams(project_name=test_name)
    assert init_params.project_uri is None
    assert init_params.project_name == test_name


def test_it_raises_when_the_project_uri_and_project_name_are_set():
    with pytest.raises(ValueError) as ex:
        KiProjectInitParams(project_uri='syn:syn123', project_name='new name')
    assert str(ex.value) == 'project_uri and project_name cannot both be set.'


def test_it_raises_when_the_project_uri_is_invalid():
    with pytest.raises(ValueError) as ex:
        KiProjectInitParams(project_uri='unknown:syn123')
    assert 'Invalid project_uri:' in str(ex.value)
