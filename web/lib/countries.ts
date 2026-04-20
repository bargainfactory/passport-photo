export interface PrintSheetSpec {
  /** "landscape" (6×4", default) or "portrait" (4×6") paper orientation. */
  orientation?: "landscape" | "portrait";
  /** Photos across × down. Defaults to 3×2 for landscape. */
  cols?: number;
  rows?: number;
  /** Thickness of the cut-line between cells, in millimetres. */
  separator_mm?: number;
  /**
   * Vertical nudge of the entire photo grid on the sheet, in millimetres
   * (positive = shift down). Affects only the print-sheet layout, not
   * the single digital download.
   */
  y_offset_mm?: number;
}

export interface PhotoSpec {
  width_mm: number;
  height_mm: number;
  bg_color: [number, number, number];
  head_pct: [number, number];
  eye_line_pct: [number, number];
  /**
   * Maximum file size in kilobytes for the digital download (JPEG).
   * Only set when the destination requires it (e.g. US State Department
   * online passport submission = 240 KB max — we cap at 230 for safety).
   * When undefined, the download is unconstrained.
   */
  max_file_size_kb?: number;
  /** Space between top of photo and crown of head, in mm. Default 3. */
  crown_top_mm?: number;
  /**
   * Optional per-spec print-sheet layout. When undefined, the default
   * 3×2 landscape sheet is used. Set for countries whose passport size
   * does not gang-up cleanly 6-up (e.g. Canada's 50×70mm fits 4-up on
   * a portrait 4×6" sheet).
   */
  print_sheet?: PrintSheetSpec;
}

export interface CountrySpec {
  name: string;
  flag: string;
  region: string;
  passport: PhotoSpec;
  visa: PhotoSpec;
  glasses: boolean;
  headgear: boolean;
  expression: string;
  notes: string;
}

