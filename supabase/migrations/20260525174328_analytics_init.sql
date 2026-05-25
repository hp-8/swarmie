-- Devices table: one row per unique browser fingerprint
create table public.devices (
  fingerprint_id text primary key,
  user_agent     text,
  platform       text,
  screen_res     text,
  timezone       text,
  first_seen_at  timestamptz not null default now(),
  last_seen_at   timestamptz not null default now()
);

-- Roast runs table: one row per roast job
create table public.roast_runs (
  id              bigint generated always as identity primary key,
  job_id          text not null unique,
  fingerprint_id  text references public.devices(fingerprint_id),
  status          text not null default 'started',
  agent_count     int,
  prompt_tokens   int default 0,
  completion_tokens int default 0,
  total_tokens    int default 0,
  cost_usd        numeric(10,6) default 0,
  model           text,
  pitch_length    int,
  error           text,
  started_at      timestamptz not null default now(),
  completed_at    timestamptz
);

-- PDF downloads table
create table public.pdf_downloads (
  id              bigint generated always as identity primary key,
  job_id          text not null references public.roast_runs(job_id),
  fingerprint_id  text references public.devices(fingerprint_id),
  downloaded_at   timestamptz not null default now()
);

-- Indexes
create index idx_roast_runs_fingerprint on public.roast_runs(fingerprint_id);
create index idx_roast_runs_started on public.roast_runs(started_at desc);
create index idx_pdf_downloads_job on public.pdf_downloads(job_id);

-- RLS: enable but allow anon inserts (public analytics, no auth)
alter table public.devices enable row level security;
alter table public.roast_runs enable row level security;
alter table public.pdf_downloads enable row level security;

-- Anon can insert (tracking) and select (reading own data by fingerprint)
create policy "anon_insert_devices" on public.devices for insert to anon with check (true);
create policy "anon_upsert_devices" on public.devices for update to anon using (true);
create policy "anon_read_devices" on public.devices for select to anon using (true);

create policy "anon_insert_runs" on public.roast_runs for insert to anon with check (true);
create policy "anon_update_runs" on public.roast_runs for update to anon using (true);
create policy "anon_read_runs" on public.roast_runs for select to anon using (true);

create policy "anon_insert_downloads" on public.pdf_downloads for insert to anon with check (true);
create policy "anon_read_downloads" on public.pdf_downloads for select to anon using (true);
