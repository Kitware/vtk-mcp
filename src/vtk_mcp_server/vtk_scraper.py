import re
import requests
from bs4 import BeautifulSoup


class VTKClassScraper:
    def __init__(self):
        self.base_url = "https://vtk.org/doc/nightly/html"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                )
            }
        )

    def get_class_info(self, class_name):
        if not class_name.startswith("vtk"):
            class_name = f"vtk{class_name}"

        url = f"{self.base_url}/class{class_name}.html"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
        except requests.RequestException:
            return None

        soup = BeautifulSoup(response.content, "html.parser")

        return self._parse_class_page(soup, class_name)

    def _parse_class_page(self, soup, class_name):
        info = {
            "class_name": class_name,
            "description": "",
            "inheritance": [],
            "methods": [],
            "brief": "",
            "detailed_description": "",
            "url": f"{self.base_url}/class{class_name}.html",
        }

        # Get class title and brief description
        title_elem = soup.find("div", class_="title")
        if title_elem:
            info["brief"] = title_elem.get_text(strip=True)

        # Get detailed description from multiple textblock divs
        textblocks = soup.find_all("div", class_="textblock")
        descriptions = []
        for block in textblocks:
            text = block.get_text(strip=True)
            if text and len(text) > 20:  # Filter out very short text
                descriptions.append(text)

        if descriptions:
            info["detailed_description"] = " ".join(
                descriptions[:2]
            )  # Take first 2 meaningful blocks

        # Get inheritance information from inheritance diagram or class hierarchy
        inheritance_links = soup.find_all("a", href=re.compile(r"class.*\.html"))
        inheritance_classes = []
        for link in inheritance_links:
            class_text = link.get_text(strip=True)
            if class_text.startswith("vtk") and class_text != class_name:
                inheritance_classes.append(class_text)

        # Remove duplicates and limit
        info["inheritance"] = list(dict.fromkeys(inheritance_classes))[:10]

        # Get public methods - try multiple approaches
        methods = []

        # Approach 1: Look for method tables
        method_tables = soup.find_all("table", class_="memberdecls")
        for table in method_tables:
            rows = table.find_all("tr")
            for row in rows:
                # Look for method signatures
                method_cell = row.find("td", class_="memItemRight")
                if method_cell:
                    method_link = method_cell.find("a")
                    if method_link:
                        method_name = method_link.get_text(strip=True)
                        # Get the full method signature
                        method_sig = method_cell.get_text(strip=True)
                        methods.append({"name": method_name, "description": method_sig})

        # Approach 2: Look for method definition lists
        if not methods:
            method_sections = soup.find_all(
                ["h2", "h3"], string=re.compile(r"Member Function|Public.*Function")
            )
            for section in method_sections:
                next_elem = section.find_next_sibling()
                while next_elem and next_elem.name not in ["h1", "h2", "h3"]:
                    if next_elem.name == "table":
                        for row in next_elem.find_all("tr"):
                            method_links = row.find_all("a", href=re.compile(r"#"))
                            for link in method_links:
                                method_name = link.get_text(strip=True)
                                if method_name and not any(
                                    x in method_name.lower()
                                    for x in ["class", "struct", "enum"]
                                ):
                                    methods.append(
                                        {
                                            "name": method_name,
                                            "description": f"Method: {method_name}",
                                        }
                                    )
                    next_elem = next_elem.find_next_sibling()

        # Approach 3: Parse all anchor links that look like methods
        if not methods:
            all_links = soup.find_all("a", href=re.compile(r"#a[0-9a-f]+"))
            for link in all_links:
                method_name = link.get_text(strip=True)
                if (
                    method_name
                    and len(method_name) > 2
                    and not any(
                        x in method_name.lower()
                        for x in ["class", "struct", "enum", "typedef"]
                    )
                ):
                    # Try to get context for the method
                    parent = link.find_parent(["td", "div", "span"])
                    context = parent.get_text(strip=True) if parent else method_name
                    methods.append(
                        {
                            "name": method_name,
                            "description": (
                                context[:200] if context else f"Method: {method_name}"
                            ),
                        }
                    )

        # Remove duplicates while preserving order
        seen = set()
        unique_methods = []
        for method in methods:
            if method["name"] not in seen:
                seen.add(method["name"])
                unique_methods.append(method)

        info["methods"] = unique_methods[:50]  # Limit to 50 methods

        return info

    def search_classes(self, search_term):
        """Search for VTK classes containing the search term"""
        try:
            url = f"{self.base_url}/annotated.html"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            class_links = soup.find_all("a", href=re.compile(r"class.*\.html"))
            matches = []

            for link in class_links:
                class_name = link.get_text(strip=True)
                if search_term.lower() in class_name.lower():
                    matches.append(class_name)

            return sorted(list(set(matches)))[:20]  # Limit to 20 results

        except requests.RequestException:
            return []
