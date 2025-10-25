#!/usr/bin/env python3
"""
psycopg2 to psycopg3 Migration Helper Script

This script analyzes your codebase and provides a migration report
for upgrading from psycopg2 to psycopg3.

Usage:
    python3 migrate_to_psycopg3.py --analyze    # Analyze only
    python3 migrate_to_psycopg3.py --migrate    # Perform migration
    python3 migrate_to_psycopg3.py --rollback   # Rollback changes
"""

import os
import re
import sys
import shutil
from pathlib import Path
from datetime import datetime

class Psycopg3Migrator:
    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.backup_dir = self.root_dir / f"migration_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.stats = {
            'files_found': 0,
            'files_modified': 0,
            'imports_updated': 0,
            'cursor_factory_updated': 0,
            'execute_values_found': 0,
            'errors_updated': 0
        }
        
    def find_python_files(self):
        """Find all Python files with psycopg2 imports"""
        python_files = []
        for root, dirs, files in os.walk(self.root_dir):
            # Skip backup and cache directories
            dirs[:] = [d for d in dirs if d not in ['__pycache__', 'migration_backup', '.git', 'venv']]
            
            for file in files:
                if file.endswith('.py'):
                    filepath = Path(root) / file
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if 'psycopg2' in content:
                                python_files.append(filepath)
                                self.stats['files_found'] += 1
                    except Exception as e:
                        print(f"⚠️  Error reading {filepath}: {e}")
        
        return python_files
    
    def analyze_file(self, filepath):
        """Analyze a single file for migration needs"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        issues = []
        
        # Check for imports
        if re.search(r'import psycopg\b', content):
            issues.append("✓ Standard psycopg2 import")
        
        if re.search(r'from psycopg.rows import dict_row', content):
            issues.append("✓ RealDictCursor import (needs update)")
        
        if re.search(r'# MIGRATION TODO: execute_values needs manual migration to executemany
# from psycopg2.extras import execute_values', content):
            issues.append("⚠️  execute_values import (manual migration needed)")
            self.stats['execute_values_found'] += 1
        
        # Check for cursor factory usage
        if re.search(r'cursor_factory\s*=\s*RealDictCursor', content):
            issues.append("✓ cursor_factory usage (needs update)")
        
        # Check for error handling
        if re.search(r'psycopg2\.(Error|DatabaseError|IntegrityError)', content):
            issues.append("✓ Error handling (needs update)")
        
        # Check for execute_values calls
        execute_values_calls = re.findall(r'execute_values\([^)]+\)', content)
        if execute_values_calls:
            issues.append(f"⚠️  {len(execute_values_calls)} execute_values() calls found")
        
        return issues
    
    def create_backup(self):
        """Create backup of files before migration"""
        print(f"\n📦 Creating backup in {self.backup_dir}...")
        self.backup_dir.mkdir(exist_ok=True)
        
        for filepath in self.find_python_files():
            rel_path = filepath.relative_to(self.root_dir)
            backup_file = self.backup_dir / rel_path
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(filepath, backup_file)
        
        print(f"✅ Backup created: {len(list(self.backup_dir.rglob('*.py')))} files backed up")
    
    def migrate_file(self, filepath):
        """Migrate a single file from psycopg2 to psycopg3"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        modified = False
        
        # 1. Update import statements
        if 'import psycopg' in content:
            content = re.sub(r'\bimport psycopg2\b', 'import psycopg', content)
            self.stats['imports_updated'] += 1
            modified = True
        
        # 2. Update RealDictCursor imports
        if 'from psycopg.rows import dict_row' in content:
            content = content.replace(
                'from psycopg.rows import dict_row',
                'from psycopg.rows import dict_row'
            )
            modified = True
        
        # 3. Update cursor_factory to row_factory
        if 'row_factory=dict_row' in content:
            content = content.replace('row_factory=dict_row', 'row_factory=dict_row')
            self.stats['cursor_factory_updated'] += 1
            modified = True
        
        # 4. Update error handling
        error_patterns = [
            (r'\bpsycopg2\.Error\b', 'psycopg.Error'),
            (r'\bpsycopg2\.DatabaseError\b', 'psycopg.DatabaseError'),
            (r'\bpsycopg2\.IntegrityError\b', 'psycopg.IntegrityError'),
            (r'\bpsycopg2\.OperationalError\b', 'psycopg.OperationalError'),
        ]
        
        for pattern, replacement in error_patterns:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                self.stats['errors_updated'] += 1
                modified = True
        
        # 5. Comment out execute_values imports (needs manual migration)
        if '# MIGRATION TODO: execute_values needs manual migration to executemany
