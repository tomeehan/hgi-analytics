{{ config(materialized='table') }}

with shopify_per_store as (
    -- Aggregate Shopify customers to (email, store_id) since the same email
    -- can have multiple customer_id rows in a single store.
    select
        email,
        store_id,
        sum(coalesce(total_spent, 0))           as total_spent,
        sum(coalesce(orders_count, 0))          as orders_count,
        boolor_agg(coalesce(accepts_marketing, false))
                                                as accepts_marketing,
        max(updated_at)                         as last_updated_at,
        max(first_name)                         as first_name,
        max(last_name)                          as last_name
    from {{ ref('stg_shopify__customers') }}
    where email is not null
    group by email, store_id
),

shopify_isclinical as (
    select email, total_spent, orders_count, accepts_marketing, first_name, last_name
    from shopify_per_store
    where store_id = 'isclinical'
),

shopify_deese_pro as (
    select email, total_spent, orders_count, accepts_marketing, first_name, last_name
    from shopify_per_store
    where store_id = 'deese_pro'
),

crm_ledger_ranked as (
    -- One ledger per email; if multiple, pick the most recently updated.
    select
        email,
        sales_ledger_id,
        customer_name,
        country,
        is_b2c,
        balance,
        credit_limit,
        currency_code,
        last_invoice_at,
        row_number() over (
            partition by email
            order by last_updated_at desc nulls last, sales_ledger_id
        ) as _rn
    from {{ ref('stg_prospect_crm__sales_ledgers') }}
    where email is not null
),

crm_ledger as (
    select * from crm_ledger_ranked where _rn = 1
),

crm_contact_ranked as (
    select
        email,
        contact_id,
        full_name,
        klaviyo_id,
        opt_in,
        row_number() over (
            partition by email
            order by last_updated_at desc nulls last, contact_id
        ) as _rn
    from {{ ref('stg_prospect_crm__contacts') }}
    where email is not null
),

crm_contact as (
    select * from crm_contact_ranked where _rn = 1
),

all_emails as (
    select email from crm_ledger
    union
    select email from crm_contact
    union
    select email from shopify_isclinical
    union
    select email from shopify_deese_pro
),

joined as (
    select
        e.email,
        coalesce(
            cl.customer_name,
            cc.full_name,
            trim(coalesce(si.first_name, sd.first_name, '') || ' ' ||
                 coalesce(si.last_name,  sd.last_name,  ''))
        )                                                       as display_name,
        cl.country,

        -- CRM presence
        cl.sales_ledger_id                                      as crm_sales_ledger_id,
        cc.contact_id                                           as crm_contact_id,
        cc.klaviyo_id,
        cl.balance                                              as crm_balance,
        cl.credit_limit                                         as crm_credit_limit,
        cl.currency_code                                        as crm_currency_code,
        cl.last_invoice_at                                      as crm_last_invoice_at,
        cc.opt_in                                               as crm_opt_in,
        case
            when cl.email is null then null
            when cl.is_b2c then 'b2c'
            else 'b2b'
        end                                                     as seen_in_crm,

        -- Shopify presence
        (si.email is not null)                                  as seen_in_shopify_isclinical,
        (sd.email is not null)                                  as seen_in_shopify_deese_pro,
        coalesce(si.total_spent, 0)                             as shopify_isclinical_total_spent,
        coalesce(si.orders_count, 0)                            as shopify_isclinical_orders_count,
        coalesce(sd.total_spent, 0)                             as shopify_deese_pro_total_spent,
        coalesce(sd.orders_count, 0)                            as shopify_deese_pro_orders_count,
        coalesce(si.total_spent, 0) + coalesce(sd.total_spent, 0)
                                                                as total_shopify_spend,
        coalesce(si.orders_count, 0) + coalesce(sd.orders_count, 0)
                                                                as total_shopify_orders,
        coalesce(si.accepts_marketing, false) or coalesce(sd.accepts_marketing, false)
                                                                as accepts_marketing
    from all_emails e
    left join crm_ledger        cl on cl.email = e.email
    left join crm_contact       cc on cc.email = e.email
    left join shopify_isclinical si on si.email = e.email
    left join shopify_deese_pro  sd on sd.email = e.email
),

with_universe as (
    select
        *,
        case
            when seen_in_crm is not null
                and (seen_in_shopify_isclinical or seen_in_shopify_deese_pro)
                then 'crm_and_shopify'
            when seen_in_crm is not null
                then 'crm_only'
            when seen_in_shopify_isclinical and seen_in_shopify_deese_pro
                then 'both_shopify_stores'
            when seen_in_shopify_isclinical
                then 'shopify_isclinical_only'
            when seen_in_shopify_deese_pro
                then 'shopify_deese_pro_only'
            else 'unknown'
        end                                                     as customer_universe,
        split_part(email, '@', 2)                               as email_domain
    from joined
),

-- A "business-looking" email is one not from a known consumer provider and
-- not from a spam/throwaway TLD. Used as a proxy for "this email belongs
-- to a business" — imperfect but cheap. Tune the consumer list as needed.
with_email_class as (
    select
        *,
        case
            when email_domain is null or email_domain = '' then false
            when email_domain like '%.fun' then false
            when email_domain like '%.in.net' then false
            when email_domain in (
                'gmail.com','googlemail.com',
                'yahoo.com','yahoo.co.uk','yahoo.co.jp',
                'hotmail.com','hotmail.co.uk','outlook.com','outlook.co.uk',
                'live.com','live.co.uk','msn.com',
                'icloud.com','me.com','mac.com',
                'aol.com','aim.com','ymail.com','rocketmail.com',
                'btinternet.com','btopenworld.com','blueyonder.co.uk',
                'virginmedia.com','virgin.net','sky.com','ntlworld.com',
                'talktalk.net','tiscali.co.uk',
                'mail.com','gmx.com','gmx.de','gmx.co.uk',
                'protonmail.com','proton.me','pm.me',
                'fastmail.com','fastmail.fm',
                'yandex.com','yandex.ru','mail.ru','rambler.ru','ukr.net',
                'web.de','t-online.de','freenet.de',
                '163.com','qq.com','sina.com','naver.com','daum.net',
                'orange.fr','wanadoo.fr','laposte.net'
            ) then false
            else true
        end                                                     as is_likely_business_email
    from with_universe
),

with_lead_flag as (
    select
        *,
        -- A "DTC → B2B lead": looks like a business buyer, has actually
        -- purchased on a Shopify DTC store, and isn't yet known to the CRM.
        (is_likely_business_email
            and seen_in_crm is null
            and (seen_in_shopify_isclinical or seen_in_shopify_deese_pro)
            and total_shopify_spend > 0)                        as is_dtc_b2b_lead
    from with_email_class
)

select * from with_lead_flag
