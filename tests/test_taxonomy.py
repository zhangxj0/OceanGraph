import pytest

from oceangraph.pipeline.taxonomy import (
    normalize_answer_type,
    normalize_ocean_subdomain,
    taxonomy_answer_types,
    taxonomy_domain_ids,
)


def test_taxonomy_exposes_exactly_five_stable_domain_ids():
    assert taxonomy_domain_ids() == [
        "physical_ocean_climate",
        "carbon_biogeochemistry",
        "remote_sensing_observing",
        "marine_ecology_fisheries",
        "coastal_hazards_human",
    ]


def test_taxonomy_uses_short_em_answer_types():
    assert taxonomy_answer_types() == [
        "entity",
        "numeric",
        "date",
        "yes_no",
        "short_text",
    ]
    assert normalize_answer_type("description") == "short_text"
    assert normalize_answer_type("boolean") == "yes_no"
    assert normalize_answer_type("list") == ""


def test_legacy_subdomain_is_normalized_to_five_domain_taxonomy():
    assert normalize_ocean_subdomain("marine_chemistry") == "carbon_biogeochemistry"
    assert normalize_ocean_subdomain(
        "",
        text="Which process transports carbon to depth? The biological pump.",
    ) == "carbon_biogeochemistry"


@pytest.mark.parametrize(
    ("domain_hint", "expected"),
    [
        ("Physical Oceanography and Climate-Ocean Dynamics", "physical_ocean_climate"),
        ("Ocean Carbon Cycle and Marine Biogeochemistry", "carbon_biogeochemistry"),
        ("Ocean Remote Sensing and Observing Systems", "remote_sensing_observing"),
        (
            "Marine Ecology, Ecosystem Response, and Fisheries Oceanography",
            "marine_ecology_fisheries",
        ),
        ("Coastal Ocean Hazards, Pollution, and Human Impacts", "coastal_hazards_human"),
    ],
)
def test_domain_runner_hints_map_to_canonical_taxonomy(domain_hint, expected):
    assert normalize_ocean_subdomain("", domain_hint=domain_hint) == expected
