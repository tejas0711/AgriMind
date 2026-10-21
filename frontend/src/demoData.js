/**
 * Verified benchmark demonstration data matching sample_data/Soil_Test_Report_Demo_Farm.pdf
 * and certified by verify_setup.py.
 *
 * This data is ONLY shown when the user clicks "Try Demo Soil" or tests demonstration mode,
 * and is always accompanied by an unambiguous "Demonstration Mode" banner.
 */

export const DEMO_SOIL_REPORT = {
  nitrogen: { value: 180, unit: "kg/ha" },
  phosphorus: { value: 15, unit: "kg/ha" },
  potassium: { value: 260, unit: "kg/ha" },
  ph: { value: 6.4, unit: null },
  organic_carbon: { value: 0.45, unit: "%" },
  electrical_conductivity: { value: 0.32, unit: "dS/m" },
  zinc: { value: 0.42, unit: "ppm" },
  iron: { value: 4.8, unit: "ppm" },
  sulphur: { value: 18.0, unit: "ppm" },
  boron: null,
  manganese: null,
  copper: null,
  measurements: {
    nitrogen: { name: "Available Nitrogen (N)", field_key: "nitrogen", value: 180, unit: "kg/ha", status: "extracted", rating: "LOW", source_text: "Available Nitrogen (N): 180 kg/ha", typical_range: "Low: <280, Med: 280-560, High: >560 kg/ha" },
    phosphorus: { name: "Available Phosphorus (P)", field_key: "phosphorus", value: 15, unit: "kg/ha", status: "extracted", rating: "MEDIUM", source_text: "Available Phosphorus (P): 15 kg/ha", typical_range: "Low: <10, Med: 10-25, High: >25 kg/ha" },
    potassium: { name: "Available Potassium (K)", field_key: "potassium", value: 260, unit: "kg/ha", status: "extracted", rating: "MEDIUM", source_text: "Available Potassium (K): 260 kg/ha", typical_range: "Low: <108, Med: 108-280, High: >280 kg/ha" },
    ph: { name: "Soil Reaction (pH)", field_key: "ph", value: 6.4, unit: null, status: "extracted", rating: "ACIDIC", source_text: "pH: 6.4", typical_range: "Acidic: <6.5, Neutral: 6.5-7.5, Alkaline: >7.5" },
    organic_carbon: { name: "Organic Carbon (OC)", field_key: "organic_carbon", value: 0.45, unit: "%", status: "extracted", rating: "LOW", source_text: "Organic Carbon: 0.45 %", typical_range: "Low: <0.50%, Med: 0.50-0.75%, High: >0.75%" },
    electrical_conductivity: { name: "Electrical Conductivity (EC)", field_key: "electrical_conductivity", value: 0.32, unit: "dS/m", status: "extracted", rating: "NORMAL", source_text: "Electrical Conductivity: 0.32 dS/m", typical_range: "Normal: <=1.0 dS/m" },
    zinc: { name: "Available Zinc (Zn)", field_key: "zinc", value: 0.42, unit: "ppm", status: "extracted", rating: "DEFICIENT", source_text: "Zinc: 0.42 ppm", typical_range: "Critical limit: 0.60 ppm" },
    iron: { name: "Available Iron (Fe)", field_key: "iron", value: 4.8, unit: "ppm", status: "extracted", rating: "SUFFICIENT", source_text: "Iron: 4.8 ppm", typical_range: "Critical limit: 4.50 ppm" },
    sulphur: { name: "Available Sulphur (S)", field_key: "sulphur", value: 18.0, unit: "ppm", status: "extracted", rating: "SUFFICIENT", source_text: "Sulphur: 18 ppm", typical_range: "Critical limit: 10.0 ppm" },
    boron: { name: "Available Boron (B)", field_key: "boron", value: null, unit: "ppm", status: "missing", rating: "UNKNOWN", source_text: null, typical_range: "Critical limit: 0.50 ppm" },
    manganese: { name: "Available Manganese (Mn)", field_key: "manganese", value: null, unit: "ppm", status: "missing", rating: "UNKNOWN", source_text: null, typical_range: "Critical limit: 2.00 ppm" },
    copper: { name: "Available Copper (Cu)", field_key: "copper", value: null, unit: "ppm", status: "missing", rating: "UNKNOWN", source_text: null, typical_range: "Critical limit: 0.20 ppm" },
  },
  raw_text_excerpt: "Soil Health Card - Demo Farm (Maharashtra). Available Nitrogen: 180 kg/ha, Available Phosphorus: 15 kg/ha, Available Potassium: 260 kg/ha, pH: 6.4, Organic Carbon: 0.45 %, EC: 0.32 dS/m, Zinc: 0.42 ppm, Iron: 4.8 ppm, Sulphur: 18 ppm.",
  extraction_warnings: [],
};

