import json
import os

manifestLocation = input("Enter the manifest file location: ")

try:
    with open(manifestLocation, "r") as file:

        basePath = os.path.dirname(manifestLocation)
        fileName = os.path.basename(file.name)
        
        if fileName != 'package.json':
            print("File is not a package.json file")
            exit()
        if fileName == 'package.json':
            print("Package.json located. Reading file...")
            
            manifestJson = json.load(file)

            dependencies = manifestJson['dependencies']
            devDependencies = manifestJson['devDependencies']
            dependencyList = []

            for dependency in dependencies:
                dependencyList.append(dependency)

            modulesDir = os.path.join(basePath, 'node_modules')

            print(os.listdir(modulesDir))
            


except Exception as e:
    print(f"Invalid path: {e}")
    exit()