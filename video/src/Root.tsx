import React from 'react';
import { Composition } from 'remotion';
import { PubliReportage } from './PubliReportage';
import timeline from '../public/timeline.json';

export const Root: React.FC = () => (
  <Composition
    id="PubliReportage"
    component={PubliReportage}
    durationInFrames={Math.ceil(timeline.total * timeline.fps)}
    fps={timeline.fps}
    width={1920}
    height={1080}
  />
);