export const DEMO_RECOMMENDATION_RESPONSE = {
  isDemo: true,
  soil: DEMO_SOIL_REPORT,
  deficiencies: [
    { nutrient: "nitrogen", status: "LOW", detail: "Nitrogen is LOW (180 kg/ha). Consider corrective fertilizer/amendment." },
    { nutrient: "phosphorus", status: "MEDIUM", detail: "Phosphorus is at an adequate MEDIUM level (15 kg/ha)." },
    { nutrient: "potassium", status: "MEDIUM", detail: "Potassium is at an adequate MEDIUM level (260 kg/ha)." },
    { nutrient: "organic_carbon", status: "LOW", detail: "Organic Carbon is LOW (0.45%). Consider corrective fertilizer/amendment." },
    { nutrient: "zinc", status: "LOW", detail: "Zinc is DEFICIENT (0.42 ppm, critical level 0.6 ppm). Correction recommended." },
    { nutrient: "iron", status: "HIGH", detail: "Iron is SUFFICIENT (4.8 ppm, critical level 4.5 ppm). No action needed." },
    { nutrient: "sulphur", status: "HIGH", detail: "Sulphur is SUFFICIENT (18.0 ppm, critical level 10.0 ppm). No action needed." },
  ],
  crop_scores: [
    {
      name: "Tomato",
      score: 85.0,
      ph_fit: true,
      n_fit: true,
      p_fit: true,
      k_fit: true,
      season_fit: true,
      reasons: [
        "Soil pH 6.4 is within Tomato's preferred range (6.0-6.8).",
        "Available nitrogen (180 kg/ha) meets Tomato's requirement.",
        "Available potassium (260 kg/ha) meets Tomato's requirement.",
      ],
    },
    {
      name: "Wheat",
      score: 80.0,
      ph_fit: true,
      n_fit: true,
      p_fit: true,
      k_fit: true,
      season_fit: true,
      reasons: [
        "Soil pH 6.4 is within Wheat's preferred range (6.0-7.5).",
        "Available phosphorus (15 kg/ha) meets Wheat's requirement.",
        "Wheat is suitable for the current season.",
      ],
    },
    {
      name: "Soybean",
      score: 75.0,
      ph_fit: true,
      n_fit: true,
      p_fit: true,
      k_fit: true,
      season_fit: true,
      reasons: [
        "Soil pH 6.4 is well suited for soybean nodulation.",
        "Nitrogen levels are adequate for early vegetative growth.",
      ],
    },
    {
      name: "Onion",
      score: 70.0,
      ph_fit: true,
      n_fit: true,
      p_fit: true,
      k_fit: true,
      season_fit: false,
      reasons: [
        "Soil pH 6.4 matches onion bulb requirements.",
        "Requires supplementary sulfur and zinc application.",
      ],
    },
  ],
  fertilizer_options: [
    {
      name: "Urea (46% N) / Neem Coated Urea",
      type: "chemical",
      nutrient: "nitrogen",
      application_notes: "Split application: 50% basal dose during land preparation, remaining in two equal splits at active tillering and panicle/flowering stages.",
      source: "ICAR Fertilizer Guidelines",
    },
    {
      name: "Farmyard Manure (FYM) / Well-decomposed Compost",
      type: "organic",
      nutrient: "organic_carbon",
      application_notes: "Apply 5-10 tonnes/ha 3-4 weeks prior to sowing and incorporate thoroughly into the topsoil to enhance microbial activity and organic carbon.",
      source: "CGIAR Soil Health Framework (2025)",
    },
    {
      name: "Zinc Sulphate Heptahydrate (ZnSO4·7H2O, 21% Zn)",
      type: "chemical",
      nutrient: "zinc",
      application_notes: "Apply 25 kg/ha as a soil basal application. Do not mix directly with phosphatic fertilizers (DAP/SSP) to prevent chemical lock-up.",
      source: "Soil Health Card Management Guide",
    },
    {
      name: "Vermicompost / Bio-fertilizer (Azotobacter)",
      type: "organic",
      nutrient: "nitrogen",
      application_notes: "Seed treatment with Azotobacter culture (200g per 10kg seed) or soil application of vermicompost @ 2.5 t/ha at field preparation.",
      source: "National Centre of Organic Farming",
    },
  ],
  application_window: {
    recommendation: "YES",
    apply_today: "GO",
    reason: "Forecast conditions today are within safe limits for application (Rain: 0 mm, Wind: 11 km/h).",
    next_window: null,
    forecast_summary: {
      date: "Today",
      precipitation_mm: 0,
      precipitation_probability_pct: 10,
      wind_max_kmh: 11,
      temp_min_c: 21,
      temp_max_c: 32,
      humidity_max_pct: 54,
    },
  },
  why: {
    reason_soil: "Nitrogen is LOW (180 kg/ha, below the 280 kg/ha alkaline permanganate threshold). Organic Carbon is LOW (0.45%, below the 0.50% SHC baseline). Zinc is DEFICIENT (0.42 ppm, below the 0.60 ppm DTPA critical limit). Phosphorus and Potassium are at adequate medium levels.",
    weather_factor: "GO: Forecast conditions today are within safe limits for application.",
    confidence: 1.0,
    contradictions: [],
    evidence: [
      {
        source: "soil_health_card_guide.md",
        text: "Under the Indian Soil Health Card rating scale: Available Nitrogen < 280 kg/ha is classified as LOW. Available Phosphorus 10-25 kg/ha is MEDIUM. Available Potassium 108-280 kg/ha is MEDIUM. Organic Carbon < 0.50% is LOW.",
        score: 0.94,
      },
      {
        source: "cgiar_soil_health_framework_2025.md",
        text: "Core Function 1: Nutrient Cycling and Supply. Soils with organic carbon below 0.5% show impaired microbial activity and reduced nitrogen use efficiency. Organic matter inputs are essential to restore soil biological health.",
        score: 0.89,
      },
      {
        source: "fertilizer_options.json",
        text: "Zinc deficiency (DTPA-Zn < 0.6 ppm) is widely prevalent in semi-arid black and alluvial soils. Soil application of 25 kg/ha zinc sulphate is standard corrective practice.",
        score: 0.86,
      },
    ],
  },
  llm_explanation: "Based on your Soil Health Card test values, your soil is fertile in Phosphorus (15 kg/ha) and Potassium (260 kg/ha), but needs corrective attention for Nitrogen (180 kg/ha), Organic Carbon (0.45%), and Zinc (0.42 ppm). Today's weather conditions in your area are favorable with no rain expected, making it safe to proceed with recommended basal applications. Applying Farmyard Manure or compost alongside Neem Coated Urea will steadily improve soil structure and crop yields.",
  language: "en",
};
