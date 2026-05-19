with isclinical as (
    select
        to_date(date, 'YYYYMMDD') as session_date,
        'isclinical' as store_id,
        sum(sessions) as sessions,
        sum(engagedsessions) as engaged_sessions,
        sum(totalrevenue) as total_revenue
    from {{ source('bronze_google_analytics_isclinical',
                   'traffic_acquisition_session_source_medium_report') }}
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
    sessions,
    engaged_sessions,
    total_revenue
from unioned
