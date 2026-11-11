import React from "react";
import { CalculateMetadataFunction, Composition } from "remotion";
import { FPS, Reel, ReelProps, totalFrames } from "./Reel";
import { loadFonts } from "./theme";

loadFonts();

const sample: ReelProps = {
  style: "sadu",
  kicker: "فعاليات البحرين",
  handle: "@waynalyoum",
  cta: "احفظ 📌",
  ctaSub: "وأرسله لربعك اللي بيجي معك",
  audio: null,
  audioKind: "silent",
  beats: [
    { headline: "نوفمبر في البحرين = 3 ويكندات ما تنفوّت 🔥", body: "", chips: [], seconds: 3 },
    { headline: "Royal Bahrain Concours 🚗", body: "سيارات كلاسيكية ونادرة من كل العالم", chips: ["6–7 نوفمبر", "النادي الملكي للغولف – الرفاع"], seconds: 6 },
    { headline: "FIBA 3x3 Manama Masters 🏀", body: "16 فريق من العالم… ومعهم فريق سيف", chips: ["20–21 نوفمبر", "الأفنيوز – المنامة"], number: "16", seconds: 6 },
    { headline: "Jewellery Arabia + Scent Arabia 💎", body: "مجوهرات وساعات وعطور بمكان واحد", chips: ["24–28 نوفمبر", "مركز البحرين العالمي للمعارض"], seconds: 6 },
  ],
};

const calculateMetadata: CalculateMetadataFunction<ReelProps> = ({ props }) => ({
  durationInFrames: totalFrames(props),
});

export const RemotionRoot: React.FC = () => (
  <Composition
    id="Reel"
    component={Reel}
    fps={FPS}
    width={1080}
    height={1920}
    durationInFrames={300}
    defaultProps={sample}
    calculateMetadata={calculateMetadata}
  />
);
