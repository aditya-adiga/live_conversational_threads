/**
 * ZoomLevelIndicator Component (Week 6)
 *
 * Visual indicator showing all 5 zoom levels with interactive navigation.
 * Displays current level, allows clicking to jump to any level.
 */

import PropTypes from 'prop-types';

export default function ZoomLevelIndicator({
  currentLevel,
  onLevelChange,
  isTransitioning,
  transitionDirection,
  showLabels = true,
  showDescription = true,
  orientation = 'horizontal', // 'horizontal' or 'vertical'
}) {
  const levels = [
    { level: 1, name: 'SENTENCE', icon: '•', color: '#ef4444' },
    { level: 2, name: 'TURN', icon: '••', color: '#f97316' },
    { level: 3, name: 'TOPIC', icon: '•••', color: '#eab308' },
    { level: 4, name: 'THEME', icon: '••••', color: '#22c55e' },
    { level: 5, name: 'ARC', icon: '•••••', color: '#3b82f6' },
  ];

  const currentLevelData = levels.find(l => l.level === currentLevel);

  const descriptions = {
    1: 'Individual sentences',
    2: 'Speaker turns',
    3: 'Topic segments',
    4: 'Major themes',
    5: 'Narrative arcs',
  };

  const handleLevelClick = (level) => {
    if (level !== currentLevel && !isTransitioning) {
      onLevelChange(level);
    }
  };

  const isHorizontal = orientation === 'horizontal';

  return (
    <div className={`flex ${isHorizontal ? 'flex-col' : 'flex-row'} gap-3`}>
      {/* Level Buttons */}
      <div className={`flex ${isHorizontal ? 'flex-row' : 'flex-col'} gap-2 items-center`}>
        {levels.map(({ level, name, icon, color }) => {
          const isCurrent = level === currentLevel;
          const isPast = isTransitioning && (
            (transitionDirection === 'in' && level > currentLevel) ||
            (transitionDirection === 'out' && level < currentLevel)
          );

          return (
            <button
              key={level}
              onClick={() => handleLevelClick(level)}
              disabled={isTransitioning}
              className={`
                relative flex flex-col items-center justify-center
                ${isHorizontal ? 'w-16 h-16' : 'w-14 h-14'}
                rounded-lg border-2 transition-all duration-300
                ${isCurrent
                  ? 'scale-110 shadow-lg'
                  : 'scale-100 hover:scale-105'
                }
                ${isTransitioning ? 'cursor-wait opacity-70' : 'cursor-pointer'}
              `}
              style={{
                borderColor: isCurrent ? color : '#d1d5db',
                background: isCurrent
                  ? `linear-gradient(135deg, ${color}20 0%, ${color}40 100%)`
                  : isPast
                  ? '#f3f4f6'
                  : 'white',
              }}
              title={`${name}: ${descriptions[level]}`}
            >
              {/* Level Number */}
              <span
                className={`text-lg font-bold ${
                  isCurrent ? 'text-gray-900' : 'text-gray-600'
                }`}
              >
                {level}
              </span>

              {/* Level Name */}
              {showLabels && (
                <span
                  className={`text-[8px] font-semibold uppercase tracking-wide ${
                    isCurrent ? 'text-gray-800' : 'text-gray-500'
                  }`}
                >
                  {name.substring(0, 4)}
                </span>
              )}

              {/* Active Indicator */}
              {isCurrent && (
                <div
                  className="absolute -top-1 -right-1 w-3 h-3 rounded-full animate-pulse"
                  style={{ backgroundColor: color }}
                />
              )}

              {/* Transition Animation */}
              {isTransitioning && isCurrent && (
                <div className="absolute inset-0 rounded-lg animate-pulse"
                  style={{
                    background: `linear-gradient(135deg, ${color}40 0%, transparent 100%)`,
                  }}
                />
              )}
            </button>
          );
        })}
      </div>

      {/* Current Level Info */}
      {showDescription && (
        <div className={`flex flex-col ${isHorizontal ? 'items-center' : 'items-start'} justify-center px-3 py-2 bg-white/90 rounded-lg border border-gray-200 shadow-sm`}>
          <div className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: currentLevelData?.color }}
            />
            <span className="text-sm font-bold text-gray-900">
              {currentLevelData?.name}
            </span>
            {isTransitioning && (
              <span className="text-xs text-gray-500 animate-pulse">
                {transitionDirection === 'in' ? '↗' : '↘'}
              </span>
            )}
          </div>
          <span className="text-xs text-gray-600 mt-0.5">
            {descriptions[currentLevel]}
          </span>
        </div>
      )}
    </div>
  );
}

ZoomLevelIndicator.propTypes = {
  currentLevel: PropTypes.number.isRequired,
  onLevelChange: PropTypes.func.isRequired,
  isTransitioning: PropTypes.bool,
  transitionDirection: PropTypes.oneOf(['in', 'out', 'none']),
  showLabels: PropTypes.bool,
  showDescription: PropTypes.bool,
  orientation: PropTypes.oneOf(['horizontal', 'vertical']),
};
