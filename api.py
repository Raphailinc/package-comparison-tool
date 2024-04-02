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
        return response.json()
    elif response.status_code == 404:
        print("Requested data not found in database.")
    else:
        print("Error:", response.status_code)

    return None

if __name__ == "__main__":
    branch = "p10"
    packages_data = get_branch_binary_packages(branch)
    if packages_data:
        print("Packages data:", packages_data)