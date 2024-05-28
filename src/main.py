import os
from src.scanners.nodeScanner import NodeScanner

manifestLocation = input("Enter the manifest file location: ")

try:
    with open(manifestLocation, "r", encoding="utf-8") as file:
        basePath = os.path.dirname(manifestLocation)
        fileName = os.path.basename(file.name)

        if fileName != 'package.json':
            print("File is not a package.json file")
            exit()

        scanner = NodeScanner(manifestLocation)
        scanner.scan()
        scanner.export_license_csv()

except Exception as e:
    print(f"Invalid path or file: {e}")
    exit()
