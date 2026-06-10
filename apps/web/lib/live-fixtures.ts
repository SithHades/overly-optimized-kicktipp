export type LiveFixtureExportRow = {
  id: number;
  source: string;
  source_match_id: string;
  date: string;
  stage: string;
  group_name: string | null;
  home_team: string;
  away_team: string;
  venue: string | null;
  status: string;
  home_score: number | null;
  away_score: number | null;
};

export type LiveFixtureExport = {
  exported_at: string | null;
  fixtures: LiveFixtureExportRow[];
};

export type ApiMatchListResponse = {
  matches: {
    id: number;
    source: string | null;
    source_match_id: string | null;
    date: string;
    stage: string;
    group_name: string | null;
    home_team: { id: number | null; name: string };
    away_team: { id: number | null; name: string };
    venue: string | null;
    status: string;
  }[];
};
