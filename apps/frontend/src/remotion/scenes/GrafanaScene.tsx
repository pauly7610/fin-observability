import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';

const spans = [
  { name: 'ML Inference', duration: 42, color: '#3b82f6' },
  { name: 'Agent Reasoning', duration: 156, color: '#8b5cf6' },
  { name: 'Human Decision', duration: 2300, color: '#eab308' },
  { name: 'Audit Log', duration: 12, color: '#22c55e' },
];

const totalWidth = 2500;

export const GrafanaScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const headerOpacity = interpolate(frame, [0, 25], [0, 1], { extrapolateRight: 'clamp' });
  const line1Opacity = interpolate(frame, [20, 40], [0, 1], { extrapolateRight: 'clamp' });
  const line2Opacity = interpolate(frame, [35, 55], [0, 1], { extrapolateRight: 'clamp' });

  const traceOpacity = interpolate(frame, [65, 90], [0, 1], { extrapolateRight: 'clamp' });
  const getSpanWidth = (index: number) => {
    const startFrame = 90 + index * 12;
    return interpolate(frame, [startFrame, startFrame + 15], [0, 1], { extrapolateRight: 'clamp' });
  };

  const linkOpacity = interpolate(frame, [150, 170], [0, 1], { extrapolateRight: 'clamp' });

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
          Full Distributed Tracing
        </h2>
      </div>
      <div style={{ opacity: line1Opacity, marginBottom: 4 }}>
        <p style={{ fontSize: 18, color: '#f1f5f9', margin: 0, fontWeight: 600 }}>
          OpenTelemetry → Grafana Cloud
        </p>
      </div>
      <div style={{ opacity: line2Opacity, marginBottom: 28 }}>
        <p style={{ fontSize: 16, color: '#94a3b8', margin: 0 }}>
          Transaction ID → ML inference → Agent reasoning → Human decision
        </p>
      </div>

      {/* Trace View */}
      <div
        style={{
          opacity: traceOpacity,
          backgroundColor: 'rgba(30, 41, 59, 0.8)',
          borderRadius: 16,
          padding: 28,
          border: '1px solid rgba(148, 163, 184, 0.2)',
          marginBottom: 24,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20 }}>
          <span style={{ color: '#64748b', fontSize: 12 }}>Trace: txn_suspicious_001</span>
          <span style={{ color: '#94a3b8', fontSize: 12 }}>•</span>
          <span style={{ color: '#22c55e', fontSize: 12 }}>2.5s total</span>
        </div>

        {/* Span bars */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {spans.map((span, index) => {
            const widthPct = (span.duration / totalWidth) * 100;
            const animWidth = widthPct * getSpanWidth(index);
            return (
              <div key={span.name} style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                <span style={{ color: '#94a3b8', fontSize: 13, width: 120, flexShrink: 0 }}>
                  {span.name}
                </span>
                <div
                  style={{
                    flex: 1,
                    height: 28,
                    backgroundColor: 'rgba(148, 163, 184, 0.1)',
                    borderRadius: 4,
                    overflow: 'hidden',
                    position: 'relative',
                  }}
                >
                  <div
                    style={{
                      position: 'absolute',
                      left: 0,
                      top: 0,
                      width: `${animWidth}%`,
                      height: '100%',
                      backgroundColor: span.color,
                      borderRadius: 4,
                      minWidth: 2,
                    }}
                  />
                </div>
                <span style={{ color: '#f1f5f9', fontSize: 13, fontWeight: 600, width: 50 }}>
                  {span.duration}ms
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Grafana link */}
      <div
        style={{
          opacity: linkOpacity,
          textAlign: 'center',
        }}
      >
        <p style={{ color: '#94a3b8', fontSize: 18, margin: 0 }}>
          pauly7610.grafana.net
        </p>
      </div>
    </AbsoluteFill>
  );
};
