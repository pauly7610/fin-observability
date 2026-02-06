import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';

export const OutroScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const logoOpacity = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: 'clamp' });
  const logoScale = spring({ frame, fps, from: 0.8, to: 1, durationInFrames: 30 });

  const textOpacity = interpolate(frame, [30, 50], [0, 1], { extrapolateRight: 'clamp' });
  const textY = spring({ frame: frame - 30, fps, from: 20, to: 0, durationInFrames: 20 });

  const ctaOpacity = interpolate(frame, [60, 80], [0, 1], { extrapolateRight: 'clamp' });
  const ctaScale = spring({ frame: frame - 60, fps, from: 0.9, to: 1, durationInFrames: 20 });

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

      {/* Logo */}
      <div
        style={{
          opacity: logoOpacity,
          transform: `scale(${logoScale})`,
          marginBottom: 24,
        }}
      >
        <span style={{ fontSize: 100 }}>🤖</span>
      </div>

      {/* Title */}
      <h1
        style={{
          fontSize: 56,
          fontWeight: 800,
          color: 'white',
          margin: 0,
          opacity: textOpacity,
          transform: `translateY(${textY}px)`,
          textAlign: 'center',
        }}
      >
        Financial AI Observability
      </h1>

      {/* Tagline */}
      <p
        style={{
          fontSize: 28,
          color: '#94a3b8',
          margin: '16px 0 40px',
          opacity: textOpacity,
          transform: `translateY(${textY}px)`,
          textAlign: 'center',
        }}
      >
        Autonomous. Compliant. Auditable.
      </p>

      {/* Feature Pills */}
      <div
        style={{
          display: 'flex',
          gap: 16,
          opacity: ctaOpacity,
          transform: `scale(${ctaScale})`,
          marginBottom: 40,
        }}
      >
        {[
          { icon: '🔍', text: 'Anomaly Detection' },
          { icon: '�', text: 'SHAP Explainability' },
          { icon: '⚡', text: 'ONNX Inference' },
          { icon: '🔄', text: 'Auto-Retraining' },
          { icon: '�', text: 'OTel Observability' },
          { icon: '🚀', text: 'Railway Deploy' },
        ].map((feature) => (
          <div
            key={feature.text}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '12px 20px',
              backgroundColor: 'rgba(59, 130, 246, 0.1)',
              border: '1px solid rgba(59, 130, 246, 0.3)',
              borderRadius: 24,
            }}
          >
            <span style={{ fontSize: 20 }}>{feature.icon}</span>
            <span style={{ color: '#93c5fd', fontSize: 16, fontWeight: 500 }}>{feature.text}</span>
          </div>
        ))}
      </div>

      {/* CTA */}
      <div
        style={{
          opacity: ctaOpacity,
          transform: `scale(${ctaScale})`,
        }}
      >
        <div
          style={{
            padding: '16px 48px',
            background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
            borderRadius: 12,
            boxShadow: '0 4px 20px rgba(59, 130, 246, 0.4)',
          }}
        >
          <span style={{ color: 'white', fontSize: 24, fontWeight: 600 }}>
            Get Started Today →
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};
