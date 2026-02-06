import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';

const services = [
  { name: 'FastAPI Backend', icon: '⚡', status: 'live', url: 'fin-observability-production.up.railway.app' },
  { name: 'OTel Collector', icon: '📡', status: 'live', url: 'ravishing-prosperity.railway.internal:4317' },
  { name: 'SQLite Database', icon: '🗄️', status: 'live', url: 'Persistent volume' },
];

const telemetryFlow = [
  { label: 'Backend', icon: '⚡' },
  { label: 'OTLP gRPC', icon: '→' },
  { label: 'Collector', icon: '📡' },
  { label: 'Export', icon: '→' },
  { label: 'Grafana / Honeycomb', icon: '📊' },
];

export const ProductionDeployScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const headerOpacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' });

  const getServiceAnimation = (index: number) => {
    const startFrame = 30 + index * 20;
    const opacity = interpolate(frame, [startFrame, startFrame + 15], [0, 1], { extrapolateRight: 'clamp' });
    const x = spring({ frame: frame - startFrame, fps, from: 60, to: 0, durationInFrames: 20 });
    return { opacity, x };
  };

  const flowOpacity = interpolate(frame, [100, 120], [0, 1], { extrapolateRight: 'clamp' });

  const getFlowNodeAnimation = (index: number) => {
    const startFrame = 110 + index * 12;
    const opacity = interpolate(frame, [startFrame, startFrame + 10], [0, 1], { extrapolateRight: 'clamp' });
    const scale = spring({ frame: frame - startFrame, fps, from: 0.5, to: 1, durationInFrames: 15 });
    return { opacity, scale };
  };

  const envVarOpacity = interpolate(frame, [170, 190], [0, 1], { extrapolateRight: 'clamp' });

  // Pulsing dot for "live" status
  const pulseOpacity = interpolate(frame % 40, [0, 20, 40], [0.4, 1, 0.4], { extrapolateRight: 'clamp' });

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
          <span style={{ fontSize: 48 }}>🚀</span>
          <h2 style={{ fontSize: 42, color: 'white', margin: 0, fontWeight: 700 }}>
            Production on Railway
          </h2>
        </div>
        <p style={{ fontSize: 24, color: '#94a3b8', marginTop: 12 }}>
          Deployed with OpenTelemetry Collector for full observability
        </p>
      </div>

      <div style={{ display: 'flex', gap: 40 }}>
        {/* Services */}
        <div style={{ flex: 1 }}>
          <div
            style={{
              backgroundColor: 'rgba(30, 41, 59, 0.8)',
              borderRadius: 16,
              padding: 32,
              border: '1px solid rgba(148, 163, 184, 0.2)',
            }}
          >
            <h3 style={{ color: '#f1f5f9', fontSize: 22, marginBottom: 24 }}>
              Railway Services
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {services.map((svc, index) => {
                const { opacity, x } = getServiceAnimation(index);
                return (
                  <div
                    key={svc.name}
                    style={{
                      opacity,
                      transform: `translateX(${x}px)`,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 16,
                      padding: 20,
                      backgroundColor: 'rgba(15, 23, 42, 0.5)',
                      borderRadius: 12,
                      border: '1px solid rgba(34, 197, 94, 0.2)',
                    }}
                  >
                    <span style={{ fontSize: 32 }}>{svc.icon}</span>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <span style={{ color: '#f1f5f9', fontSize: 18, fontWeight: 600 }}>{svc.name}</span>
                        <div
                          style={{
                            width: 8,
                            height: 8,
                            borderRadius: '50%',
                            backgroundColor: '#22c55e',
                            opacity: pulseOpacity,
                            boxShadow: '0 0 6px #22c55e',
                          }}
                        />
                        <span style={{ color: '#22c55e', fontSize: 12, fontWeight: 600, textTransform: 'uppercase' }}>
                          {svc.status}
                        </span>
                      </div>
                      <span style={{ color: '#64748b', fontSize: 13, fontFamily: 'monospace' }}>{svc.url}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Telemetry Flow + Env Vars */}
        <div style={{ flex: 1 }}>
          {/* Telemetry Pipeline */}
          <div
            style={{
              opacity: flowOpacity,
              backgroundColor: 'rgba(30, 41, 59, 0.8)',
              borderRadius: 16,
              padding: 24,
              border: '1px solid rgba(148, 163, 184, 0.2)',
              marginBottom: 24,
            }}
          >
            <h3 style={{ color: '#f1f5f9', fontSize: 20, marginBottom: 20 }}>
              📡 Telemetry Pipeline
            </h3>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, flexWrap: 'wrap' }}>
              {telemetryFlow.map((node, index) => {
                const { opacity, scale } = getFlowNodeAnimation(index);
                const isArrow = node.icon === '→';
                return (
                  <div
                    key={index}
                    style={{
                      opacity,
                      transform: `scale(${scale})`,
                    }}
                  >
                    {isArrow ? (
                      <span style={{ color: '#3b82f6', fontSize: 24, fontWeight: 700 }}>→</span>
                    ) : (
                      <div
                        style={{
                          padding: '10px 16px',
                          backgroundColor: 'rgba(59, 130, 246, 0.15)',
                          border: '1px solid rgba(59, 130, 246, 0.4)',
                          borderRadius: 8,
                          textAlign: 'center',
                        }}
                      >
                        <div style={{ fontSize: 22 }}>{node.icon}</div>
                        <div style={{ color: '#93c5fd', fontSize: 12, fontWeight: 600, marginTop: 4 }}>{node.label}</div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Env Var Config */}
          <div
            style={{
              opacity: envVarOpacity,
              backgroundColor: 'rgba(15, 23, 42, 0.9)',
              borderRadius: 12,
              padding: 20,
              border: '1px solid rgba(148, 163, 184, 0.2)',
              fontFamily: 'monospace',
            }}
          >
            <div style={{ color: '#64748b', fontSize: 12, marginBottom: 12 }}>
              # Railway Environment Variables
            </div>
            {[
              'OTEL_EXPORTER_OTLP_ENDPOINT=ravishing-prosperity.railway.internal:4317',
              'DATABASE_URL=sqlite:///./data.db',
              'CORS_ORIGINS=*',
              'JWT_SECRET_KEY=••••••••',
            ].map((line, i) => (
              <div key={i} style={{ color: '#22c55e', fontSize: 13, lineHeight: 1.8 }}>
                {line}
              </div>
            ))}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
