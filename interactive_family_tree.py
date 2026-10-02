import copy

from family_tree import (
    add_parsed_relationship,
    generation_levels,
    load_tree,
    parse_relationships,
    save_tree,
)


def show_tree(tree):
    try:
        levels = generation_levels(tree)
    except ValueError as error:
        print(f"Cannot display this tree: {error}")
        return

    by_generation = {}
    for name, level in levels.items():
        by_generation.setdefault(level, []).append(name)

    for level in sorted(by_generation):
        print(f"\nGeneration {level + 1}")
        for name in sorted(by_generation[level], key=str.casefold):
            relations = tree.get(name, {})
            parents = [
                f"{role}: {relations[role]}"
                for role in ("mother", "father")
                if relations.get(role)
            ]
            if relations.get("siblings"):
                parents.append("siblings: " + ", ".join(relations["siblings"]))
            print(f"  - {name}" + (f" ({'; '.join(parents)})" if parents else ""))


def main():
    try:
        family = load_tree()
    except (OSError, ValueError) as error:
        print(f"Could not load the saved family tree: {error}")
        return 1

    print("Family Tree Builder")
    print("Enter a parent or sibling relationship, 'show tree', 'save', or 'exit'.")
    print(f"Loaded {len(family)} family members.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            return 0

        command = user_input.casefold()
        if command in {"exit", "quit"}:
            return 0
        if command in {"show", "show tree"}:
            show_tree(family)
            continue
        if command == "save":
            try:
                save_tree(family)
                print("Family tree saved.")
            except OSError as error:
                print(f"Could not save the family tree: {error}")
            continue

        relationships = parse_relationships(user_input)
        if not relationships:
            print("No clear relationship found. Try naming a parent or sibling explicitly.")
            continue

        updated = copy.deepcopy(family)
        try:
            for relation in relationships:
                add_parsed_relationship(updated, relation)
            save_tree(updated)
            family = updated
            print("Relationship added and saved.")
        except (OSError, ValueError) as error:
            print(f"Could not add that relationship: {error}")


if __name__ == "__main__":
    raise SystemExit(main())
