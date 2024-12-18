from collections import defaultdict, deque
import csv
import json
import os
from ..utils.licenseCategorize import categorizeLicense 

class NodeScanner:

    def __init__(self, manifestLocation):
        self.manifest_location = manifestLocation
        self._base_path = os.path.dirname(manifestLocation)
        self._modules_dir = os.path.join(self._base_path, 'node_modules')
        self.license_collection = []
        self._analyzed_module_paths = []
        self._dependency_queue = deque()

    ## Scan the package.json file for dependencies and their licenses
    def scan(self):
        try:
            with open(self.manifest_location, "r") as file:
                if os.path.basename(file.name) != 'package.json':
                    print("Error: Provided file is not a package.json")
                    return
                
                print("Package.json located. Reading file...")
                manifest_json = json.load(file)
                self.dependency_list = list(manifest_json.get('dependencies', {}).keys()) + list(manifest_json.get('devDependencies', {}).keys())

                ## Now we have our dependencies (and dev dependencies), we can scan the modules directory for their licenses
                self._scan_modules()

                print("Scan complete. Dependencies and their licenses:")
                for dep, lic in self.license_collection:
                    print(f"{dep}: {lic}")

        except Exception as e:
            print(f"Error processing the file: {e}")

    def _scan_modules(self):
        ## Enqueue the root module's dependencies
        self._dependency_queue = deque([(self._modules_dir, dep) for dep in self.dependency_list])

        ## Dependency queue will continue to be populated until all dependencies have been analyzed
        while self._dependency_queue:
            modules_dir, dependency = self._dependency_queue.popleft()
            ## Check root module by combining the node_modules directory and the dependency name
            root_dependency_dir = os.path.join(modules_dir, dependency)
            ## Check if the dependency has already been analyzed - packages can share dependencies
            if root_dependency_dir not in self._analyzed_module_paths:
                self._check_dependency(root_dependency_dir, dependency)

    def _check_dependency(self, dependency_dir, dependency):
        ## Check if the dependency has a package.json file
        if os.path.exists(os.path.join(dependency_dir, 'package.json')):
            print(f"Checking {dependency_dir} for license information from dependency {dependency}.")

            with open(os.path.join(dependency_dir, 'package.json'), "r", encoding="utf-8") as file:
                ## Load the package.json file into JSON and extract the license information
                dependency_json = json.load(file)
                ## License information can be stored in 'license' or 'licenses' key
                license = dependency_json.get('license') or dependency_json.get('licenses') or 'No license found'
                ## Sometimes, the license information is stored in a list
                if isinstance(license, list):
                    ##REMINDER! Revisit this later. Am I only considering the first license in the list? Yikes...
                    license = license[0].get('type') or license[0].get('name') or 'No license found'

                ## Append the dependency and its license to the license collection
                self.license_collection.append((dependency, license))
                self._analyzed_module_paths.append(dependency_dir)

                ## While we're here, we need to check for transitive dependencies
                ## Only dependencies are analyzed, because dev dependencies are not included in the final package that we use.
                transitive_deps = list(dependency_json.get('dependencies', {}).keys())
                if transitive_deps:
                    analyzed_nested_deps = self._check_transitive_dependencies(transitive_deps, dependency_dir)
                    if analyzed_nested_deps:
                        '''
                        If a package is found within a dependency's own node_modules, we can infer it has a 
                        counterpart with a different version in the root node_modules. In this case, the root 
                        version does not belong directly to our package, so we will not enqueue it here. 
                        Instead, we allow the root version to be analyzed when it’s enqueued by its actual owner.
                        '''
                        transitive_deps = [dep for dep in transitive_deps if dep not in analyzed_nested_deps]

                self._enqueue_child_dependencies(transitive_deps)
        else:
            print(f"No package.json found for {dependency} at {dependency_dir}")

    '''
    If you are wondering why we scan a dependency's own `node_modules` directory before enqueuing 
    its transitive dependencies, it’s because of deduplication behavior in Node.js. When multiple 
    packages depend on the same version of a dependency, Node.js deduplication places that dependency 
    at the root `node_modules`. However, if different versions are required, deduplication does not apply.
    The most common (or first encountered) will be placed at the root, and the others will be placed in
    the dependency's `node_modules` directory.

    By scanning each dependency's own `node_modules` directory first, we ensure we capture all unique 
    versions of transitive dependencies that might not have been hoisted to the root. Without this step, 
    we would incorrectly assume all transitive dependencies are located at the root, leading to missed 
    dependencies in cases where deduplication was not applied due to version differences.
    '''

    def _check_transitive_dependencies(self, transitive_deps, dependency_dir):
        analyzed_transitive_deps = []
        ## First, let's ensure the package has a node_modules directory. If not, we can skip.
        ## If no node_modules directory is found, we can assume all transitive dependencies can be found in the root node_modules.
        if os.path.exists(os.path.join(dependency_dir, 'node_modules')):
            for transitive_dep in transitive_deps:
                transitive_dep_dir = os.path.join(dependency_dir, 'node_modules', transitive_dep)
                ## Check if the transitive dependency has already been analyzed
                ## REMINDER! Revisit this later. Do we need to be concerned about transitive dependencies being analyzed multiple times?
                if transitive_dep_dir not in self._analyzed_module_paths and os.path.exists(os.path.join(transitive_dep_dir, 'package.json')):
                    with open(os.path.join(transitive_dep_dir, 'package.json'), "r", encoding="utf-8") as file:
                        transitive_dep_json = json.load(file)
                        ## REMINDER! Revisit this later. We have duplicate code here. Refactor.
                        transitive_license = transitive_dep_json.get('license') or transitive_dep_json.get('licenses') or 'No license found'
                        if isinstance(transitive_license, list):
                            transitive_license = transitive_license[0].get('type') or license[0].get('name') or 'No license found'
                            self.license_collection.append((transitive_dep, transitive_license))
                            analyzed_transitive_deps.append(transitive_dep)
                            return analyzed_transitive_deps

    def _enqueue_child_dependencies(self, dependencies):
        for child_dep in dependencies:
            ## Construct file paths for transitive dependencies
            child_dep_dir = os.path.join(self._modules_dir, child_dep)
            if child_dep_dir not in self._analyzed_module_paths:
                print(f"Enqueuing child dependency {child_dep} from {self._modules_dir}")
                self._dependency_queue.append((os.path.join(self._modules_dir), child_dep))

    def get_license_collection(self):
        return self.license_collection
    
    def _categorize_license(self, license_name):
        return categorizeLicense(license_name)
        

    def export_license_csv(self):
        # Initialize the category count dictionary
        category_counts = defaultdict(int)
        categorized_licenses = defaultdict(list)

        # Categorize and count licenses
        self.license_collection.sort()
        for dep, lic in self.license_collection:
            category = self._categorize_license(lic)
            categorized_licenses[category].append((dep, lic))
            category_counts[category] += 1

        with open('license_report.csv', 'w', newline='') as file:
            writer = csv.writer(file)

            # Write the category counts
            writer.writerow(['Category', 'Count'])
            for category, count in category_counts.items():
                writer.writerow([category, count])

            writer.writerow(['', ''])

            writer.writerow(['Dependency', 'License'])
            writer.writerow(['', ''])
            # Write the categorized dependencies and their licenses
            for category, licenses in categorized_licenses.items():
                writer.writerow([category, ''])
                for dep, lic in licenses:
                    writer.writerow([dep, lic])
                writer.writerow(['', ''])