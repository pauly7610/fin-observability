import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';

const stages = [
  { name: 'Triage', icon: '🔍', status: 'complete', color: '#22c55e' },
  { name: 'Remediate', icon: '🔧', status: 'complete', color: '#22c55e' },
  { name: 'Compliance', icon: '📋', status: 'active', color: '#3b82f6' },
  { name: 'Audit Summary', icon: '📊', status: 'pending', color: '#64748b' },
];

export const AgenticWorkflowScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const headerOpacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' });

  // Stagger the stage animations
  const getStageAnimation = (index: number) => {
    const startFrame = 30 + index * 25;
    const opacity = interpolate(frame, [startFrame, startFrame + 20], [0, 1], { extrapolateRight: 'clamp' });
    const scale = spring({ frame: frame - startFrame, fps, from: 0.8, to: 1, durationInFrames: 20 });
    return { opacity, scale };
  };

  // Progress line animation
  const progressWidth = interpolate(frame, [30, 130], [0, 75], { extrapolateRight: 'clamp' });

  // Auto-approval badge animation
  const autoApprovalOpacity = interpolate(frame, [140, 160], [0, 1], { extrapolateRight: 'clamp' });
  const autoApprovalScale = spring({ frame: frame - 140, fps, from: 0.5, to: 1, durationInFrames: 20 });

  return (
    <AbsoluteFill
      style={{
        background: 'linear-gradient(180deg, #0f172a 0%, #1e293b 100%)',
        padding: 60,
        fontFamily: 'system-ui, -apple-system, sans-serif',
      }}
    >
      {/* Header */}
      <div style={{ opacity: headerOpacity, marginBottom: 60 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <span style={{ fontSize: 48 }}>⚡</span>
          <h2 style={{ fontSize: 42, color: 'white', margin: 0, fontWeight: 700 }}>
            Agentic Workflow Orchestration
          </h2>
        </div>
        <p style={{ fontSize: 24, color: '#94a3b8', marginTop: 12 }}>
          4-stage automated pipeline with human-in-the-loop governance
        </p>
      </div>

      {/* Workflow Pipeline */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          position: 'relative',
          padding: '0 40px',
        }}
      >
        {/* Progress Line Background */}
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: 100,
            right: 100,
            height: 4,
            backgroundColor: 'rgba(148, 163, 184, 0.2)',
            transform: 'translateY(-50%)',
            borderRadius: 2,
          }}
        />
        
        {/* Progress Line Animated */}
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: 100,
            width: `${progressWidth}%`,
            height: 4,
            backgroundColor: '#22c55e',
            transform: 'translateY(-50%)',
            borderRadius: 2,
            boxShadow: '0 0 10px rgba(34, 197, 94, 0.5)',
          }}
        />

        {/* Stage Cards */}
        {stages.map((stage, index) => {
          const { opacity, scale } = getStageAnimation(index);
          return (
            <div
              key={stage.name}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                opacity,
                transform: `scale(${scale})`,
                zIndex: 1,
              }}
            >
              {/* Icon Circle */}
              <div
                style={{
                  width: 100,
                  height: 100,
                  borderRadius: '50%',
                  backgroundColor: stage.status === 'pending' ? 'rgba(100, 116, 139, 0.2)' : `${stage.color}20`,
                  border: `3px solid ${stage.color}`,
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  fontSize: 40,
                  boxShadow: stage.status === 'active' ? `0 0 20px ${stage.color}50` : 'none',
                }}
              >
                {stage.status === 'complete' ? '✓' : stage.icon}
              </div>
              
              {/* Label */}
              <span
                style={{
                  marginTop: 16,
                  fontSize: 20,
                  fontWeight: 600,
                  color: stage.status === 'pending' ? '#64748b' : '#f1f5f9',
                }}
              >
                {stage.name}
              </span>
              
              {/* Status Badge */}
              <span
                style={{
                  marginTop: 8,
                  padding: '4px 12px',
                  borderRadius: 12,
                  fontSize: 12,
                  fontWeight: 600,
                  backgroundColor: `${stage.color}20`,
                  color: stage.color,
                  textTransform: 'uppercase',
                }}
              >
                {stage.status}
              </span>
            </div>
          );
        })}
      </div>

      {/* Auto-Approval Info Box */}
      <div
        style={{
          marginTop: 60,
          opacity: autoApprovalOpacity,
          transform: `scale(${autoApprovalScale})`,
        }}
      >
        <div
          style={{
            backgroundColor: 'rgba(34, 197, 94, 0.1)',
            border: '2px solid rgba(34, 197, 94, 0.3)',
            borderRadius: 16,
            padding: 24,
            display: 'flex',
            alignItems: 'center',
            gap: 20,
          }}
        >
          <div
            style={{
              width: 60,
              height: 60,
              borderRadius: '50%',
              backgroundColor: 'rgba(34, 197, 94, 0.2)',
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              fontSize: 28,
            }}
          >
            🚀
          </div>
          <div>
            <h4 style={{ color: '#22c55e', fontSize: 22, margin: 0, fontWeight: 600 }}>
              Auto-Approval Enabled
            </h4>
            <p style={{ color: '#86efac', fontSize: 16, margin: '8px 0 0' }}>
              Low-risk decisions (confidence ≥95%) advance automatically. High-risk actions require human approval.
            </p>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
