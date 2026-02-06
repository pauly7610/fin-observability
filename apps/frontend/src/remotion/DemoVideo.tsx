import { AbsoluteFill, Sequence, useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';
import { IntroScene } from './scenes/IntroScene';
import { ComplianceAgentScene } from './scenes/ComplianceAgentScene';
import { AgenticWorkflowScene } from './scenes/AgenticWorkflowScene';
import { AnomalyDetectionScene } from './scenes/AnomalyDetectionScene';
import { ExplainabilityScene } from './scenes/ExplainabilityScene';
import { ProductionDeployScene } from './scenes/ProductionDeployScene';
import { AutoRetrainingScene } from './scenes/AutoRetrainingScene';
import { OutroScene } from './scenes/OutroScene';

export const DemoVideo: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: '#0f172a' }}>
      {/* Intro - 0 to 150 frames (5s) */}
      <Sequence from={0} durationInFrames={150}>
        <IntroScene />
      </Sequence>

      {/* Compliance Agent Demo - 150 to 400 frames (8.3s) */}
      <Sequence from={150} durationInFrames={250}>
        <ComplianceAgentScene />
      </Sequence>

      {/* Agentic Workflow Demo - 400 to 600 frames (6.7s) */}
      <Sequence from={400} durationInFrames={200}>
        <AgenticWorkflowScene />
      </Sequence>

      {/* Anomaly Detection Demo - 600 to 780 frames (6s) */}
      <Sequence from={600} durationInFrames={180}>
        <AnomalyDetectionScene />
      </Sequence>

      {/* SHAP Explainability - 780 to 1020 frames (8s) */}
      <Sequence from={780} durationInFrames={240}>
        <ExplainabilityScene />
      </Sequence>

      {/* Production Deploy + OTel - 1020 to 1260 frames (8s) */}
      <Sequence from={1020} durationInFrames={240}>
        <ProductionDeployScene />
      </Sequence>

      {/* Auto-Retraining + ONNX - 1260 to 1530 frames (9s) */}
      <Sequence from={1260} durationInFrames={270}>
        <AutoRetrainingScene />
      </Sequence>

      {/* Outro - 1530 to 1680 frames (5s) */}
      <Sequence from={1530} durationInFrames={150}>
        <OutroScene />
      </Sequence>
    </AbsoluteFill>
  );
};
