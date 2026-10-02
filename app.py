import copy

import plotly.graph_objects as go
import streamlit as st

from family_tree import (
    add_parsed_relationship,
    add_relationship,
    add_sibling_relationship,
    delete_person,
    family_layout,
    generation_levels,
    load_tree,
    parse_relationships,
    save_tree,
)

ADD_NEW_MEMBER = "__add_new_member__"


st.set_page_config(page_title="Family Tree", page_icon="🌳", layout="wide")

st.markdown(
    """
    <style>
    :root { color-scheme: light; }
    .stApp { background: linear-gradient(145deg, #f4f5eb 0%, #e5eee3 48%, #f7f2e8 100%); }
    [data-testid="stSidebar"] { background: #e8eee4; border-right: 1px solid #d3dfd1; }
    h1, h2, h3 { color: #213c31; }
    [data-testid="stMetric"] { background: rgba(255,255,255,.68); border: 1px solid #dce5d9; padding: 12px 16px; border-radius: 8px; }
    div.stButton > button[kind="primary"] { background: #315b45; border-color: #315b45; }
    </style>
    """,
    unsafe_allow_html=True,
)


def member_picker(label, key, members, excluded_name=""):
    available_members = [
        member for member in members if member.casefold() != excluded_name.casefold()
    ]
    selection = st.selectbox(
        label,
        [None, ADD_NEW_MEMBER, *available_members],
        format_func=lambda value: {
            None: "Choose a member",
            ADD_NEW_MEMBER: "Add a new member...",
        }.get(value, value),
        key=f"{key}_selection",
    )
    if selection == ADD_NEW_MEMBER:
        return st.text_input(f"New {label.lower()} name", key=f"{key}_new").strip()
    return selection or ""


@st.cache_data(show_spinner=False)
def tree_figure(tree):
    levels, positions = family_layout(tree)

    edge_x = {"father": [], "mother": [], "siblings": []}
    edge_y = {"father": [], "mother": [], "siblings": []}
    for child, relations in tree.items():
        for role in ("father", "mother"):
            parent = relations.get(role)
            if parent and parent in positions and child in positions:
                parent_x, parent_y = positions[parent]
                child_x, child_y = positions[child]
                horizontal_curve = (child_x - parent_x) * 0.16
                edge_x[role].extend(
                    [parent_x, parent_x + horizontal_curve, child_x - horizontal_curve, child_x, None]
                )
                edge_y[role].extend(
                    [parent_y, parent_y - 0.8, child_y + 0.8, child_y, None]
                )
        for sibling in relations.get("siblings", []):
            if child.casefold() < sibling.casefold() and sibling in positions:
                first_x, first_y = positions[child]
                second_x, second_y = positions[sibling]
                left_x, right_x = sorted((first_x, second_x))
                branch_y = (first_y + second_y) / 2 + 0.42
                edge_x["siblings"].extend([left_x, left_x, right_x, right_x, None])
                edge_y["siblings"].extend(
                    [branch_y - 0.18, branch_y, branch_y, branch_y - 0.18, None]
                )

    figure = go.Figure()
    for role, color in (("father", "#806149"), ("mother", "#799274")):
        figure.add_trace(
            go.Scatter(
                x=edge_x[role],
                y=edge_y[role],
                mode="lines",
                line={"color": color, "width": 3, "shape": "spline"},
                hoverinfo="skip",
                name=f"{role.title()} branch",
            )
        )
    figure.add_trace(
        go.Scatter(
            x=edge_x["siblings"],
            y=edge_y["siblings"],
            mode="lines",
            line={"color": "#bf8050", "width": 2, "dash": "dot"},
            hoverinfo="skip",
            name="Sibling link",
        )
    )

    names = list(positions)
    hover_text = []
    for name in names:
        relations = tree.get(name, {})
        parents = [relations.get(role) for role in ("mother", "father") if relations.get(role)]
        siblings = relations.get("siblings", [])
        hover_text.append(
            "Parents: "
            + (", ".join(parents) if parents else "Not recorded")
            + "<br>Siblings: "
            + (", ".join(siblings) if siblings else "Not recorded")
        )

    figure.add_trace(
        go.Scatter(
            x=[positions[name][0] for name in names],
            y=[positions[name][1] for name in names],
            mode="markers+text",
            text=names,
            textposition="bottom center",
            textfont={"color": "#25392e", "size": 13},
            hovertext=hover_text,
            hovertemplate="<b>%{text}</b><br>%{hovertext}<extra></extra>",
            marker={
                "size": 30,
                "color": ["#416b50" if levels[name] == 0 else "#6f8e61" for name in names],
                "line": {"color": "#f8faf3", "width": 2},
                "symbol": "circle",
            },
            name="Family members",
        )
    )

    max_level = max(levels.values(), default=0)
    figure.update_layout(
        height=max(450, 150 + 150 * (max_level + 1)),
        margin={"l": 30, "r": 30, "t": 55, "b": 50},
        paper_bgcolor="rgba(255,255,255,.7)",
        plot_bgcolor="#f1f4e9",
        font={"family": "Georgia, serif", "color": "#26392e"},
        legend={"orientation": "h", "y": 1.08, "x": 0},
        xaxis={"visible": False, "zeroline": False},
        yaxis={
            "tickmode": "array",
            "tickvals": [-level * 2.3 for level in range(max_level + 1)],
            "ticktext": [f"Generation {level + 1}" for level in range(max_level + 1)],
            "showgrid": False,
            "zeroline": False,
            "range": [-max_level * 2.3 - 1.2, 1.2],
        },
        hoverlabel={"bgcolor": "#fffdf6", "font": {"color": "#26392e"}},
    )
    return figure


