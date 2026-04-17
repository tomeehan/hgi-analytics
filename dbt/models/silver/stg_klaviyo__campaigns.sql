with isclinical as (
    select
        id::varchar                                     as campaign_id,
        attributes:name::varchar                        as campaign_name,
        attributes:status::varchar                      as status,
        attributes:channel::varchar                     as channel,
        attributes:send_time::timestamp_tz              as send_time,
        attributes:created_at::timestamp_tz             as created_at,
        attributes:updated_at::timestamp_tz             as updated_at,
        attributes:audiences:included::variant          as audiences_included,
        'isclinical'                                    as store_id
    from {{ source('bronze_klaviyo_isclinical', 'campaigns') }}
    where _airbyte_meta:changes is null
       or array_size(_airbyte_meta:changes) = 0
),

deese_pro as (
    select
        id::varchar                                     as campaign_id,
        attributes:name::varchar                        as campaign_name,
        attributes:status::varchar                      as status,
        attributes:channel::varchar                     as channel,
        attributes:send_time::timestamp_tz              as send_time,
        attributes:created_at::timestamp_tz             as created_at,
        attributes:updated_at::timestamp_tz             as updated_at,
        attributes:audiences:included::variant          as audiences_included,
        'deese_pro'                                     as store_id
    from {{ source('bronze_klaviyo_deese_pro', 'campaigns') }}
    where _airbyte_meta:changes is null
       or array_size(_airbyte_meta:changes) = 0
),

unioned as (
    select * from isclinical
    union all
    select * from deese_pro
)

select * from unioned