# from psycopg2.extras import execute_values' in content:
            content = content.replace(
                '# MIGRATION TODO: execute_values needs manual migration to executemany
# from psycopg2.extras import execute_values',
                '# MIGRATION TODO: execute_values needs manual migration to executemany\n# # MIGRATION TODO: execute_values needs manual migration to executemany
# from psycopg2.extras import execute_values'
            )
            modified = True
        
        if modified:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            self.stats['files_modified'] += 1
            return True
        
        return False
    
    def analyze(self):
        """Analyze the codebase for migration"""
        print("\n" + "="*70)
        print("🔍 ANALYZING CODEBASE FOR PSYCOPG2 → PSYCOPG3 MIGRATION")
        print("="*70)
        
        files = self.find_python_files()
        
        if not files:
            print("\n✅ No files with psycopg2 imports found!")
            return
        
        print(f"\n📊 Found {len(files)} files using psycopg2:\n")
        
        for filepath in files:
            rel_path = filepath.relative_to(self.root_dir)
            print(f"\n📄 {rel_path}")
            issues = self.analyze_file(filepath)
            for issue in issues:
                print(f"   {issue}")
        
        print("\n" + "="*70)
        print("📊 MIGRATION SUMMARY")
        print("="*70)
        print(f"Files with psycopg2:        {self.stats['files_found']}")
        print(f"execute_values usage:       {self.stats['execute_values_found']} (needs manual migration)")
        print("\n⚠️  MANUAL MIGRATION REQUIRED FOR:")
        print("   - execute_values() calls → executemany()")
        print("   - Bulk insert operations")
        print("   - Custom cursor classes")
        
    def migrate(self):
        """Perform the migration"""
        print("\n" + "="*70)
        print("🚀 MIGRATING PSYCOPG2 → PSYCOPG3")
        print("="*70)
        
        # Create backup first
        self.create_backup()
        
        files = self.find_python_files()
        
        print(f"\n🔄 Migrating {len(files)} files...\n")
        
        for filepath in files:
            rel_path = filepath.relative_to(self.root_dir)
            if self.migrate_file(filepath):
                print(f"✅ {rel_path}")
            else:
                print(f"⏭️  {rel_path} (no changes needed)")
        
        print("\n" + "="*70)
        print("📊 MIGRATION RESULTS")
        print("="*70)
        print(f"Files analyzed:             {self.stats['files_found']}")
        print(f"Files modified:             {self.stats['files_modified']}")
        print(f"Import statements updated:  {self.stats['imports_updated']}")
        print(f"Cursor factories updated:   {self.stats['cursor_factory_updated']}")
        print(f"Error handlers updated:     {self.stats['errors_updated']}")
        print(f"execute_values found:       {self.stats['execute_values_found']}")
        
        print("\n⚠️  NEXT STEPS:")
        print("1. Review files with execute_values() calls")
        print("2. Manually migrate execute_values to executemany")
        print("3. Update requirements.txt:")
        print("   - Remove: psycopg2-binary==2.9.7")
        print("   - Add: psycopg[binary,pool]==3.2.1")
        print("4. Test thoroughly before deploying")
        print(f"5. Backup location: {self.backup_dir}")
        
    def rollback(self):
        """Rollback migration using most recent backup"""
        backups = sorted(self.root_dir.glob('migration_backup_*'))
        
        if not backups:
            print("❌ No backup found to rollback!")
            return
        
        latest_backup = backups[-1]
        print(f"\n🔙 Rolling back from: {latest_backup}")
        
        backup_files = list(latest_backup.rglob('*.py'))
        
        for backup_file in backup_files:
            rel_path = backup_file.relative_to(latest_backup)
            target_file = self.root_dir / rel_path
            shutil.copy2(backup_file, target_file)
            print(f"✅ Restored {rel_path}")
        
        print(f"\n✅ Rollback complete: {len(backup_files)} files restored")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    action = sys.argv[1]
    root_dir = sys.argv[2] if len(sys.argv) > 2 else "."
    
    migrator = Psycopg3Migrator(root_dir)
    
    if action == '--analyze':
        migrator.analyze()
    elif action == '--migrate':
        confirm = input("\n⚠️  This will modify your files. Continue? (yes/no): ")
        if confirm.lower() == 'yes':
            migrator.migrate()
        else:
            print("❌ Migration cancelled")
    elif action == '--rollback':
        confirm = input("\n⚠️  This will restore files from backup. Continue? (yes/no): ")
        if confirm.lower() == 'yes':
            migrator.rollback()
        else:
            print("❌ Rollback cancelled")
    else:
        print(f"❌ Unknown action: {action}")
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
