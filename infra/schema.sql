CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS teams (
  id serial PRIMARY KEY,
  fifa_code text,
  name text NOT NULL UNIQUE,
  aliases text[] DEFAULT '{}',
  confederation text,
  current_fifa_rank integer,
  current_elo double precision
);

CREATE TABLE IF NOT EXISTS matches (
  id serial PRIMARY KEY,
  source text,
  source_match_id text,
  date timestamptz,
  tournament text,
  stage text,
  group_name text,
  home_team_id integer REFERENCES teams(id),
  away_team_id integer REFERENCES teams(id),
  neutral boolean DEFAULT true,
  venue text,
  city text,
  country text,
  home_score integer,
  away_score integer,
  status text NOT NULL DEFAULT 'scheduled',
  UNIQUE (source, source_match_id)
);

CREATE TABLE IF NOT EXISTS model_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at timestamptz NOT NULL DEFAULT now(),
  git_sha text,
  train_data_until date,
  model_type text NOT NULL,
  metrics jsonb NOT NULL DEFAULT '{}',
  artifact_path text,
  is_active boolean NOT NULL DEFAULT false
);

CREATE TABLE IF NOT EXISTS predictions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  model_run_id uuid REFERENCES model_runs(id),
  match_id integer REFERENCES matches(id),
  predicted_at timestamptz NOT NULL DEFAULT now(),
  p_home_win double precision NOT NULL,
  p_draw double precision NOT NULL,
  p_away_win double precision NOT NULL,
  lambda_home double precision,
  lambda_away double precision,
  score_distribution jsonb NOT NULL DEFAULT '{}',
  explanation jsonb NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS simulation_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  model_run_id uuid REFERENCES model_runs(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  n_sims integer NOT NULL,
  result jsonb NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS odds_snapshots (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  match_id integer REFERENCES matches(id),
  bookmaker text NOT NULL,
  market text NOT NULL,
  home_odds double precision,
  draw_odds double precision,
  away_odds double precision,
  over_under_lines jsonb NOT NULL DEFAULT '{}',
  captured_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(date);
CREATE INDEX IF NOT EXISTS idx_predictions_match_id ON predictions(match_id);
CREATE INDEX IF NOT EXISTS idx_odds_snapshots_match_market ON odds_snapshots(match_id, market, captured_at DESC);

CREATE TABLE IF NOT EXISTS tournament_tips (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  phase text NOT NULL,
  question_key text NOT NULL,
  question_label text NOT NULL,
  answer jsonb NOT NULL,
  confidence double precision NOT NULL DEFAULT 0,
  generated_at timestamptz NOT NULL DEFAULT now(),
  model_version text NOT NULL DEFAULT 'baseline-strength-v1',
  source_state jsonb NOT NULL DEFAULT '{}',
  UNIQUE (phase, question_key)
);

CREATE INDEX IF NOT EXISTS idx_tournament_tips_phase ON tournament_tips(phase, generated_at DESC);
