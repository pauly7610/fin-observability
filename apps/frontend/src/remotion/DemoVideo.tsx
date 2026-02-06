import { AbsoluteFill, Sequence, useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';
import { IntroScene } from './scenes/IntroScene';
import { ComplianceAgentScene } from './scenes/ComplianceAgentScene';
import { AgenticWorkflowScene } from './scenes/AgenticWorkflowScene';
import { AnomalyDetectionScene } from './scenes/AnomalyDetectionScene';
import { OutroScene } from './scenes/OutroScene';

export const DemoVideo: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: '#0f172a' }}>
      {/* Intro - 0 to 150 frames (5 seconds) */}
      <Sequence from={0} durationInFrames={150}>
        <IntroScene />
      </Sequence>

      {/* Compliance Agent Demo - 150 to 400 frames (8.3 seconds) */}
      <Sequence from={150} durationInFrames={250}>
        <ComplianceAgentScene />
      </Sequence>

      {/* Agentic Workflow Demo - 400 to 600 frames (6.7 seconds) */}
      <Sequence from={400} durationInFrames={200}>
        <AgenticWorkflowScene />
      </Sequence>

      {/* Anomaly Detection Demo - 600 to 780 frames (6 seconds) */}
      <Sequence from={600} durationInFrames={180}>
        <AnomalyDetectionScene />
      </Sequence>

      {/* Outro - 780 to 900 frames (4 seconds) */}
      <Sequence from={780} durationInFrames={120}>
        <OutroScene />
      </Sequence>
    </AbsoluteFill>
  );
};
