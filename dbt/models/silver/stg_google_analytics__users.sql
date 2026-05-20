-- Daily GA4 total users by store_id. Sourced from the WEBSITE_OVERVIEW
-- stream, which carries GA4's session-level traffic overview metrics
-- (sessions, totalusers, newusers, bounce rate). totalusers is GA4's
-- distinct-user count for the date.
--
-- Currently iS Clinical only; mirrors the connection coverage of
-- stg_google_analytics__sessions. Re-add brand CTEs here when their GA4
-- Airbyte connections land.

with isclinical as (
    select
        to_date(date, 'YYYYMMDD') as session_date,
        'isclinical' as store_id,
        sum(totalusers) as users
    from {{ source('bronze_google_analytics_isclinical', 'website_overview') }}
    where date is not null
    group by 1, 2
),

unioned as (
    select * from isclinical
)

select
    session_date,
    date_trunc('month', session_date)::date as order_month,
    store_id,
    users
from unioned
