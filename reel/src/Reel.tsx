import React from "react";
import {
  AbsoluteFill,
  Easing,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Audio } from "@remotion/media";
import { TransitionSeries, springTiming } from "@remotion/transitions";
import { slide } from "@remotion/transitions/slide";
import { wipe } from "@remotion/transitions/wipe";
import { fade } from "@remotion/transitions/fade";
import { StyleKey, Theme, THEMES } from "./theme";

export type Beat = {
  headline: string;
  body: string;
  chips: string[];
  number?: string | null;
  seconds: number;
  bg?: string | null;
};

export type ReelProps = {
  style: StyleKey;
  kicker: string;
  handle: string;
  beats: Beat[];
  cta: string;
  ctaSub: string;
  audio?: string | null;
  audioKind?: "voice" | "music" | "silent";
};

export const FPS = 30;
export const TRANSITION = 14;
export const OUTRO = 84;

export const beatFrames = (b: Beat) => Math.max(60, Math.round(b.seconds * FPS));
export const totalFrames = (p: ReelProps) =>
  p.beats.reduce((s, b) => s + beatFrames(b), 0) + OUTRO - TRANSITION * p.beats.length;

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const EMOJI = /(\p{Extended_Pictographic}(️|‍\p{Extended_Pictographic})*)/gu;
const splitEmoji = (t: string) => ({
  text: t.replace(EMOJI, "").replace(/\s+/g, " ").trim(),
  emoji: (t.match(EMOJI) || [])[0] || null,
});

/* ───────────────────────── background ───────────────────────── */
const Background: React.FC<{ theme: Theme }> = ({ theme }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  return (
    <AbsoluteFill style={{ background: `linear-gradient(160deg, ${theme.bg[0]}, ${theme.bg[1]})`, overflow: "hidden" }}>
      {theme.blobs.map((c, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            width: 760,
            height: 760,
            borderRadius: "50%",
            background: `radial-gradient(circle, ${c} 0%, ${c}00 68%)`,
            opacity: theme.pattern === "grid" ? 0.55 : 0.5,
            left: width * (0.15 + 0.35 * i) + Math.sin(frame / 70 + i * 2) * 220 - 380,
            top: height * (0.2 + 0.28 * i) + Math.cos(frame / 85 + i) * 260 - 380,
          }}
        />
      ))}
      {theme.pattern === "pearl" && <PearlRings />}
      {theme.pattern === "sadu" && <SaduBands theme={theme} />}
      {theme.pattern === "grid" && <MovingGrid />}
      <Grain />
    </AbsoluteFill>
  );
};

const PearlRings: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <svg width={1400} height={1400} style={{ position: "absolute", right: -520, top: -420, opacity: 0.35, rotate: `${frame * 0.15}deg` }}>
      {Array.from({ length: 9 }).map((_, i) => (
        <circle key={i} cx={700} cy={700} r={120 + i * 64 + Math.sin(frame / 25 + i) * 6} fill="none" stroke="#CDAE78" strokeWidth={3} />
      ))}
    </svg>
  );
};

const SaduBand: React.FC<{ theme: Theme; y: number; dir: 1 | -1 }> = ({ theme, y, dir }) => {
  const frame = useCurrentFrame();
  const unit = 76;
  const shift = ((frame * 2.2 * dir) % (unit * 2) + unit * 2) % (unit * 2);
  const n = 22;
  return (
    <svg width={1080 + unit * 4} height={unit + 36} style={{ position: "absolute", top: y, left: -unit * 2 - shift + unit }}>
      <rect x={0} y={18} width={1080 + unit * 4} height={unit} fill={theme.accent} />
      {Array.from({ length: n }).map((_, i) => {
        const cx = i * unit + unit / 2;
        const cy = 18 + unit / 2;
        const col = i % 2 ? "#1E1A17" : "#F7EEDC";
        return (
          <g key={i}>
            <polygon points={`${cx},${cy - 32} ${cx + 32},${cy} ${cx},${cy + 32} ${cx - 32},${cy}`} fill={col} />
            <polygon points={`${cx},${cy - 12} ${cx + 12},${cy} ${cx},${cy + 12} ${cx - 12},${cy}`} fill={theme.accent} />
            <polygon points={`${i * unit},16 ${i * unit + unit / 2},2 ${i * unit + unit},16`} fill={i % 2 ? theme.accent : "#1E1A17"} />
            <polygon points={`${i * unit},${unit + 20} ${i * unit + unit / 2},${unit + 34} ${i * unit + unit},${unit + 20}`} fill={i % 2 ? "#1E1A17" : theme.accent} />
          </g>
        );
      })}
    </svg>
  );
};

