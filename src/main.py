from collections import deque
import json
import os

manifestLocation = input("Enter the manifest file location: ")
analyzedModulePath = []
licenseCollection = []

def scanModules(modulesDir, dependencyList):
    queue = deque([(modulesDir, dep) for dep in dependencyList])
    while queue:
        currentDir, dependency = queue.popleft()
        dependencyDir = os.path.join(currentDir, dependency)
        nestedModulesDir = os.path.join(dependencyDir, 'node_modules')

        # Check for license in nested node_modules first
        nestedDependencyDir = os.path.join(nestedModulesDir, dependency)
        if os.path.exists(nestedDependencyDir) and os.path.exists(os.path.join(nestedDependencyDir, 'package.json')):
            print(f"Checking {nestedDependencyDir}...")
            with open(os.path.join(nestedDependencyDir, 'package.json'), "r", encoding="utf-8") as file:
                dependencyJson = json.load(file)
                license = dependencyJson.get('license') or dependencyJson.get('licenses') or 'No license found'
                print (f"License: {type(license)}")
                if type(license) == list:
                    license = license[0].get('type') or license[0].get('name') or 'No license found'
                
                licenseCollection.append((dependency, license))
                continue  # Proceed to next item in queue
        else:
            print(f"No nested dependency directory for {dependency}")

        # Check the root node_modules

        if dependencyDir in analyzedModulePath:
            print(f"Dependency {dependency} already analyzed")
            continue

        if os.path.exists(dependencyDir) and os.path.exists(os.path.join(dependencyDir, 'package.json')):
            print(f"Checking {dependencyDir}...")
            with open(os.path.join(dependencyDir, 'package.json'), "r", encoding="utf-8") as file:
                dependencyJson = json.load(file)
                license = dependencyJson.get('license') or dependencyJson.get('licenses') or 'No license found'
                if type(license) is list:
                    license = license[0].get('type') or license[0].get('name') or 'No license found'
                licenseCollection.append((dependency, license))
                analyzedModulePath.append(dependencyDir)
                
                # Enqueue child dependencies
                dependencies = dependencyJson.get('dependencies') or {}
                for childDep in dependencies.keys():
                    print(f"Adding child dependency {childDep} from {dependency}")
                    queue.append((currentDir, childDep))
        else:
            print(f"Dependency {dependency} does not exist in {currentDir}")

    return licenseCollection

try:
    with open(manifestLocation, "r", encoding="utf-8") as file:
        basePath = os.path.dirname(manifestLocation)
        fileName = os.path.basename(file.name)
        modulesDir = os.path.join(basePath, 'node_modules')

        if fileName != 'package.json':
            print("File is not a package.json file")
            exit()

        print("package.json located. Reading file...")

        manifestJson = json.load(file)

        dependencies = manifestJson.get('dependencies', {})
        devDependencies = manifestJson.get('devDependencies', {})
        dependencyList = list(dependencies.keys()) + list(devDependencies.keys())

        scanModules(modulesDir, dependencyList)
        print("Scan complete.")
        print("Dependencies and their licenses:")
        for dep, lic in licenseCollection:
            print(f"{dep}: {lic}")

except Exception as e:
    print(f"Invalid path or file: {e}")
    exit()
