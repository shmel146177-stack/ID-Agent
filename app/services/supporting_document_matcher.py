import re


class SupportingDocumentMatcher:
    def _normalize(self, value: str) -> str:
        return (value or "").lower().replace("ё", "е")

    def _contains_keyword(
        self,
        text: str,
        keyword: str,
    ) -> bool:

        normalized_keyword = self._normalize(keyword)

        if not normalized_keyword:
            return False

        pattern = rf"(?<!\w){re.escape(normalized_keyword)}"

        return (
            re.search(
                pattern,
                text,
            )
            is not None
        )

    def matches(
        self,
        requirement: dict,
        document: dict,
    ) -> bool:

        allowed_types = requirement.get("document_types", [])
        classification = document.get("classification", "")

        if allowed_types and classification not in allowed_types:
            return False

        normalized_text = self._normalize(document.get("text", ""))

        keywords = requirement.get("match_keywords", [])

        if not all(
            self._contains_keyword(
                normalized_text,
                keyword,
            )
            for keyword in keywords
        ):
            return False

        any_keywords = requirement.get("match_any_keywords", [])

        if any_keywords and not any(
            self._contains_keyword(
                normalized_text,
                keyword,
            )
            for keyword in any_keywords
        ):
            return False

        return True

    def build_documents(
        self,
        project_analysis: dict,
        page_analysis: dict,
    ) -> list[dict]:

        pages_by_filename = {
            document.get("filename"): document
            for document in page_analysis.get("documents", [])
            if document.get("filename")
        }

        result = []

        for document in project_analysis.get("documents", []):
            filename = document.get("filename", "")
            page_document = pages_by_filename.get(filename, {})

            page_texts = []

            for page in page_document.get("pages", []):
                text = page.get("text", "") or ""

                if text:
                    page_texts.append(text)

            result.append(
                {
                    "filename": filename,
                    "path": document.get("path", ""),
                    "classification": document.get(
                        "classification",
                        "Не определён",
                    ),
                    "text": "\n".join(page_texts),
                }
            )

        return result

    def match_analysis(
        self,
        requirements: list[dict],
        project_analysis: dict,
        page_analysis: dict,
    ) -> dict:

        documents = self.build_documents(
            project_analysis,
            page_analysis,
        )

        return self.match_requirements(
            requirements,
            documents,
        )

    def match_requirements(
        self,
        requirements: list[dict],
        documents: list[dict],
    ) -> dict:

        compatible_documents = [
            [
                index
                for index, document in enumerate(documents)
                if self.matches(requirement, document)
            ]
            for requirement in requirements
        ]
        requirement_by_document = {}

        def assign(requirement_index: int, visited: set[int]) -> bool:
            for document_index in compatible_documents[requirement_index]:
                if document_index in visited:
                    continue
                visited.add(document_index)
                previous = requirement_by_document.get(document_index)
                if previous is None or assign(previous, visited):
                    requirement_by_document[document_index] = requirement_index
                    return True
            return False

        for requirement_index in range(len(requirements)):
            assign(requirement_index, set())

        document_by_requirement = {
            requirement_index: document_index
            for document_index, requirement_index in requirement_by_document.items()
        }
        matched = []
        missing = []
        for requirement_index, requirement in enumerate(requirements):
            document_index = document_by_requirement.get(requirement_index)
            if document_index is None:
                missing.append(
                    {
                        "requirement_code": requirement.get("code"),
                        "title": requirement.get("title"),
                    }
                )
            else:
                matched_document = documents[document_index]
                matched.append(
                    {
                        "requirement_code": requirement.get("code"),
                        "title": requirement.get("title"),
                        "filename": matched_document.get("filename"),
                        "classification": matched_document.get("classification"),
                    }
                )

        return {
            "required_count": len(requirements),
            "found_count": len(matched),
            "missing_count": len(missing),
            "matched": matched,
            "missing": missing,
        }


supporting_document_matcher = SupportingDocumentMatcher()
