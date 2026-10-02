import json
from unittest.mock import Mock, patch

import pytest

from family_tree import (
    add_parsed_relationship,
    add_relationship,
    add_sibling_relationship,
    delete_person,
    family_layout,
    generation_levels,
    load_tree,
    parse_relationships,
    parse_with_ollama,
    save_tree,
)


@pytest.mark.parametrize(
    ("sentence", "expected"),
    [
        ("Abhay's father is Raj", [{"child": "Abhay", "father": "Raj"}]),
        ("Abhay's mom is Neha.", [{"child": "Abhay", "mother": "Neha"}]),
        ("Raj is the father of Abhay", [{"child": "Abhay", "father": "Raj"}]),
        ("Raj is Abhay's dad", [{"child": "Abhay", "father": "Raj"}]),
        (
            "Raj is Abhay's father. Neha is Abhay's mother.",
            [{"child": "Abhay", "father": "Raj"}, {"child": "Abhay", "mother": "Neha"}],
        ),
        ("Mira is Abhay's sister", [{"person": "Abhay", "sibling": "Mira"}]),
        ("Abhay's brother is Dev", [{"person": "Abhay", "sibling": "Dev"}]),
        ("Dev is the brother of Abhay", [{"person": "Abhay", "sibling": "Dev"}]),
        ("Mira is a sister to Abhay", [{"person": "Abhay", "sibling": "Mira"}]),
        ("Abhay has a sister named Mira.", [{"person": "Abhay", "sibling": "Mira"}]),
        ("Abhay and Mira are siblings", [{"person": "Abhay", "sibling": "Mira"}]),
        ("Abhay and Mira share the same parents", [{"person": "Abhay", "sibling": "Mira"}]),
        (
            "Abhay's siblings are Mira and Dev",
            [{"person": "Abhay", "sibling": "Mira"}, {"person": "Abhay", "sibling": "Dev"}],
        ),
        ("Tell me a story about a family", []),
    ],
)
def test_parse_relationships(sentence, expected):
    assert parse_relationships(sentence) == expected


def test_add_relationship_preserves_existing_parent_and_rejects_conflicts():
    tree = {}
    add_relationship(tree, "Abhay", father="Raj")
    add_relationship(tree, "Abhay", mother="Neha")
    assert tree["Abhay"] == {"father": "Raj", "mother": "Neha", "siblings": []}
    with pytest.raises(ValueError, match="already has a recorded father"):
        add_relationship(tree, "Abhay", father="Dev")


def test_add_relationship_rejects_cycles():
    tree = {}
    add_relationship(tree, "Abhay", father="Raj")
    with pytest.raises(ValueError, match="cycle"):
        add_relationship(tree, "Raj", father="Abhay")


def test_sibling_relationships_are_symmetric_and_idempotent():
    tree = {}
    add_sibling_relationship(tree, "Abhay", "Mira")
    add_sibling_relationship(tree, "Mira", "Abhay")
    assert tree["Abhay"]["siblings"] == ["Mira"]
    assert tree["Mira"]["siblings"] == ["Abhay"]


def test_legacy_sibling_data_is_normalized_to_a_symmetric_link(tmp_path):
    path = tmp_path / "family_tree.json"
    path.write_text(
        json.dumps(
            {
                "Abhay": {"father": "", "mother": "", "siblings": ["Mira", "Mira"]},
                "Mira": {"father": "", "mother": "", "siblings": ["Abhay", "Abhay"]},
            }
        ),
        encoding="utf-8",
    )
    tree = load_tree(path)
    assert tree["Abhay"]["siblings"] == ["Mira"]
    assert tree["Mira"]["siblings"] == ["Abhay"]


def test_parent_and_child_cannot_be_added_as_siblings():
    tree = {}
    add_relationship(tree, "Abhay", father="Raj")
    with pytest.raises(ValueError, match="parent and child"):
        add_sibling_relationship(tree, "Abhay", "Raj")


def test_parsed_sibling_relationship_updates_shared_tree():
    tree = {}
    add_parsed_relationship(tree, {"person": "Abhay", "sibling": "Mira"})
    assert tree["Abhay"]["siblings"] == ["Mira"]
    assert tree["Mira"]["siblings"] == ["Abhay"]


def test_ollama_response_can_include_siblings():
    response = Mock()
    response.json.return_value = {
        "response": json.dumps({
            "relationships": [{"child": "Abhay", "father": "Raj", "siblings": ["Mira"]}]
        })
    }
    with patch("family_tree.requests.post", return_value=response):
        assert parse_with_ollama("Abhay's father is Raj and Mira is his sister") == [
            {"child": "Abhay", "father": "Raj"},
            {"person": "Abhay", "sibling": "Mira"},
        ]


def test_generation_levels_follow_parent_branches():
    tree = {}
    add_relationship(tree, "Abhay", father="Raj", mother="Neha")
    add_relationship(tree, "Mira", father="Abhay")
    assert generation_levels(tree) == {"Raj": 0, "Neha": 0, "Abhay": 1, "Mira": 2}


def test_siblings_share_a_generation_and_layout_group():
    tree = {}
    add_relationship(tree, "Abhay", father="Raj")
    add_sibling_relationship(tree, "Abhay", "Mira")
    levels, positions = family_layout(tree)
    assert levels["Abhay"] == levels["Mira"] == 1
    assert positions["Abhay"][1] == positions["Mira"][1]
    assert abs(positions["Abhay"][0] - positions["Mira"][0]) == 2.5


def test_generation_levels_reject_cycles_in_saved_data():
    tree = {
        "Abhay": {"father": "Raj", "mother": ""},
        "Raj": {"father": "Abhay", "mother": ""},
    }
    with pytest.raises(ValueError, match="cycle"):
        generation_levels(tree)


def test_family_layout_keeps_descendant_branches_grouped():
    tree = {}
    add_relationship(tree, "Ava", father="Mark")
    add_relationship(tree, "Nia", father="Zed")
    add_relationship(tree, "Liam", father="Ava")
    add_relationship(tree, "Owen", father="Nia")
    levels, positions = family_layout(tree)
    assert levels["Liam"] == levels["Owen"] == 2
    assert positions["Ava"][0] < positions["Nia"][0]
    assert positions["Liam"][0] < positions["Owen"][0]


def test_delete_person_clears_sibling_references():
    tree = {}
    add_sibling_relationship(tree, "Abhay", "Mira")
    delete_person(tree, "Mira")
    assert tree["Abhay"]["siblings"] == []


def test_save_and_load_use_legacy_json_shape(tmp_path):
    path = tmp_path / "family_tree.json"
    save_tree({"Abhay": {"father": "Raj", "mother": ""}}, path)
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "Abhay": {"father": "Raj", "mother": ""}
    }
    assert load_tree(path) == {
        "Abhay": {"father": "Raj", "mother": "", "siblings": []},
        "Raj": {"father": "", "mother": "", "siblings": []},
    }