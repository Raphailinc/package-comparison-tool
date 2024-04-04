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
        "packages_only_in_branch1": [
            {
                "name": pkg["name"],
                "epoch": pkg["epoch"],
                "version": pkg["version"],
                "release": pkg["release"],
                "arch": pkg["arch"],
                "buildtime": pkg["buildtime"],
                "disttag": pkg["disttag"],
                "url": f"https://packages.altlinux.org/ru/{branch1}/binary/{pkg['name']}/{pkg['arch']}/"
            } 
            for pkg in packages1.values() if pkg["name"] not in packages2
        ],
        "packages_only_in_branch2": [
            {
                "name": pkg["name"],
                "epoch": pkg["epoch"],
                "version": pkg["version"],
                "release": pkg["release"],
                "arch": pkg["arch"],
                "buildtime": pkg["buildtime"],
                "disttag": pkg["disttag"],
                "url": f"https://packages.altlinux.org/ru/{branch2}/binary/{pkg['name']}/{pkg['arch']}/"
            } 
            for pkg in packages2.values() if pkg["name"] not in packages1
        ],
        "packages_with_higher_version_in_branch1": [
            {
                "name": pkg["name"],
                "epoch": pkg["epoch"],
                "version": pkg["version"],
                "release": pkg["release"],
                "arch": pkg["arch"],
                "buildtime": pkg["buildtime"],
                "disttag": pkg["disttag"],
                "url": f"https://packages.altlinux.org/ru/{branch1}/binary/{pkg['name']}/{pkg['arch']}/"
            } 
            for pkg in packages1.values() 
            if pkg["name"] in packages2 and compare_version_release(pkg["version"] + '-' + pkg["release"], 
                                                                    packages2[pkg["name"]]["version"] 
                                                                    + '-' + packages2[pkg["name"]]["release"]) > 0
        ]
    }

    return comparison_result

def compare_version_release(version_release1, version_release2):
    version_release_parts1 = version_release1.split('-')
    version_release_parts2 = version_release2.split('-')

    if len(version_release_parts1) == 1:
        version1 = version_release_parts1[0]
        release1 = ""
    else:
        version1, release1 = version_release_parts1

    if len(version_release_parts2) == 1:
        version2 = version_release_parts2[0]
        release2 = ""
    else:
        version2, release2 = version_release_parts2

    version_parts1 = version1.split('.')
    version_parts2 = version2.split('.')

    max_length = max(len(version_parts1), len(version_parts2))
    version_parts1 += ['0'] * (max_length - len(version_parts1))
    version_parts2 += ['0'] * (max_length - len(version_parts2))

    for part1, part2 in zip(version_parts1, version_parts2):
        if part1.isdigit() and part2.isdigit():
            if int(part1) > int(part2):
                return 1
            elif int(part1) < int(part2):
                return -1
        elif part1.isdigit():
            return -1
        elif part2.isdigit():
            return 1
        else:
            if part1 > part2:
                return 1
            elif part1 < part2:
                return -1

    if len(version_parts1) > len(version_parts2):
        return 1
    elif len(version_parts1) < len(version_parts2):
        return -1

    if release1 and not release2:
        return -1
    elif release2 and not release1:
        return 1
    elif release1 and release2:
        if release1 > release2:
            return 1
        elif release1 < release2:
            return -1

    return 0

def main():
    """
    Основная функция утилиты.
    """
    branch1 = "sisyphus"
    branch2 = "p10"
    comparison_result = compare_packages(branch1, branch2)

    if comparison_result:
        with open("comparison_result.txt", "w") as file:
            file.write("Comparison Result:\n")
            file.write(json.dumps(comparison_result, indent=4))

if __name__ == "__main__":
    main()