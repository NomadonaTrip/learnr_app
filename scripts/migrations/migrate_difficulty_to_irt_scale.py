#!/usr/bin/env python3
"""
Migration script: Convert difficulty values from 0.0-1.0 scale to IRT b-parameter (-3 to +3).

This script:
1. Reads existing difficulty values from the questions table
2. Converts them to standard IRT b-parameter scale
3. Optionally adds difficulty_label column for human readability
4. Updates the database constraint

Usage:
    # Dry run (preview changes without applying)
    python scripts/migrations/migrate_difficulty_to_irt_scale.py --dry-run

    # Apply migration
    python scripts/migrations/migrate_difficulty_to_irt_scale.py --apply

    # Rollback to 0.0-1.0 scale
    python scripts/migrations/migrate_difficulty_to_irt_scale.py --rollback
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Literal

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# IRT scale mappings
# Original 0.0-1.0 values from import script:
# Easy=0.3, Medium=0.5, Hard=0.7

# New IRT b-parameter scale (-3 to +3):
# Easy=-1.5, Medium=0.0, Hard=+1.5

LEGACY_TO_IRT_MAP = {
    # Discrete legacy values -> IRT tier centers
    0.3: -1.5,   # Easy -> Easy tier center
    0.5: 0.0,    # Medium -> Medium tier center
    0.7: 1.5,    # Hard -> Hard tier center
}

# For values not in the discrete map, use linear transformation
def legacy_to_irt(legacy_value: float) -> float:
    """Convert 0.0-1.0 legacy difficulty to IRT b-parameter (-3 to +3).

    Uses discrete mapping for known values, linear transformation otherwise.

    Args:
        legacy_value: Difficulty on 0.0-1.0 scale

    Returns:
        Difficulty on IRT b-parameter scale (-3 to +3)
    """
    # Check for known discrete values (with small tolerance)
    for legacy, irt in LEGACY_TO_IRT_MAP.items():
        if abs(legacy_value - legacy) < 0.01:
            return irt

    # Linear transformation: maps [0, 1] -> [-3, 3]
    # Formula: b = (d - 0.5) * 6
    return (legacy_value - 0.5) * 6


def irt_to_legacy(irt_value: float) -> float:
    """Convert IRT b-parameter (-3 to +3) back to legacy 0.0-1.0 scale.

    Args:
        irt_value: Difficulty on IRT b-parameter scale

    Returns:
        Difficulty on 0.0-1.0 scale
    """
    # Inverse of linear transformation: d = (b / 6) + 0.5
    return (irt_value / 6) + 0.5


def classify_difficulty_label(irt_value: float) -> str:
    """Classify IRT b-parameter into human-readable label.

    Args:
        irt_value: Difficulty on IRT scale (-3 to +3)

    Returns:
        'Easy', 'Medium', or 'Hard'
    """
    if irt_value < -1.0:
        return 'Easy'
    elif irt_value <= 1.0:
        return 'Medium'
    else:
        return 'Hard'


async def get_database_url() -> str:
    """Get database URL from environment or config."""
    import os
    return os.environ.get(
        'DATABASE_URL',
        'postgresql+asyncpg://learnr:learnr@localhost:5432/learnr'
    )


async def preview_migration(session: AsyncSession) -> dict:
    """Preview what the migration will do without applying changes.

    Returns:
        Statistics about the migration
    """
    result = await session.execute(
        text("SELECT id, difficulty FROM questions ORDER BY difficulty")
    )
    rows = result.fetchall()

    stats = {
        'total_questions': len(rows),
        'by_legacy_value': {},
        'conversions': [],
    }

    for row in rows:
        question_id, legacy_diff = row
        irt_diff = legacy_to_irt(legacy_diff)
        label = classify_difficulty_label(irt_diff)

        # Count by legacy value
        legacy_key = f"{legacy_diff:.2f}"
        if legacy_key not in stats['by_legacy_value']:
            stats['by_legacy_value'][legacy_key] = {
                'count': 0,
                'irt_value': irt_diff,
                'label': label,
            }
        stats['by_legacy_value'][legacy_key]['count'] += 1

        # Store sample conversions (first 5)
        if len(stats['conversions']) < 5:
            stats['conversions'].append({
                'id': str(question_id),
                'legacy': legacy_diff,
                'irt': irt_diff,
                'label': label,
            })

    return stats


async def apply_migration(session: AsyncSession, dry_run: bool = False) -> dict:
    """Apply the difficulty scale migration.

    Args:
        session: Database session
        dry_run: If True, preview only without applying

    Returns:
        Migration statistics
    """
    stats = await preview_migration(session)

    if dry_run:
        return stats

    # Step 1: Add difficulty_label column if it doesn't exist
    try:
        await session.execute(text("""
            ALTER TABLE questions
            ADD COLUMN IF NOT EXISTS difficulty_label VARCHAR(10)
        """))
        print("Added difficulty_label column")
    except Exception as e:
        print(f"Note: difficulty_label column may already exist: {e}")

    # Step 2: Drop the old constraint
    try:
        await session.execute(text("""
            ALTER TABLE questions
            DROP CONSTRAINT IF EXISTS ck_questions_difficulty_range
        """))
        print("Dropped old difficulty constraint")
    except Exception as e:
        print(f"Note: Old constraint may not exist: {e}")

    # Step 3: Update all difficulty values and labels
    result = await session.execute(
        text("SELECT id, difficulty FROM questions")
    )
    rows = result.fetchall()

    updated_count = 0
    for row in rows:
        question_id, legacy_diff = row
        irt_diff = legacy_to_irt(legacy_diff)
        label = classify_difficulty_label(irt_diff)

        await session.execute(
            text("""
                UPDATE questions
                SET difficulty = :irt_diff,
                    difficulty_label = :label
                WHERE id = :id
            """),
            {'id': question_id, 'irt_diff': irt_diff, 'label': label}
        )
        updated_count += 1

    print(f"Updated {updated_count} questions")

    # Step 4: Add the new constraint
    await session.execute(text("""
        ALTER TABLE questions
        ADD CONSTRAINT ck_questions_difficulty_range
        CHECK (difficulty >= -3.0 AND difficulty <= 3.0)
    """))
    print("Added new IRT difficulty constraint (-3.0 to 3.0)")

    await session.commit()
    stats['updated_count'] = updated_count
    return stats


async def rollback_migration(session: AsyncSession) -> dict:
    """Rollback to the legacy 0.0-1.0 difficulty scale.

    Returns:
        Rollback statistics
    """
    # Step 1: Drop IRT constraint
    try:
        await session.execute(text("""
            ALTER TABLE questions
            DROP CONSTRAINT IF EXISTS ck_questions_difficulty_range
        """))
        print("Dropped IRT difficulty constraint")
    except Exception as e:
        print(f"Note: Constraint may not exist: {e}")

    # Step 2: Convert all values back to 0.0-1.0 scale
    result = await session.execute(
        text("SELECT id, difficulty FROM questions")
    )
    rows = result.fetchall()

    updated_count = 0
    for row in rows:
        question_id, irt_diff = row
        legacy_diff = irt_to_legacy(irt_diff)

        # Clamp to valid range
        legacy_diff = max(0.0, min(1.0, legacy_diff))

        await session.execute(
            text("""
                UPDATE questions
                SET difficulty = :legacy_diff
                WHERE id = :id
            """),
            {'id': question_id, 'legacy_diff': legacy_diff}
        )
        updated_count += 1

    print(f"Converted {updated_count} questions to legacy scale")

    # Step 3: Restore original constraint
    await session.execute(text("""
        ALTER TABLE questions
        ADD CONSTRAINT ck_questions_difficulty_range
        CHECK (difficulty >= 0.0 AND difficulty <= 1.0)
    """))
    print("Restored legacy difficulty constraint (0.0 to 1.0)")

    await session.commit()
    return {'updated_count': updated_count}


async def main():
    parser = argparse.ArgumentParser(
        description='Migrate difficulty values to IRT b-parameter scale'
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--dry-run', action='store_true',
                       help='Preview migration without applying changes')
    group.add_argument('--apply', action='store_true',
                       help='Apply the migration')
    group.add_argument('--rollback', action='store_true',
                       help='Rollback to legacy 0.0-1.0 scale')

    args = parser.parse_args()

    database_url = await get_database_url()
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        if args.dry_run:
            print("\n=== DRY RUN: Preview Migration ===\n")
            stats = await preview_migration(session)
            print(f"Total questions: {stats['total_questions']}")
            print("\nBy legacy difficulty value:")
            for legacy_val, info in sorted(stats['by_legacy_value'].items()):
                print(f"  {legacy_val} -> {info['irt_value']:+.1f} ({info['label']}): {info['count']} questions")
            print("\nSample conversions:")
            for conv in stats['conversions']:
                print(f"  {conv['id'][:8]}...: {conv['legacy']} -> {conv['irt']:+.2f} ({conv['label']})")

        elif args.apply:
            print("\n=== Applying IRT Scale Migration ===\n")
            confirm = input("This will modify the database. Continue? [y/N]: ")
            if confirm.lower() != 'y':
                print("Migration cancelled.")
                return
            stats = await apply_migration(session)
            print(f"\nMigration complete! Updated {stats.get('updated_count', 0)} questions.")

        elif args.rollback:
            print("\n=== Rolling Back to Legacy Scale ===\n")
            confirm = input("This will convert IRT values back to 0.0-1.0. Continue? [y/N]: ")
            if confirm.lower() != 'y':
                print("Rollback cancelled.")
                return
            stats = await rollback_migration(session)
            print(f"\nRollback complete! Converted {stats['updated_count']} questions.")

    await engine.dispose()


if __name__ == '__main__':
    asyncio.run(main())
