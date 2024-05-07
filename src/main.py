import os

manifestLocation = input("Enter the manifest file location: ")

try:
    with open(manifestLocation, "r") as file:

        fileName = os.path.basename(file.name)
        
        if fileName != 'package.json':
            print("File is not a package.json file")
            exit()
        if fileName == 'package.json':
            print("Package.json located. Reading file...")
            print(file.read())

except Exception as e:
    print(f"Invalid path: {e}")
    exit()