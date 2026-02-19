/**
 * Database Migration Script: tenant_id → organization_id
 *
 * This script adds organization_id field alongside existing tenant_id field
 * for backward compatibility during the migration period.
 *
 * Run with:
 * mongosh "mongodb://admin:aawwER4444%@127.0.0.1:27017/kasaai_core?authSource=admin" migrate_tenant_id_to_organization_id.js
 */

// Collections that need migration
const collectionsToMigrate = [
  'wallets',
  'payment_methods',
  'audiences',
  'analytics_data',
  'campaigns'
];

// Track migration results
const results = {
  success: [],
  errors: [],
  skipped: []
};

print('========================================');
print('Starting tenant_id → organization_id Migration');
print('========================================\n');

collectionsToMigrate.forEach(function(collName) {
  print(`\n📦 Processing collection: ${collName}`);

  try {
    // Check if collection exists
    const collectionExists = db.getCollectionNames().includes(collName);
    if (!collectionExists) {
      print(`  ⚠️  Collection does not exist, skipping`);
      results.skipped.push(collName);
      return;
    }

    // Count documents with tenant_id but without organization_id
    const needsMigration = db[collName].countDocuments({
      tenant_id: { $exists: true },
      organization_id: { $exists: false }
    });

    if (needsMigration === 0) {
      print(`  ✅ All documents already have organization_id, skipping`);
      results.skipped.push(collName);
      return;
    }

    print(`  📊 Found ${needsMigration} documents needing migration`);

    // Perform migration: Copy tenant_id to organization_id
    const updateResult = db[collName].updateMany(
      {
        tenant_id: { $exists: true },
        organization_id: { $exists: false }
      },
      [
        {
          $set: {
            organization_id: "$tenant_id",
            migrated_at: new Date(),
            migration_version: "1.0"
          }
        }
      ]
    );

    print(`  ✅ Migrated ${updateResult.modifiedCount} documents`);

    // Verify migration
    const remaining = db[collName].countDocuments({
      tenant_id: { $exists: true },
      organization_id: { $exists: false }
    });

    if (remaining > 0) {
      print(`  ⚠️  WARNING: ${remaining} documents still need migration`);
    } else {
      print(`  ✅ Verification passed - all documents migrated`);
    }

    // Show sample migrated document
    const sample = db[collName].findOne({
      organization_id: { $exists: true },
      tenant_id: { $exists: true }
    });

    if (sample) {
      print(`  📄 Sample document:`);
      print(`     tenant_id: ${sample.tenant_id}`);
      print(`     organization_id: ${sample.organization_id}`);
    }

    results.success.push({
      collection: collName,
      migrated: updateResult.modifiedCount,
      remaining: remaining
    });

  } catch (error) {
    print(`  ❌ Error migrating ${collName}: ${error.message}`);
    results.errors.push({
      collection: collName,
      error: error.message
    });
  }
});

// Print summary
print('\n========================================');
print('Migration Summary');
print('========================================\n');

print('✅ Successfully migrated collections:');
results.success.forEach(function(r) {
  print(`   - ${r.collection}: ${r.migrated} documents (${r.remaining} remaining)`);
});

if (results.skipped.length > 0) {
  print('\n⏭️  Skipped collections:');
  results.skipped.forEach(function(c) {
    print(`   - ${c}`);
  });
}

if (results.errors.length > 0) {
  print('\n❌ Errors:');
  results.errors.forEach(function(e) {
    print(`   - ${e.collection}: ${e.error}`);
  });
}

// Create indexes for organization_id
print('\n========================================');
print('Creating indexes for organization_id');
print('========================================\n');

const indexResults = [];

collectionsToMigrate.forEach(function(collName) {
  try {
    if (!db.getCollectionNames().includes(collName)) {
      return;
    }

    // Check if index already exists
    const indexes = db[collName].getIndexes();
    const hasOrgIndex = indexes.some(idx =>
      idx.key && idx.key.organization_id === 1
    );

    if (hasOrgIndex) {
      print(`  ⏭️  ${collName}: organization_id index already exists`);
      return;
    }

    // Create index
    db[collName].createIndex(
      { organization_id: 1 },
      { name: 'organization_id_1', background: true }
    );

    print(`  ✅ ${collName}: Created organization_id index`);
    indexResults.push({ collection: collName, status: 'created' });

  } catch (error) {
    print(`  ❌ ${collName}: Error creating index - ${error.message}`);
    indexResults.push({ collection: collName, status: 'error', error: error.message });
  }
});

// Final statistics
print('\n========================================');
print('Final Statistics');
print('========================================\n');

let totalMigrated = 0;
results.success.forEach(function(r) {
  totalMigrated += r.migrated;
});

print(`Total documents migrated: ${totalMigrated}`);
print(`Collections processed: ${collectionsToMigrate.length}`);
print(`Successful: ${results.success.length}`);
print(`Skipped: ${results.skipped.length}`);
print(`Errors: ${results.errors.length}`);
print(`Indexes created: ${indexResults.filter(r => r.status === 'created').length}`);

print('\n✅ Migration complete!\n');
