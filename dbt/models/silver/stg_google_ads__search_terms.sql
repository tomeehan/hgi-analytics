-- iS Clinical Google Ads search-term performance, one row per
-- (search_date, search_term). Sourced from the Airbyte Google Ads
-- search-query stream (BRONZE_GOOGLE_ADS_ISCLINICAL.ADS_SEARCHQUERYSTATS_*),
-- which lands one row per (day, search term, ad group, campaign, ...).
-- We aggregate that to the (day, search term) grain.
--
-- cost is converted from micros: Google Ads reports cost_micros, GBP cost
-- = cost_micros / 1e6.
--
-- brand_intent is a name-pattern classification of the search term text,
-- not a native Google Ads field. See CLAUDE.md -> "Google Ads brand_intent
-- classification". A term is "branded" if it contains the brand name, a
-- common misspelling, or an iS Clinical product name; everything else is
-- "non_branded" (generic acquisition intent). The classifier is matched
-- against the lower-cased, trimmed search term.

{% set brand_intent_case %}
    case
        when search_term like '%is clinical%'
          or search_term like '%isclinical%'
          or search_term like '%is-clinical%'
          -- truncated / misspelt brand stems
          or search_term like '%is clini%'
          or search_term like '%isclinic%'
          or search_term like '%is clin%'
          or search_term like '%es clinical%'
          or search_term like '%is skin%'
          -- iS Clinical product names appearing without the brand prefix
          or search_term like '%cleansing complex%'
          or search_term like '%pro heal serum%'
          or search_term like '%pro heal%'
          or search_term like '%hydra cool serum%'
          or search_term like '%hydracool serum%'
          or search_term like '%active serum%'
          or search_term like '%super serum%'
          or search_term like '%sheald%'
          or search_term like '%shield recovery balm%'
          or search_term like '%youth eye complex%'
          or search_term like '%youth intensive creme%'
          or search_term like '%warming honey cleanser%'
          or search_term like '%honey cleanser%'
          or search_term like '%reparative moisture emulsion%'
          or search_term like '%moisturizing complex%'
          or search_term like '%moisturising complex%'
          or search_term like '%genexc%'
          or search_term like '%flash brightening peel%'
          or search_term like '%active peel system%'
            then 'branded'
        else 'non_branded'
    end
{% endset %}

with source as (

    select
        try_to_date(left(segments_date, 10), 'YYYY-MM-DD') as search_date,
        lower(trim(search_term_view_search_term))          as search_term,
        metrics_clicks                                     as clicks,
        metrics_cost_micros / 1e6                          as cost,
        metrics_conversions                                as conversions
    from {{ source('bronze_google_ads_isclinical', 'search_query_stats') }}
    where segments_date is not null
      and search_term_view_search_term is not null

),

aggregated as (

    select
        search_date,
        search_term,
        sum(clicks)      as clicks,
        sum(cost)        as cost,
        sum(conversions) as conversions
    from source
    group by search_date, search_term

)

select
    search_date,
    search_term,
    date_trunc('month', search_date)::date           as order_month,
    to_char(date_trunc('month', search_date), 'YYYY-MM') as order_month_label,
    'isclinical'                                     as store_id,
    {{ brand_intent_case }}                          as brand_intent,
    clicks,
    cost,
    conversions
from aggregated
