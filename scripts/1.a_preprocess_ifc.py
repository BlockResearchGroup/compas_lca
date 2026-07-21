from compas_lca.project import Project


def main():
    # 1. Create project from config.yaml
    project = Project.from_config_yaml()

    # 2. Run IFC preprocessing with default parameters
    project.preprocess_ifc()

if __name__ == "__main__":
    main()
