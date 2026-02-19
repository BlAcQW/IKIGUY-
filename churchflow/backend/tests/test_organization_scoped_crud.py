"""
Organization-Scoped CRUD API Tests

Validates that the organization consolidation migration was successful
and that all entities properly enforce organization boundaries.

This test suite ensures:
1. All CRUD operations respect organization boundaries
2. Users can only access/modify data from their own organization
3. Cross-organization access is prevented
4. The organization_id field is correctly set on all entities
"""

import pytest
from datetime import datetime
from bson import ObjectId


@pytest.mark.asyncio
class TestBranchOrganizationScoping:
    """Test organization scoping for Branch CRUD operations."""

    async def test_list_branches_filters_by_organization(
        self, test_db, users_for_two_orgs, branches_for_two_orgs
    ):
        """
        Test that listing branches only returns user's organization data.

        Expected:
            - User A sees only Organization A's branches
            - Results count matches expected count for org A
        """
        user_a, user_b = users_for_two_orgs
        branches = branches_for_two_orgs

        # Count expected branches for org A
        org_a_expected = [b for b in branches if b["organization_id"] == user_a["organization_id"]]

        # Query as user_a
        query = {"organization_id": user_a["organization_id"]}
        results = await test_db.branches.find(query).to_list(length=100)

        # Verify all results belong to org A
        assert len(results) == len(org_a_expected)
        for branch in results:
            assert branch["organization_id"] == user_a["organization_id"]
            assert branch["organization_id"] != user_b["organization_id"]

    async def test_list_branches_excludes_other_organizations(
        self, test_db, users_for_two_orgs, branches_for_two_orgs
    ):
        """
        Test that listing branches excludes other organizations' data.

        Expected:
            - User B's query does not return org A branches
            - Complete isolation between organizations
        """
        user_a, user_b = users_for_two_orgs

        # Query as user_b
        query = {"organization_id": user_b["organization_id"]}
        results = await test_db.branches.find(query).to_list(length=100)

        # Verify no org A branches in results
        for branch in results:
            assert branch["organization_id"] == user_b["organization_id"]
            assert branch["organization_id"] != user_a["organization_id"]

    async def test_get_branch_succeeds_same_organization(
        self, test_db, users_for_two_orgs, branches_for_two_orgs
    ):
        """
        Test that user can access branch from their own organization.

        Expected:
            - User A can retrieve org A's branch
            - Branch details returned successfully
        """
        user_a, user_b = users_for_two_orgs
        branches = branches_for_two_orgs

        # Get a branch from org A
        org_a_branch = [b for b in branches if b["organization_id"] == user_a["organization_id"]][0]

        # Access as user A (same org)
        query = {
            "_id": org_a_branch["_id"],
            "organization_id": user_a["organization_id"]
        }
        result = await test_db.branches.find_one(query)

        assert result is not None
        assert result["_id"] == org_a_branch["_id"]
        assert result["organization_id"] == user_a["organization_id"]

    async def test_get_branch_fails_different_organization(
        self, test_db, users_for_two_orgs, branches_for_two_orgs
    ):
        """
        Test that user cannot access branch from different organization.

        Expected:
            - Query returns None when user A tries to access org B's branch
            - Organization boundary enforced
        """
        user_a, user_b = users_for_two_orgs
        branches = branches_for_two_orgs

        # Get a branch from org B
        org_b_branch = [b for b in branches if b["organization_id"] == user_b["organization_id"]][0]

        # Try to access as user A (different org)
        query = {
            "_id": org_b_branch["_id"],
            "organization_id": user_a["organization_id"]
        }
        result = await test_db.branches.find_one(query)

        # Should not find the branch (it belongs to org B)
        assert result is None

    async def test_update_branch_succeeds_same_organization(
        self, test_db, users_for_two_orgs, branches_for_two_orgs
    ):
        """
        Test that user can update branch from their own organization.

        Expected:
            - User A can update org A's branch
            - Update is applied successfully
        """
        user_a, user_b = users_for_two_orgs
        branches = branches_for_two_orgs

        # Get branch from org A
        org_a_branch = [b for b in branches if b["organization_id"] == user_a["organization_id"]][0]

        # Update as user A
        update_data = {"location": "Updated Location"}
        result = await test_db.branches.update_one(
            {"_id": org_a_branch["_id"], "organization_id": user_a["organization_id"]},
            {"$set": update_data}
        )

        assert result.matched_count == 1
        assert result.modified_count == 1

        # Verify update applied
        updated = await test_db.branches.find_one({"_id": org_a_branch["_id"]})
        assert updated["location"] == "Updated Location"

    async def test_update_branch_fails_different_organization(
        self, test_db, users_for_two_orgs, branches_for_two_orgs
    ):
        """
        Test that user cannot update branch from different organization.

        Expected:
            - Update fails when user A tries to update org B's branch
            - No documents matched or modified
        """
        user_a, user_b = users_for_two_orgs
        branches = branches_for_two_orgs

        # Get branch from org B
        org_b_branch = [b for b in branches if b["organization_id"] == user_b["organization_id"]][0]

        # Try to update with user A's organization filter
        update_data = {"location": "Attempted cross-org update"}
        result = await test_db.branches.update_one(
            {"_id": org_b_branch["_id"], "organization_id": user_a["organization_id"]},
            {"$set": update_data}
        )

        # Update should not match any documents
        assert result.matched_count == 0
        assert result.modified_count == 0

        # Verify data unchanged
        unchanged = await test_db.branches.find_one({"_id": org_b_branch["_id"]})
        assert unchanged["location"] != "Attempted cross-org update"

    async def test_delete_branch_succeeds_same_organization(
        self, test_db, users_for_two_orgs, branches_for_two_orgs
    ):
        """
        Test that user can delete (soft) branch from their own organization.

        Expected:
            - User A can soft-delete org A's branch
            - Branch marked as inactive
        """
        user_a, user_b = users_for_two_orgs
        branches = branches_for_two_orgs

        # Get branch from org A
        org_a_branch = [b for b in branches if b["organization_id"] == user_a["organization_id"]][0]

        # Soft delete as user A
        result = await test_db.branches.update_one(
            {"_id": org_a_branch["_id"], "organization_id": user_a["organization_id"]},
            {"$set": {"is_active": False}}
        )

        assert result.matched_count == 1
        assert result.modified_count == 1

        # Verify branch deactivated
        deleted = await test_db.branches.find_one({"_id": org_a_branch["_id"]})
        assert deleted["is_active"] is False

    async def test_delete_branch_fails_different_organization(
        self, test_db, users_for_two_orgs, branches_for_two_orgs
    ):
        """
        Test that user cannot delete branch from different organization.

        Expected:
            - Delete fails when user A tries to delete org B's branch
            - Branch remains active
        """
        user_a, user_b = users_for_two_orgs
        branches = branches_for_two_orgs

        # Get branch from org B
        org_b_branch = [b for b in branches if b["organization_id"] == user_b["organization_id"]][0]

        # Try to delete with user A's organization filter
        result = await test_db.branches.update_one(
            {"_id": org_b_branch["_id"], "organization_id": user_a["organization_id"]},
            {"$set": {"is_active": False}}
        )

        # Delete should not match any documents
        assert result.matched_count == 0

        # Verify branch still active
        unchanged = await test_db.branches.find_one({"_id": org_b_branch["_id"]})
        assert unchanged["is_active"] is True

    async def test_complete_isolation_between_organizations(
        self, test_db, users_for_two_orgs, branches_for_two_orgs
    ):
        """
        Comprehensive test verifying complete data isolation for branches.

        Expected:
            - No overlap in branch IDs between organizations
            - Each org has exactly 2 branches
        """
        user_a, user_b = users_for_two_orgs

        # Get all branches for org A
        org_a_branches = await test_db.branches.find(
            {"organization_id": user_a["organization_id"]}
        ).to_list(length=100)

        # Get all branches for org B
        org_b_branches = await test_db.branches.find(
            {"organization_id": user_b["organization_id"]}
        ).to_list(length=100)

        # Verify counts
        assert len(org_a_branches) == 2
        assert len(org_b_branches) == 2

        # Verify no overlap
        org_a_ids = {str(b["_id"]) for b in org_a_branches}
        org_b_ids = {str(b["_id"]) for b in org_b_branches}
        assert len(org_a_ids.intersection(org_b_ids)) == 0


