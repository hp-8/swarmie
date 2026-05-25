import React from "react";
import {
  AbsoluteFill,
  Sequence,
  Audio,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Easing,
  spring,
} from "remotion";
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { loadFont as loadDM } from "@remotion/google-fonts/DMMono";

const HAS_MUSIC = true;

// Camera wrapper — animated transform around scene content for parallax/zoom
const Camera: React.FC<React.PropsWithChildren<{
  scaleFrom?: number;
  scaleTo?: number;
  panX?: number;
  panY?: number;
  rotate?: number;
  duration: number;
  shakeAt?: number;
  shakeIntensity?: number;
}>> = ({
  children,
  scaleFrom = 1,
  scaleTo = 1,
  panX = 0,
  panY = 0,
  rotate = 0,
  duration,
  shakeAt,
  shakeIntensity = 0,
}) => {
  const frame = useCurrentFrame();
  const t = Math.min(1, Math.max(0, frame / duration));
  const ease = Easing.bezier(0.5, 0, 0.5, 1)(t);
  const scale = scaleFrom + (scaleTo - scaleFrom) * ease;
  const tx = panX * ease;
  const ty = panY * ease;
  const rot = rotate * ease;
  let sx = 0,
    sy = 0;
  if (shakeAt !== undefined && shakeIntensity > 0) {
    const sd = frame - shakeAt;
    if (sd >= 0 && sd < 14) {
      const decay = 1 - sd / 14;
      sx = Math.sin(sd * 2.3) * shakeIntensity * decay;
      sy = Math.cos(sd * 2.7) * shakeIntensity * decay;
    }
  }
  return (
    <AbsoluteFill
      style={{
        transform: `translate(${tx + sx}px, ${ty + sy}px) scale(${scale}) rotate(${rot}deg)`,
        transformOrigin: "center center",
      }}
    >
      {children}
    </AbsoluteFill>
  );
};

const { fontFamily: INTER } = loadInter();
const { fontFamily: MONO } = loadDM();

export const PROMO_FPS = 30;
export const PROMO_DURATION = 420; // 14s
export const PROMO_WIDTH = 1920;
export const PROMO_HEIGHT = 1080;

// Palette — cream + bright
const CREAM = "#f5efe2";
const CREAM_2 = "#ece4d2";
const INK = "#191814";
const INK_SOFT = "#5e574c";
const ORANGE = "#ff6b35";
const YELLOW = "#ffc94f";
const BLUE = "#2d6ef7";
const TEAL = "#15c1a3";
const PINK = "#ff5da2";
const RED = "#ff3b3b";

