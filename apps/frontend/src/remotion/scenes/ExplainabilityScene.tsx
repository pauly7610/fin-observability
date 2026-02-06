import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';

const waterfallData = [
  { name: 'Base Score', value: 0.45, cumulative: 0.45, isTotal: true },
  { name: 'Amount ($50K)', value: 0.18, cumulative: 0.63, isPositive: true },
  { name: 'Off-Hours', value: 0.12, cumulative: 0.75, isPositive: true },
  { name: 'Wire Transfer', value: 0.08, cumulative: 0.83, isPositive: true },
  { name: 'Weekday', value: -0.05, cumulative: 0.78, isPositive: false },
  { name: 'Known Acct', value: -0.03, cumulative: 0.75, isPositive: false },
  { name: 'Final Score', value: 0.75, cumulative: 0.75, isTotal: true },
];

const maxVal = 0.85;

export const ExplainabilityScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const headerOpacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' });

  const getBarAnimation = (index: number) => {
    const startFrame = 30 + index * 18;
    const width = interpolate(frame, [startFrame, startFrame + 20], [0, 1], { extrapolateRight: 'clamp' });
    const opacity = interpolate(frame, [startFrame, startFrame + 10], [0, 1], { extrapolateRight: 'clamp' });
    return { width, opacity };
  };

  const insightOpacity = interpolate(frame, [170, 190], [0, 1], { extrapolateRight: 'clamp' });
  const insightScale = spring({ frame: frame - 170, fps, from: 0.9, to: 1, durationInFrames: 20 });

  return (
    <AbsoluteFill
      style={{
        background: 'linear-gradient(180deg, #0f172a 0%, #1e293b 100%)',
        padding: 60,
        fontFamily: 'system-ui, -apple-system, sans-serif',
      }}
    >
      {/* Header */}
      <div style={{ opacity: headerOpacity, marginBottom: 40 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <span style={{ fontSize: 48 }}>📊</span>
          <h2 style={{ fontSize: 42, color: 'white', margin: 0, fontWeight: 700 }}>
            SHAP Explainability
          </h2>
        </div>
        <p style={{ fontSize: 24, color: '#94a3b8', marginTop: 12 }}>
          Understand exactly why the model flagged a transaction
        </p>
      </div>

      <div style={{ display: 'flex', gap: 40 }}>
        {/* Waterfall Chart */}
        <div style={{ flex: 2 }}>
          <div
            style={{
              backgroundColor: 'rgba(30, 41, 59, 0.8)',
              borderRadius: 16,
              padding: 32,
              border: '1px solid rgba(148, 163, 184, 0.2)',
            }}
          >
            <h3 style={{ color: '#f1f5f9', fontSize: 22, marginBottom: 24 }}>
              Score Waterfall
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
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
                  <div key={bar.name} style={{ opacity, display: 'flex', alignItems: 'center', gap: 16 }}>
                    <span style={{ color: '#94a3b8', fontSize: 14, width: 120, textAlign: 'right', flexShrink: 0 }}>
                      {bar.name}
                    </span>
                    <div style={{ flex: 1, height: 28, position: 'relative', backgroundColor: 'rgba(148, 163, 184, 0.1)', borderRadius: 4 }}>
                      <div
                        style={{
                          position: 'absolute',
                          left: `${offset * 100}%`,
                          width: `${barWidth * width * 100}%`,
                          height: '100%',
                          backgroundColor: barColor,
                          borderRadius: 4,
                          boxShadow: `0 0 8px ${barColor}40`,
                        }}
                      />
                    </div>
                    <span style={{ color: '#f1f5f9', fontSize: 14, fontWeight: 600, width: 60, flexShrink: 0 }}>
                      {bar.value > 0 ? '+' : ''}{bar.value.toFixed(2)}
                    </span>
                  </div>
                );
              })}
            </div>

            {/* Legend */}
            <div style={{ display: 'flex', gap: 24, marginTop: 20 }}>
              {[
                { color: '#6366f1', label: 'Total' },
                { color: '#ef4444', label: 'Risk Increasing' },
                { color: '#22c55e', label: 'Risk Decreasing' },
              ].map((item) => (
                <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ width: 12, height: 12, borderRadius: 3, backgroundColor: item.color }} />
                  <span style={{ color: '#94a3b8', fontSize: 13 }}>{item.label}</span>
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
              padding: 24,
              border: '1px solid rgba(148, 163, 184, 0.2)',
            }}
          >
            <h3 style={{ color: '#f1f5f9', fontSize: 20, marginBottom: 20 }}>
              🧠 Key Insights
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div style={{ padding: 16, backgroundColor: 'rgba(239, 68, 68, 0.1)', borderRadius: 8, borderLeft: '3px solid #ef4444' }}>
                <p style={{ color: '#fca5a5', fontSize: 14, margin: 0, fontWeight: 600 }}>Top Risk Factor</p>
                <p style={{ color: '#f1f5f9', fontSize: 16, margin: '8px 0 0' }}>Transaction amount ($50K) is 3.2x above account average</p>
              </div>

              <div style={{ padding: 16, backgroundColor: 'rgba(34, 197, 94, 0.1)', borderRadius: 8, borderLeft: '3px solid #22c55e' }}>
                <p style={{ color: '#86efac', fontSize: 14, margin: 0, fontWeight: 600 }}>Top Safe Factor</p>
                <p style={{ color: '#f1f5f9', fontSize: 16, margin: '8px 0 0' }}>Weekday transaction matches normal account behavior</p>
              </div>

              <div style={{ padding: 16, backgroundColor: 'rgba(139, 92, 246, 0.1)', borderRadius: 8, border: '1px solid rgba(139, 92, 246, 0.3)' }}>
                <p style={{ color: '#a78bfa', fontSize: 14, margin: 0 }}>
                  💡 SHAP values computed via TreeExplainer in ~5ms per prediction
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
