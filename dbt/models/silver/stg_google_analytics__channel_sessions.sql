with isclinical as (
    select
        to_date(date, 'YYYYMMDD') as session_date,
        'isclinical' as store_id,
        case
            when sessiondefaultchannelgrouping = 'Direct'         then 'Direct'
            when sessiondefaultchannelgrouping = 'Organic Search' then 'Organic Search'
            when sessiondefaultchannelgrouping = 'Paid Search'    then 'Paid Search'
            when sessiondefaultchannelgrouping = 'Paid Social'    then 'Paid Social'
            when sessiondefaultchannelgrouping = 'Email'          then 'Email / CRM'
            when sessiondefaultchannelgrouping in ('Referral', 'Affiliates')
                                                                  then 'Referral / Affiliates'
            else 'Other'
        end as channel,
        sum(sessions) as sessions,
        sum(totalrevenue) as channel_revenue
    from {{ source('bronze_google_analytics_isclinical',
                   'traffic_acquisition_session_default_channel_grouping_report') }}
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
    channel,
    sessions,
    channel_revenue
from unioned
