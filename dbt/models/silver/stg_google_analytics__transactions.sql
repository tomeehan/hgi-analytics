-- Daily GA4 transaction count (purchase events) by store_id. Sourced from
-- the EVENTS_REPORT stream filtered to eventname='purchase'. eventcount is
-- the number of times the event fired on that date, which Google Analytics
-- equates to the transaction count for the purchase event.
--
-- Currently iS Clinical only; mirrors the connection coverage of
-- stg_google_analytics__sessions. Re-add brand CTEs here when their GA4
-- Airbyte connections land.

with isclinical as (
    select
        to_date(date, 'YYYYMMDD') as session_date,
        'isclinical' as store_id,
        sum(eventcount) as transactions
    from {{ source('bronze_google_analytics_isclinical', 'events_report') }}
    where date is not null and eventname = 'purchase'
    group by 1, 2
),

unioned as (
    select * from isclinical
)

select
    session_date,
    date_trunc('month', session_date)::date as order_month,
    store_id,
    transactions
from unioned
