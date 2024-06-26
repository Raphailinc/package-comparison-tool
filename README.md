# Package Comparison Tool

This CLI utility compares binary packages between two branches of ALT Linux repositories. It retrieves package information using the ALT Linux API and provides a JSON report with the comparison results.

## Installation

1. Make sure you have Python 3 and pip installed on your system. You can install them using the following commands:

    ```
    sudo apt update
    sudo apt install python3 python3-pip
    ```

2. Clone the repository:

    ```
    git clone https://github.com/Raphailinc/package-comparison-tool.git
    cd package-comparison-tool
    ```

3. Create and activate a virtual environment:

    ```
    python3 -m venv venv
    source venv/bin/activate
    ```

4. Install dependencies:

    ```
    pip3 install -r requirements.txt
    ```

## Usage

To use the Package Comparison Tool, follow these steps:

1. Open a terminal window and navigate to the directory where you cloned the repository.

2. Activate the virtual environment:

    ```
    source venv/bin/activate
    ```

3. Run the CLI utility with the following command:

    ```
    python3 cli.py
    ```

4. The utility will compare binary packages between the "sisyphus" and "p10" branches by default and display the comparison results in JSON format.

    Example output:

    ```
    Comparison Result:
    {
    "packages_only_in_branch1": [
        {
        "name": "example-package",
        "epoch": 0,
        "version": "1.0",
        "release": "alt1",
        "arch": "x86_64",
        "buildtime": "1708646095",
        "disttag": "sisyphus+341252.500.2.3",
        "url": "https://packages.altlinux.org/ru/sisyphus/binary/example-package/x86_64/"
        }
    ],
    "packages_only_in_branch2": [],
    "packages_with_higher_version_in_branch1": []
    }
    ```

5. You can also specify branches to compare explicitly by providing their names as command-line arguments:

    ```
    python3 cli.py
    ```

6. The utility will then compare the specified branches and display the results accordingly.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.