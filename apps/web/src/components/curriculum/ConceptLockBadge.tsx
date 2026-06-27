interface ConceptLockBadgeProps {
  isUnlocked: boolean
}

/**
 * Small pill showing whether a concept is unlocked or locked (AC 4).
 */
export function ConceptLockBadge({ isUnlocked }: ConceptLockBadgeProps) {
  return (
    <span
      aria-label={isUnlocked ? 'Concept unlocked' : 'Concept locked'}
      className={
        isUnlocked
          ? 'inline-flex items-center gap-1 rounded-full bg-green-50 px-2.5 py-0.5 text-xs font-medium text-green-700'
          : 'inline-flex items-center gap-1 rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-500'
      }
    >
      {isUnlocked ? 'Unlocked' : 'Locked'}
    </span>
  )
}
