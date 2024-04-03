import json
import api

def main():
    branch = input("Введите название ветки: ")
    result = api.get_branch_binary_packages(branch)
    if result:
        print(json.dumps(result, indent=4))
    else:
        print("Не удалось получить данные о бинарных пакетах.")

if __name__ == "__main__":
    main()