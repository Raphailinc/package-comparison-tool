import requests

def get_branch_binary_packages(branch):
    """
    Получает списки бинарных пакетов для указанной ветки.

    Args:
        branch (str): Название ветки (например, "sisyphus" или "p10").

    Returns:
        dict: Словарь с данными о бинарных пакетах.
    """
    url = f"https://rdb.altlinux.org/api/export/branch_binary_packages/{branch}"
    response = requests.get(url)

    if response.status_code == 200:
        packages_data = response.json()
        packages = []
        for pkg in packages_data["packages"]:
            package_info = {
                "name": pkg["name"],
                "version": pkg["version"],
                "release": pkg["release"],
                "arch": pkg["arch"],
                "url": f"https://packages.altlinux.org/ru/{branch}/binary/{pkg['name']}/{pkg['arch']}/"
            }
            packages.append(package_info)
        return {"packages": packages}
    elif response.status_code == 404:
        print("Requested data not found in database.")
    else:
        print("Error:", response.status_code)

    return None