import json

from package_comparison_tool.api import fetch_branch_binary_packages


def main() -> None:
    branch = input("Введите название ветки: ")
    packages = fetch_branch_binary_packages(branch)
    print(json.dumps({"packages": [p.to_dict(branch=branch) for p in packages]}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

