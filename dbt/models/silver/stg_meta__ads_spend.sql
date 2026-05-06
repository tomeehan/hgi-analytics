with raw as (
    select * from {{ source('bronze_meta_isclinical', 'ads_insights') }}
    where date_start is not null
),

base_daily as (
    select
        date_start as spend_date,
        sum(spend) as spend,
        sum(impressions) as impressions,
        sum(clicks) as clicks
    from raw
    group by date_start
),

purchases_daily as (
    select
        r.date_start as spend_date,
        sum(case when a.value:action_type::string = 'purchase'
                 then a.value:value::float else 0 end) as purchases
    from raw r,
         lateral flatten(input => r.actions, outer => true) a
    group by r.date_start
),

purchase_value_daily as (
    select
        r.date_start as spend_date,
        sum(case when av.value:action_type::string = 'purchase'
                 then av.value:value::float else 0 end) as purchase_value
    from raw r,
         lateral flatten(input => r.action_values, outer => true) av
    group by r.date_start
),

isclinical as (
    select
        b.spend_date,
        'isclinical' as store_id,
        b.spend,
        b.impressions,
        b.clicks,
        coalesce(p.purchases, 0) as purchases,
        coalesce(pv.purchase_value, 0) as purchase_value
    from base_daily b
    left join purchases_daily p using (spend_date)
    left join purchase_value_daily pv using (spend_date)
),

unioned as (
    select * from isclinical
)

select * from unioned
