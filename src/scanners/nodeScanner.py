from collections import defaultdict, deque
import csv
import json
import os

class NodeScanner:

    def __init__(self, manifestLocation):
        self.manifest_location = manifestLocation
        self.base_path = os.path.dirname(manifestLocation)
        self.modules_dir = os.path.join(self.base_path, 'node_modules')
        self.license_collection = []
        self.analyzed_module_paths = []
        self.dependency_queue = deque()

    def scan(self):
        try:
            with open(self.manifest_location, "r", encoding="utf-8") as file:
                if os.path.basename(file.name) != 'package.json':
                    print("Error: Provided file is not a package.json")
                    return
                print("package.json located. Reading file...")
                manifest_json = json.load(file)
                self.dependency_list = list(manifest_json.get('dependencies', {}).keys()) + list(manifest_json.get('devDependencies', {}).keys())
                self._scan_modules()
                print("Scan complete. Dependencies and their licenses:")
                for dep, lic in self.license_collection:
                    print(f"{dep}: {lic}")
        except Exception as e:
            print(f"Error processing the file: {e}")

    def _scan_modules(self):
        self.dependency_queue = deque([(self.modules_dir, dep) for dep in self.dependency_list])
        while self.dependency_queue:
            modules_dir, dependency = self.dependency_queue.popleft()
            # Check root module
            root_dependency_dir = os.path.join(modules_dir, dependency)
            if root_dependency_dir not in self.analyzed_module_paths:
                self._check_dependency(root_dependency_dir, dependency)

    def _check_dependency(self, dependency_dir, dependency):
        if os.path.exists(os.path.join(dependency_dir, 'package.json')):
            print(f"Checking {dependency_dir} for license information...")
            with open(os.path.join(dependency_dir, 'package.json'), "r", encoding="utf-8") as file:
                dependency_json = json.load(file)
                license = dependency_json.get('license') or dependency_json.get('licenses') or 'No license found'
                if isinstance(license, list):
                    license = license[0].get('type') or license[0].get('name') or 'No license found'
                self.license_collection.append((dependency, license))
                self.analyzed_module_paths.append(dependency_dir)

                ##check nested node_modules
                transitive_deps = dependency_json.get('dependencies', {}).keys()
                if transitive_deps:
                    analyzed_nested_deps = self._check_transitive_dependencies(transitive_deps, dependency_dir)
                    if analyzed_nested_deps:
                        ## Remove analyzed nested dependencies from transitive dependencies. Not doing so would result in checking the root module, which
                        ## we can infer belongs to another package based on th existence of the nested dependency
                        transitive_deps = [dep for dep in transitive_deps if dep not in analyzed_nested_deps]

                # Enqueue child dependencies if present
                self._enqueue_child_dependencies(transitive_deps)
        else:
            print(f"No package.json found for {dependency} at {dependency_dir}")
        
    def _check_transitive_dependencies(self, transitive_deps, dependency_dir):

        analyzed_transitive_deps = []

        if os.path.exists(os.path.join(dependency_dir, 'node_modules')):
                    for transitive_dep in transitive_deps:
                        transitive_dep_dir = os.path.join(dependency_dir, 'node_modules', transitive_dep)
                        if transitive_dep_dir not in self.analyzed_module_paths and os.path.exists(os.path.join(transitive_dep_dir, 'package.json')):
                            with open(os.path.join(transitive_dep_dir, 'package.json'), "r", encoding="utf-8") as file:
                                transitive_dep_json = json.load(file)
                                transitive_license = transitive_dep_json.get('license') or transitive_dep_json.get('licenses') or 'No license found'
                                self.license_collection.append((transitive_dep, transitive_license))
                                analyzed_transitive_deps.append(transitive_dep)
                                return analyzed_transitive_deps

    def _enqueue_child_dependencies(self, dependencies):
        for child_dep in dependencies:
            child_dep_dir = os.path.join(self.modules_dir, child_dep)
            if child_dep_dir not in self.analyzed_module_paths:
                print(f"Enqueuing child dependency {child_dep} from {self.modules_dir}")
                self.dependency_queue.append((os.path.join(self.modules_dir), child_dep))

    def get_license_collection(self):
        return self.license_collection
    
    def _categorize_license(self, license_name):
        open_source_licenses = [
            'MIT', 'Apache-2.0', 'GPL-3.0', 'BSD-3-Clause', 'ISC',
            'BSD-2-Clause', 'Python-2.0', 'CC0-1.0'
        ]
        closed_source_licenses = ['Proprietary']
        partial_licenses = ['LGPL-2.1', 'LGPL-3.0']

        # Handle multiple licenses
        if 'AND' in license_name or 'OR' in license_name:
            licenses = license_name.split(' AND ') if 'AND' in license_name else license_name.split(' OR ')
            categories = set(self._categorize_license(lic.strip().strip('()')) for lic in licenses)
            if len(categories) == 1:
                return categories.pop()  # If all licenses fall into the same category. Sets cannot be indexed.
            else:
                return 'Mixed'

        if license_name in open_source_licenses:
            return 'Open Source'
        elif license_name in closed_source_licenses:
            return 'Closed Source'
        elif license_name in partial_licenses:
            return 'Partial'
        else:
            return 'Unknown'


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
            
            # Write the dependency and license headers
            writer.writerow(['Dependency', 'License'])
            writer.writerow(['', ''])

            # Write the categorized dependencies and their licenses
            for category, licenses in categorized_licenses.items():
                writer.writerow([category, ''])
                for dep, lic in licenses:
                    writer.writerow([dep, lic])
                writer.writerow(['', ''])

            # Write the category counts
            writer.writerow(['Category', 'Count'])
            for category, count in category_counts.items():
                writer.writerow([category, count])