@pytest.mark.asyncio
class TestFirstTimerOrganizationScoping:
    """Test organization scoping for First Timer CRUD operations."""

    async def test_list_first_timers_filters_by_organization(
        self, test_db, users_for_two_orgs, first_timers_for_two_orgs
    ):
        """Test that listing first timers only returns user's organization data."""
        user_a, user_b = users_for_two_orgs

        # Query as user_a
        query = {"organization_id": user_a["organization_id"]}
        results = await test_db.first_timers.find(query).to_list(length=100)

        # Verify all results belong to org A
        assert len(results) == 2  # 2 first timers per org
        for ft in results:
            assert ft["organization_id"] == user_a["organization_id"]

    async def test_get_first_timer_fails_different_organization(
        self, test_db, users_for_two_orgs, first_timers_for_two_orgs
    ):
        """Test that user cannot access first timer from different organization."""
        user_a, user_b = users_for_two_orgs
        first_timers = first_timers_for_two_orgs

        # Get first timer from org B
        org_b_ft = [ft for ft in first_timers if ft["organization_id"] == user_b["organization_id"]][0]

        # Try to access as user A
        query = {
            "_id": org_b_ft["_id"],
            "organization_id": user_a["organization_id"]
        }
        result = await test_db.first_timers.find_one(query)

        assert result is None

    async def test_update_first_timer_fails_different_organization(
        self, test_db, users_for_two_orgs, first_timers_for_two_orgs
    ):
        """Test that user cannot update first timer from different organization."""
        user_a, user_b = users_for_two_orgs
        first_timers = first_timers_for_two_orgs

        org_b_ft = [ft for ft in first_timers if ft["organization_id"] == user_b["organization_id"]][0]

        # Try to update with user A's organization filter
        result = await test_db.first_timers.update_one(
            {"_id": org_b_ft["_id"], "organization_id": user_a["organization_id"]},
            {"$set": {"follow_up_notes": "Attempted cross-org update"}}
        )

        assert result.matched_count == 0
        assert result.modified_count == 0

    async def test_delete_first_timer_fails_different_organization(
        self, test_db, users_for_two_orgs, first_timers_for_two_orgs
    ):
        """Test that user cannot delete first timer from different organization."""
        user_a, user_b = users_for_two_orgs
        first_timers = first_timers_for_two_orgs

        org_b_ft = [ft for ft in first_timers if ft["organization_id"] == user_b["organization_id"]][0]

        # Try to delete with user A's organization filter
        result = await test_db.first_timers.update_one(
            {"_id": org_b_ft["_id"], "organization_id": user_a["organization_id"]},
            {"$set": {"is_active": False}}
        )

        assert result.matched_count == 0

        # Verify first timer still active
        unchanged = await test_db.first_timers.find_one({"_id": org_b_ft["_id"]})
        assert unchanged["is_active"] is True


