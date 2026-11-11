// Fails when a theme's interface colors drift blue or carry stray transparency.
// Run: bun script/check-colors.ts
import path from "node:path"

type Rgb = { r: number; g: number; b: number; a: number }

const themes = ["z1-default", "z1-soft", "z1-ocean"]

// A light theme is white surfaces with black accents; a dark one, the reverse.
const light = new Set(["z1-ocean"])

// Colors that carry meaning rather than surface: status, brackets, terminal palettes.
const exempt = (key: string) =>
  key.startsWith("editorMarkerNavigation") ||
  key.startsWith("terminal.ansi") ||
  /(error|warning|added|deleted|modified|gitDecoration|ansi|unexpectedBracket|minimapGutter|debugIcon|charts\.|symbolIcon)/.test(key)

// Keys whose value is a region of the window rather than text drawn on it.
const surface = /(^|\.)(background|Background)$|background$/

// A badge or a button is an accent drawn on the surface, not a surface itself.
const accent = /^(button|badge|activityBarBadge|activityWarningBadge|activityErrorBadge|panelTitleBadge|progressBar|extensionButton|inputOption|radio|\.*\.?(error|warning)Badge)\./

// The debug toolbar is a floating dark bar on purpose, the way it reads in every light theme.
const intentionalDark = /^(debug(ToolBar|ExceptionWidget)|statusBar|banner|activityBarBadge|badge|button|tab|list|menu|quickInputList|inputOption|radio|checkbox|progressBar)\./

// Terminal palettes name the colors a program asked for; they are not ours to change.
const allowed = (key: string) => key.startsWith("terminal.ansi")

function parse(value: unknown): Rgb | undefined {
  if (typeof value !== "string") return undefined
  const hex = /^#([0-9a-f]{6})([0-9a-f]{2})?$/i.exec(value)
  if (!hex) return undefined
  const n = parseInt(hex[1], 16)
  return {
    r: (n >> 16) & 0xff,
    g: (n >> 8) & 0xff,
    b: n & 0xff,
    a: hex[2] === undefined ? 1 : parseInt(hex[2], 16) / 255,
  }
}

// What the eye sees: a translucent color over the surface it is drawn on.
function over(top: Rgb, bottom: Rgb): Rgb {
  const mix = (t: number, b: number) => Math.round(t * top.a + b * (1 - top.a))
  return { r: mix(top.r, bottom.r), g: mix(top.g, bottom.g), b: mix(top.b, bottom.b), a: 1 }
}

function isBlue(c: Rgb) {
  return c.b > c.r + 18 && c.b > c.g + 18
}

let failed = 0

for (const theme of themes) {
  const file = path.join(import.meta.dirname, "..", "themes", `${theme}.json`)
  const data = await Bun.file(file).json()
  const colors: Record<string, string> = data.colors
  const background = parse(colors["editor.background"]) ?? { r: 0, g: 0, b: 0, a: 1 }
  const bar = parse(colors["titleBar.activeBackground"]) ?? background

  if (data.include) {
    console.error(`${theme}: has an include chain (${data.include}); the theme must be self-contained`)
    failed++
  }

  for (const [key, value] of Object.entries(colors)) {
    if (allowed(key)) continue
    const c = parse(value)
    if (!c) {
      console.error(`${theme}: ${key} = ${value} is not a 6- or 8-digit hex color`)
      failed++
      continue
    }
    const seen = over(c, key.startsWith("statusBar") || key.startsWith("titleBar") ? bar : background)
    if (isBlue(seen)) {
      console.error(`${theme}: ${key} = ${value} reads as blue ${JSON.stringify(seen)} over the surface`)
      failed++
    }
    // A light theme keeps every surface light; text and accents are black on purpose.
    if (light.has(theme) && surface.test(key) && !accent.test(key) && !exempt(key) && !intentionalDark.test(key) && seen.r + seen.g + seen.b < 3 * 200) {
      console.error(`${theme}: ${key} = ${value} is a dark surface in a light theme ${JSON.stringify(seen)}`)
      failed++
    }
  }
  console.log(`${theme}: ${Object.keys(colors).length} colors checked`)
}

if (failed > 0) {
  console.error(`\n${failed} problem(s) found`)
  process.exit(1)
}
console.log("\nno blue in any interface color")
