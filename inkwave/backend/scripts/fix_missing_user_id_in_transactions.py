#!/usr/bin/env python3
"""
Script to fix old transactions missing user_id field.

This script:
1. Finds all transactions without user_id
2. Looks up the wallet to get user_id
3. Updates the transaction with the correct user_id

Author: KasaAI Team
Date: 2025-12-06
"""

import asyncio
import os
import sys
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
backend_dir = Path(__file__).parent.parent
env_file = backend_dir / ".env"
if env_file.exists():
    load_dotenv(dotenv_path=env_file, override=True)


async def fix_missing_user_ids():
    """
    Fix transactions missing user_id field.
    """
    # Get MongoDB connection from environment
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    database_name = os.getenv("MONGODB_DATABASE", "inkwave")

    print(f"Connecting to MongoDB: {database_name}")
    client = AsyncIOMotorClient(mongodb_uri)
    db = client[database_name]

    # Find all transactions without user_id
    missing_user_id = await db.transactions.count_documents({"user_id": {"$exists": False}})
    print(f"\nFound {missing_user_id} transactions without user_id")

    if missing_user_id == 0:
        print("No transactions to fix!")
        return

    # Process each transaction
    cursor = db.transactions.find({"user_id": {"$exists": False}})
    fixed_count = 0
    error_count = 0

    async for transaction in cursor:
        transaction_id = transaction.get("id", transaction.get("_id"))
        wallet_id = transaction.get("wallet_id")

        if not wallet_id:
            print(f"❌ Transaction {transaction_id} has no wallet_id - skipping")
            error_count += 1
            continue

        # Look up wallet to get user_id
        wallet = await db.wallets.find_one({"id": wallet_id})

        if not wallet:
            print(f"❌ Wallet {wallet_id} not found for transaction {transaction_id} - skipping")
            error_count += 1
            continue

        user_id = wallet.get("user_id")
        if not user_id:
            print(f"❌ Wallet {wallet_id} has no user_id - skipping")
            error_count += 1
            continue

        # Update transaction with user_id
        result = await db.transactions.update_one(
            {"_id": transaction["_id"]},
            {"$set": {"user_id": user_id}}
        )

        if result.modified_count > 0:
            print(f"✅ Fixed transaction {transaction_id} - added user_id: {user_id}")
            fixed_count += 1
        else:
            print(f"⚠️  Transaction {transaction_id} not updated")
            error_count += 1

    print(f"\n{'='*60}")
    print(f"Migration complete!")
    print(f"  Fixed: {fixed_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total: {fixed_count + error_count}")
    print(f"{'='*60}")

    # Close connection
    client.close()


if __name__ == "__main__":
    asyncio.run(fix_missing_user_ids())