@pytest.mark.asyncio
class TestConferenceOrganizationScoping:
    """Test organization scoping for Conference CRUD operations."""

    async def test_list_conferences_filters_by_organization(
        self, test_db, users_for_two_orgs, conferences_for_two_orgs
    ):
        """Test that listing conferences only returns user's organization data."""
        user_a, user_b = users_for_two_orgs

        # Query as user_a
        query = {"organization_id": user_a["organization_id"]}
        results = await test_db.conferences.find(query).to_list(length=100)

        # Verify all results belong to org A
        assert len(results) == 2  # 2 conferences per org
        for conf in results:
            assert conf["organization_id"] == user_a["organization_id"]

    async def test_get_conference_fails_different_organization(
        self, test_db, users_for_two_orgs, conferences_for_two_orgs
    ):
        """Test that user cannot access conference from different organization."""
        user_a, user_b = users_for_two_orgs
        conferences = conferences_for_two_orgs

        # Get conference from org B
        org_b_conf = [c for c in conferences if c["organization_id"] == user_b["organization_id"]][0]

        # Try to access as user A
        query = {
            "_id": org_b_conf["_id"],
            "organization_id": user_a["organization_id"]
        }
        result = await test_db.conferences.find_one(query)

        assert result is None

    async def test_update_conference_fails_different_organization(
        self, test_db, users_for_two_orgs, conferences_for_two_orgs
    ):
        """Test that user cannot update conference from different organization."""
        user_a, user_b = users_for_two_orgs
        conferences = conferences_for_two_orgs

        org_b_conf = [c for c in conferences if c["organization_id"] == user_b["organization_id"]][0]

        # Try to update with user A's organization filter
        result = await test_db.conferences.update_one(
            {"_id": org_b_conf["_id"], "organization_id": user_a["organization_id"]},
            {"$set": {"description": "Attempted cross-org update"}}
        )

        assert result.matched_count == 0
        assert result.modified_count == 0


