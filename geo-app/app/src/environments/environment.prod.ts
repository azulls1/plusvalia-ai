// src/environments/environment.prod.ts - Configuración para producción
export const environment = { // objeto de configuración exportado para producción
  production: true, // modo producción activado
  supabaseUrl: "https://iagenteksupabase.iagentek.com.mx", // URL base de Supabase
  // NOTE: supabaseAnonKey is intentionally public. Supabase anon keys are designed
  // to be used in frontend code. Row Level Security (RLS) policies in Supabase
  // protect data at the database level. See CONTRIBUTING.md for details.
  supabaseAnonKey: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ewogICJyb2xlIjogImFub24iLAogICJpc3MiOiAic3VwYWJhc2UiLAogICJpYXQiOiAxNzE1MDUwODAwLAogICJleHAiOiAxODcyODE3MjAwCn0.23LYnOepZ9yTJObLFoTnszO5WdHpbekvgwMt8bn2o_k", // clave anónima pública de Supabase
  n8nBase: "https://iagentekn8nwebhook.iagentek.com.mx", // URL base de webhooks n8n
  mlApiBase: "https://plusvalia-api.iagentek.com.mx",
  osmUserAgent: "inmo-geo-mvp/1.0 (contacto@iagentek.com.mx)", // User Agent para peticiones OSM
  nominatimBase: "https://nominatim.openstreetmap.org", // URL de Nominatim (geocodificación)
  overpassBase: "https://overpass-api.de/api/interpreter", // URL de Overpass API (consultas OSM)
  cityDefault: "Guadalajara", // ciudad por defecto para búsquedas
  stateDefault: "Jalisco", // estado por defecto para búsquedas
  gridDegStep: 0.005, // paso en grados para la grilla (~500m aprox)
  chatWebhookUrl: 'https://iagentekn8nwebhook.iagentek.com.mx/webhook/a9fb43e2-1ca2-4e62-96f6-83b91221f3ea' // URL del webhook de n8n para chatbot
};

