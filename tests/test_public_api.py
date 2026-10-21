from oceangraph import OceanGraph, OceanGraphConfig, OceanGraphResults, __version__


def test_public_api_uses_oceangraph_names():
    assert OceanGraph.__module__ == "oceangraph.api"
    assert OceanGraphConfig.__module__ == "oceangraph.api"
    assert OceanGraphResults.__module__ == "oceangraph.api"
    assert __version__ == "4.0.0"


def test_default_config_is_text_pipeline_ready():
    config = OceanGraphConfig()

    assert config.input_dir
    assert config.output_dir
    assert config.backend
