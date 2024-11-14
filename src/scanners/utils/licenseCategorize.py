def categorizeLicense(license_name):
        open_source_licenses = [
            'MIT', 'Apache-2.0', 'GPL-3.0', 'BSD', 'BSD-3-Clause', 'ISC',
            'BSD-2-Clause', 'Python-2.0', 'CC0-1.0', 'CC-BY-4.0', '0BSD', 'CC-BY-3.0', 'OFL-1.1', 'MPL-2.0'
        ]
        closed_source_licenses = ['Proprietary']
        partial_licenses = ['LGPL-2.1', 'LGPL-3.0']
        unlicensed_licenses = ['UNLICENSED', 'Unlicense']
        eula_licenses = ['SEE LICENSE IN EULA_MICROSOFT VISUAL STUDIO TEAM SERVICES AUTHHELPER FOR NPM.txt']

        # Some licenses are combined with 'AND' or 'OR'. We will to categorize them as 'Mixed'.
        if 'AND' in license_name or 'OR' in license_name:
            licenses = license_name.replace('AND', 'OR').split('OR')
            categories = set()
            for lic in licenses:
                lic = lic.strip().strip('()')
                if lic in open_source_licenses:
                    categories.add('Open Source')
                elif lic in closed_source_licenses:
                    categories.add('Closed Source')
                elif lic in partial_licenses:
                    categories.add('Partial')
                elif lic in unlicensed_licenses:
                    categories.add('Unlicensed')
                elif lic in eula_licenses:
                    categories.add('EULA')
                else:
                    categories.add('Unknown')
        
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
        elif license_name in unlicensed_licenses:
            return 'Unlicensed'
        elif license_name in eula_licenses:
            return 'EULA'
        else:
            return 'Unknown'

