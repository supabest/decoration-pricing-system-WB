import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://lnvtykghcpsjpwczbqsm.supabase.co'
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'sb_publishable_VQNxLrsKEZuZDeAGa7xOAg__SUeFH_Q'

export const hasSupabaseConfig = true

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
