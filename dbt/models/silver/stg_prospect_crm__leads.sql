with source as (
    select *,
        row_number() over (
            partition by leadid
            order by _airbyte_extracted_at desc
        ) as _rn
    from {{ source('bronze_prospect_crm', 'leads') }}
),

deduped as (
    select * from source where _rn = 1
),

renamed as (
    select
        leadid                                              as lead_id,
        contactid                                           as contact_id,
        ownerid                                             as owner_id,
        salespersonid                                       as salesperson_id,
        responsibleuser                                     as responsible_user,
        pipelineid                                          as pipeline_id,
        statusid                                            as status_id,
        statusdetailid                                      as status_detail_id,
        statusflag                                          as status_flag,
        sourceid                                            as source_id,
        sourceother                                         as source_other,
        typeid                                              as type_id,
        sizeid                                              as size_id,
        objectiveid                                         as objective_id,
        addressid                                           as address_id,
        divisionid                                          as division_id,
        value                                               as deal_value,
        bestvalue                                           as best_value,
        worstvalue                                          as worst_value,
        likelyvalue                                         as likely_value,
        weightedvalue                                       as weighted_value,
        marginvalue                                         as margin_value,
        guttometer                                          as gut_o_meter,
        utmsource                                           as utm_source,
        utmmedium                                           as utm_medium,
        utmname                                             as utm_campaign,
        utmterm                                             as utm_term,
        utmcontent                                          as utm_content,
        created                           as created_at,
        closedate                         as closed_at,
        estimatedclose                    as estimated_close_at,
        statuschanged                     as status_changed_at,
        lastactiveengagement              as last_active_engagement_at,
        firstactiveengagement             as first_active_engagement_at,
        lastupdatedtimestamp              as last_updated_at
    from deduped
)

select * from renamed
