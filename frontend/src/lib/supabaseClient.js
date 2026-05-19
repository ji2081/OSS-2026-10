import { createClient } from "@supabase/supabase-js";

const SUPABASE_URL = "https://gzcadtiiroufqywlsjsz.supabase.co";
const SUPABASE_ANON_KEY =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd6Y2FkdGlpcm91ZnF5d2xzanN6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0MjczNDUsImV4cCI6MjA5MzAwMzM0NX0.Qtg2e36no5u31aFmCtB__qUMdwGuAC7oB2EBk7x03ns";

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