export const COUNTRIES: CountrySpec[] = [
  // Americas
  {
    name: "United States",
    flag: "\u{1F1FA}\u{1F1F8}",
    region: "Americas",
    passport: { width_mm: 51, height_mm: 51, bg_color: [255, 255, 255], head_pct: [70, 70], eye_line_pct: [56, 69], max_file_size_kb: 230 },
    visa:     { width_mm: 51, height_mm: 51, bg_color: [255, 255, 255], head_pct: [70, 70], eye_line_pct: [56, 69], max_file_size_kb: 230 },
    glasses: false, headgear: false,
    expression: "Neutral, eyes open, mouth closed",
    notes: "No glasses since 2016. No headgear except religious. White background only. Digital file capped at 230 KB for online submission.",
  },
  {
    name: "Canada",
    flag: "\u{1F1E8}\u{1F1E6}",
    region: "Americas",
    // head_pct [50, 51] → target head ~35mm on a 70mm photo (spec: 35-36mm).
    passport: {
      width_mm: 50, height_mm: 70,
      bg_color: [255, 255, 255],
      head_pct: [50, 51],
      eye_line_pct: [56, 69],
      crown_top_mm: 10,
      print_sheet: { orientation: "portrait", cols: 2, rows: 2, separator_mm: 0.3, y_offset_mm: 4 },
    },
    visa: {
      width_mm: 35, height_mm: 45,
      bg_color: [255, 255, 255],
      head_pct: [70, 80],
      eye_line_pct: [56, 69],
      crown_top_mm: 10,
    },
    glasses: false, headgear: false,
    expression: "Neutral, mouth closed, eyes open",
    notes: "Head 35-36mm in height on 50x70mm photo. White or light background.",
  },
  {
    name: "Brazil",
    flag: "\u{1F1E7}\u{1F1F7}",
    region: "Americas",
    passport: { width_mm: 50, height_mm: 70, bg_color: [255, 255, 255], head_pct: [60, 80], eye_line_pct: [56, 69] },
    visa:     { width_mm: 51, height_mm: 51, bg_color: [255, 255, 255], head_pct: [60, 80], eye_line_pct: [56, 69] },
    glasses: false, headgear: false,
    expression: "Neutral, mouth closed",
    notes: "White background. No glasses.",
  },
  {
    name: "Mexico",
    flag: "\u{1F1F2}\u{1F1FD}",
    region: "Americas",
    passport: { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    visa:     { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    glasses: false, headgear: false,
    expression: "Neutral, no smile",
    notes: "White background. No glasses.",
  },
  // Europe
  {
    name: "United Kingdom",
    flag: "\u{1F1EC}\u{1F1E7}",
    region: "Europe",
    passport: { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    visa:     { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    glasses: false, headgear: false,
    expression: "Neutral, mouth closed, no smile",
    notes: "No glasses. Light grey background also accepted.",
  },
  {
    name: "Schengen / EU",
    flag: "\u{1F1EA}\u{1F1FA}",
    region: "Europe",
    passport: { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    visa:     { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    glasses: true, headgear: false,
    expression: "Neutral, mouth closed",
    notes: "Covers all Schengen states. White or light grey background. Glasses allowed if eyes visible.",
  },
  {
    name: "Germany",
    flag: "\u{1F1E9}\u{1F1EA}",
    region: "Europe",
    passport: { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    visa:     { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    glasses: true, headgear: false,
    expression: "Neutral, mouth closed, eyes open",
    notes: "White or light grey background. Glasses allowed if no glare.",
  },
  {
    name: "France",
    flag: "\u{1F1EB}\u{1F1F7}",
    region: "Europe",
    passport: { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    visa:     { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    glasses: false, headgear: false,
    expression: "Neutral, mouth closed",
    notes: "No glasses since 2018. White or light background.",
  },
  {
    name: "Russia",
    flag: "\u{1F1F7}\u{1F1FA}",
    region: "Europe",
    passport: { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    visa:     { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    glasses: true, headgear: false,
    expression: "Neutral, mouth closed",
    notes: "White background preferred. Glasses allowed if clear lenses.",
  },
  {
    name: "Turkey",
    flag: "\u{1F1F9}\u{1F1F7}",
    region: "Europe",
    passport: { width_mm: 50, height_mm: 60, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    visa:     { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    glasses: true, headgear: false,
    expression: "Neutral, eyes open",
    notes: "White background. Glasses ok if clear lenses.",
  },
  // Asia-Pacific
  {
    name: "Australia",
    flag: "\u{1F1E6}\u{1F1FA}",
    region: "Asia-Pacific",
    passport: { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [64, 80], eye_line_pct: [56, 69] },
    visa:     { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [64, 80], eye_line_pct: [56, 69] },
    glasses: false, headgear: false,
    expression: "Neutral, mouth closed",
    notes: "No glasses. Plain white or light grey background.",
  },
  {
    name: "New Zealand",
    flag: "\u{1F1F3}\u{1F1FF}",
    region: "Asia-Pacific",
    passport: { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [66, 80], eye_line_pct: [56, 69] },
    visa:     { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [66, 80], eye_line_pct: [56, 69] },
    glasses: false, headgear: false,
    expression: "Neutral, mouth closed, eyes open",
    notes: "No glasses. White or off-white background.",
  },
  {
    name: "India",
    flag: "\u{1F1EE}\u{1F1F3}",
    region: "Asia-Pacific",
    passport: { width_mm: 51, height_mm: 51, bg_color: [255, 255, 255], head_pct: [50, 70], eye_line_pct: [56, 69] },
    visa:     { width_mm: 51, height_mm: 51, bg_color: [255, 255, 255], head_pct: [50, 70], eye_line_pct: [56, 69] },
    glasses: false, headgear: false,
    expression: "Neutral, eyes open, mouth closed",
    notes: "White background only. No glasses.",
  },
  {
    name: "China",
    flag: "\u{1F1E8}\u{1F1F3}",
    region: "Asia-Pacific",
    passport: { width_mm: 33, height_mm: 48, bg_color: [255, 255, 255], head_pct: [62, 73], eye_line_pct: [56, 69] },
    visa:     { width_mm: 33, height_mm: 48, bg_color: [255, 255, 255], head_pct: [62, 73], eye_line_pct: [56, 69] },
    glasses: false, headgear: false,
    expression: "Neutral, no smile, eyes open",
    notes: "White background. Head height 28-33mm. No glasses.",
  },
  {
    name: "Japan",
    flag: "\u{1F1EF}\u{1F1F5}",
    region: "Asia-Pacific",
    passport: { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    visa:     { width_mm: 45, height_mm: 45, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    glasses: true, headgear: false,
    expression: "Neutral, mouth closed, eyes open",
    notes: "White or light background. Glasses ok if no glare.",
  },
  {
    name: "South Korea",
    flag: "\u{1F1F0}\u{1F1F7}",
    region: "Asia-Pacific",
    passport: { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [71, 80], eye_line_pct: [56, 69] },
    visa:     { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [71, 80], eye_line_pct: [56, 69] },
    glasses: false, headgear: false,
    expression: "Neutral, mouth closed",
    notes: "White background. Head 32-36mm. No glasses preferred.",
  },
  {
    name: "Thailand",
    flag: "\u{1F1F9}\u{1F1ED}",
    region: "Asia-Pacific",
    passport: { width_mm: 40, height_mm: 60, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    visa:     { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    glasses: true, headgear: false,
    expression: "Neutral, eyes open",
    notes: "White or light background. Glasses ok if not reflective.",
  },
  {
    name: "Philippines",
    flag: "\u{1F1F5}\u{1F1ED}",
    region: "Asia-Pacific",
    passport: { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [71, 80], eye_line_pct: [56, 69] },
    visa:     { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [71, 80], eye_line_pct: [56, 69] },
    glasses: false, headgear: false,
    expression: "Neutral (slight smile ok, no teeth)",
    notes: "White or light blue background. Head 32-36mm. No glasses unless medical.",
  },
  {
    name: "Indonesia",
    flag: "\u{1F1EE}\u{1F1E9}",
    region: "Asia-Pacific",
    passport: { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [60, 70], eye_line_pct: [56, 69] },
    visa:     { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [60, 70], eye_line_pct: [56, 69] },
    glasses: false, headgear: false,
    expression: "Neutral, eyes open",
    notes: "White background. Religious headgear allowed.",
  },
  {
    name: "Vietnam",
    flag: "\u{1F1FB}\u{1F1F3}",
    region: "Asia-Pacific",
    passport: { width_mm: 40, height_mm: 60, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    visa:     { width_mm: 51, height_mm: 51, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    glasses: false, headgear: false,
    expression: "Neutral, eyes open",
    notes: "White background. No glasses, no headgear.",
  },
  {
    name: "Malaysia",
    flag: "\u{1F1F2}\u{1F1FE}",
    region: "Asia-Pacific",
    passport: { width_mm: 35, height_mm: 50, bg_color: [255, 255, 255], head_pct: [50, 60], eye_line_pct: [56, 69] },
    visa:     { width_mm: 35, height_mm: 50, bg_color: [255, 255, 255], head_pct: [50, 60], eye_line_pct: [56, 69] },
    glasses: true, headgear: true,
    expression: "Neutral, mouth closed",
    notes: "White background. Glasses ok if clear. Dark-colored headscarf allowed.",
  },
  {
    name: "Singapore",
    flag: "\u{1F1F8}\u{1F1EC}",
    region: "Asia-Pacific",
    passport: { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    visa:     { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    glasses: false, headgear: false,
    expression: "Neutral, eyes open",
    notes: "White background. No glasses if possible. Religious headgear allowed.",
  },
  {
    name: "Hong Kong",
    flag: "\u{1F1ED}\u{1F1F0}",
    region: "Asia-Pacific",
    passport: { width_mm: 40, height_mm: 50, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    visa:     { width_mm: 40, height_mm: 50, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    glasses: true, headgear: false,
    expression: "Neutral, eyes open",
    notes: "White background. Head 32-36mm. Religious/medical headgear allowed.",
  },
  {
    name: "Pakistan",
    flag: "\u{1F1F5}\u{1F1F0}",
    region: "Asia-Pacific",
    passport: { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    visa:     { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    glasses: true, headgear: false,
    expression: "Neutral, eyes open",
    notes: "White background. Glasses if eyes visible. No hats.",
  },
  // Middle East
  {
    name: "Saudi Arabia",
    flag: "\u{1F1F8}\u{1F1E6}",
    region: "Middle East",
    passport: { width_mm: 40, height_mm: 60, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    visa:     { width_mm: 51, height_mm: 51, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    glasses: false, headgear: false,
    expression: "Neutral, eyes open, mouth closed",
    notes: "White or light gray background. No glasses. No headgear except religious.",
  },
  {
    name: "United Arab Emirates",
    flag: "\u{1F1E6}\u{1F1EA}",
    region: "Middle East",
    passport: { width_mm: 40, height_mm: 60, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    visa:     { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    glasses: true, headgear: false,
    expression: "Neutral, eyes open",
    notes: "White background. Glasses if eyes clearly visible. Religious headgear allowed.",
  },
  {
    name: "Egypt",
    flag: "\u{1F1EA}\u{1F1EC}",
    region: "Middle East",
    passport: { width_mm: 40, height_mm: 60, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    visa:     { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    glasses: false, headgear: false,
    expression: "Neutral, eyes open",
    notes: "White background. No glasses, no headgear.",
  },
  {
    name: "Qatar",
    flag: "\u{1F1F6}\u{1F1E6}",
    region: "Middle East",
    passport: { width_mm: 38, height_mm: 48, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    visa:     { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    glasses: true, headgear: false,
    expression: "Neutral, eyes open",
    notes: "White or light blue background. Glasses ok if clear.",
  },
  {
    name: "Jordan",
    flag: "\u{1F1EF}\u{1F1F4}",
    region: "Middle East",
    passport: { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    visa:     { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    glasses: true, headgear: false,
    expression: "Neutral, eyes open",
    notes: "White background. Glasses if eyes visible.",
  },
  {
    name: "Iran",
    flag: "\u{1F1EE}\u{1F1F7}",
    region: "Middle East",
    passport: { width_mm: 40, height_mm: 60, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    visa:     { width_mm: 40, height_mm: 60, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    glasses: false, headgear: true,
    expression: "Neutral, eyes open",
    notes: "White background. No glasses. Headscarf required for women.",
  },
  {
    name: "Israel",
    flag: "\u{1F1EE}\u{1F1F1}",
    region: "Middle East",
    passport: { width_mm: 35, height_mm: 45, bg_color: [240, 240, 240], head_pct: [70, 80], eye_line_pct: [56, 69] },
    visa:     { width_mm: 35, height_mm: 45, bg_color: [240, 240, 240], head_pct: [70, 80], eye_line_pct: [56, 69] },
    glasses: true, headgear: false,
    expression: "Neutral, eyes open",
    notes: "Light background (white or light grey). Glasses ok.",
  },
  // Africa
  {
    name: "South Africa",
    flag: "\u{1F1FF}\u{1F1E6}",
    region: "Africa",
    passport: { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [60, 80], eye_line_pct: [56, 69] },
    visa:     { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [60, 80], eye_line_pct: [56, 69] },
    glasses: true, headgear: false,
    expression: "Neutral, eyes open",
    notes: "White or light grey background.",
  },
  {
    name: "Nigeria",
    flag: "\u{1F1F3}\u{1F1EC}",
    region: "Africa",
    passport: { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    visa:     { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    glasses: false, headgear: false,
    expression: "Neutral, eyes open, mouth closed",
    notes: "White background. No glasses, no headgear except religious.",
  },
  {
    name: "Kenya",
    flag: "\u{1F1F0}\u{1F1EA}",
    region: "Africa",
    passport: { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    visa:     { width_mm: 35, height_mm: 45, bg_color: [255, 255, 255], head_pct: [70, 80], eye_line_pct: [56, 69] },
    glasses: false, headgear: false,
    expression: "Neutral, eyes open",
    notes: "White background. No glasses, no headgear.",
  },
];

export function getSpec(country: CountrySpec, docType: "passport" | "visa"): PhotoSpec {
  return docType === "visa" ? country.visa : country.passport;
}

export function mmToPx(mm: number, dpi = 300): number {
  return Math.round(mm * dpi / 25.4);
}
