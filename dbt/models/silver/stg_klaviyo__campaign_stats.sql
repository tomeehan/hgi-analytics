with isclinical as (
    select
        campaign_id::varchar                                as campaign_id,
        campaign_message_id::varchar                        as campaign_message_id,
        date::date                                          as stat_date,
        send_channel::varchar                               as send_channel,
        statistics:opens::number                            as opens,
        statistics:unique_opens::number                     as unique_opens,
        statistics:clicks::number                           as clicks,
        statistics:unique_clicks::number                    as unique_clicks,
        statistics:delivered::number                        as delivered,
        statistics:bounced::number                          as bounced,
        statistics:unsubscribed::number                     as unsubscribed,
        statistics:revenue::float                           as revenue,
        statistics:spam_complaints::number                  as spam_complaints,
        'isclinical'                                        as store_id
    from {{ source('bronze_klaviyo_isclinical', 'campaign_values_reports') }}
    where _airbyte_meta:changes is null
       or array_size(_airbyte_meta:changes) = 0
),

deese_pro as (
    select
        campaign_id::varchar                                as campaign_id,
        campaign_message_id::varchar                        as campaign_message_id,
        date::date                                          as stat_date,
        send_channel::varchar                               as send_channel,
        statistics:opens::number                            as opens,
        statistics:unique_opens::number                     as unique_opens,
        statistics:clicks::number                           as clicks,
        statistics:unique_clicks::number                    as unique_clicks,
        statistics:delivered::number                        as delivered,
        statistics:bounced::number                          as bounced,
        statistics:unsubscribed::number                     as unsubscribed,
        statistics:revenue::float                           as revenue,
        statistics:spam_complaints::number                  as spam_complaints,
        'deese_pro'                                         as store_id
    from {{ source('bronze_klaviyo_deese_pro', 'campaign_values_reports') }}
    where _airbyte_meta:changes is null
       or array_size(_airbyte_meta:changes) = 0
),

harper_grace as (
    select
        campaign_id::varchar                                as campaign_id,
        campaign_message_id::varchar                        as campaign_message_id,
        date::date                                          as stat_date,
        send_channel::varchar                               as send_channel,
        statistics:opens::number                            as opens,
        statistics:unique_opens::number                     as unique_opens,
        statistics:clicks::number                           as clicks,
        statistics:unique_clicks::number                    as unique_clicks,
        statistics:delivered::number                        as delivered,
        statistics:bounced::number                          as bounced,
        statistics:unsubscribed::number                     as unsubscribed,
        statistics:revenue::float                           as revenue,
        statistics:spam_complaints::number                  as spam_complaints,
        'harper_grace'                                      as store_id
    from {{ source('bronze_klaviyo_harper_grace', 'campaign_values_reports') }}
    where _airbyte_meta:changes is null
       or array_size(_airbyte_meta:changes) = 0
),

unioned as (
    select * from isclinical
    union all
    select * from deese_pro
    union all
    select * from harper_grace
)

select * from unioned