const SaduBands: React.FC<{ theme: Theme }> = ({ theme }) => (
  <>
    <SaduBand theme={theme} y={190} dir={1} />
    <SaduBand theme={theme} y={1920 - 300} dir={-1} />
  </>
);

const MovingGrid: React.FC = () => {
  const frame = useCurrentFrame();
  const off = (frame * 1.5) % 90;
  return (
    <AbsoluteFill
      style={{
        backgroundImage:
          "linear-gradient(rgba(255,255,255,0.08) 2px, transparent 2px), linear-gradient(90deg, rgba(255,255,255,0.08) 2px, transparent 2px)",
        backgroundSize: "90px 90px",
        backgroundPosition: `${off}px ${off}px`,
      }}
    >
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          height: 260,
          top: ((frame * 9) % 2400) - 300,
          background: "linear-gradient(transparent, rgba(255,255,255,0.10), transparent)",
        }}
      />
    </AbsoluteFill>
  );
};

const Grain: React.FC = () => (
  <svg width="100%" height="100%" style={{ position: "absolute", inset: 0, opacity: 0.07, mixBlendMode: "overlay" }}>
    <filter id="n">
      <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={2} />
    </filter>
    <rect width="100%" height="100%" filter="url(#n)" />
  </svg>
);

/* ───────────────────────── text animation ───────────────────────── */
const ARABIC = /[\u0600-\u06FF]/;
const LATIN = /[A-Za-z]/;
// Arabic words animate one by one; consecutive Latin/number words are kept as one LTR chunk
const tokens = (line: string): string[] => {
  const out: string[] = [];
  for (const w of line.split(" ").filter(Boolean)) {
    const prev = out[out.length - 1];
    // join only words that contain Latin letters (or numbers glued to them, like "3x3")
    if (prev !== undefined && LATIN.test(w) && LATIN.test(prev) && !ARABIC.test(w) && !ARABIC.test(prev)) out[out.length - 1] = `${prev} ${w}`;
    else out.push(w);
  }
  return out;
};
const Words: React.FC<{ text: string; delay: number; size: number; font: string; weight: number; color: string; stagger?: number; lineHeight?: number }> = ({
  text, delay, size, font, weight, color, stagger = 3, lineHeight = 1.25,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const lines = text.split("\n");
  let k = 0;
  return (
    <div style={{ direction: "rtl", textAlign: "center" }}>
      {lines.map((line, li) => (
        <div key={li} style={{ display: "flex", flexWrap: "wrap", justifyContent: "center", gap: `0 ${size * 0.28}px`, direction: "rtl" }}>
          {tokens(line).map((w, wi) => {
            const s = spring({ frame: frame - delay - k++ * stagger, fps, config: { damping: 14, stiffness: 160, mass: 0.7 } });
            return (
              <span
                key={wi}
                style={{
                  display: "inline-block",
                  direction: LATIN.test(w) && !ARABIC.test(w) ? "ltr" : "rtl",
                  unicodeBidi: "isolate",
                  fontFamily: font,
                  fontWeight: weight,
                  fontSize: size,
                  lineHeight,
                  color,
                  opacity: interpolate(s, [0, 0.4], [0, 1], clamp),
                  translate: `0px ${interpolate(s, [0, 1], [size * 0.7, 0])}px`,
                  scale: interpolate(s, [0, 1], [0.7, 1]),
                  filter: `blur(${interpolate(s, [0, 1], [10, 0])}px)`,
                }}
              >
                {w}
              </span>
            );
          })}
        </div>
      ))}
    </div>
  );
};

const Counter: React.FC<{ value: string; theme: Theme; delay: number }> = ({ value, theme, delay }) => {
  const frame = useCurrentFrame();
  const m = value.match(/^([^\d]*)([\d.,]+)(.*)$/);
  if (!m) return null;
  const target = parseFloat(m[2].replace(/,/g, ""));
  const decimals = (m[2].split(".")[1] || "").length;
  const p = interpolate(frame - delay, [0, 32], [0, 1], { ...clamp, easing: Easing.bezier(0.16, 1, 0.3, 1) });
  const shown = (target * p).toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
  return (
    <div
      style={{
        fontFamily: "Cairo",
        fontWeight: 1000,
        fontSize: value.length > 8 ? 170 : 230,
        lineHeight: 1,
        color: theme.accent,
        direction: "ltr",
        textAlign: "center",
        scale: interpolate(frame - delay, [0, 10, 18], [0.6, 1.08, 1], clamp),
        opacity: interpolate(frame - delay, [0, 6], [0, 1], clamp),
        textShadow: theme.pattern === "grid" ? "0 10px 40px rgba(0,0,0,0.35)" : "none",
      }}
    >
      {m[1]}
      {shown}
      {m[3]}
    </div>
  );
};

const Chips: React.FC<{ chips: string[]; theme: Theme; delay: number }> = ({ chips, theme, delay }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 18, marginTop: 40 }}>
      {chips.map((c, i) => {
        const s = spring({ frame: frame - delay - i * 6, fps, config: { damping: 15, stiffness: 140 } });
        const isDate = /\d/.test(c) && /(يناير|فبراير|مارس|أبريل|مايو|يونيو|يوليو|أغسطس|سبتمبر|أكتوبر|نوفمبر|ديسمبر|\d{1,2}[-–]\d{1,2})/.test(c);
        return (
          <div
            key={i}
            style={{
              direction: "rtl",
              display: "flex",
              alignItems: "center",
              gap: 16,
              padding: "16px 34px",
              borderRadius: 999,
              background: i === 0 ? theme.accent : "rgba(255,255,255,0.88)",
              color: i === 0 ? theme.onAccent : "#14181d",
              fontFamily: "Tajawal",
              fontWeight: 800,
              fontSize: 46,
              boxShadow: "0 12px 30px rgba(0,0,0,0.18)",
              translate: `${interpolate(s, [0, 1], [-700, 0])}px 0px`,
              rotate: `${interpolate(s, [0, 1], [-6, 0])}deg`,
            }}
          >
            <span style={{ fontSize: 44 }}>{isDate ? "🗓️" : "📍"}</span>
            <span>{c}</span>
          </div>
        );
      })}
    </div>
  );
};

