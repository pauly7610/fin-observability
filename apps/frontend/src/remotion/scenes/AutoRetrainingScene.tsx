import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';

const datasetStats = [
  { label: 'Transactions', value: '10,000' },
  { label: 'Accounts', value: '200 profiles' },
  { label: 'Jurisdictions', value: '20 countries' },
  { label: 'Time Span', value: '14 months' },
];

const pipelineSteps = [
  { icon: '📂', label: 'Load Dataset', detail: '10K transactions CSV' },
  { icon: '🧠', label: 'Retrain Model', detail: 'Isolation Forest + PCA' },
  { icon: '📦', label: 'Export ONNX', detail: '~2x faster inference' },
  { icon: '✅', label: 'Auto-Version', detail: 'v2.0.0 → v2.0.1' },
];

export const AutoRetrainingScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const headerOpacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' });

  // Dataset stats stagger
  const getStatAnimation = (index: number) => {
    const startFrame = 25 + index * 12;
    const opacity = interpolate(frame, [startFrame, startFrame + 12], [0, 1], { extrapolateRight: 'clamp' });
    const y = spring({ frame: frame - startFrame, fps, from: 20, to: 0, durationInFrames: 15 });
    return { opacity, y };
  };

  // Pipeline steps stagger
  const getStepAnimation = (index: number) => {
    const startFrame = 80 + index * 22;
    const opacity = interpolate(frame, [startFrame, startFrame + 15], [0, 1], { extrapolateRight: 'clamp' });
    const x = spring({ frame: frame - startFrame, fps, from: -40, to: 0, durationInFrames: 20 });
    // Checkmark appears after the step fades in
    const checkOpacity = interpolate(frame, [startFrame + 18, startFrame + 25], [0, 1], { extrapolateRight: 'clamp' });
    return { opacity, x, checkOpacity };
  };

  // Schedule badge
  const scheduleOpacity = interpolate(frame, [180, 200], [0, 1], { extrapolateRight: 'clamp' });
  const scheduleScale = spring({ frame: frame - 180, fps, from: 0.8, to: 1, durationInFrames: 20 });

  // ONNX badge pulse
  const onnxGlow = interpolate(frame % 50, [0, 25, 50], [0.3, 0.7, 0.3], { extrapolateRight: 'clamp' });

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
          <span style={{ fontSize: 48 }}>🔄</span>
          <h2 style={{ fontSize: 42, color: 'white', margin: 0, fontWeight: 700 }}>
            Auto-Retraining Pipeline
          </h2>
        </div>
        <p style={{ fontSize: 24, color: '#94a3b8', marginTop: 12 }}>
          Enhanced dataset + ONNX Runtime + scheduled retraining
        </p>
      </div>

      <div style={{ display: 'flex', gap: 40 }}>
        {/* Left: Dataset + Pipeline */}
        <div style={{ flex: 1.2 }}>
          {/* Dataset Stats */}
          <div
            style={{
              backgroundColor: 'rgba(30, 41, 59, 0.8)',
              borderRadius: 16,
              padding: 28,
              border: '1px solid rgba(148, 163, 184, 0.2)',
              marginBottom: 24,
            }}
          >
            <h3 style={{ color: '#f1f5f9', fontSize: 20, marginBottom: 20 }}>
              📊 Enhanced Dataset
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              {datasetStats.map((stat, index) => {
                const { opacity, y } = getStatAnimation(index);
                return (
                  <div
                    key={stat.label}
                    style={{
                      opacity,
                      transform: `translateY(${y}px)`,
                      padding: 16,
                      backgroundColor: 'rgba(59, 130, 246, 0.08)',
                      borderRadius: 10,
                      border: '1px solid rgba(59, 130, 246, 0.2)',
                      textAlign: 'center',
                    }}
                  >
                    <div style={{ color: '#60a5fa', fontSize: 26, fontWeight: 700 }}>{stat.value}</div>
                    <div style={{ color: '#94a3b8', fontSize: 13, marginTop: 4 }}>{stat.label}</div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Pipeline Steps */}
          <div
            style={{
              backgroundColor: 'rgba(30, 41, 59, 0.8)',
              borderRadius: 16,
              padding: 28,
              border: '1px solid rgba(148, 163, 184, 0.2)',
            }}
          >
            <h3 style={{ color: '#f1f5f9', fontSize: 20, marginBottom: 20 }}>
              ⚙️ Retraining Pipeline
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {pipelineSteps.map((step, index) => {
                const { opacity, x, checkOpacity } = getStepAnimation(index);
                return (
                  <div
                    key={step.label}
                    style={{
                      opacity,
                      transform: `translateX(${x}px)`,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 16,
                      padding: '14px 18px',
                      backgroundColor: 'rgba(15, 23, 42, 0.5)',
                      borderRadius: 10,
                      border: '1px solid rgba(148, 163, 184, 0.15)',
                    }}
                  >
                    <span style={{ fontSize: 26, width: 36, textAlign: 'center' }}>{step.icon}</span>
                    <div style={{ flex: 1 }}>
                      <div style={{ color: '#f1f5f9', fontSize: 16, fontWeight: 600 }}>{step.label}</div>
                      <div style={{ color: '#64748b', fontSize: 13 }}>{step.detail}</div>
                    </div>
                    <div
                      style={{
                        opacity: checkOpacity,
                        width: 28,
                        height: 28,
                        borderRadius: '50%',
                        backgroundColor: 'rgba(34, 197, 94, 0.2)',
                        border: '2px solid #22c55e',
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        color: '#22c55e',
                        fontSize: 14,
                        fontWeight: 700,
                      }}
                    >
                      ✓
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right: ONNX + Schedule */}
        <div style={{ flex: 0.8 }}>
          {/* ONNX Runtime Card */}
          <div
            style={{
              backgroundColor: 'rgba(30, 41, 59, 0.8)',
              borderRadius: 16,
              padding: 28,
              border: '1px solid rgba(139, 92, 246, 0.3)',
              marginBottom: 24,
              boxShadow: `0 0 20px rgba(139, 92, 246, ${onnxGlow * 0.3})`,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
              <div
                style={{
                  padding: '6px 14px',
                  backgroundColor: 'rgba(139, 92, 246, 0.2)',
                  borderRadius: 6,
                  border: '1px solid rgba(139, 92, 246, 0.5)',
                }}
              >
                <span style={{ color: '#a78bfa', fontSize: 14, fontWeight: 700 }}>ONNX Runtime</span>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {[
                { label: 'Architecture', value: '2-Layer PCA' },
                { label: 'Layer 1', value: '20 → 12 components' },
                { label: 'Layer 2', value: '12 → 6 bottleneck' },
                { label: 'Inference', value: '~2x faster' },
                { label: 'Fallback', value: 'NumPy (graceful)' },
              ].map((item) => (
                <div key={item.label} style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94a3b8', fontSize: 14 }}>{item.label}</span>
                  <span style={{ color: '#f1f5f9', fontSize: 14, fontWeight: 500 }}>{item.value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Schedule Card */}
          <div
            style={{
              opacity: scheduleOpacity,
              transform: `scale(${scheduleScale})`,
              backgroundColor: 'rgba(34, 197, 94, 0.08)',
              borderRadius: 16,
              padding: 24,
              border: '2px solid rgba(34, 197, 94, 0.3)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
              <div
                style={{
                  width: 44,
                  height: 44,
                  borderRadius: '50%',
                  backgroundColor: 'rgba(34, 197, 94, 0.2)',
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  fontSize: 22,
                }}
              >
                ⏰
              </div>
              <div>
                <h4 style={{ color: '#22c55e', fontSize: 18, margin: 0, fontWeight: 600 }}>
                  Weekly Schedule
                </h4>
                <p style={{ color: '#86efac', fontSize: 13, margin: '4px 0 0' }}>
                  APScheduler • Configurable via env
                </p>
              </div>
            </div>
            <div
              style={{
                padding: 12,
                backgroundColor: 'rgba(15, 23, 42, 0.6)',
                borderRadius: 8,
                fontFamily: 'monospace',
              }}
            >
              <span style={{ color: '#64748b', fontSize: 12 }}>RETRAIN_SCHEDULE_HOURS=</span>
              <span style={{ color: '#22c55e', fontSize: 12, fontWeight: 600 }}>168</span>
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
