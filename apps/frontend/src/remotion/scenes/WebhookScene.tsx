import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';

const channels = [
  {
    name: 'Inbound',
    desc: 'Plaid, Stripe, bank feeds',
    icon: '↓',
    color: '#3b82f6',
  },
  {
    name: 'SSE Stream',
    desc: 'Real-time decisions',
    icon: '⚡',
    color: '#8b5cf6',
  },
  {
    name: 'Outbound Callbacks',
    desc: '3x retry + DLQ',
    icon: '→',
    color: '#eab308',
  },
  {
    name: 'Scheduled Pull',
    desc: 'Poll external APIs',
    icon: '⏰',
    color: '#22c55e',
  },
];

export const WebhookScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const headerOpacity = interpolate(frame, [0, 25], [0, 1], { extrapolateRight: 'clamp' });
  const taglineOpacity = interpolate(frame, [25, 45], [0, 1], { extrapolateRight: 'clamp' });

  const getChannelAnimation = (index: number) => {
    const startFrame = 55 + index * 18;
    const opacity = interpolate(frame, [startFrame, startFrame + 15], [0, 1], { extrapolateRight: 'clamp' });
    const scale = spring({ frame: frame - startFrame, fps, from: 0.85, to: 1, durationInFrames: 18 });
    return { opacity, scale };
  };

  const dlqOpacity = interpolate(frame, [140, 160], [0, 1], { extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill
      style={{
        background: 'linear-gradient(180deg, #0f172a 0%, #1e293b 100%)',
        padding: 50,
        fontFamily: 'system-ui, -apple-system, sans-serif',
      }}
    >
      {/* Header */}
      <div style={{ opacity: headerOpacity, marginBottom: 12 }}>
        <h2 style={{ fontSize: 32, color: 'white', margin: 0, fontWeight: 700 }}>
          4 Ways to Integrate
        </h2>
      </div>
      <div style={{ opacity: taglineOpacity, marginBottom: 36 }}>
        <p style={{ fontSize: 18, color: '#94a3b8', margin: 0 }}>
          Webhooks, SSE, callbacks, scheduled pull. Dead letter queue included.
        </p>
      </div>

      {/* Channel grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 20,
          marginBottom: 28,
        }}
      >
        {channels.map((ch, index) => {
          const { opacity, scale } = getChannelAnimation(index);
          return (
            <div
              key={ch.name}
              style={{
                opacity,
                transform: `scale(${scale})`,
                backgroundColor: 'rgba(30, 41, 59, 0.8)',
                borderRadius: 16,
                padding: 24,
                border: `1px solid ${ch.color}40`,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
                <span style={{ fontSize: 28 }}>{ch.icon}</span>
                <span style={{ color: ch.color, fontSize: 18, fontWeight: 700 }}>{ch.name}</span>
              </div>
              <p style={{ color: '#94a3b8', fontSize: 14, margin: 0, lineHeight: 1.4 }}>
                {ch.desc}
              </p>
            </div>
          );
        })}
      </div>

      {/* Endpoints */}
      <div
        style={{
          opacity: dlqOpacity,
          display: 'flex',
          gap: 16,
          flexWrap: 'wrap',
          justifyContent: 'center',
        }}
      >
        <code
          style={{
            padding: '10px 16px',
            backgroundColor: 'rgba(30, 41, 59, 0.9)',
            borderRadius: 8,
            color: '#22c55e',
            fontSize: 12,
            fontFamily: 'monospace',
            border: '1px solid rgba(148, 163, 184, 0.2)',
          }}
        >
          POST /webhooks/transactions
        </code>
        <code
          style={{
            padding: '10px 16px',
            backgroundColor: 'rgba(30, 41, 59, 0.9)',
            borderRadius: 8,
            color: '#22c55e',
            fontSize: 12,
            fontFamily: 'monospace',
            border: '1px solid rgba(148, 163, 184, 0.2)',
          }}
        >
          GET /webhooks/stream
        </code>
        <code
          style={{
            padding: '10px 16px',
            backgroundColor: 'rgba(30, 41, 59, 0.9)',
            borderRadius: 8,
            color: '#22c55e',
            fontSize: 12,
            fontFamily: 'monospace',
            border: '1px solid rgba(148, 163, 184, 0.2)',
          }}
        >
          POST /webhooks/callbacks
        </code>
      </div>
    </AbsoluteFill>
  );
};