try:
    family = load_tree()
except (OSError, ValueError) as error:
    st.error(f"The saved family tree could not be loaded: {error}")
    st.stop()

st.title("🌳 Family Tree")
st.caption("Build a clear, growing picture of your family, one relationship at a time.")

with st.sidebar:
    st.header("Add a relationship")
    member_names = sorted(family, key=str.casefold)
    first_member = member_picker("Person", "first_member", member_names)
    relationship_type = st.selectbox(
        "Relationship",
        ("Father", "Mother", "Brother", "Sister"),
        key="relationship_type",
    )
    second_member = member_picker(
        "Related person", "second_member", member_names, excluded_name=first_member
    )

    if first_member and second_member:
        if relationship_type in {"Brother", "Sister"}:
            st.caption(f"{first_member} and {second_member} will be added as siblings.")
        else:
            st.caption(f"{first_member} will be recorded as {second_member}'s {relationship_type.lower()}.")

    if st.button("Save relationship", type="primary", width="stretch"):
        if not first_member or not second_member:
            st.warning("Choose existing members or enter names for both people.")
        else:
            updated = copy.deepcopy(family)
            try:
                if relationship_type in {"Brother", "Sister"}:
                    add_sibling_relationship(updated, first_member, second_member)
                else:
                    add_relationship(
                        updated,
                        child=second_member,
                        father=first_member if relationship_type == "Father" else None,
                        mother=first_member if relationship_type == "Mother" else None,
                    )
                save_tree(updated)
                family = updated
                st.success("Relationship saved.")
            except ValueError as error:
                st.error(str(error))

    with st.expander("Describe a relationship in plain English"):
        with st.form("natural_language_relationship", clear_on_submit=True):
            description = st.text_area(
                "Relationship description",
                placeholder="For example: Abhay's dad is Raj, and Mira is his sister",
                help="Try “Raj is Abhay's father,” “Mira is Abhay's sister,” or “Abhay and Mira are siblings.”",
            )
            description_submitted = st.form_submit_button("Interpret description", width="stretch")

        if description_submitted:
            relationships = parse_relationships(description)
            if not description.strip():
                st.warning("Enter a relationship description first.")
            elif not relationships:
                st.info("No clear relationship found. Try selecting a relationship from the dropdowns.")
            else:
                updated = copy.deepcopy(family)
                try:
                    for relation in relationships:
                        add_parsed_relationship(updated, relation)
                    save_tree(updated)
                    family = updated
                    st.success(f"Added {len(relationships)} relationship{'s' if len(relationships) != 1 else ''}.")
                except ValueError as error:
                    st.error(str(error))

    st.divider()
    st.subheader("Manage members")
    if family:
        selected_person = st.selectbox("Remove a person", sorted(family, key=str.casefold))
        if st.button("Remove person", width="stretch"):
            updated = copy.deepcopy(family)
            delete_person(updated, selected_person)
            save_tree(updated)
            st.rerun()

    confirm_reset = st.checkbox("I understand this clears the whole tree")
    if st.button("Clear family tree", disabled=not confirm_reset, width="stretch"):
        save_tree({})
        st.rerun()

member_count = len(family)
relationship_count = sum(
    bool(relations.get(role)) for relations in family.values() for role in ("father", "mother")
)
sibling_pairs = {
    tuple(sorted((name.casefold(), sibling.casefold())))
    for name, relations in family.items()
    for sibling in relations.get("siblings", [])
}
sibling_count = len(sibling_pairs)
try:
    levels = generation_levels(family) if family else {}
    generations = len(set(levels.values()))
except ValueError as error:
    levels = {}
    generations = 0
    st.warning(f"The saved data contains a cycle and cannot be laid out: {error}")

metric_columns = st.columns(4)
metric_columns[0].metric("Members", member_count)
metric_columns[1].metric("Parent links", relationship_count)
metric_columns[2].metric("Sibling pairs", sibling_count)
metric_columns[3].metric("Generations", generations)

st.subheader("Your family")
if family:
    try:
        st.plotly_chart(tree_figure(family), width="stretch", config={"displaylogo": False})
    except ValueError as error:
        st.error(f"This tree cannot be drawn because its relationships contain a cycle: {error}")
    with st.expander("View recorded relationships"):
        rows = []
        for name, relations in sorted(family.items(), key=lambda item: item[0].casefold()):
            rows.append(
                {
                    "Person": name,
                    "Mother": relations.get("mother") or "Not recorded",
                    "Father": relations.get("father") or "Not recorded",
                    "Siblings": ", ".join(relations.get("siblings", [])) or "Not recorded",
                }
            )
        st.dataframe(rows, hide_index=True, width="stretch")
else:
    st.info("Your tree is ready to grow. Add a relationship from the sidebar to begin.")