// Deterministic PRNG
function mulberry(seed: number) {
  return () => {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const easeOut = Easing.bezier(0.16, 1, 0.3, 1);
const easeInOut = Easing.bezier(0.65, 0, 0.35, 1);

// ============ Scene 1 (0..60) — comment chaos rain ============
const COMMENTS = [
  { text: "This solves nothing.", color: RED, w: 240 },
  { text: "wait this is smart", color: TEAL, w: 220 },
  { text: "Too expensive.", color: ORANGE, w: 200 },
  { text: "I'd use this.", color: BLUE, w: 180 },
  { text: "Who is this for?", color: INK, w: 230 },
  { text: "This could blow up 🚀", color: PINK, w: 260 },
  { text: "another GPT wrapper?", color: ORANGE, w: 270 },
  { text: "shut up and take my $", color: TEAL, w: 240 },
  { text: "where's the moat", color: RED, w: 210 },
  { text: "ngl this is cool", color: BLUE, w: 200 },
  { text: "needs better onboarding", color: YELLOW, w: 270 },
  { text: "ok but pricing?", color: ORANGE, w: 200 },
  { text: "✓ signed up", color: TEAL, w: 160 },
  { text: "saw this on HN already", color: INK_SOFT, w: 240 },
];

const Scene1: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const rng = mulberry(21);

  // Distribute bubbles in a soft 6x5 jittered grid so screen fills evenly
  const cols = 6;
  const rows = 5;
  const cellW = width / cols;
  const cellH = height / rows;
  const bubbles = Array.from({ length: cols * rows }, (_, i) => {
    const cx = (i % cols) * cellW + cellW / 2;
    const cy = Math.floor(i / cols) * cellH + cellH / 2;
    const jitterX = (rng() - 0.5) * cellW * 0.45;
    const jitterY = (rng() - 0.5) * cellH * 0.45;
    const c = COMMENTS[i % COMMENTS.length];
    const angle = rng() * Math.PI * 2;
    const speed = 30 + rng() * 60;
    const delay = (i * 13) % 40; // pseudorandom stagger
    const rotate = (rng() - 0.5) * 10;
    return {
      ...c,
      startX: cx + jitterX - 120,
      startY: cy + jitterY - 24,
      angle,
      speed,
      delay,
      rotate,
      idx: i,
    };
  });

  return (
    <Camera duration={60} scaleFrom={1.18} scaleTo={1.0} panX={-30} panY={0}>
    <AbsoluteFill style={{ background: CREAM }}>
      {/* grain overlay */}
      <GrainTexture />

      {bubbles.map((b) => {
        const localFrame = frame - b.delay;
        if (localFrame < 0) return null;

        const enter = spring({
          frame: localFrame,
          fps,
          config: { damping: 12, mass: 0.5, stiffness: 140 },
        });
        const dx = Math.cos(b.angle) * b.speed * (localFrame / fps);
        const dy = Math.sin(b.angle) * b.speed * (localFrame / fps);
        const fade = interpolate(localFrame, [0, 4, 40, 55], [0, 1, 1, 0], {
          extrapolateRight: "clamp",
          extrapolateLeft: "clamp",
        });

        return (
          <div
            key={b.idx}
            style={{
              position: "absolute",
              left: b.startX,
              top: b.startY,
              transform: `translate(${dx}px, ${dy}px) scale(${enter}) rotate(${b.rotate}deg)`,
              opacity: fade,
              background: "white",
              border: `1.5px solid ${b.color}`,
              borderRadius: 22,
              padding: "12px 22px",
              fontFamily: INTER,
              fontSize: 24,
              fontWeight: 600,
              color: b.color,
              boxShadow: "0 8px 24px rgba(0,0,0,0.06)",
              whiteSpace: "nowrap",
            }}
          >
            {b.text}
          </div>
        );
      })}

      {/* tiny arrows + notification dots */}
      {Array.from({ length: 12 }).map((_, i) => {
        const x = rng() * width;
        const y = rng() * height;
        const f = (frame + i * 4) % 60;
        const op = interpolate(f, [0, 10, 30, 60], [0, 1, 1, 0]);
        return (
          <div
            key={`d-${i}`}
            style={{
              position: "absolute",
              left: x,
              top: y,
              width: 10,
              height: 10,
              borderRadius: 99,
              background: i % 2 ? ORANGE : BLUE,
              opacity: op * 0.5,
            }}
          />
        );
      })}
    </AbsoluteFill>
    </Camera>
  );
};

// ============ Scene 2 (60..150) — pitch card → swarm activation ============
const Scene2: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const cx = width / 2;
  const cy = height / 2;
  const rng = mulberry(42);

  // Card slides in 0..15, holds 15..40, then nodes blast from 40..90
  const cardEnter = spring({ frame, fps, config: { damping: 15, mass: 0.6, stiffness: 120 } });
  const cardLift = interpolate(frame, [40, 60], [0, -40], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  const cardScale = interpolate(frame, [40, 60], [1, 0.85], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  const cardFade = interpolate(frame, [55, 80], [1, 0.18], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Nodes appear from 40
  const nodeCount = 80;
  const nodeReveal = interpolate(frame, [40, 90], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });

  const nodes = Array.from({ length: nodeCount }, (_, i) => {
    const angle = (i / nodeCount) * Math.PI * 2 + rng() * 0.4;
    const r = 200 + rng() * 280;
    const colorPool = [ORANGE, YELLOW, BLUE, TEAL, PINK];
    const color = colorPool[i % colorPool.length];
    const appearAt = 40 + (i / nodeCount) * 30;
    return { angle, r, color, appearAt, i };
  });

  // Text reveal 65..85
  const textOp = interpolate(frame, [65, 78], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  const textY = interpolate(frame, [65, 78], [12, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });

  return (
    <Camera duration={90} scaleFrom={1.0} scaleTo={1.1} panY={-15} shakeAt={40} shakeIntensity={10}>
    <AbsoluteFill style={{ background: CREAM }}>
      <GrainTexture />

      {/* node bloom */}
      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        {nodes.map((n) => {
          if (frame < n.appearAt) return null;
          const local = frame - n.appearAt;
          const t = Math.min(1, local / 20);
          const r = n.r * t;
          const x = cx + Math.cos(n.angle) * r;
          const y = cy + Math.sin(n.angle) * r;
          const op = interpolate(local, [0, 6, 35], [0, 1, 0.9], { extrapolateRight: "clamp" });
          return (
            <g key={n.i}>
              <line x1={cx} y1={cy} x2={x} y2={y} stroke={n.color} strokeOpacity={op * 0.25} strokeWidth={1} />
              <circle cx={x} cy={y} r={5 + (1 - t) * 6} fill={n.color} opacity={op} />
            </g>
          );
        })}
      </svg>

      {/* pitch card */}
      <div
        style={{
          position: "absolute",
          left: cx - 280,
          top: cy - 170 + cardLift,
          width: 560,
          background: "white",
          borderRadius: 18,
          padding: 28,
          fontFamily: INTER,
          boxShadow: "0 30px 60px -20px rgba(0,0,0,0.18)",
          transform: `scale(${cardEnter * cardScale})`,
          transformOrigin: "center",
          opacity: cardFade,
          border: `1px solid ${CREAM_2}`,
        }}
      >
        <div style={{ display: "flex", gap: 8, marginBottom: 14 }}>
          <span style={{ width: 10, height: 10, borderRadius: 99, background: ORANGE }} />
          <span style={{ width: 10, height: 10, borderRadius: 99, background: YELLOW }} />
          <span style={{ width: 10, height: 10, borderRadius: 99, background: TEAL }} />
        </div>
        <div style={{ fontSize: 14, fontFamily: MONO, color: INK_SOFT, letterSpacing: 2, textTransform: "uppercase" }}>
          your pitch
        </div>
        <div style={{ fontSize: 32, fontWeight: 700, color: INK, marginTop: 8, lineHeight: 1.2 }}>
          AI-native CRM for indie founders.
        </div>
        <div style={{ fontSize: 18, color: INK_SOFT, marginTop: 12, lineHeight: 1.4 }}>
          Auto-logs every conversation. $19/mo. Free for solo.
        </div>
        <div style={{ display: "flex", gap: 8, marginTop: 18 }}>
          <Chip color={BLUE}>B2B</Chip>
          <Chip color={TEAL}>SaaS</Chip>
          <Chip color={ORANGE}>$19/mo</Chip>
        </div>
      </div>

      {/* center pulse */}
      <div
        style={{
          position: "absolute",
          left: cx - 40,
          top: cy - 40,
          width: 80,
          height: 80,
          borderRadius: 99,
          background: ORANGE,
          opacity: nodeReveal,
          boxShadow: `0 0 60px ${ORANGE}`,
        }}
      />

      {/* text overlay */}
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          bottom: 120,
          textAlign: "center",
          fontFamily: INTER,
          fontWeight: 800,
          fontSize: 72,
          color: INK,
          opacity: textOp,
          transform: `translateY(${textY}px)`,
          letterSpacing: -1.5,
        }}
      >
        500 AI users <span style={{ color: ORANGE }}>activated.</span>
      </div>
    </AbsoluteFill>
    </Camera>
  );
};

const Chip: React.FC<React.PropsWithChildren<{ color: string }>> = ({ color, children }) => (
  <span
    style={{
      padding: "5px 12px",
      borderRadius: 99,
      background: `${color}1a`,
      color,
      fontSize: 14,
      fontWeight: 600,
      fontFamily: MONO,
      letterSpacing: 0.5,
    }}
  >
    {children}
  </span>
);

// ============ Scene 3 (150..270) — modular UI dashboards ============
const Scene3: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const rng = mulberry(99);

  // 6 panel slots, staggered enter
  const panels = [
    { kind: "objections" as const, x: 80, y: 100, w: 460, h: 280 },
    { kind: "sentiment" as const, x: 580, y: 100, w: 460, h: 200 },
    { kind: "pmf" as const, x: 1080, y: 100, w: 760, h: 280 },
    { kind: "feed" as const, x: 80, y: 420, w: 600, h: 560 },
    { kind: "personas" as const, x: 720, y: 320, w: 580, h: 380 },
    { kind: "icp" as const, x: 1340, y: 420, w: 500, h: 380 },
    { kind: "kpi1" as const, x: 720, y: 720, w: 280, h: 260 },
    { kind: "kpi2" as const, x: 1020, y: 720, w: 280, h: 260 },
    { kind: "tagline" as const, x: 1340, y: 820, w: 500, h: 160 },
  ];

  const tagFrame = frame - 40;
  const tags = [
    { text: "Top objection found", color: ORANGE, at: 6 },
    { text: "Messaging gap detected", color: BLUE, at: 30 },
    { text: "ICP match: indie devs", color: TEAL, at: 56 },
    { text: "Score: 7.4 / 10", color: INK, at: 82 },
  ];

  return (
    <Camera duration={120} scaleFrom={1.08} scaleTo={1.0} panX={15} panY={-10}>
    <AbsoluteFill style={{ background: CREAM }}>
      <GrainTexture />

      {panels.map((p, i) => {
        const delay = i * 5;
        const local = frame - delay;
        const enter = spring({ frame: local, fps, config: { damping: 14, mass: 0.6, stiffness: 110 } });
        const op = interpolate(local, [0, 8], [0, 1], { extrapolateRight: "clamp" });
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: p.x,
              top: p.y,
              width: p.w,
              height: p.h,
              transform: `scale(${0.85 + enter * 0.15})`,
              opacity: op,
              transformOrigin: "center",
            }}
          >
            <PanelByKind kind={p.kind} frame={frame - delay} rng={rng} />
          </div>
        );
      })}

      {/* flash tags from bottom center */}
      {tags.map((tag, i) => {
        const local = tagFrame - tag.at;
        if (local < 0) return null;
        const op = interpolate(local, [0, 6, 22, 28], [0, 1, 1, 0], { extrapolateRight: "clamp" });
        const y = interpolate(local, [0, 8], [22, 0], { extrapolateRight: "clamp", easing: easeOut });
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: 0,
              right: 0,
              bottom: 36,
              textAlign: "center",
              opacity: op,
              transform: `translateY(${y}px)`,
              pointerEvents: "none",
            }}
          >
            <span
              style={{
                fontFamily: MONO,
                fontSize: 22,
                fontWeight: 600,
                letterSpacing: 2,
                textTransform: "uppercase",
                color: "white",
                background: tag.color,
                padding: "10px 20px",
                borderRadius: 8,
              }}
            >
              ▸ {tag.text}
            </span>
          </div>
        );
      })}
    </AbsoluteFill>
    </Camera>
  );
};

