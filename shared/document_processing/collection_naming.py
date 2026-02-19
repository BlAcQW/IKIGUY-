"""
Collection naming utilities for RAG knowledge bases.

Provides consistent, organization-scoped collection naming
across all KasaAI applications.

Author: KasaAI Team
Date: 2025-11-28
"""

import re
from typing import Optional


class CollectionNaming:
    """
    Utility for generating consistent RAG collection names.

    Supports multiple naming strategies:
    1. Organization-scoped (multi-tenant)
    2. Document-specific (per-book, per-material)
    3. Category-based (per-subject, per-grade)
    """

    @staticmethod
    def sanitize(name: str) -> str:
        """
        Sanitize a name for use in collection identifiers.

        Args:
            name: Raw name string

        Returns:
            Sanitized lowercase string with underscores
        """
        # Convert to lowercase and replace spaces/hyphens with underscores
        sanitized = name.lower().strip()
        sanitized = re.sub(r"[\s\-]+", "_", sanitized)
        # Remove any non-alphanumeric characters except underscore
        sanitized = re.sub(r"[^a-z0-9_]", "", sanitized)
        # Remove consecutive underscores
        sanitized = re.sub(r"_+", "_", sanitized)
        # Remove leading/trailing underscores
        return sanitized.strip("_")

    @classmethod
    def for_document(
        cls,
        app_name: str,
        document_id: str,
        organization_id: Optional[str] = None,
    ) -> str:
        """
        Generate collection name for a specific document.

        Pattern: {app}_{org}_{doc_id} or {app}_{doc_id}

        Args:
            app_name: Application name (inkwave, studyflow, etc.)
            document_id: Unique document identifier
            organization_id: Organization ID for multi-tenancy

        Returns:
            Collection name
        """
        app = cls.sanitize(app_name)
        doc = cls.sanitize(document_id)

        if organization_id:
            org = cls.sanitize(organization_id)
            return f"{app}_{org}_{doc}"
        return f"{app}_{doc}"

    @classmethod
    def for_category(
        cls,
        app_name: str,
        category: str,
        subcategory: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> str:
        """
        Generate collection name for a category (subject, genre, etc.).

        Pattern: {app}_{org}_{category}_{subcategory}

        Args:
            app_name: Application name
            category: Primary category (subject, genre)
            subcategory: Optional subcategory (grade level, sub-genre)
            organization_id: Organization ID for multi-tenancy

        Returns:
            Collection name
        """
        app = cls.sanitize(app_name)
        cat = cls.sanitize(category)

        parts = [app]

        if organization_id:
            parts.append(cls.sanitize(organization_id))

        parts.append(cat)

        if subcategory:
            parts.append(cls.sanitize(subcategory))

        return "_".join(parts)

    @classmethod
    def for_subject_grade(
        cls,
        app_name: str,
        subject: str,
        grade: Optional[int] = None,
        organization_id: Optional[str] = None,
    ) -> str:
        """
        Generate collection name for subject/grade (educational apps).

        Pattern: {app}_{org}_{subject}_grade{N}

        Args:
            app_name: Application name
            subject: Subject name
            grade: Grade level (optional)
            organization_id: Organization ID

        Returns:
            Collection name
        """
        app = cls.sanitize(app_name)
        subj = cls.sanitize(subject)

        parts = [app]

        if organization_id:
            parts.append(cls.sanitize(organization_id))

        parts.append(subj)

        if grade is not None:
            parts.append(f"grade{grade}")

        return "_".join(parts)

    @classmethod
    def for_book(
        cls,
        book_id: str,
        organization_id: Optional[str] = None,
    ) -> str:
        """
        Generate collection name for a book (InkWave pattern).

        Args:
            book_id: Book identifier
            organization_id: Organization ID

        Returns:
            Collection name
        """
        return cls.for_document("inkwave", book_id, organization_id)

    @classmethod
    def for_material(
        cls,
        subject: str,
        grade: Optional[int] = None,
        organization_id: Optional[str] = None,
    ) -> str:
        """
        Generate collection name for study material (StudyFlow pattern).

        Args:
            subject: Subject name
            grade: Grade level
            organization_id: Organization ID

        Returns:
            Collection name
        """
        return cls.for_subject_grade("studyflow", subject, grade, organization_id)

    @classmethod
    def parse(cls, collection_name: str) -> dict:
        """
        Parse a collection name to extract components.

        Args:
            collection_name: Collection name to parse

        Returns:
            Dictionary with parsed components
        """
        parts = collection_name.split("_")

        result = {
            "raw": collection_name,
            "app": parts[0] if parts else None,
            "organization_id": None,
            "category": None,
            "subcategory": None,
            "document_id": None,
            "grade": None,
        }

        if len(parts) < 2:
            return result

        # Check for grade pattern
        for i, part in enumerate(parts):
            if part.startswith("grade") and part[5:].isdigit():
                result["grade"] = int(part[5:])
                # Everything before grade (except app and possibly org) is category
                category_parts = parts[1:i]
                if len(category_parts) >= 2:
                    result["organization_id"] = category_parts[0]
                    result["category"] = "_".join(category_parts[1:])
                elif len(category_parts) == 1:
                    result["category"] = category_parts[0]
                break
        else:
            # No grade pattern found
            if len(parts) >= 3:
                # Could be org_category or category_subcategory
                result["organization_id"] = parts[1]
                result["category"] = "_".join(parts[2:])
            elif len(parts) == 2:
                result["category"] = parts[1]

        return result


# Convenience functions
def collection_for_book(
    book_id: str,
    organization_id: Optional[str] = None,
) -> str:
    """Generate collection name for a book."""
    return CollectionNaming.for_book(book_id, organization_id)


def collection_for_material(
    subject: str,
    grade: Optional[int] = None,
    organization_id: Optional[str] = None,
) -> str:
    """Generate collection name for study material."""
    return CollectionNaming.for_material(subject, grade, organization_id)
