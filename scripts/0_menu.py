from dataclasses import dataclass

from typing import Callable
from typing import Optional
from typing import List

from compas_lca.project import Project
from compas_lca.project import ProjectError
from compas_lca.project import MissingInput

# ----------------------------
# Menu model
# ----------------------------

Action = Callable[[Project], None]


@dataclass(frozen=True)
class MenuItem:
    key: str
    name: str
    action: Optional[Action] = None
    is_group: bool = False


def not_implemented(label: str) -> Action:
    def _action(_project: Project) -> None:
        print(f"Not implemented yet: {label}")
    return _action


def safe_run(action: Action, project: Project) -> None:
    """Run an action with basic error handling."""
    try:
        action(project)
        print("✅ Done.")
        print("")
    except MissingInput as e:
        print(f"❌ Missing input: {e}")
    except ProjectError as e:
        print(f"❌ Project error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")



# ----------------------------
# Step actions (call Project methods)
# ----------------------------

def step_01a_preprocess(project: Project) -> None:
    project.preprocess_ifc()

def step_01b_select_representatives(project: Project) -> None:
    project.select_representatives()

def step_01c_extract_building_data(project: Project) -> None:
    # Placeholder: implement later as project.extract_ifc()
    not_implemented("Step 01c: extract building data with AI")(project)

def step_01d_match_epds(project: Project) -> None:
    not_implemented("Step 01d: match building data with EPDs")(project)


def step_01e_create_report(project: Project) -> None:
    not_implemented("Step 01e: create LCA report")(project)


def step_02a_preprocess_env(project: Project) -> None:
    not_implemented("Step 02a: preprocess environmental data")(project)


def step_02b_normalize_env(project: Project) -> None:
    not_implemented("Step 02b: normalize environmental data with AI")(project)

def step_02c_edit_env(project: Project) -> None:
    not_implemented("Step 02c: edit environmental data within COMPAS LCA database")(project)

def preview_config(project: Project) -> None:
    print("\n--- Active config (loaded from config.yaml) ---")
    for k, v in project.config.items():
        print(f"{k}: {v}")
    print(f"\nProject folder: {project.path}")
    print("--------------------------------------------\n")


# ----------------------------
# Pipeline groups (run multiple steps)
# ----------------------------

def run_group(project: Project, actions: List[Action]) -> None:
    for action in actions:
        safe_run(action, project)
        input("Press Enter to continue...")


# ----------------------------
# Menu definition
# ----------------------------

MENU: List[MenuItem] = [
    MenuItem(key="p", name="Preview Configuration", action=preview_config),

    MenuItem(key="01", name="🏠 RUN LCA PROJECT 🏠", is_group=True),
    MenuItem(key="01a", name="Step 1: Preprocess building data", action=step_01a_preprocess),
    MenuItem(key="01b", name="Step 2: Representative building data selection", action=step_01b_select_representatives),
    MenuItem(key="01c", name="Step 3: Extract building data with AI", action=step_01c_extract_building_data),
    MenuItem(key="01d", name="Step 4: Match building data with EPDs", action=step_01d_match_epds),
    MenuItem(key="01e", name="Step 5: Create LCA report", action=step_01e_create_report),

    MenuItem(key="02", name="🌱 ADD ENVIRONMENTAL DATA 🌱", is_group=True),
    MenuItem(key="02a", name="Preprocess environmental data", action=step_02a_preprocess_env),
    MenuItem(key="02b", name="Normalize environmental data with AI", action=step_02b_normalize_env),
    MenuItem(key="02c", name="Edit environmental data within COMPAS LCA database", action=step_02c_edit_env),
]


GROUPS = {
    "01": ["01a", "01b", "01c", "01d", "01e"],
    "02": ["02a", "02b"],
}


# ----------------------------
# Menu loop
# ----------------------------

def pipeline_menu() -> None:
    # Instantiate exactly one project per menu session
    project = Project.from_config_yaml()

    # Fast lookup
    items_by_key = {item.key.lower(): item for item in MENU}

    while True:
        print("\n=================")
        print("♻️  COMPAS LCA ♻️")
        print("=================\n")
        print("Enter the character combination on the left of each action to run a (sub)module:\n")

        for item in MENU:
            print(f"  {item.key.upper()}. {item.name}")

            # Your old spacing rules; keep them if you like
            if item.key.lower() == "p":
                print("")
            if item.key.lower() == "01e":
                print("")

        print("  Q. Quit")

        choice = input("\nYour choice: ").strip().lower()

        if choice == "q":
            print("Exiting.")
            break

        if choice not in items_by_key:
            print("Unknown choice.")
            continue

        selected = items_by_key[choice]

        if selected.is_group:
            step_keys = GROUPS.get(selected.key.lower(), [])
            actions = []
            for k in step_keys:
                mi = items_by_key.get(k)
                if mi and mi.action:
                    actions.append(mi.action)
            if not actions:
                print(f"No steps configured for group '{selected.key}'.")
            else:
                run_group(project, actions)
        else:
            if not selected.action:
                print("No action attached to this menu item.")
            else:
                safe_run(selected.action, project)
                input("Press Enter to return to the menu...")


if __name__ == "__main__":
    pipeline_menu()
