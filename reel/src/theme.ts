import { loadFont } from "@remotion/fonts";
import { staticFile } from "remotion";

export type StyleKey = "pearl" | "sadu" | "swiss";

export type Theme = {
  bg: [string, string];
  blobs: string[];
  ink: string;
  sub: string;
  accent: string;
  accent2: string;
  onAccent: string;
  head: string; // headline font family
  body: string; // body font family
  pattern: "pearl" | "sadu" | "grid";
};

export const THEMES: Record<StyleKey, Theme> = {
  // لؤلؤ — informational
  pearl: {
    bg: ["#FBF7EF", "#EFE3CC"],
    blobs: ["#F4B9A8", "#CDAE78", "#9CC9D9"],
    ink: "#0B2A43",
    sub: "#4A5560",
    accent: "#E4664F",
    accent2: "#CDAE78",
    onAccent: "#FFFFFF",
    head: "Amiri",
    body: "Plex",
    pattern: "pearl",
  },
  // سدو — Bahrain news / events / places
  sadu: {
    bg: ["#F1E4C6", "#E2CC9E"],
    blobs: ["#C2412D", "#E9B44C", "#7A2A1E"],
    ink: "#1E1A17",
    sub: "#4B3B2E",
    accent: "#9E2A1E",
    accent2: "#E9B44C",
    onAccent: "#F7EEDC",
    head: "Reem",
    body: "Tajawal",
    pattern: "sadu",
  },
  // شبكة — international / GCC
  swiss: {
    bg: ["#0E4C92", "#082F5E"],
    blobs: ["#2E7DF6", "#FF5E4D", "#29C7AC"],
    ink: "#FFFFFF",
    sub: "#CFE0FF",
    accent: "#FF5E4D",
    accent2: "#FFFFFF",
    onAccent: "#FFFFFF",
    head: "Cairo",
    body: "Cairo",
    pattern: "grid",
  },
};

let loaded: Promise<unknown> | null = null;
export const loadFonts = () => {
  if (!loaded) {
    loaded = Promise.all([
      loadFont({ family: "Tajawal", url: staticFile("fonts/Tajawal-Black.ttf"), weight: "900" }),
      loadFont({ family: "Tajawal", url: staticFile("fonts/Tajawal-ExtraBold.ttf"), weight: "800" }),
      loadFont({ family: "Tajawal", url: staticFile("fonts/Tajawal-Bold.ttf"), weight: "700" }),
      loadFont({ family: "Tajawal", url: staticFile("fonts/Tajawal-Medium.ttf"), weight: "500" }),
      loadFont({ family: "Amiri", url: staticFile("fonts/Amiri-Bold.ttf"), weight: "700" }),
      loadFont({ family: "Reem", url: staticFile("fonts/ReemKufi.ttf"), weight: "400 700" }),
      loadFont({ family: "Cairo", url: staticFile("fonts/Cairo.ttf"), weight: "200 1000" }),
      loadFont({ family: "Plex", url: staticFile("fonts/IBMPlexSansArabic-Bold.ttf"), weight: "700" }),
      loadFont({ family: "Plex", url: staticFile("fonts/IBMPlexSansArabic-Medium.ttf"), weight: "500" }),
      loadFont({ family: "Lalezar", url: staticFile("fonts/Lalezar-Regular.ttf"), weight: "400" }),
    ]);
  }
  return loaded;
};
