-- GA4 traffic-acquisition sessions at session_date x store_id x source/medium
-- grain. The sibling stg_google_analytics__sessions collapses source/medium
-- away (date grain only); this model keeps it, so dashboards can rank traffic
-- by source/medium. transactions is not emitted: the source/medium Bronze
-- report has no purchase-event count, and no GA4 events report carries the
-- source/medium dimension, so a per-source/medium transaction count cannot be
-- derived. See ticket 008 for the data-engineering prerequisite.
--
-- Currently iS Clinical only; mirrors the connection coverage of
-- stg_google_analytics__sessions. Re-add brand CTEs here when their GA4
-- Airbyte connections land.

with isclinical as (
    select
        to_date(date, 'YYYYMMDD') as session_date,
        'isclinical' as store_id,
        sessionsource || ' / ' || sessionmedium as source_medium,
        sum(sessions) as sessions,
        sum(totalrevenue) as revenue
    from {{ source('bronze_google_analytics_isclinical',
                   'traffic_acquisition_session_source_medium_report') }}
    where date is not null
    group by 1, 2, 3
),

unioned as (
    select * from isclinical
)

select
    session_date,
    date_trunc('month', session_date)::date as order_month,
    store_id,
    source_medium,
    sessions,
    revenue
from unioned
