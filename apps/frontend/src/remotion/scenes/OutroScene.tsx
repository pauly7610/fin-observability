import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';

const links = [
  { icon: '🌐', label: 'Live App', url: 'fin-observability-production.up.railway.app' },
  { icon: '📊', label: 'Grafana', url: 'pauly7610.grafana.net' },
  { icon: '🔌', label: 'MCP Server', url: '/mcp' },
];

export const OutroScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleOpacity = interpolate(frame, [0, 25], [0, 1], { extrapolateRight: 'clamp' });
  const titleY = spring({ frame, fps, from: -20, to: 0, durationInFrames: 25 });

  const taglineOpacity = interpolate(frame, [25, 45], [0, 1], { extrapolateRight: 'clamp' });

  const getLinkAnimation = (index: number) => {
    const startFrame = 50 + index * 18;
    const opacity = interpolate(frame, [startFrame, startFrame + 15], [0, 1], { extrapolateRight: 'clamp' });
    const scale = spring({ frame: frame - startFrame, fps, from: 0.9, to: 1, durationInFrames: 15 });
    return { opacity, scale };
  };

  const badgeOpacity = interpolate(frame, [110, 130], [0, 1], { extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill
      style={{
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)',
        justifyContent: 'center',
        alignItems: 'center',
        fontFamily: 'system-ui, -apple-system, sans-serif',
      }}
    >
      {/* Animated background */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `
            radial-gradient(circle at 20% 50%, rgba(59, 130, 246, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 80% 50%, rgba(139, 92, 246, 0.1) 0%, transparent 50%)
          `,
        }}
      />

      {/* Title */}
      <h1
        style={{
          fontSize: 48,
          fontWeight: 800,
          color: 'white',
          margin: 0,
          opacity: titleOpacity,
          transform: `translateY(${titleY}px)`,
          textAlign: 'center',
        }}
      >
        Financial AI Observability
      </h1>

      {/* Tagline */}
      <p
        style={{
          fontSize: 24,
          color: '#94a3b8',
          margin: '16px 0 36px',
          opacity: taglineOpacity,
          textAlign: 'center',
        }}
      >
        Production. Open Source. MCP-ready.
      </p>

      {/* Links */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 14,
          marginBottom: 36,
          alignItems: 'center',
        }}
      >
        {links.map((link, index) => {
          const { opacity, scale } = getLinkAnimation(index);
          return (
            <div
              key={link.url}
              style={{
                opacity,
                transform: `scale(${scale})`,
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '14px 28px',
                backgroundColor: 'rgba(30, 41, 59, 0.8)',
                borderRadius: 12,
                border: '1px solid rgba(148, 163, 184, 0.2)',
                minWidth: 400,
              }}
            >
              <span style={{ fontSize: 24 }}>{link.icon}</span>
              <span style={{ color: '#94a3b8', fontSize: 14, width: 90 }}>{link.label}</span>
              <span style={{ color: '#60a5fa', fontSize: 14, fontFamily: 'monospace' }}>
                {link.url}
              </span>
            </div>
          );
        })}
      </div>

      {/* GitHub badge */}
      <div
        style={{
          opacity: badgeOpacity,
          display: 'flex',
          gap: 16,
          alignItems: 'center',
        }}
      >
        <div
          style={{
            padding: '10px 20px',
            backgroundColor: 'rgba(30, 41, 59, 0.9)',
            borderRadius: 8,
            border: '1px solid rgba(148, 163, 184, 0.2)',
          }}
        >
          <span style={{ color: '#94a3b8', fontSize: 14 }}>GitHub</span>
          <span style={{ color: '#f1f5f9', fontSize: 14, fontWeight: 600, marginLeft: 8 }}>
            pauly7610/fin-observability
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};