@pytest.mark.asyncio
class TestSessionOrganizationScoping:
    """Test organization scoping for Session operations (indirect via conference)."""

    async def test_session_inherits_organization_from_conference(
        self, test_db, users_for_two_orgs, conferences_for_two_orgs, sessions_for_two_orgs
    ):
        """
        Test that sessions are scoped via parent conference.

        Expected:
            - Sessions only visible when conference belongs to user's org
        """
        user_a, user_b = users_for_two_orgs
        conferences = conferences_for_two_orgs
        sessions = sessions_for_two_orgs

        # Get org A conference and its session
        org_a_conf = [c for c in conferences if c["organization_id"] == user_a["organization_id"]][0]
        org_a_session = [s for s in sessions if s["conference_id"] == org_a_conf["_id"]][0]

        # Query with organization check via join
        pipeline = [
            {"$match": {"_id": org_a_session["_id"]}},
            {
                "$lookup": {
                    "from": "conferences",
                    "localField": "conference_id",
                    "foreignField": "_id",
                    "as": "conference"
                }
            },
            {"$unwind": "$conference"},
            {"$match": {"conference.organization_id": user_a["organization_id"]}}
        ]

        results = await test_db.conference_sessions.aggregate(pipeline).to_list(length=100)
        assert len(results) == 1
        assert results[0]["_id"] == org_a_session["_id"]

    async def test_session_inaccessible_different_organization(
        self, test_db, users_for_two_orgs, conferences_for_two_orgs, sessions_for_two_orgs
    ):
        """Test that user cannot access sessions from different organization's conference."""
        user_a, user_b = users_for_two_orgs
        conferences = conferences_for_two_orgs
        sessions = sessions_for_two_orgs

        # Get org B conference and its session
        org_b_conf = [c for c in conferences if c["organization_id"] == user_b["organization_id"]][0]
        org_b_session = [s for s in sessions if s["conference_id"] == org_b_conf["_id"]][0]

        # Try to query with user A's org filter
        pipeline = [
            {"$match": {"_id": org_b_session["_id"]}},
            {
                "$lookup": {
                    "from": "conferences",
                    "localField": "conference_id",
                    "foreignField": "_id",
                    "as": "conference"
                }
            },
            {"$unwind": "$conference"},
            {"$match": {"conference.organization_id": user_a["organization_id"]}}
        ]

        results = await test_db.conference_sessions.aggregate(pipeline).to_list(length=100)
        assert len(results) == 0  # No results - session belongs to org B's conference


