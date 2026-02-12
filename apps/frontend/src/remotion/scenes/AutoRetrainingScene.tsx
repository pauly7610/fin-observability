import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';

const driftChartData = [
  { day: 'Mon', psi: 0.12 },
  { day: 'Tue', psi: 0.18 },
  { day: 'Wed', psi: 0.25 },
  { day: 'Thu', psi: 0.32 },
  { day: 'Fri', psi: 0.41 },
  { day: 'Sat', psi: 0.52 },
  { day: 'Sun', psi: 0.58 },
];

const THRESHOLD = 0.35;

export const AutoRetrainingScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const headerOpacity = interpolate(frame, [0, 25], [0, 1], { extrapolateRight: 'clamp' });
  const taglineOpacity = interpolate(frame, [20, 45], [0, 1], { extrapolateRight: 'clamp' });

  const chartOpacity = interpolate(frame, [55, 80], [0, 1], { extrapolateRight: 'clamp' });
  const getBarWidth = (index: number) => {
    const startFrame = 75 + index * 8;
    return interpolate(frame, [startFrame, startFrame + 15], [0, 1], { extrapolateRight: 'clamp' });
  };

  const alertOpacity = interpolate(frame, [140, 165], [0, 1], { extrapolateRight: 'clamp' });
  const alertScale = spring({ frame: frame - 140, fps, from: 0.9, to: 1, durationInFrames: 20 });

  const f1OldOpacity = interpolate(frame, [180, 200], [0, 1], { extrapolateRight: 'clamp' });
  const f1NewOpacity = interpolate(frame, [210, 230], [0, 1], { extrapolateRight: 'clamp' });
  const abTestOpacity = interpolate(frame, [240, 260], [0, 1], { extrapolateRight: 'clamp' });
  const promotedOpacity = interpolate(frame, [265, 285], [0, 1], { extrapolateRight: 'clamp' });

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
          Self-Healing ML
        </h2>
      </div>
      <div style={{ opacity: taglineOpacity, marginBottom: 28 }}>
        <p style={{ fontSize: 18, color: '#94a3b8', margin: 0 }}>
          Detects drift, retrains, A/B tests, auto-promotes
        </p>
      </div>

      <div style={{ display: 'flex', gap: 32 }}>
        {/* Left - Drift Chart + Alert */}
        <div style={{ flex: 1.2 }}>
          <div
            style={{
              opacity: chartOpacity,
              backgroundColor: 'rgba(30, 41, 59, 0.8)',
              borderRadius: 16,
              padding: 24,
              border: '1px solid rgba(148, 163, 184, 0.2)',
              marginBottom: 20,
            }}
          >
            <h3 style={{ color: '#f1f5f9', fontSize: 18, marginBottom: 20 }}>
              PSI — Population Stability Index
            </h3>
            <div style={{ display: 'flex', alignItems: 'flex-end', gap: 12, height: 100 }}>
              {driftChartData.map((d, i) => (
                <div key={d.day} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <div
                    style={{
                      width: '100%',
                      height: `${(d.psi / 0.7) * 80}px`,
                      backgroundColor: d.psi > THRESHOLD ? '#ef4444' : '#3b82f6',
                      borderRadius: '4px 4px 0 0',
                      transform: `scaleY(${getBarWidth(i)})`,
                      transformOrigin: 'bottom',
                    }}
                  />
                  <span style={{ color: '#94a3b8', fontSize: 11, marginTop: 8 }}>{d.day}</span>
                </div>
              ))}
            </div>
            <div
              style={{
                position: 'relative',
                height: 2,
                backgroundColor: '#eab308',
                marginTop: 8,
                marginLeft: '14%',
                width: '72%',
              }}
            >
              <span style={{ position: 'absolute', right: -40, top: -22, color: '#eab308', fontSize: 11 }}>
                threshold 0.35
              </span>
            </div>
          </div>

          {/* Drift Alert */}
          <div
            style={{
              opacity: alertOpacity,
              transform: `scale(${alertScale})`,
              padding: 20,
              backgroundColor: 'rgba(239, 68, 68, 0.15)',
              borderRadius: 12,
              border: '2px solid rgba(239, 68, 68, 0.5)',
            }}
          >
            <p style={{ color: '#fca5a5', fontSize: 16, margin: 0, fontWeight: 700 }}>
              Drift detected — triggering retrain
            </p>
            <p style={{ color: '#94a3b8', fontSize: 13, margin: '8px 0 0' }}>
              PSI exceeded threshold. Retraining pipeline started.
            </p>
          </div>
        </div>

        {/* Right - F1 + A/B Test */}
        <div style={{ flex: 0.9 }}>
          <div
            style={{
              opacity: f1OldOpacity,
              backgroundColor: 'rgba(30, 41, 59, 0.8)',
              borderRadius: 12,
              padding: 20,
              border: '1px solid rgba(148, 163, 184, 0.2)',
              marginBottom: 16,
            }}
          >
            <p style={{ color: '#94a3b8', fontSize: 12, marginBottom: 8 }}>Old Model</p>
            <p style={{ color: '#f1f5f9', fontSize: 28, margin: 0, fontWeight: 700 }}>
              F1: 0.87
            </p>
          </div>

          <div
            style={{
              opacity: f1NewOpacity,
              backgroundColor: 'rgba(34, 197, 94, 0.1)',
              borderRadius: 12,
              padding: 20,
              border: '1px solid rgba(34, 197, 94, 0.4)',
              marginBottom: 16,
            }}
          >
            <p style={{ color: '#86efac', fontSize: 12, marginBottom: 8 }}>New Model (retrained)</p>
            <p style={{ color: '#22c55e', fontSize: 28, margin: 0, fontWeight: 700 }}>
              F1: 0.91
            </p>
          </div>

          <div
            style={{
              opacity: abTestOpacity,
              backgroundColor: 'rgba(30, 41, 59, 0.8)',
              borderRadius: 12,
              padding: 20,
              border: '1px solid rgba(148, 163, 184, 0.2)',
              marginBottom: 16,
            }}
          >
            <p style={{ color: '#94a3b8', fontSize: 12, marginBottom: 8 }}>A/B Test</p>
            <p style={{ color: '#f1f5f9', fontSize: 14, margin: 0 }}>
              p &lt; 0.05 — new model significant
            </p>
          </div>

          <div
            style={{
              opacity: promotedOpacity,
              padding: 18,
              backgroundColor: 'rgba(34, 197, 94, 0.15)',
              borderRadius: 12,
              border: '2px solid rgba(34, 197, 94, 0.5)',
            }}
          >
            <p style={{ color: '#22c55e', fontSize: 18, margin: 0, fontWeight: 700 }}>
              PROMOTED
            </p>
            <p style={{ color: '#86efac', fontSize: 12, margin: '6px 0 0' }}>
              v2.0.1 now live
            </p>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