/* ───────────────────────── scenes ───────────────────────── */
const BeatScene: React.FC<{ beat: Beat; index: number; theme: Theme }> = ({ beat, index, theme }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const head = splitEmoji(beat.headline);
  const body = splitEmoji(beat.body);
  const emoji = head.emoji || body.emoji;
  const isHook = index === 0;
  const len = head.text.length;
  const size = isHook ? (len > 34 ? 104 : len > 20 ? 124 : 150) : len > 40 ? 88 : len > 24 ? 104 : 120;
  const headDelay = beat.number ? 16 : 4;
  const words = head.text.split(/\s+/).length;
  const bodyDelay = headDelay + words * 3 + 8;
  const chipDelay = bodyDelay + 10;
  const hookPunch = isHook ? interpolate(frame, [0, 8, 16], [1.25, 0.97, 1], clamp) : 1;
  const shake = isHook && frame < 10 ? Math.sin(frame * 3) * (10 - frame) : 0;
  const emojiS = spring({ frame: frame - 2, fps, config: { damping: 8, stiffness: 120 } });
  const markerP = interpolate(frame, [headDelay + words * 3, headDelay + words * 3 + 12], [0, 1], { ...clamp, easing: Easing.bezier(0.65, 0, 0.35, 1) });
  const drift = interpolate(frame, [0, durationInFrames], [0, -40]);

  return (
    <AbsoluteFill>
      {beat.bg && (
        <AbsoluteFill style={{ overflow: "hidden" }}>
          <Img
            src={staticFile(beat.bg)}
            style={{ width: "100%", height: "100%", objectFit: "cover", scale: interpolate(frame, [0, durationInFrames], [1.05, 1.18]) }}
          />
          <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,0.25), rgba(0,0,0,0.65))" }} />
        </AbsoluteFill>
      )}
      <AbsoluteFill
        style={{
          justifyContent: "center",
          alignItems: "center",
          padding: "0 130px",
          scale: hookPunch,
          translate: `${shake}px ${drift}px`,
        }}
      >
        {emoji && (
          <div
            style={{
              fontSize: isHook ? 190 : 150,
              marginBottom: 24,
              scale: interpolate(emojiS, [0, 1], [0, 1]),
              rotate: `${Math.sin(frame / 9) * 8}deg`,
              translate: `0px ${Math.sin(frame / 12) * 10}px`,
            }}
          >
            {emoji}
          </div>
        )}
        {beat.number && <Counter value={beat.number} theme={theme} delay={2} />}
        <div style={{ position: "relative", marginTop: 10 }}>
          <div
            style={{
              position: "absolute",
              right: -20,
              left: -20,
              bottom: size * 0.08,
              height: size * 0.38,
              background: theme.accent2,
              opacity: theme.pattern === "grid" ? 0.25 : 0.55,
              borderRadius: 12,
              scale: `${markerP} 1`,
              transformOrigin: "right center",
            }}
          />
          <div style={{ position: "relative" }}>
            <Words text={head.text} delay={headDelay} size={size} font={theme.head} weight={theme.head === "Cairo" ? 900 : 700} color={beat.bg ? "#FFFFFF" : theme.ink} />
          </div>
        </div>
        {body.text && (
          <div style={{ marginTop: 34, maxWidth: 820 }}>
            <Words text={body.text} delay={bodyDelay} size={52} font={theme.body} weight={500} color={beat.bg ? "#EDEDED" : theme.sub} stagger={2} lineHeight={1.45} />
          </div>
        )}
        {beat.chips.length > 0 && <Chips chips={beat.chips} theme={theme} delay={chipDelay} />}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const Outro: React.FC<{ theme: Theme; cta: string; ctaSub: string; handle: string }> = ({ theme, cta, ctaSub, handle }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - 18, fps, config: { damping: 10, stiffness: 120 } });
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <svg width={1600} height={1600} style={{ position: "absolute", rotate: `${frame * 0.6}deg`, opacity: 0.18 }}>
        {Array.from({ length: 24 }).map((_, i) => (
          <polygon key={i} points="800,800 780,0 820,0" fill={theme.accent} transform={`rotate(${i * 15} 800 800)`} />
        ))}
      </svg>
      <Words text={cta} delay={2} size={140} font="Lalezar" weight={400} color={theme.ink} stagger={4} />
      <div style={{ marginTop: 20 }}>
        <Words text={ctaSub} delay={12} size={64} font={theme.body} weight={700} color={theme.sub} />
      </div>
      <div
        style={{
          marginTop: 60,
          padding: "22px 56px",
          borderRadius: 999,
          background: theme.accent,
          color: theme.onAccent,
          fontFamily: "Cairo",
          fontWeight: 900,
          fontSize: 64,
          direction: "ltr",
          scale: interpolate(s, [0, 1], [0, 1]) * (1 + Math.sin(frame / 6) * 0.03),
          boxShadow: "0 20px 60px rgba(0,0,0,0.25)",
        }}
      >
        {handle}
      </div>
    </AbsoluteFill>
  );
};

