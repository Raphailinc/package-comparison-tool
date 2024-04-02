import json
from api import get_branch_binary_packages

def compare_packages(branch1, branch2):
    """
    Сравнивает пакеты между двумя ветками.

    Args:
        branch1 (str): Название первой ветки.
        branch2 (str): Название второй ветки.

    Returns:
        dict: Словарь с результатами сравнения.
    """
    packages_branch1 = get_branch_binary_packages(branch1)
    packages_branch2 = get_branch_binary_packages(branch2)

    if not packages_branch1 or not packages_branch2:
        return None

    packages1 = {pkg["name"]: pkg for pkg in packages_branch1["packages"]}
    packages2 = {pkg["name"]: pkg for pkg in packages_branch2["packages"]}

    comparison_result = {
        "packages_only_in_branch1": [pkg for pkg in packages1 if pkg not in packages2],
        "packages_only_in_branch2": [pkg for pkg in packages2 if pkg not in packages1],
        "packages_with_higher_version_in_branch1": [
            pkg for pkg in packages1
            if pkg in packages2 and packages1[pkg]["version"] > packages2[pkg]["version"]
        ]
    }

    return comparison_result

def compare_version_release(version_release1, version_release2):
    version1, release1 = version_release1.split('-')
    version2, release2 = version_release2.split('-')

    version_parts1 = version1.split('.')
    version_parts2 = version2.split('.')

    for part1, part2 in zip(version_parts1, version_parts2):
        if part1.isdigit() and part2.isdigit():
            if int(part1) > int(part2):
                return 1
            elif int(part1) < int(part2):
                return -1
        elif part1.isdigit():
            return 1
        elif part2.isdigit():
            return -1
        else:
            if part1 > part2:
                return 1
            elif part1 < part2:
                return -1

    if len(version_parts1) > len(version_parts2):
        return 1
    elif len(version_parts1) < len(version_parts2):
        return -1

    if release1.isdigit() and release2.isdigit():
        return int(release1) - int(release2)
    elif release1.isdigit():
        return 1
    elif release2.isdigit():
        return -1
    else:
        if release1 > release2:
            return 1
        elif release1 < release2:
            return -1
        else:
            return 0

def main():
    """
    Основная функция утилиты.
    """
    branch1 = "sisyphus"
    branch2 = "p10"
    comparison_result = compare_packages(branch1, branch2)

    if comparison_result:
        print("Comparison Result:")
        print(json.dumps(comparison_result, indent=4))

if __name__ == "__main__":
    main()