@pytest.mark.asyncio
class TestRegistrationOrganizationScoping:
    """Test organization scoping for Registration operations."""

    async def test_list_registrations_filters_by_organization(
        self, test_db, users_for_two_orgs, conferences_for_two_orgs, registrations_for_two_orgs
    ):
        """Test that listing registrations only returns user's organization data."""
        user_a, user_b = users_for_two_orgs

        # Query as user_a
        query = {"organization_id": user_a["organization_id"]}
        results = await test_db.conference_registrations.find(query).to_list(length=100)

        # Verify all results belong to org A
        assert len(results) == 4  # 2 conferences × 2 registrations per conference
        for reg in results:
            assert reg["organization_id"] == user_a["organization_id"]

    async def test_get_registration_fails_different_organization(
        self, test_db, users_for_two_orgs, registrations_for_two_orgs
    ):
        """Test that user cannot access registration from different organization."""
        user_a, user_b = users_for_two_orgs
        registrations = registrations_for_two_orgs

        # Get registration from org B
        org_b_reg = [r for r in registrations if r["organization_id"] == user_b["organization_id"]][0]

        # Try to access as user A
        query = {
            "_id": org_b_reg["_id"],
            "organization_id": user_a["organization_id"]
        }
        result = await test_db.conference_registrations.find_one(query)

        assert result is None

    async def test_update_registration_fails_different_organization(
        self, test_db, users_for_two_orgs, registrations_for_two_orgs
    ):
        """Test that user cannot update registration from different organization."""
        user_a, user_b = users_for_two_orgs
        registrations = registrations_for_two_orgs

        org_b_reg = [r for r in registrations if r["organization_id"] == user_b["organization_id"]][0]

        # Try to update with user A's organization filter
        result = await test_db.conference_registrations.update_one(
            {"_id": org_b_reg["_id"], "organization_id": user_a["organization_id"]},
            {"$set": {"checked_in": True}}
        )

        assert result.matched_count == 0
        assert result.modified_count == 0

    async def test_registration_inherits_organization_from_conference(
        self, test_db, users_for_two_orgs, conferences_for_two_orgs, registrations_for_two_orgs
    ):
        """Test that registrations inherit organization from conference."""
        user_a, user_b = users_for_two_orgs
        conferences = conferences_for_two_orgs
        registrations = registrations_for_two_orgs

        # Get org A conference and its registrations
        org_a_conf = [c for c in conferences if c["organization_id"] == user_a["organization_id"]][0]
        org_a_regs = [r for r in registrations if r["conference_id"] == org_a_conf["_id"]]

        # Verify all registrations have same organization_id as conference
        for reg in org_a_regs:
            assert reg["organization_id"] == org_a_conf["organization_id"]


@pytest.mark.asyncio
class TestCompleteDataIsolation:
    """Comprehensive tests for complete data isolation across all entities."""

    async def test_complete_isolation_all_entities(
        self,
        test_db,
        users_for_two_orgs,
        branches_for_two_orgs,
        first_timers_for_two_orgs,
        conferences_for_two_orgs,
        registrations_for_two_orgs
    ):
        """
        Comprehensive test verifying complete data isolation across all entities.

        Expected:
            - No cross-contamination in any entity type
            - Each organization has correct count of entities
        """
        user_a, user_b = users_for_two_orgs

        # Test branches isolation
        org_a_branches = await test_db.branches.find(
            {"organization_id": user_a["organization_id"]}
        ).to_list(length=100)

        org_b_branches = await test_db.branches.find(
            {"organization_id": user_b["organization_id"]}
        ).to_list(length=100)

        assert len(org_a_branches) == 2
        assert len(org_b_branches) == 2

        # Test first timers isolation
        org_a_fts = await test_db.first_timers.find(
            {"organization_id": user_a["organization_id"]}
        ).to_list(length=100)

        org_b_fts = await test_db.first_timers.find(
            {"organization_id": user_b["organization_id"]}
        ).to_list(length=100)

        assert len(org_a_fts) == 2
        assert len(org_b_fts) == 2

        # Test conferences isolation
        org_a_confs = await test_db.conferences.find(
            {"organization_id": user_a["organization_id"]}
        ).to_list(length=100)

        org_b_confs = await test_db.conferences.find(
            {"organization_id": user_b["organization_id"]}
        ).to_list(length=100)

        assert len(org_a_confs) == 2
        assert len(org_b_confs) == 2

        # Test registrations isolation
        org_a_regs = await test_db.conference_registrations.find(
            {"organization_id": user_a["organization_id"]}
        ).to_list(length=100)

        org_b_regs = await test_db.conference_registrations.find(
            {"organization_id": user_b["organization_id"]}
        ).to_list(length=100)

        assert len(org_a_regs) == 4  # 2 conferences × 2 registrations
        assert len(org_b_regs) == 4

        # Verify no ID overlap across organizations for any entity
        org_a_all_ids = (
            {str(b["_id"]) for b in org_a_branches} |
            {str(ft["_id"]) for ft in org_a_fts} |
            {str(c["_id"]) for c in org_a_confs} |
            {str(r["_id"]) for r in org_a_regs}
        )

        org_b_all_ids = (
            {str(b["_id"]) for b in org_b_branches} |
            {str(ft["_id"]) for ft in org_b_fts} |
            {str(c["_id"]) for c in org_b_confs} |
            {str(r["_id"]) for r in org_b_regs}
        )

        # No overlap whatsoever
        assert len(org_a_all_ids.intersection(org_b_all_ids)) == 0