/* ───────────────────────── chrome: logo + progress ───────────────────────── */
const Chrome: React.FC<{ p: ReelProps; theme: Theme }> = ({ p, theme }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const starts: number[] = [];
  let acc = 0;
  for (const b of p.beats) {
    starts.push(acc);
    acc += beatFrames(b) - TRANSITION;
  }
  const inP = interpolate(frame, [0, 14], [0, 1], { ...clamp, easing: Easing.bezier(0.16, 1, 0.3, 1) });
  const light = theme.pattern === "grid";
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div style={{ position: "absolute", top: 100, left: 90, right: 90, display: "flex", gap: 10, direction: "rtl" }}>
        {p.beats.map((b, i) => {
          const f = interpolate(frame, [starts[i], starts[i] + beatFrames(b) - TRANSITION], [0, 1], clamp);
          return (
            <div key={i} style={{ flex: 1, height: 8, borderRadius: 4, background: light ? "rgba(255,255,255,0.25)" : "rgba(0,0,0,0.12)", overflow: "hidden" }}>
              <div style={{ width: `${f * 100}%`, height: "100%", background: theme.accent, marginLeft: "auto" }} />
            </div>
          );
        })}
      </div>
      <div
        style={{
          position: "absolute",
          top: 135,
          right: 90,
          left: 90,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          direction: "rtl",
          opacity: inP * interpolate(frame, [durationInFrames - OUTRO + 4, durationInFrames - OUTRO + 14], [1, 0], clamp),
          translate: `0px ${interpolate(inP, [0, 1], [-40, 0])}px`,
        }}
      >
        <div style={{ fontFamily: "Lalezar", fontSize: 58, color: theme.ink, background: light ? "transparent" : "rgba(255,255,255,0.0)" }}>وين اليوم</div>
        <div
          style={{
            fontFamily: "Tajawal",
            fontWeight: 800,
            fontSize: 34,
            color: theme.onAccent,
            background: theme.accent,
            padding: "8px 24px",
            borderRadius: 10,
          }}
        >
          {p.kicker}
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* ───────────────────────── main ───────────────────────── */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const PRESENTATIONS: Array<() => any> = [
  () => slide({ direction: "from-left" }),
  () => wipe({ direction: "from-left" }),
  () => slide({ direction: "from-bottom" }),
  () => fade(),
];

export const Reel: React.FC<ReelProps> = (p) => {
  const theme = THEMES[p.style] || THEMES.sadu;
  const items: React.ReactNode[] = [];
  p.beats.forEach((b, i) => {
    items.push(
      <TransitionSeries.Sequence key={`b${i}`} durationInFrames={beatFrames(b)}>
        <BeatScene beat={b} index={i} theme={theme} />
      </TransitionSeries.Sequence>,
    );
    items.push(
      <TransitionSeries.Transition
        key={`t${i}`}
        presentation={PRESENTATIONS[i % PRESENTATIONS.length]()}
        timing={springTiming({ config: { damping: 200 }, durationInFrames: TRANSITION })}
      />,
    );
  });
  items.push(
    <TransitionSeries.Sequence key="outro" durationInFrames={OUTRO}>
      <Outro theme={theme} cta={p.cta} ctaSub={p.ctaSub} handle={p.handle} />
    </TransitionSeries.Sequence>,
  );
  return (
    <AbsoluteFill>
      <Background theme={theme} />
      <TransitionSeries>{items}</TransitionSeries>
      <Chrome p={p} theme={theme} />
      {p.audio && (
        <Audio
          src={staticFile(p.audio)}
          volume={(f) =>
            p.audioKind === "music"
              ? interpolate(f, [0, 15, totalFrames(p) - 45, totalFrames(p)], [0, 0.8, 0.8, 0], clamp)
              : 1
          }
        />
      )}
    </AbsoluteFill>
  );
};
