import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';

export const IntroScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const line1Opacity = interpolate(frame, [0, 25], [0, 1], { extrapolateRight: 'clamp' });
  const line1Y = spring({ frame, fps, from: -30, to: 0, durationInFrames: 25 });

  const line2Opacity = interpolate(frame, [20, 45], [0, 1], { extrapolateRight: 'clamp' });
  const line2Y = spring({ frame: frame - 20, fps, from: -20, to: 0, durationInFrames: 25 });

  const questions = [
    'Why did the model flag this?',
    'Is it still accurate?',
    'Who approved what?',
  ];

  const getQuestionOpacity = (index: number) => {
    const startFrame = 55 + index * 20;
    return interpolate(frame, [startFrame, startFrame + 15], [0, 1], { extrapolateRight: 'clamp' });
  };

  const getQuestionY = (index: number) => {
    const startFrame = 55 + index * 20;
    return spring({ frame: frame - startFrame, fps, from: 20, to: 0, durationInFrames: 15 });
  };

  const endOpacity = interpolate(frame, [125, 145], [0, 1], { extrapolateRight: 'clamp' });
  const endScale = spring({ frame: frame - 125, fps, from: 0.9, to: 1, durationInFrames: 20 });

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

      <div style={{ textAlign: 'center', maxWidth: 800 }}>
        {/* Line 1 */}
        <p
          style={{
            fontSize: 36,
            fontWeight: 600,
            color: 'white',
            margin: 0,
            opacity: line1Opacity,
            transform: `translateY(${line1Y}px)`,
          }}
        >
          AI models make high-stakes financial decisions.
        </p>

        {/* Line 2 */}
        <p
          style={{
            fontSize: 36,
            fontWeight: 600,
            color: '#94a3b8',
            margin: '16px 0 48px',
            opacity: line2Opacity,
            transform: `translateY(${line2Y}px)`,
          }}
        >
          Most teams have no idea why.
        </p>

        {/* Three questions */}
        {questions.map((q, index) => (
          <p
            key={q}
            style={{
              fontSize: 28,
              color: '#60a5fa',
              margin: '12px 0',
              opacity: getQuestionOpacity(index),
              transform: `translateY(${getQuestionY(index)}px)`,
              fontWeight: 500,
            }}
          >
            {q}
          </p>
        ))}

        {/* End line */}
        <p
          style={{
            fontSize: 40,
            fontWeight: 800,
            color: 'white',
            margin: '40px 0 0',
            opacity: endOpacity,
            transform: `scale(${endScale})`,
          }}
        >
          We answer all three.
        </p>
      </div>
    </AbsoluteFill>
  );
};
