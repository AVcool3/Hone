// Hone runtime configuration.
//
// Accounts + saved portfolios are OPTIONAL and powered by Supabase.
// Leave these blank and Hone runs exactly as before — no login, nothing
// saved, everything in-browser. Fill them in (and follow docs/SUPABASE.md)
// to enable sign-in and per-user saved portfolios.
//
// These are PUBLIC values (safe to ship to the browser): the project URL
// and the "anon" public API key. Never put the service-role key here.
// In a hosted deploy you can instead inject them via a build step or a
// small endpoint; a static file is the simplest starting point.
window.HONE_CONFIG = {
  supabaseUrl: "https://jmovvvgncslnqxoxjumh.supabase.co",
  // Publishable (browser-safe) key — NOT the sb_secret_ key.
  supabaseAnonKey: "sb_publishable_uscZE3056c12p_q2eVQDzQ_am1Wor4i",
};
