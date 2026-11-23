-- Defence in depth (security review 2026-11-23): RLS already blocks these, but if RLS were ever disabled by mistake
-- the public API key must still see nothing. All access to these tables goes through SECURITY DEFINER functions.
revoke all on table job_secrets, job_state, studio_keys, room_alerts, contact_reveals,
                    pageviews, site_events, moderation_log from anon, authenticated;
-- listings / profiles / listing_photos / favorites / reports keep their grants: the site uses them under RLS policies.
