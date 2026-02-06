import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';

export const IntroScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleOpacity = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: 'clamp' });
  const titleY = spring({ frame, fps, from: -50, to: 0, durationInFrames: 40 });
  
  const subtitleOpacity = interpolate(frame, [40, 70], [0, 1], { extrapolateRight: 'clamp' });
  const subtitleY = spring({ frame: frame - 40, fps, from: 30, to: 0, durationInFrames: 30 });

  const badgeOpacity = interpolate(frame, [80, 110], [0, 1], { extrapolateRight: 'clamp' });
  const badgeScale = spring({ frame: frame - 80, fps, from: 0.5, to: 1, durationInFrames: 30 });

  return (
    <AbsoluteFill
      style={{
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)',
        justifyContent: 'center',
        alignItems: 'center',
        fontFamily: 'system-ui, -apple-system, sans-serif',
      }}
    >
      {/* Animated background grid */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `
            linear-gradient(rgba(59, 130, 246, 0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(59, 130, 246, 0.1) 1px, transparent 1px)
          `,
          backgroundSize: '50px 50px',
          opacity: 0.5,
        }}
      />

      {/* Logo/Icon */}
      <div
        style={{
          opacity: titleOpacity,
          transform: `translateY(${titleY}px)`,
          marginBottom: 20,
        }}
      >
        <div
          style={{
            fontSize: 80,
            marginBottom: 10,
          }}
        >
          🤖
        </div>
      </div>

      {/* Title */}
      <h1
        style={{
          fontSize: 72,
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

      {/* Subtitle */}
      <p
        style={{
          fontSize: 32,
          color: '#94a3b8',
          margin: '20px 0 40px',
          opacity: subtitleOpacity,
          transform: `translateY(${subtitleY}px)`,
          textAlign: 'center',
        }}
      >
        Autonomous Compliance Monitoring & Incident Response
      </p>

      {/* Badges */}
      <div
        style={{
          display: 'flex',
          gap: 16,
          opacity: badgeOpacity,
          transform: `scale(${badgeScale})`,
        }}
      >
        {['FINRA 4511', 'SEC 17a-4', 'Basel III'].map((badge) => (
          <div
            key={badge}
            style={{
              padding: '12px 24px',
              backgroundColor: 'rgba(59, 130, 246, 0.2)',
              border: '2px solid rgba(59, 130, 246, 0.5)',
              borderRadius: 8,
              color: '#60a5fa',
              fontSize: 18,
              fontWeight: 600,
            }}
          >
            {badge}
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};
