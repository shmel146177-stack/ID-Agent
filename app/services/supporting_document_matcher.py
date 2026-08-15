class SupportingDocumentMatcher:
    def _normalize(self, value: str) -> str:
        return (value or "").lower().replace("ё", "е")

    def matches(
        self,
        requirement: dict,
        document: dict,
    ) -> bool:

        allowed_types = requirement.get("document_types", [])
        classification = document.get("classification", "")

        if allowed_types and classification not in allowed_types:
            return False

        text = " ".join(
            [
                document.get("filename", ""),
                document.get("text", ""),
            ]
        )

        normalized_text = self._normalize(text)

        keywords = requirement.get("match_keywords", [])

        if not all(
            self._normalize(keyword) in normalized_text
            for keyword in keywords
        ):
            return False

        any_keywords = requirement.get("match_any_keywords", [])

        if any_keywords and not any(
            self._normalize(keyword) in normalized_text
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

        used_document_indexes = set()
        matched = []
        missing = []

        for requirement in requirements:
            matched_document = None
            matched_index = None

            for index, document in enumerate(documents):
                if index in used_document_indexes:
                    continue

                if self.matches(requirement, document):
                    matched_document = document
                    matched_index = index
                    break

            if matched_document is None:
                missing.append(
                    {
                        "requirement_code": requirement.get("code"),
                        "title": requirement.get("title"),
                    }
                )
                continue

            used_document_indexes.add(matched_index)

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
