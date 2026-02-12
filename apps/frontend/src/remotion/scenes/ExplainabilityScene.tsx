import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';

const waterfallData = [
  { name: 'Base', value: 0.45, cumulative: 0.45, isTotal: true },
  { name: 'Transaction Amount', value: 0.32, cumulative: 0.77, isPositive: true },
  { name: 'Off-Hours', value: 0.28, cumulative: 1.05, isPositive: true },
  { name: 'Counterparty', value: 0.15, cumulative: 1.2, isPositive: true },
  { name: 'Weekday', value: -0.12, cumulative: 1.08, isPositive: false },
  { name: 'Known Acct', value: -0.08, cumulative: 1.0, isPositive: false },
  { name: 'Final', value: 0.75, cumulative: 0.75, isTotal: true },
];

const maxVal = 1.25;

export const ExplainabilityScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const headerOpacity = interpolate(frame, [0, 25], [0, 1], { extrapolateRight: 'clamp' });
  const line1Opacity = interpolate(frame, [15, 35], [0, 1], { extrapolateRight: 'clamp' });
  const line2Opacity = interpolate(frame, [30, 50], [0, 1], { extrapolateRight: 'clamp' });

  const getBarAnimation = (index: number) => {
    const startFrame = 55 + index * 20;
    const width = interpolate(frame, [startFrame, startFrame + 18], [0, 1], { extrapolateRight: 'clamp' });
    const opacity = interpolate(frame, [startFrame, startFrame + 10], [0, 1], { extrapolateRight: 'clamp' });
    return { width, opacity };
  };

  const insightOpacity = interpolate(frame, [200, 220], [0, 1], { extrapolateRight: 'clamp' });
  const insightScale = spring({ frame: frame - 200, fps, from: 0.9, to: 1, durationInFrames: 20 });

  const regulatoryOpacity = interpolate(frame, [220, 235], [0, 1], { extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill
      style={{
        background: 'linear-gradient(180deg, #0f172a 0%, #1e293b 100%)',
        padding: 50,
        fontFamily: 'system-ui, -apple-system, sans-serif',
      }}
    >
      {/* Header */}
      <div style={{ opacity: headerOpacity, marginBottom: 16 }}>
        <h2 style={{ fontSize: 36, color: 'white', margin: 0, fontWeight: 700 }}>
          SHAP Explainability
        </h2>
      </div>

      <div style={{ opacity: line1Opacity, marginBottom: 8 }}>
        <p style={{ fontSize: 24, color: '#f1f5f9', margin: 0, fontWeight: 600 }}>
          Not just &quot;flagged&quot; — here&apos;s why
        </p>
      </div>
      <div style={{ opacity: line2Opacity, marginBottom: 32 }}>
        <p style={{ fontSize: 18, color: '#94a3b8', margin: 0 }}>
          SHAP feature importance for every prediction
        </p>
      </div>

      <div style={{ display: 'flex', gap: 32 }}>
        {/* Waterfall Chart */}
        <div style={{ flex: 2 }}>
          <div
            style={{
              backgroundColor: 'rgba(30, 41, 59, 0.8)',
              borderRadius: 16,
              padding: 28,
              border: '1px solid rgba(148, 163, 184, 0.2)',
            }}
          >
            <h3 style={{ color: '#f1f5f9', fontSize: 20, marginBottom: 20 }}>
              Score Waterfall
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {waterfallData.map((bar, index) => {
                const { width, opacity } = getBarAnimation(index);
                const barColor = bar.isTotal
                  ? '#6366f1'
                  : bar.isPositive
                    ? '#ef4444'
                    : '#22c55e';

                const barWidth = (bar.isTotal ? bar.value : Math.abs(bar.value)) / maxVal;
                const offset = bar.isTotal
                  ? 0
                  : bar.isPositive
                    ? (bar.cumulative - bar.value) / maxVal
                    : bar.cumulative / maxVal;

                return (
                  <div key={bar.name} style={{ opacity, display: 'flex', alignItems: 'center', gap: 14 }}>
                    <span style={{ color: '#94a3b8', fontSize: 13, width: 130, textAlign: 'right', flexShrink: 0 }}>
                      {bar.name}
                    </span>
                    <div style={{ flex: 1, height: 24, position: 'relative', backgroundColor: 'rgba(148, 163, 184, 0.1)', borderRadius: 4 }}>
                      <div
                        style={{
                          position: 'absolute',
                          left: `${(offset / maxVal) * 100}%`,
                          width: `${barWidth * width * 100}%`,
                          height: '100%',
                          backgroundColor: barColor,
                          borderRadius: 4,
                          boxShadow: `0 0 6px ${barColor}40`,
                        }}
                      />
                    </div>
                    <span style={{ color: '#f1f5f9', fontSize: 13, fontWeight: 600, width: 50, flexShrink: 0 }}>
                      {bar.value > 0 ? '+' : ''}{bar.value.toFixed(2)}
                    </span>
                  </div>
                );
              })}
            </div>

            {/* Legend */}
            <div style={{ display: 'flex', gap: 20, marginTop: 16 }}>
              {[
                { color: '#6366f1', label: 'Total' },
                { color: '#ef4444', label: 'Risk Increasing' },
                { color: '#22c55e', label: 'Risk Decreasing' },
              ].map((item) => (
                <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <div style={{ width: 10, height: 10, borderRadius: 3, backgroundColor: item.color }} />
                  <span style={{ color: '#94a3b8', fontSize: 12 }}>{item.label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Insight Panel */}
        <div
          style={{
            flex: 1,
            opacity: insightOpacity,
            transform: `scale(${insightScale})`,
          }}
        >
          <div
            style={{
              backgroundColor: 'rgba(30, 41, 59, 0.8)',
              borderRadius: 16,
              padding: 20,
              border: '1px solid rgba(148, 163, 184, 0.2)',
            }}
          >
            <h3 style={{ color: '#f1f5f9', fontSize: 18, marginBottom: 16 }}>
              Key Insights
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div style={{ padding: 14, backgroundColor: 'rgba(239, 68, 68, 0.1)', borderRadius: 8, borderLeft: '3px solid #ef4444' }}>
                <p style={{ color: '#fca5a5', fontSize: 12, margin: 0, fontWeight: 600 }}>Top Risk Factor</p>
                <p style={{ color: '#f1f5f9', fontSize: 14, margin: '6px 0 0', lineHeight: 1.4 }}>
                  Transaction amount ($50K) is 3.2x above account average
                </p>
              </div>

              <div style={{ padding: 14, backgroundColor: 'rgba(34, 197, 94, 0.1)', borderRadius: 8, borderLeft: '3px solid #22c55e' }}>
                <p style={{ color: '#86efac', fontSize: 12, margin: 0, fontWeight: 600 }}>Top Safe Factor</p>
                <p style={{ color: '#f1f5f9', fontSize: 14, margin: '6px 0 0', lineHeight: 1.4 }}>
                  Weekday transaction matches normal account behavior
                </p>
              </div>

              <div
                style={{
                  opacity: regulatoryOpacity,
                  padding: 12,
                  backgroundColor: 'rgba(139, 92, 246, 0.1)',
                  borderRadius: 8,
                  border: '1px solid rgba(139, 92, 246, 0.3)',
                }}
              >
                <p style={{ color: '#a78bfa', fontSize: 12, margin: 0, fontWeight: 600 }}>
                  Required by EU AI Act, FINRA, SEC
                </p>
                <p style={{ color: '#94a3b8', fontSize: 11, margin: '4px 0 0' }}>
                  SHAP TreeExplainer ~5ms per prediction
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
