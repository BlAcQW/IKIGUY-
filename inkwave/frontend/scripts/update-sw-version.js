/**
 * Update Service Worker Version
 * Simple script to update SW version during build
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const version = Date.now().toString();
console.log(`Service worker version: ${version}`);

// Write version to a file that can be imported
const versionFile = path.join(__dirname, '..', 'public', 'sw-version.js');
fs.writeFileSync(versionFile, `self.SW_VERSION = "${version}";`);

console.log('Service worker version updated successfully');