const PanelByKind: React.FC<{ kind: string; frame: number; rng: () => number }> = ({ kind, frame }) => {
  const card: React.CSSProperties = {
    width: "100%",
    height: "100%",
    background: "white",
    border: `1px solid ${CREAM_2}`,
    borderRadius: 14,
    padding: 18,
    fontFamily: INTER,
    color: INK,
    boxSizing: "border-box",
    boxShadow: "0 8px 24px rgba(0,0,0,0.05)",
    display: "flex",
    flexDirection: "column",
    gap: 10,
  };
  const eyebrow: React.CSSProperties = {
    fontFamily: MONO,
    fontSize: 11,
    letterSpacing: 2,
    textTransform: "uppercase",
    color: INK_SOFT,
  };

  if (kind === "objections") {
    const objs = [
      { label: "price too high", v: 0.74 },
      { label: "wrong icp", v: 0.52 },
      { label: "no moat", v: 0.41 },
      { label: "trust", v: 0.28 },
    ];
    return (
      <div style={card}>
        <span style={eyebrow}>top objections</span>
        {objs.map((o, i) => {
          const grow = interpolate(frame, [10 + i * 6, 28 + i * 6], [0, o.v], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: easeOut,
          });
          return (
            <div key={i}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 16, fontWeight: 600, marginBottom: 4 }}>
                <span>{o.label}</span>
                <span style={{ fontFamily: MONO, color: ORANGE }}>{Math.round(grow * 100)}%</span>
              </div>
              <div style={{ height: 8, background: CREAM, borderRadius: 99, overflow: "hidden" }}>
                <div style={{ width: `${grow * 100}%`, height: "100%", background: ORANGE, borderRadius: 99 }} />
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  if (kind === "sentiment") {
    const pos = interpolate(frame, [8, 28], [0, 38], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
    const neu = interpolate(frame, [8, 28], [0, 35], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
    const neg = interpolate(frame, [8, 28], [0, 27], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
    return (
      <div style={card}>
        <span style={eyebrow}>sentiment</span>
        <div style={{ display: "flex", height: 50, borderRadius: 8, overflow: "hidden" }}>
          <div style={{ flex: pos, background: TEAL, display: "flex", alignItems: "center", justifyContent: "center", color: "white", fontWeight: 700, fontFamily: MONO }}>
            {pos > 6 ? `${Math.round(pos)}%` : ""}
          </div>
          <div style={{ flex: neu, background: YELLOW, display: "flex", alignItems: "center", justifyContent: "center", color: INK, fontWeight: 700, fontFamily: MONO }}>
            {neu > 6 ? `${Math.round(neu)}%` : ""}
          </div>
          <div style={{ flex: neg, background: RED, display: "flex", alignItems: "center", justifyContent: "center", color: "white", fontWeight: 700, fontFamily: MONO }}>
            {neg > 6 ? `${Math.round(neg)}%` : ""}
          </div>
        </div>
      </div>
    );
  }

  if (kind === "pmf") {
    const score = interpolate(frame, [10, 50], [0, 7.4], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
    return (
      <div style={card}>
        <span style={eyebrow}>pmf · /10</span>
        <div style={{ display: "flex", alignItems: "baseline", gap: 18 }}>
          <span style={{ fontFamily: INTER, fontWeight: 800, fontSize: 140, color: ORANGE, lineHeight: 1, letterSpacing: -4 }}>
            {score.toFixed(1)}
          </span>
          <span style={{ fontSize: 22, color: INK_SOFT, fontWeight: 500 }}>positive lean</span>
        </div>
        <div style={{ display: "flex", gap: 4 }}>
          {Array.from({ length: 10 }).map((_, i) => {
            const on = i < Math.floor(score);
            return <div key={i} style={{ flex: 1, height: 6, borderRadius: 4, background: on ? ORANGE : CREAM_2 }} />;
          })}
        </div>
      </div>
    );
  }

  if (kind === "feed") {
    const items = [
      { who: "@skeptic_dev", tone: "skeptic", text: "another gpt wrapper? show me retention.", c: RED },
      { who: "@indie_hacker", tone: "curious", text: "wait the $19 tier is generous", c: TEAL },
      { who: "@pm_at_ramp", tone: "ask", text: "how does it handle slack threads?", c: BLUE },
      { who: "@lurker99", tone: "upvote", text: "↑ upvoted", c: INK_SOFT },
      { who: "@vc_friend", tone: "skeptic", text: "what's the moat past 6 months?", c: ORANGE },
      { who: "@kira", tone: "fan", text: "okay this slaps, signing up", c: PINK },
    ];
    return (
      <div style={card}>
        <span style={eyebrow}>live · agent reactions</span>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {items.map((it, i) => {
            const local = frame - (8 + i * 7);
            if (local < 0) return null;
            const op = interpolate(local, [0, 8], [0, 1], { extrapolateRight: "clamp" });
            const x = interpolate(local, [0, 10], [10, 0], { extrapolateRight: "clamp", easing: easeOut });
            return (
              <div
                key={i}
                style={{
                  borderLeft: `3px solid ${it.c}`,
                  paddingLeft: 12,
                  opacity: op,
                  transform: `translateX(${x}px)`,
                  display: "flex",
                  flexDirection: "column",
                  gap: 3,
                }}
              >
                <div style={{ display: "flex", gap: 10, alignItems: "baseline" }}>
                  <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: 13, color: it.c }}>{it.who}</span>
                  <span style={{ fontFamily: MONO, fontSize: 10, color: INK_SOFT, letterSpacing: 1, textTransform: "uppercase" }}>{it.tone}</span>
                </div>
                <span style={{ fontSize: 16, color: INK }}>{it.text}</span>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  if (kind === "personas") {
    const cols = 14;
    const rows = 8;
    const dots = Array.from({ length: cols * rows }, (_, i) => i);
    return (
      <div style={card}>
        <span style={eyebrow}>500 personas · 8 archetypes</span>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: `repeat(${cols}, 1fr)`,
            gridTemplateRows: `repeat(${rows}, 1fr)`,
            gap: 5,
            flex: 1,
            minHeight: 0,
          }}
        >
          {dots.map((d) => {
            const colors = [ORANGE, YELLOW, BLUE, TEAL, PINK, RED, "#9b8cff", INK];
            const c = colors[Math.floor(d / cols) % colors.length];
            const on = frame > 6 + (d % 28);
            return (
              <div
                key={d}
                style={{
                  width: "100%",
                  height: "100%",
                  borderRadius: 99,
                  background: on ? c : `${c}25`,
                }}
              />
            );
          })}
        </div>
      </div>
    );
  }

  if (kind === "icp") {
    const segs = [
      { label: "indie devs", fit: 0.82 },
      { label: "PMs", fit: 0.61 },
      { label: "VCs", fit: 0.18 },
      { label: "creators", fit: 0.44 },
    ];
    return (
      <div style={card}>
        <span style={eyebrow}>icp fit</span>
        {segs.map((s, i) => {
          const grow = interpolate(frame, [10 + i * 6, 28 + i * 6], [0, s.fit], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: easeOut,
          });
          return (
            <div key={i}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 15, fontWeight: 600 }}>
                <span>{s.label}</span>
                <span style={{ fontFamily: MONO, color: TEAL }}>{Math.round(grow * 100)}%</span>
              </div>
              <div style={{ height: 6, background: CREAM, borderRadius: 99, overflow: "hidden", marginTop: 4 }}>
                <div style={{ width: `${grow * 100}%`, height: "100%", background: TEAL, borderRadius: 99 }} />
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  if (kind === "kpi1") {
    const v = Math.floor(interpolate(frame, [4, 30], [0, 247], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut }));
    return (
      <div style={card}>
        <span style={eyebrow}>reactions</span>
        <span style={{ fontSize: 84, fontWeight: 800, color: BLUE, lineHeight: 1, letterSpacing: -2 }}>{v}</span>
        <span style={{ fontSize: 14, color: INK_SOFT }}>in 58s</span>
      </div>
    );
  }

  if (kind === "kpi2") {
    const v = interpolate(frame, [4, 30], [0, 0.38], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
    return (
      <div style={card}>
        <span style={eyebrow}>cost</span>
        <span style={{ fontSize: 84, fontWeight: 800, color: TEAL, lineHeight: 1, letterSpacing: -2 }}>${v.toFixed(2)}</span>
        <span style={{ fontSize: 14, color: INK_SOFT }}>real LLM run</span>
      </div>
    );
  }

  if (kind === "tagline") {
    return (
      <div style={{ ...card, justifyContent: "center" }}>
        <span style={eyebrow}>✨ insight</span>
        <span style={{ fontSize: 22, fontWeight: 700, lineHeight: 1.3 }}>
          Lead with retention, not pricing.
        </span>
      </div>
    );
  }

  return null;
};

// ============ Scene 4 (270..360) — chaos converges to logo ============
const Scene4: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const cx = width / 2;
  const cy = height / 2;
  const rng = mulberry(7);

  const particleCount = 120;
  const particles = Array.from({ length: particleCount }, (_, i) => {
    const ang0 = rng() * Math.PI * 2;
    const r0 = 400 + rng() * 500;
    const sx = cx + Math.cos(ang0) * r0;
    const sy = cy + Math.sin(ang0) * r0;
    const colors = [ORANGE, YELLOW, BLUE, TEAL, PINK];
    return { sx, sy, color: colors[i % colors.length], delay: i * 0.4, i };
  });

  // converge over 0..60
  const logoOp = interpolate(frame, [40, 70], [0, 1], { extrapolateRight: "clamp", easing: easeOut });
  const logoScale = interpolate(frame, [40, 75], [0.5, 1], { extrapolateRight: "clamp", easing: easeOut });

  return (
    <Camera duration={90} scaleFrom={1.0} scaleTo={1.12} rotate={-1.5}>
    <AbsoluteFill style={{ background: CREAM }}>
      <GrainTexture />

      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        {particles.map((p) => {
          const local = frame - p.delay;
          const t = Math.min(1, Math.max(0, local / 50));
          const ease = easeInOut(t);
          const x = p.sx + (cx - p.sx) * ease;
          const y = p.sy + (cy - p.sy) * ease;
          const op = interpolate(t, [0, 0.1, 0.9, 1], [0, 1, 1, 0.2]);
          const r = 6 - t * 3;
          return <circle key={p.i} cx={x} cy={y} r={r} fill={p.color} opacity={op} />;
        })}
      </svg>

      {/* logo */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          opacity: logoOp,
          transform: `scale(${logoScale})`,
        }}
      >
        <LogoMark />
      </div>
    </AbsoluteFill>
    </Camera>
  );
};

const LogoMark: React.FC = () => {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
      <svg width={120} height={120} viewBox="0 0 120 120">
        <circle cx={60} cy={60} r={36} fill={ORANGE} />
        <circle cx={28} cy={42} r={11} fill={BLUE} />
        <circle cx={92} cy={42} r={11} fill={TEAL} />
        <circle cx={28} cy={82} r={11} fill={YELLOW} />
        <circle cx={92} cy={82} r={11} fill={PINK} />
        <line x1={60} y1={60} x2={28} y2={42} stroke={INK} strokeWidth={2} strokeOpacity={0.5} />
        <line x1={60} y1={60} x2={92} y2={42} stroke={INK} strokeWidth={2} strokeOpacity={0.5} />
        <line x1={60} y1={60} x2={28} y2={82} stroke={INK} strokeWidth={2} strokeOpacity={0.5} />
        <line x1={60} y1={60} x2={92} y2={82} stroke={INK} strokeWidth={2} strokeOpacity={0.5} />
      </svg>
      <span style={{ fontFamily: INTER, fontWeight: 800, fontSize: 110, color: INK, letterSpacing: -3 }}>
        Swarmie<span style={{ color: ORANGE }}>.</span>
      </span>
    </div>
  );
};

// ============ Scene 5 (360..420) — tagline hold ============
const Scene5: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const logoY = interpolate(frame, [0, 15], [0, -20], { extrapolateRight: "clamp", easing: easeOut });
  const tagOp = interpolate(frame, [10, 25], [0, 1], { extrapolateRight: "clamp", easing: easeOut });
  const tagY = interpolate(frame, [10, 25], [12, 0], { extrapolateRight: "clamp", easing: easeOut });
  const ambient = Math.sin((frame / 30) * Math.PI * 2) * 4;

  return (
    <Camera duration={60} scaleFrom={1.0} scaleTo={1.04}>
    <AbsoluteFill style={{ background: CREAM, alignItems: "center", justifyContent: "center" }}>
      <GrainTexture />

      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 30, transform: `translateY(${logoY + ambient}px)` }}>
        <LogoMark />
        <div
          style={{
            fontFamily: INTER,
            fontSize: 36,
            fontWeight: 500,
            color: INK,
            opacity: tagOp,
            transform: `translateY(${tagY}px)`,
            textAlign: "center",
            maxWidth: 1100,
            lineHeight: 1.3,
          }}
        >
          Roast your startup with <span style={{ color: ORANGE, fontWeight: 700 }}>500 AI users</span> in <span style={{ color: BLUE, fontWeight: 700 }}>60 seconds.</span>
        </div>
        <div
          style={{
            opacity: tagOp,
            fontFamily: MONO,
            fontSize: 14,
            color: INK_SOFT,
            letterSpacing: 4,
            textTransform: "uppercase",
            marginTop: 10,
          }}
        >
          swarmie.dev
        </div>
      </div>
    </AbsoluteFill>
    </Camera>
  );
};

// ============ Grain texture ============
const GrainTexture: React.FC = () => {
  return (
    <svg
      width="100%"
      height="100%"
      style={{ position: "absolute", inset: 0, mixBlendMode: "multiply", opacity: 0.06, pointerEvents: "none" }}
    >
      <filter id="g">
        <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch" />
        <feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0" />
      </filter>
      <rect width="100%" height="100%" filter="url(#g)" />
    </svg>
  );
};

// Small cross-fade wrapper to soften scene cuts
const FadeIn: React.FC<React.PropsWithChildren<{ frames?: number }>> = ({ children, frames = 6 }) => {
  const f = useCurrentFrame();
  const op = interpolate(f, [0, frames], [0, 1], { extrapolateRight: "clamp" });
  return <div style={{ opacity: op, width: "100%", height: "100%" }}>{children}</div>;
};

// ============ Master composition ============
export const Promo: React.FC = () => {
  return (
    <AbsoluteFill style={{ background: CREAM }}>
      {HAS_MUSIC && <Audio src={staticFile("music.mp3")} volume={0.85} />}

      <Sequence from={0} durationInFrames={60} layout="none">
        <Scene1 />
      </Sequence>
      <Sequence from={60} durationInFrames={90} layout="none">
        <FadeIn><Scene2 /></FadeIn>
      </Sequence>
      <Sequence from={150} durationInFrames={120} layout="none">
        <FadeIn><Scene3 /></FadeIn>
      </Sequence>
      <Sequence from={270} durationInFrames={90} layout="none">
        <FadeIn><Scene4 /></FadeIn>
      </Sequence>
      <Sequence from={360} durationInFrames={60} layout="none">
        <FadeIn><Scene5 /></FadeIn>
      </Sequence>
    </AbsoluteFill>
  );
};
